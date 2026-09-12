using System.Globalization;
using System.IO;
using System.Text.Json;
using SharpDX;
using SharpDX.Direct3D9;

namespace CFRezManager;

internal static class FxoInspectCommand
{
    public static bool IsInvocation(string[] args)
    {
        return args.Length > 0 &&
               (string.Equals(args[0], "--inspect-fxo", StringComparison.OrdinalIgnoreCase) ||
                string.Equals(args[0], "inspect-fxo", StringComparison.OrdinalIgnoreCase));
    }

    public static int Run(string[] args)
    {
        try
        {
            if (args.Length < 3)
            {
                throw new InvalidOperationException("Usage: --inspect-fxo <input.fxo> <output.json>");
            }

            string input = Path.GetFullPath(args[1]);
            string output = Path.GetFullPath(args[2]);
            if (!File.Exists(input))
            {
                throw new FileNotFoundException("FXO input does not exist.", input);
            }

            byte[] data = File.ReadAllBytes(input);
            object report = Inspect(input, data);
            string? directory = Path.GetDirectoryName(output);
            if (!string.IsNullOrWhiteSpace(directory))
            {
                Directory.CreateDirectory(directory);
            }

            File.WriteAllText(output, JsonSerializer.Serialize(report, new JsonSerializerOptions { WriteIndented = true }) + Environment.NewLine);
            Console.WriteLine($"Report: {output}");
            return 0;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine(ex.Message);
            if (ex.InnerException is not null)
            {
                Console.Error.WriteLine(ex.InnerException.Message);
            }

            return 1;
        }
    }

    private static object Inspect(string inputPath, byte[] data)
    {
        var attempts = new List<object>();
        Direct3D? d3d = null;
        Device? device = null;
        Effect? effect = null;
        try
        {
            d3d = new Direct3D();
            PresentParameters present = CreatePresentParameters();
            Exception? last = null;
            foreach (DeviceType deviceType in new[] { DeviceType.NullReference, DeviceType.Hardware, DeviceType.Reference })
            {
                try
                {
                    device?.Dispose();
                    device = new Device(d3d, 0, deviceType, IntPtr.Zero, CreateFlags.SoftwareVertexProcessing, present);
                    attempts.Add(new { device_type = deviceType.ToString(), ok = true });
                    last = null;
                    break;
                }
                catch (Exception ex)
                {
                    last = ex;
                    attempts.Add(new
                    {
                        device_type = deviceType.ToString(),
                        ok = false,
                        error = ex.Message,
                        hresult = (ex as SharpDXException)?.ResultCode.Code.ToString("X8", CultureInfo.InvariantCulture)
                    });
                }
            }

            if (device is null)
            {
                throw new InvalidOperationException("Failed to create a D3D9 device for FXO inspection.", last);
            }

            try
            {
                effect = Effect.FromMemory(device, data, ShaderFlags.None);
            }
            catch (Exception ex)
            {
                throw new InvalidOperationException(
                    $"D3DXCreateEffect/FromMemory failed: {ex.Message} HRESULT={(ex as SharpDXException)?.ResultCode.Code.ToString("X8", CultureInfo.InvariantCulture)}",
                    ex);
            }

            return new
            {
                schema = "cf2.d3d9-effect-inspect.v1",
                input = inputPath,
                byte_count = data.Length,
                device_attempts = attempts,
                description = DescribeEffect(effect),
                parameters = EnumerateParameters(effect),
                techniques = EnumerateTechniques(effect)
            };
        }
        finally
        {
            effect?.Dispose();
            device?.Dispose();
            d3d?.Dispose();
        }
    }

    private static PresentParameters CreatePresentParameters()
    {
        return new PresentParameters
        {
            BackBufferWidth = 1,
            BackBufferHeight = 1,
            BackBufferFormat = Format.Unknown,
            DeviceWindowHandle = IntPtr.Zero,
            Windowed = true,
            SwapEffect = SwapEffect.Discard,
            PresentationInterval = PresentInterval.Immediate
        };
    }

    private static object DescribeEffect(Effect effect)
    {
        EffectDescription description = effect.Description;
        return new
        {
            creator = description.Creator,
            parameters = description.Parameters,
            techniques = description.Techniques,
            functions = description.Functions
        };
    }

    private static List<object> EnumerateParameters(Effect effect)
    {
        var rows = new List<object>();
        for (int index = 0; index < effect.Description.Parameters; index++)
        {
            EffectHandle handle = effect.GetParameter(null, index);
            ParameterDescription description = effect.GetParameterDescription(handle);
            rows.Add(new
            {
                index,
                name = description.Name,
                semantic = description.Semantic,
                class_name = description.Class.ToString(),
                type = description.Type.ToString(),
                rows = description.Rows,
                columns = description.Columns,
                elements = description.Elements,
                annotations = description.Annotations,
                struct_members = description.StructMembers,
                value = TryReadValue(effect, handle, description)
            });
        }

        return rows;
    }

    private static List<object> EnumerateTechniques(Effect effect)
    {
        var rows = new List<object>();
        for (int techniqueIndex = 0; techniqueIndex < effect.Description.Techniques; techniqueIndex++)
        {
            EffectHandle technique = effect.GetTechnique(techniqueIndex);
            TechniqueDescription techniqueDescription = effect.GetTechniqueDescription(technique);
            var passes = new List<object>();
            for (int passIndex = 0; passIndex < techniqueDescription.Passes; passIndex++)
            {
                EffectHandle pass = effect.GetPass(technique, passIndex);
                PassDescription passDescription = effect.GetPassDescription(pass);
                passes.Add(new { index = passIndex, name = passDescription.Name, annotations = passDescription.Annotations });
            }

            rows.Add(new
            {
                index = techniqueIndex,
                name = techniqueDescription.Name,
                passes = techniqueDescription.Passes,
                annotations = techniqueDescription.Annotations,
                pass_list = passes
            });
        }

        return rows;
    }

    private static object? TryReadValue(Effect effect, EffectHandle handle, ParameterDescription description)
    {
        try
        {
            if (description.Class == ParameterClass.Scalar && description.Type == ParameterType.Float)
            {
                return effect.GetValue<float>(handle);
            }

            if (description.Class == ParameterClass.Scalar && description.Type == ParameterType.Int)
            {
                return effect.GetValue<int>(handle);
            }

            if (description.Class == ParameterClass.Scalar && description.Type == ParameterType.Bool)
            {
                return effect.GetValue<bool>(handle);
            }

            if (description.Class == ParameterClass.Vector && description.Type == ParameterType.Float)
            {
                SharpDX.Mathematics.Interop.RawVector4 vector = effect.GetValue<SharpDX.Mathematics.Interop.RawVector4>(handle);
                return new[] { vector.X, vector.Y, vector.Z, vector.W };
            }

            if (description.Type == ParameterType.Texture ||
                description.Type == ParameterType.Texture1D ||
                description.Type == ParameterType.Texture2D ||
                description.Type == ParameterType.Texture3D ||
                description.Type == ParameterType.TextureCube)
            {
                return new { kind = "texture_slot", type = description.Type.ToString() };
            }
        }
        catch (Exception ex)
        {
            return new { read_error = ex.Message };
        }

        return null;
    }

}
