using System.Globalization;
using System.IO;
using System.Text.Json;

namespace CFRezManager;

/// <summary>
/// Dumps a skinned LTB model (skeleton hierarchy + bind matrices + per-vertex
/// bone weights/indices + triangles + UVs) to JSON for external DCC use.
/// Read-only: never modifies the source file or any archive.
/// </summary>
internal static class LithTechSkinDumpCommand
{
    public static bool IsInvocation(string[] args)
    {
        return args.Any(arg =>
            string.Equals(arg, "--dump-ltb-skin", StringComparison.OrdinalIgnoreCase) ||
            string.Equals(arg, "dump-ltb-skin", StringComparison.OrdinalIgnoreCase));
    }

    public static int Run(string[] args)
    {
        try
        {
            string? input = null;
            string? output = null;
            for (int i = 0; i < args.Length; i++)
            {
                string arg = args[i];
                if (string.Equals(arg, "--dump-ltb-skin", StringComparison.OrdinalIgnoreCase) ||
                    string.Equals(arg, "dump-ltb-skin", StringComparison.OrdinalIgnoreCase))
                {
                    continue;
                }
                if ((string.Equals(arg, "--input", StringComparison.OrdinalIgnoreCase) ||
                     string.Equals(arg, "--model", StringComparison.OrdinalIgnoreCase) ||
                     string.Equals(arg, "--ltb", StringComparison.OrdinalIgnoreCase)) &&
                    i + 1 < args.Length)
                {
                    input = args[++i];
                    continue;
                }
                if ((string.Equals(arg, "--output", StringComparison.OrdinalIgnoreCase) ||
                     string.Equals(arg, "--json", StringComparison.OrdinalIgnoreCase) ||
                     string.Equals(arg, "--out", StringComparison.OrdinalIgnoreCase)) &&
                    i + 1 < args.Length)
                {
                    output = args[++i];
                    continue;
                }
            }

            if (string.IsNullOrWhiteSpace(input) || string.IsNullOrWhiteSpace(output))
            {
                Console.Error.WriteLine("usage: --dump-ltb-skin --input <model.ltb> --output <dump.json>");
                return 2;
            }

            byte[] sourceBytes = File.ReadAllBytes(input);
            string extension = Path.GetExtension(input).TrimStart('.');
            if (!LithTechModelDecoder.TryDecode(
                    sourceBytes,
                    Path.GetFileName(input),
                    extension,
                    out LithTechModelDocument? document,
                    out string? errorMessage) ||
                document is null)
            {
                throw new InvalidOperationException(errorMessage ?? "LithTech model could not be decoded.");
            }

            var skeleton = (document.SkeletonNodes ?? Array.Empty<LithTechSkeletonNode>())
                .Select(node => new Dictionary<string, object?>
                {
                    ["index"] = node.Index,
                    ["name"] = node.Name,
                    ["parent"] = node.ParentIndex,
                    ["child_count"] = node.ChildCount,
                    ["bind_matrix"] = node.BindMatrix,
                })
                .ToList();

            var meshes = new List<Dictionary<string, object?>>();
            foreach (LithTechMesh mesh in document.Meshes)
            {
                var vertices = new List<double>(mesh.Vertices.Count * 3);
                foreach (LithTechVector3 v in mesh.Vertices)
                {
                    vertices.Add(v.X);
                    vertices.Add(v.Y);
                    vertices.Add(v.Z);
                }

                List<double>? uvs = null;
                if (mesh.HasTextureCoordinates && mesh.TextureCoordinates is not null)
                {
                    uvs = new List<double>(mesh.TextureCoordinates.Count * 2);
                    foreach (LithTechVector2 uv in mesh.TextureCoordinates)
                    {
                        uvs.Add(uv.X);
                        uvs.Add(uv.Y);
                    }
                }

                List<double>? weights = null;
                if (mesh.HasBoneWeights && mesh.BoneWeights is not null)
                {
                    weights = new List<double>(mesh.BoneWeights.Count * 3);
                    foreach (LithTechVertexWeights w in mesh.BoneWeights)
                    {
                        weights.Add(w.First);
                        weights.Add(w.Second);
                        weights.Add(w.Third);
                    }
                }

                List<int>? boneIndices = null;
                if (mesh.HasBoneIndices && mesh.BoneIndices is not null)
                {
                    boneIndices = new List<int>(mesh.BoneIndices.Count * 4);
                    foreach (LithTechVertexBoneIndices bi in mesh.BoneIndices)
                    {
                        boneIndices.Add(bi.First);
                        boneIndices.Add(bi.Second);
                        boneIndices.Add(bi.Third);
                        boneIndices.Add(bi.Fourth);
                    }
                }

                meshes.Add(new Dictionary<string, object?>
                {
                    ["name"] = mesh.Name,
                    ["material_hints"] = mesh.MaterialHints,
                    ["texture_path"] = mesh.TexturePath,
                    ["vertex_count"] = mesh.Vertices.Count,
                    ["vertices"] = vertices,
                    ["triangles"] = mesh.TriangleIndices,
                    ["uvs"] = uvs,
                    ["bone_weights"] = weights,
                    ["bone_indices"] = boneIndices,
                });
            }

            var report = new Dictionary<string, object?>
            {
                ["schema"] = "cf2.lithtech.skin-dump.v1",
                ["source"] = Path.GetFileName(input),
                ["storage"] = document.StorageDescription,
                ["skeleton"] = skeleton,
                ["meshes"] = meshes,
            };

            string outputPath = Path.GetFullPath(output);
            string? dir = Path.GetDirectoryName(outputPath);
            if (!string.IsNullOrWhiteSpace(dir))
            {
                Directory.CreateDirectory(dir);
            }

            File.WriteAllText(
                outputPath,
                JsonSerializer.Serialize(report, new JsonSerializerOptions { WriteIndented = false }) + Environment.NewLine);
            Console.WriteLine($"Dump: {outputPath}");
            Console.WriteLine($"Meshes: {document.Meshes.Count}");
            Console.WriteLine($"Vertices: {document.VertexCount.ToString(CultureInfo.InvariantCulture)}");
            Console.WriteLine($"Skeleton nodes: {skeleton.Count}");
            Console.WriteLine($"Skinned meshes: {meshes.Count(m => m["bone_weights"] is not null)}");
            return 0;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine(ex.Message);
            return 1;
        }
    }
}
