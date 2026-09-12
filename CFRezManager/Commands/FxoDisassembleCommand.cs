using System.Globalization;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text.Json;
using SharpDX;
using SharpDX.Direct3D9;

namespace CFRezManager;

internal static class FxoDisassembleCommand
{
    public static bool IsInvocation(string[] args)
    {
        return args.Length > 0 &&
               (string.Equals(args[0], "--disassemble-fxo", StringComparison.OrdinalIgnoreCase) ||
                string.Equals(args[0], "disassemble-fxo", StringComparison.OrdinalIgnoreCase));
    }

    public static int Run(string[] args)
    {
        try
        {
            if (args.Length < 4)
            {
                throw new InvalidOperationException("Usage: --disassemble-fxo <input.fxo> <output.json> <asm_dir>");
            }

            string input = Path.GetFullPath(args[1]);
            string output = Path.GetFullPath(args[2]);
            string asmDir = Path.GetFullPath(args[3]);
            if (!File.Exists(input))
            {
                throw new FileNotFoundException("FXO input does not exist.", input);
            }

            byte[] data = File.ReadAllBytes(input);
            object report = Disassemble(input, data, asmDir);
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

    private static object Disassemble(string inputPath, byte[] data, string asmDir)
    {
        Directory.CreateDirectory(asmDir);
        var uniqueDir = Path.Combine(asmDir, "unique");
        Directory.CreateDirectory(uniqueDir);

        Direct3D? d3d = null;
        Device? device = null;
        Effect? effect = null;
        var attempts = new List<object>();
        try
        {
            d3d = new Direct3D();
            PresentParameters present = new PresentParameters
            {
                BackBufferWidth = 1,
                BackBufferHeight = 1,
                BackBufferFormat = Format.Unknown,
                DeviceWindowHandle = IntPtr.Zero,
                Windowed = true,
                SwapEffect = SwapEffect.Discard,
                PresentationInterval = PresentInterval.Immediate
            };

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
                throw new InvalidOperationException("Failed to create a D3D9 device for FXO disassembly.", last);
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

            var uniqueShaders = new Dictionary<string, object>(StringComparer.OrdinalIgnoreCase);
            object effectDisassembly = TryDisassembleEffect(effect, asmDir);
            var techniques = new List<object>();

            for (int techniqueIndex = 0; techniqueIndex < effect.Description.Techniques; techniqueIndex++)
            {
                EffectHandle technique = effect.GetTechnique(techniqueIndex);
                TechniqueDescription techniqueDescription = effect.GetTechniqueDescription(technique);
                var passes = new List<object>();
                for (int passIndex = 0; passIndex < techniqueDescription.Passes; passIndex++)
                {
                    EffectHandle pass = effect.GetPass(technique, passIndex);
                    PassDescription passDescription = effect.GetPassDescription(pass);
                    passes.Add(new
                    {
                        index = passIndex,
                        name = passDescription.Name,
                        annotations = passDescription.Annotations,
                        vs = CaptureShader(passDescription.PVertexShaderFunction, "vs", uniqueDir, uniqueShaders),
                        ps = CaptureShader(passDescription.PPixelShaderFunction, "ps", uniqueDir, uniqueShaders)
                    });
                }

                techniques.Add(new
                {
                    index = techniqueIndex,
                    name = techniqueDescription.Name,
                    passes = techniqueDescription.Passes,
                    annotations = techniqueDescription.Annotations,
                    pass_list = passes
                });
            }

            return new
            {
                schema = "cf2.d3d9-effect-disassemble.v1",
                input = inputPath,
                byte_count = data.Length,
                device_attempts = attempts,
                effect_disassembly = effectDisassembly,
                unique_shader_count = uniqueShaders.Count,
                unique_shaders = uniqueShaders.Values.ToList(),
                techniques
            };
        }
        finally
        {
            effect?.Dispose();
            device?.Dispose();
            d3d?.Dispose();
        }
    }

    [DllImport("d3dx9_43.dll", CallingConvention = CallingConvention.StdCall)]
    private static extern int D3DXDisassembleEffect(IntPtr pEffect, int enableColorCode, out IntPtr ppDisassembly);

    [ComImport]
    [Guid("8BA5FB08-5195-40e2-AC58-0D989C3A0102")]
    [InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    private interface ID3DXBuffer
    {
        IntPtr GetBufferPointer();
        int GetBufferSize();
    }

    private static object TryDisassembleEffect(Effect effect, string asmDir)
    {
        IntPtr blobPtr = IntPtr.Zero;
        try
        {
            int hr = D3DXDisassembleEffect(effect.NativePointer, 0, out blobPtr);
            if (hr < 0)
            {
                return new { ok = false, error = "D3DXDisassembleEffect failed", hresult = hr.ToString("X8", CultureInfo.InvariantCulture) };
            }

            var buffer = (ID3DXBuffer)Marshal.GetObjectForIUnknown(blobPtr);
            string text = Marshal.PtrToStringAnsi(buffer.GetBufferPointer(), buffer.GetBufferSize())?.TrimEnd('\0') ?? string.Empty;
            string relative = "effect_disassembly.asm";
            File.WriteAllText(Path.Combine(asmDir, relative), text);
            return new { ok = true, path = relative, chars = text.Length };
        }
        catch (Exception ex)
        {
            return new
            {
                ok = false,
                error = ex.Message,
                hresult = (ex as SharpDXException)?.ResultCode.Code.ToString("X8", CultureInfo.InvariantCulture)
            };
        }
        finally
        {
            if (blobPtr != IntPtr.Zero)
            {
                Marshal.Release(blobPtr);
            }
        }
    }

    private static object CaptureShader(IntPtr function, string kind, string uniqueDir, Dictionary<string, object> uniqueShaders)
    {
        if (function == IntPtr.Zero)
        {
            return new { present = false };
        }

        try
        {
            int size = ShaderBytecode.GetShaderSize(function);
            byte[] bytes = ReadPointer(function, size);
            using var bytecode = new ShaderBytecode(bytes);
            string sha = Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant();
            string fileName = $"{sha[..16]}_{kind}.asm";
            if (!uniqueShaders.ContainsKey(sha))
            {
                string asm = bytecode.Disassemble();
                File.WriteAllText(Path.Combine(uniqueDir, fileName), asm);
                uniqueShaders[sha] = new
                {
                    sha256 = sha,
                    kind,
                    byte_count = bytes.Length,
                    version = DescribeVersion(bytes),
                    file = "unique/" + fileName,
                    samplers = TryGetSamplers(bytecode),
                    constants = TryGetConstants(bytecode)
                };
            }

            return new
            {
                present = true,
                sha256 = sha,
                byte_count = bytes.Length,
                file = "unique/" + fileName
            };
        }
        catch (Exception ex)
        {
            return new
            {
                present = true,
                error = ex.Message,
                hresult = (ex as SharpDXException)?.ResultCode.Code.ToString("X8", CultureInfo.InvariantCulture)
            };
        }
    }

    private static object TryGetSamplers(ShaderBytecode bytecode)
    {
        try
        {
            string[]? names = bytecode.GetSamplers();
            return names ?? Array.Empty<string>();
        }
        catch (Exception ex)
        {
            return new { error = ex.Message };
        }
    }

    private static object TryGetConstants(ShaderBytecode bytecode)
    {
        try
        {
            ConstantTable? table = bytecode.ConstantTable;
            if (table is null)
            {
                return Array.Empty<object>();
            }

            ConstantTableDescription description = table.Description;
            var rows = new List<object>();
            for (int index = 0; index < description.Constants; index++)
            {
                EffectHandle handle = table.GetConstant(null, index);
                ConstantDescription constant = table.GetConstantDescription(handle);
                int samplerIndex = -1;
                try
                {
                    samplerIndex = table.GetSamplerIndex(handle);
                }
                catch
                {
                    samplerIndex = -1;
                }

                rows.Add(new
                {
                    name = constant.Name,
                    register_set = constant.RegisterSet.ToString(),
                    register_index = constant.RegisterIndex,
                    register_count = constant.RegisterCount,
                    class_name = constant.Class.ToString(),
                    type = constant.Type.ToString(),
                    rows = constant.Rows,
                    columns = constant.Columns,
                    elements = constant.Elements,
                    bytes = constant.Bytes,
                    sampler_index = samplerIndex
                });
            }

            return rows;
        }
        catch (Exception ex)
        {
            return new { error = ex.Message };
        }
    }

    private static string DescribeVersion(byte[] bytes)
    {
        if (bytes.Length < 4)
        {
            return "unknown";
        }

        uint token = BitConverter.ToUInt32(bytes, 0);
        uint kind = token >> 16;
        uint major = (token >> 8) & 0xFFu;
        uint minor = token & 0xFFu;
        string prefix = kind == 0xFFFE ? "vs" : kind == 0xFFFF ? "ps" : $"unk_{kind:X4}";
        return $"{prefix}_{major}_{minor}";
    }

    private static byte[] ReadPointer(IntPtr pointer, int size)
    {
        var bytes = new byte[size];
        Marshal.Copy(pointer, bytes, 0, size);
        return bytes;
    }
}
