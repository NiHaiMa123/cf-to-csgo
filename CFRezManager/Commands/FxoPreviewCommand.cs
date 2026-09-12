using System.Globalization;
using System.IO;
using System.Numerics;
using System.Runtime.InteropServices;
using System.Text.Json;
using System.Windows.Forms;
using SharpDX;
using SharpDX.Direct3D9;
using SharpDX.Mathematics.Interop;

namespace CFRezManager;

internal static class FxoPreviewCommand
{
    [StructLayout(LayoutKind.Sequential)]
    private struct MeshVertex
    {
        public Vector3 Position;
        public Vector3 Normal;
        public Vector2 Uv;
        public Vector3 Tangent;
        public Vector3 Bitangent;
    }

    public static bool IsInvocation(string[] args)
    {
        return args.Length > 0 &&
               (string.Equals(args[0], "--preview-fxo", StringComparison.OrdinalIgnoreCase) ||
                string.Equals(args[0], "preview-fxo", StringComparison.OrdinalIgnoreCase));
    }

    public static int Run(string[] args)
    {
        try
        {
            if (args.Length < 3)
            {
                throw new InvalidOperationException("Usage: --preview-fxo <config.json> <output_dir>");
            }

            string configPath = Path.GetFullPath(args[1]);
            string outputDir = Path.GetFullPath(args[2]);
            using JsonDocument document = JsonDocument.Parse(File.ReadAllText(configPath));
            Directory.CreateDirectory(outputDir);
            object report = Preview(document.RootElement, outputDir);
            File.WriteAllText(
                Path.Combine(outputDir, "preview.json"),
                JsonSerializer.Serialize(report, new JsonSerializerOptions { WriteIndented = true }) + Environment.NewLine);
            return 0;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine(ex);
            if (ex.InnerException is not null)
            {
                Console.Error.WriteLine(ex.InnerException);
            }

            return 1;
        }
    }

    private static object Preview(JsonElement config, string outputDir)
    {
        string fxo = config.GetProperty("fxo").GetString() ?? throw new InvalidOperationException("fxo");
        string obj = config.GetProperty("obj").GetString() ?? throw new InvalidOperationException("obj");
        string techniqueName = config.GetProperty("technique").GetString() ?? "tPlayerViewMeshAlphaAproxSnellTransformedCube";
        int passIndex = config.TryGetProperty("pass", out JsonElement passElement) ? passElement.GetInt32() : 0;
        int width = config.TryGetProperty("width", out JsonElement widthElement) ? widthElement.GetInt32() : 1280;
        int height = config.TryGetProperty("height", out JsonElement heightElement) ? heightElement.GetInt32() : 720;
        var skip = new List<string>();
        if (config.TryGetProperty("skip_groups", out JsonElement skipElement))
        {
            foreach (JsonElement item in skipElement.EnumerateArray())
            {
                skip.Add(item.GetString() ?? "");
            }
        }

        MeshVertex[] vertices = LoadWeaponObj(obj, skip, out int[] indices, out Vector3 center, out float radius);
        using var form = new Form
        {
            Text = "fxo-preview",
            ShowInTaskbar = false,
            FormBorderStyle = FormBorderStyle.None,
            StartPosition = FormStartPosition.Manual,
            Location = new System.Drawing.Point(-32000, -32000),
            ClientSize = new System.Drawing.Size(width, height)
        };
        form.Show();
        Application.DoEvents();

        Direct3D? d3d = null;
        Device? device = null;
        Effect? effect = null;
        var attempts = new List<object>();
        var textures = new List<Resource>();
        try
        {
            d3d = new Direct3D();
            PresentParameters present = new PresentParameters
            {
                BackBufferWidth = width,
                BackBufferHeight = height,
                BackBufferFormat = Format.A8R8G8B8,
                AutoDepthStencilFormat = Format.D24S8,
                EnableAutoDepthStencil = true,
                DeviceWindowHandle = form.Handle,
                Windowed = true,
                SwapEffect = SwapEffect.Discard,
                PresentationInterval = PresentInterval.Immediate
            };
            Exception? last = null;
            foreach (DeviceType deviceType in new[] { DeviceType.Hardware, DeviceType.Reference })
            {
                try
                {
                    device?.Dispose();
                    CreateFlags flags = deviceType == DeviceType.Hardware
                        ? CreateFlags.HardwareVertexProcessing
                        : CreateFlags.SoftwareVertexProcessing;
                    device = new Device(d3d, 0, deviceType, form.Handle, flags, present);
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
                throw new InvalidOperationException("Failed to create a renderable D3D9 device.", last);
            }

            effect = Effect.FromMemory(device, File.ReadAllBytes(fxo), ShaderFlags.None);
            EffectHandle technique = effect.GetTechnique(techniqueName);
            BindTextures(device, effect, config.GetProperty("textures"), textures);
            using VertexDeclaration declaration = new VertexDeclaration(device, new[]
            {
                new VertexElement(0, 0, DeclarationType.Float3, DeclarationMethod.Default, DeclarationUsage.Position, 0),
                new VertexElement(0, 12, DeclarationType.Float3, DeclarationMethod.Default, DeclarationUsage.Normal, 0),
                new VertexElement(0, 24, DeclarationType.Float2, DeclarationMethod.Default, DeclarationUsage.TextureCoordinate, 0),
                new VertexElement(0, 32, DeclarationType.Float3, DeclarationMethod.Default, DeclarationUsage.TextureCoordinate, 1),
                new VertexElement(0, 44, DeclarationType.Float3, DeclarationMethod.Default, DeclarationUsage.TextureCoordinate, 2),
                VertexElement.VertexDeclarationEnd
            });
            using var vertexBuffer = new VertexBuffer(device, vertices.Length * 56, Usage.WriteOnly, VertexFormat.None, Pool.Managed);
            using (DataStream stream = vertexBuffer.Lock(0, 0, LockFlags.None))
            {
                stream.WriteRange(vertices);
                vertexBuffer.Unlock();
            }

            using var indexBuffer = new IndexBuffer(device, indices.Length * 4, Usage.WriteOnly, Pool.Managed, false);
            using (DataStream stream = indexBuffer.Lock(0, 0, LockFlags.None))
            {
                stream.WriteRange(indices);
                indexBuffer.Unlock();
            }

            Vector3 eye = center + new Vector3(radius * 0.95f, radius * 0.28f, radius * 0.82f);
            Matrix4x4 world = Matrix4x4.Identity;
            Matrix4x4 view = LookAtLh(eye, center, Vector3.UnitY);
            Matrix4x4 projection = PerspectiveFovLh((float)Math.PI / 4f, width / (float)height, Math.Max(0.05f, radius * 0.01f), radius * 20f);
            Matrix4x4 viewProjection = view * projection;
            Vector3 light = Vector3.Normalize(new Vector3(0.35f, 0.85f, 0.4f));

            SetMatrix(effect, "WorldMatrix", world);
            SetMatrix(effect, "ViewMatrix", view);
            SetMatrix(effect, "ViewProjectionMatrix", viewProjection);
            SetMatrix(effect, "ProjectionMatrix", projection);
            SetMatrix(effect, "WorldViewMatrix", world * view);
            SetMatrix(effect, "WorldViewProjectionMatrix", world * viewProjection);
            SetFloat3(effect, "CameraPosition", eye);
            SetFloat3(effect, "LightDirection", light);
            SetFloat3(effect, "TransformedLitDirection", light);

            device.SetRenderState(RenderState.ZEnable, true);
            device.SetRenderState(RenderState.ZWriteEnable, true);
            device.SetRenderState(RenderState.CullMode, Cull.None);
            device.VertexDeclaration = declaration;
            device.SetStreamSource(0, vertexBuffer, 0, 56);
            device.Indices = indexBuffer;

            var shots = new List<object>();
            foreach (JsonElement shot in config.GetProperty("shots").EnumerateArray())
            {
                string name = shot.GetProperty("name").GetString() ?? "shot";
                if (shot.TryGetProperty("set", out JsonElement values))
                {
                    ApplyScalars(effect, values);
                }

                device.Clear(ClearFlags.Target | ClearFlags.ZBuffer, new RawColorBGRA(48, 48, 48, 255), 1f, 0);
                device.BeginScene();
                effect.Technique = technique;
                int passes = effect.Begin();
                int used = Math.Min(Math.Max(passIndex, 0), Math.Max(passes - 1, 0));
                effect.BeginPass(used);
                device.DrawIndexedPrimitive(PrimitiveType.TriangleList, 0, 0, vertices.Length, 0, indices.Length / 3);
                effect.EndPass();
                effect.End();
                device.EndScene();
                device.Present();

                string png = Path.Combine(outputDir, name + ".png");
                using (Surface back = device.GetBackBuffer(0, 0))
                {
                    Surface.ToFile(back, png, ImageFileFormat.Png);
                }

                shots.Add(new
                {
                    name,
                    png,
                    pass = used,
                    technique = techniqueName,
                    bytes = new FileInfo(png).Length
                });
            }

            return new
            {
                schema = "cf2.d3d9-fxo-preview.v1",
                fxo,
                obj,
                technique = techniqueName,
                vertex_count = vertices.Length,
                triangle_count = indices.Length / 3,
                center = new[] { center.X, center.Y, center.Z },
                radius,
                device_attempts = attempts,
                shots
            };
        }
        finally
        {
            foreach (Resource resource in textures)
            {
                resource.Dispose();
            }

            effect?.Dispose();
            device?.Dispose();
            d3d?.Dispose();
            form.Close();
        }
    }

    private static void BindTextures(Device device, Effect effect, JsonElement textures, List<Resource> keep)
    {
        foreach (JsonProperty property in textures.EnumerateObject())
        {
            string path = property.Value.GetString() ?? "";
            if (!File.Exists(path))
            {
                throw new FileNotFoundException("texture missing", path);
            }

            BaseTexture texture;
            if (property.Name.IndexOf("cube", StringComparison.OrdinalIgnoreCase) >= 0 ||
                path.EndsWith(".dds", StringComparison.OrdinalIgnoreCase))
            {
                try
                {
                    texture = CubeTexture.FromFile(device, path);
                }
                catch
                {
                    texture = Texture.FromFile(device, path);
                }
            }
            else
            {
                texture = Texture.FromFile(device, path);
            }

            keep.Add(texture);
            effect.SetTexture(property.Name, texture);
            try
            {
                effect.SetTexture(property.Name + "Sampler", texture);
            }
            catch
            {
                // Sampler parameter may be a sampler_state block, not a texture.
            }
        }
    }

    private static void ApplyScalars(Effect effect, JsonElement values)
    {
        foreach (JsonProperty property in values.EnumerateObject())
        {
            if (property.Value.ValueKind == JsonValueKind.True || property.Value.ValueKind == JsonValueKind.False)
            {
                SetBool(effect, property.Name, property.Value.GetBoolean());
            }
            else if (property.Value.ValueKind == JsonValueKind.Number)
            {
                SetFloat(effect, property.Name, property.Value.GetSingle());
            }
            else if (property.Value.ValueKind == JsonValueKind.Array)
            {
                float[] numbers = property.Value.EnumerateArray().Select(item => item.GetSingle()).ToArray();
                if (numbers.Length >= 4)
                {
                    effect.SetValue(property.Name, new RawVector4(numbers[0], numbers[1], numbers[2], numbers[3]));
                }
                else if (numbers.Length == 3)
                {
                    SetFloat3(effect, property.Name, new Vector3(numbers[0], numbers[1], numbers[2]));
                }
            }
        }
    }

    private static void SetFloat(Effect effect, string name, float value)
    {
        try
        {
            effect.SetValue(name, value);
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"set float {name}: {ex.Message}");
        }
    }

    private static void SetBool(Effect effect, string name, bool value)
    {
        try
        {
            effect.SetValue(name, value);
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"set bool {name}: {ex.Message}");
        }
    }

    private static void SetFloat3(Effect effect, string name, Vector3 value)
    {
        try
        {
            effect.SetValue(name, new RawVector4(value.X, value.Y, value.Z, 0f));
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"set float3 {name}: {ex.Message}");
        }
    }

    private static void SetMatrix(Effect effect, string name, Matrix4x4 value)
    {
        try
        {
            effect.SetValue(name, ToRawMatrix(value));
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"set matrix {name}: {ex.Message}");
        }
    }

    private static RawMatrix ToRawMatrix(Matrix4x4 m)
    {
        return new RawMatrix
        {
            M11 = m.M11, M12 = m.M12, M13 = m.M13, M14 = m.M14,
            M21 = m.M21, M22 = m.M22, M23 = m.M23, M24 = m.M24,
            M31 = m.M31, M32 = m.M32, M33 = m.M33, M34 = m.M34,
            M41 = m.M41, M42 = m.M42, M43 = m.M43, M44 = m.M44
        };
    }

    private static Matrix4x4 LookAtLh(Vector3 eye, Vector3 at, Vector3 up)
    {
        Vector3 z = Vector3.Normalize(at - eye);
        Vector3 x = Vector3.Normalize(Vector3.Cross(up, z));
        Vector3 y = Vector3.Cross(z, x);
        Matrix4x4 m = Matrix4x4.Identity;
        m.M11 = x.X; m.M12 = y.X; m.M13 = z.X; m.M14 = 0;
        m.M21 = x.Y; m.M22 = y.Y; m.M23 = z.Y; m.M24 = 0;
        m.M31 = x.Z; m.M32 = y.Z; m.M33 = z.Z; m.M34 = 0;
        m.M41 = -Vector3.Dot(x, eye);
        m.M42 = -Vector3.Dot(y, eye);
        m.M43 = -Vector3.Dot(z, eye);
        m.M44 = 1;
        return m;
    }

    private static Matrix4x4 PerspectiveFovLh(float fov, float aspect, float zn, float zf)
    {
        float yScale = 1f / MathF.Tan(fov * 0.5f);
        float xScale = yScale / aspect;
        Matrix4x4 m = default;
        m.M11 = xScale;
        m.M22 = yScale;
        m.M33 = zf / (zf - zn);
        m.M34 = 1f;
        m.M43 = -zn * zf / (zf - zn);
        return m;
    }

    private static MeshVertex[] LoadWeaponObj(string path, List<string> skip, out int[] indices, out Vector3 center, out float radius)
    {
        var positions = new List<Vector3>();
        var uvs = new List<Vector2>();
        var normals = new List<Vector3>();
        var faces = new List<(int p, int t, int n)[]>();
        bool skipGroup = false;
        foreach (string raw in File.ReadLines(path))
        {
            string line = raw.Trim();
            if (line.StartsWith("g ", StringComparison.Ordinal) || line.StartsWith("o ", StringComparison.Ordinal))
            {
                string name = line[2..];
                skipGroup = skip.Any(mark => name.IndexOf(mark, StringComparison.OrdinalIgnoreCase) >= 0);
                continue;
            }

            if (line.Length == 0 || line[0] == '#')
            {
                continue;
            }

            if (line.StartsWith("v ", StringComparison.Ordinal))
            {
                string[] parts = line.Split(' ', StringSplitOptions.RemoveEmptyEntries);
                positions.Add(new Vector3(float.Parse(parts[1], CultureInfo.InvariantCulture), float.Parse(parts[2], CultureInfo.InvariantCulture), float.Parse(parts[3], CultureInfo.InvariantCulture)));
            }
            else if (line.StartsWith("vt ", StringComparison.Ordinal))
            {
                string[] parts = line.Split(' ', StringSplitOptions.RemoveEmptyEntries);
                float u = float.Parse(parts[1], CultureInfo.InvariantCulture);
                float v = float.Parse(parts[2], CultureInfo.InvariantCulture);
                uvs.Add(new Vector2(u, 1f - v));
            }
            else if (line.StartsWith("vn ", StringComparison.Ordinal))
            {
                string[] parts = line.Split(' ', StringSplitOptions.RemoveEmptyEntries);
                normals.Add(new Vector3(float.Parse(parts[1], CultureInfo.InvariantCulture), float.Parse(parts[2], CultureInfo.InvariantCulture), float.Parse(parts[3], CultureInfo.InvariantCulture)));
            }
            else if (line.StartsWith("f ", StringComparison.Ordinal))
            {
                if (skipGroup)
                {
                    continue;
                }

                string[] parts = line.Split(' ', StringSplitOptions.RemoveEmptyEntries);
                var corners = new (int p, int t, int n)[parts.Length - 1];
                for (int i = 1; i < parts.Length; i++)
                {
                    string[] idx = parts[i].Split('/');
                    corners[i - 1] = (
                        int.Parse(idx[0], CultureInfo.InvariantCulture) - 1,
                        idx.Length > 1 && idx[1].Length > 0 ? int.Parse(idx[1], CultureInfo.InvariantCulture) - 1 : 0,
                        idx.Length > 2 && idx[2].Length > 0 ? int.Parse(idx[2], CultureInfo.InvariantCulture) - 1 : 0);
                }

                for (int i = 1; i + 1 < corners.Length; i++)
                {
                    faces.Add(new[] { corners[0], corners[i], corners[i + 1] });
                }
            }
        }

        var unique = new Dictionary<(int p, int t, int n), int>();
        var verts = new List<MeshVertex>();
        var indexList = new List<int>();
        foreach ((int p, int t, int n)[] face in faces)
        {
            foreach ((int p, int t, int n) corner in face)
            {
                if (!unique.TryGetValue(corner, out int index))
                {
                    Vector3 position = positions[corner.p];
                    Vector3 normal = corner.n >= 0 && corner.n < normals.Count ? Vector3.Normalize(normals[corner.n]) : Vector3.UnitY;
                    Vector2 uv = corner.t >= 0 && corner.t < uvs.Count ? uvs[corner.t] : Vector2.Zero;
                    index = verts.Count;
                    unique[corner] = index;
                    verts.Add(new MeshVertex { Position = position, Normal = normal, Uv = uv, Tangent = Vector3.UnitX, Bitangent = Vector3.UnitZ });
                }

                indexList.Add(index);
            }
        }

        var tan = new Vector3[verts.Count];
        var bit = new Vector3[verts.Count];
        for (int i = 0; i < indexList.Count; i += 3)
        {
            MeshVertex a = verts[indexList[i]];
            MeshVertex b = verts[indexList[i + 1]];
            MeshVertex c = verts[indexList[i + 2]];
            Vector3 e1 = b.Position - a.Position;
            Vector3 e2 = c.Position - a.Position;
            Vector2 u1 = b.Uv - a.Uv;
            Vector2 u2 = c.Uv - a.Uv;
            float det = u1.X * u2.Y - u2.X * u1.Y;
            if (Math.Abs(det) < 1e-8f)
            {
                continue;
            }

            float inv = 1f / det;
            Vector3 t = (e1 * u2.Y - e2 * u1.Y) * inv;
            Vector3 bt = (e2 * u1.X - e1 * u2.X) * inv;
            tan[indexList[i]] += t;
            tan[indexList[i + 1]] += t;
            tan[indexList[i + 2]] += t;
            bit[indexList[i]] += bt;
            bit[indexList[i + 1]] += bt;
            bit[indexList[i + 2]] += bt;
        }

        Vector3 min = new Vector3(float.MaxValue);
        Vector3 max = new Vector3(float.MinValue);
        for (int i = 0; i < verts.Count; i++)
        {
            MeshVertex vertex = verts[i];
            Vector3 t = Vector3.Normalize(tan[i] == Vector3.Zero ? Vector3.UnitX : tan[i]);
            Vector3 n = vertex.Normal;
            t = Vector3.Normalize(t - n * Vector3.Dot(n, t));
            Vector3 b = Vector3.Normalize(bit[i] == Vector3.Zero ? Vector3.Cross(n, t) : bit[i]);
            vertex.Tangent = t;
            vertex.Bitangent = b;
            verts[i] = vertex;
            min = Vector3.Min(min, vertex.Position);
            max = Vector3.Max(max, vertex.Position);
        }

        center = (min + max) * 0.5f;
        radius = Math.Max(0.1f, Vector3.Distance(min, max) * 0.5f);
        indices = indexList.ToArray();
        return verts.ToArray();
    }
}
