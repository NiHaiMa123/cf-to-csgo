using System.Globalization;
using System.IO;
using System.Security.Cryptography;
using System.Text.Json;

namespace CFRezManager;

/// <summary>
/// Emits a field-level, machine-readable audit of one LTB/LTA/LTC model.  It
/// intentionally reports unsupported fields as missing/partial instead of
/// inventing a skeleton or animation stream.
/// </summary>
internal static class LithTechInspectCommand
{
    private sealed record Options(string InputPath, string OutputPath);

    public static bool IsInvocation(string[] args)
    {
        return args.Any(arg =>
            string.Equals(arg, "--inspect-ltb", StringComparison.OrdinalIgnoreCase) ||
            string.Equals(arg, "inspect-ltb", StringComparison.OrdinalIgnoreCase));
    }

    public static int Run(string[] args)
    {
        try
        {
            Options options = ParseOptions(args);
            byte[] sourceBytes = File.ReadAllBytes(options.InputPath);
            string extension = Path.GetExtension(options.InputPath).TrimStart('.');
            if (!LithTechModelDecoder.TryDecode(
                    sourceBytes,
                    Path.GetFileName(options.InputPath),
                    extension,
                    out LithTechModelDocument? document,
                    out string? errorMessage) ||
                document is null)
            {
                throw new InvalidOperationException(errorMessage ?? "LithTech model could not be decoded.");
            }

            object report = BuildReport(options.InputPath, sourceBytes, document);
            string outputPath = Path.GetFullPath(options.OutputPath);
            string? outputDirectory = Path.GetDirectoryName(outputPath);
            if (!string.IsNullOrWhiteSpace(outputDirectory))
            {
                Directory.CreateDirectory(outputDirectory);
            }

            File.WriteAllText(
                outputPath,
                JsonSerializer.Serialize(report, new JsonSerializerOptions { WriteIndented = true }) + Environment.NewLine);
            Console.WriteLine($"Report: {outputPath}");
            Console.WriteLine($"Meshes: {document.Meshes.Count}");
            Console.WriteLine($"Vertices: {document.VertexCount.ToString(CultureInfo.InvariantCulture)}");
            Console.WriteLine($"Triangles: {document.TriangleCount.ToString(CultureInfo.InvariantCulture)}");
            return 0;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine(ex.Message);
            return 1;
        }
    }

    private static Options ParseOptions(string[] args)
    {
        string? inputPath = null;
        string? outputPath = null;
        for (int index = 0; index < args.Length; index++)
        {
            string arg = args[index];
            if (string.Equals(arg, "--inspect-ltb", StringComparison.OrdinalIgnoreCase) ||
                string.Equals(arg, "inspect-ltb", StringComparison.OrdinalIgnoreCase))
            {
                continue;
            }

            if (TryReadOptionValue(args, ref index, "--input", out string? inputValue) ||
                TryReadOptionValue(args, ref index, "--model", out inputValue))
            {
                inputPath = inputValue;
                continue;
            }

            if (TryReadOptionValue(args, ref index, "--output", out string? outputValue) ||
                TryReadOptionValue(args, ref index, "-o", out outputValue))
            {
                outputPath = outputValue;
                continue;
            }

            inputPath ??= arg;
        }

        if (string.IsNullOrWhiteSpace(inputPath))
        {
            throw new InvalidOperationException("Missing --input <model.ltb>.");
        }

        inputPath = Path.GetFullPath(inputPath);
        if (!File.Exists(inputPath))
        {
            throw new FileNotFoundException("LithTech model not found.", inputPath);
        }

        outputPath ??= Path.Combine(
            Path.GetDirectoryName(inputPath) ?? Environment.CurrentDirectory,
            $"{Path.GetFileNameWithoutExtension(inputPath)}_b1_report.json");
        return new Options(inputPath, outputPath);
    }

    private static bool TryReadOptionValue(string[] args, ref int index, string optionName, out string? value)
    {
        value = null;
        if (!string.Equals(args[index], optionName, StringComparison.OrdinalIgnoreCase))
        {
            return false;
        }

        if (index + 1 >= args.Length)
        {
            throw new InvalidOperationException($"Missing value for {optionName}.");
        }

        value = args[++index];
        return true;
    }

    private static object BuildReport(string inputPath, byte[] sourceBytes, LithTechModelDocument document)
    {
        List<object> meshes = document.Meshes.Select(mesh => BuildMeshReport(mesh)).ToList();
        bool hasNormals = document.Meshes.Count > 0 && document.Meshes.All(mesh => mesh.HasNormals);
        bool hasWeights = document.Meshes.Any(mesh => mesh.HasBoneWeights);
        bool hasMaterialHints = document.Meshes.Any(mesh =>
            !string.IsNullOrWhiteSpace(mesh.TexturePath) ||
            mesh.MaterialHints is { Count: > 0 });
        var decodedWeights = document.Meshes.SelectMany(mesh => mesh.BoneWeights ?? []).ToArray();
        var decodedBoneIndices = document.Meshes.SelectMany(mesh => mesh.BoneIndices ?? []).ToArray();
        bool hasBoneIndices = document.Meshes.Any(mesh => mesh.HasBoneIndices);
        bool hasSkeleton = document.SkeletonNodes is { Count: > 0 };
        bool boneIndicesRangeChecked = hasBoneIndices && decodedBoneIndices.All(indices =>
            new[] { indices.First, indices.Second, indices.Third, indices.Fourth }
                .Where(index => index != 255)
                .All(index => index >= 0 && index < 256));
        int invalidWeightSumCount = decodedWeights.Count(weight =>
            !(IsFinite(weight.First) && IsFinite(weight.Second) && IsFinite(weight.Third) &&
              weight.First >= -0.001 && weight.Second >= -0.001 && weight.Third >= -0.001 &&
              Math.Abs(weight.Sum - 1.0) <= 0.01));
        bool allWeightSumsValid = decodedWeights.All(weight =>
                IsFinite(weight.First) && IsFinite(weight.Second) && IsFinite(weight.Third) &&
                weight.First >= -0.001 && weight.Second >= -0.001 && weight.Third >= -0.001 &&
                Math.Abs(weight.Sum - 1.0) <= 0.01);
        BindPoseValidationResult bindPose = ValidateBindPose(document);

        return new
        {
            schema = "cf2.lithtech.ltb-diagnostic.v1",
            generated_at_utc = DateTimeOffset.UtcNow,
            input = new
            {
                path = inputPath,
                extension = Path.GetExtension(inputPath).TrimStart('.').ToLowerInvariant(),
                size_bytes = sourceBytes.Length,
                sha256 = Convert.ToHexString(SHA256.HashData(sourceBytes)).ToLowerInvariant()
            },
            storage = new
            {
                description = document.StorageDescription,
                source_byte_count = document.SourceByteCount,
                decoded_byte_count = document.DecodedByteCount
            },
            geometry = new
            {
                mesh_count = document.Meshes.Count,
                vertex_count = document.VertexCount,
                triangle_count = document.TriangleCount,
                coordinate_space = "raw LTB coordinates; decoder does not center, scale, or rotate",
                meshes
            },
            skeleton = BuildSkeletonReport(document.SkeletonNodes),
            capabilities = new
            {
                normals = new { status = hasNormals ? "available" : "missing", evidence = "decoded from the LTB vertex stream" },
                tangents = new { status = "missing", evidence = "no tangent field is decoded from LTB" },
                bone_weights = new { status = hasWeights ? "partial" : "missing", evidence = hasWeights ? "up to three vertex weight values decoded" : "no skinned vertex stream detected" },
                bone_indices = new { status = hasBoneIndices ? "available" : "missing", evidence = hasBoneIndices ? "decoded from packed per-vertex-range node-index records and validated against the LTB node-count header; 255 is the empty influence sentinel" : "the node/lookup table is not decoded into per-vertex bone indices" },
                skeleton_nodes = new { status = hasSkeleton ? "available" : "missing", evidence = hasSkeleton ? "decoded node names, preorder child counts, parent links, and 4x4 bind matrices" : "LTB node names, hierarchy, and transforms are not decoded" },
                bind_pose = new { status = bindPose.Passed ? "available" : hasSkeleton ? "partial" : "missing", evidence = bindPose.Checked ? "weighted bind-pose round-trip was evaluated against the decoded node matrices" : "no bind-pose bone transforms are available for a round-trip" },
                animation_clips = new { status = "missing", evidence = "LTB animation blocks are not decoded" },
                material_bindings = new { status = hasMaterialHints ? "partial" : "missing", evidence = hasMaterialHints ? "texture/material hints are preserved per mesh" : "no direct material reference was decoded" },
                coordinate_transform = new { status = "available", evidence = "raw coordinates are preserved; OBJ exporter transform is reported separately" }
            },
            validation = new
            {
                finite_vertex_positions = document.Meshes.SelectMany(mesh => mesh.Vertices).All(vertex => IsFinite(vertex.X) && IsFinite(vertex.Y) && IsFinite(vertex.Z)),
                finite_normals = document.Meshes.SelectMany(mesh => mesh.Normals ?? []).All(normal => IsFinite(normal.X) && IsFinite(normal.Y) && IsFinite(normal.Z)),
                normal_vectors_nonzero = document.Meshes.SelectMany(mesh => mesh.Normals ?? []).All(normal => Math.Sqrt(normal.X * normal.X + normal.Y * normal.Y + normal.Z * normal.Z) > 0.000001),
                weight_sums_near_one = hasWeights && allWeightSumsValid,
                decoded_weight_sample_count = decodedWeights.Length,
                invalid_weight_sum_count = invalidWeightSumCount,
                bone_index_range_checked = boneIndicesRangeChecked,
                decoded_bone_index_sample_count = decodedBoneIndices.Length,
                bind_pose_skinning_roundtrip_checked = bindPose.Checked,
                bind_pose_skinning_roundtrip_passed = bindPose.Passed,
                bind_pose_sample_count = bindPose.SampleCount,
                bind_pose_invalid_matrix_count = bindPose.InvalidMatrixCount,
                bind_pose_max_error = bindPose.MaxError,
                bind_pose_average_error = bindPose.AverageError,
                bind_pose_residual_weight_samples = bindPose.ResidualWeightSampleCount,
                animation_continuity_checked = false
            },
            limitations = new[]
            {
                "This report does not claim CF skeleton or animation support.",
                "Weight values, packed per-vertex bone indices, node hierarchy, and bind matrices are decoded; animation blocks and material bindings remain unresolved.",
                "The OBJ exporter still applies its legacy center-and-4.5-scale transform; use raw coordinates for B3.",
                "A mesh texture hint is not proof that the corresponding DTX/Shader material was resolved."
            }
        };
    }

    private sealed record BindPoseValidationResult(
        bool Checked,
        bool Passed,
        int SampleCount,
        int InvalidMatrixCount,
        int ResidualWeightSampleCount,
        double MaxError,
        double AverageError);

    private static object BuildSkeletonReport(IReadOnlyList<LithTechSkeletonNode>? nodes)
    {
        if (nodes is null || nodes.Count == 0)
        {
            return new { status = "missing", node_count = 0, nodes = Array.Empty<object>() };
        }

        return new
        {
            status = "available",
            node_count = nodes.Count,
            nodes = nodes.Select(node => new
            {
                index = node.Index,
                name = node.Name,
                parent_index = node.ParentIndex,
                child_count = node.ChildCount,
                bind_matrix = node.BindMatrix
            }).ToArray()
        };
    }

    private static BindPoseValidationResult ValidateBindPose(LithTechModelDocument document)
    {
        IReadOnlyList<LithTechSkeletonNode>? nodes = document.SkeletonNodes;
        if (nodes is null || nodes.Count == 0)
        {
            return new BindPoseValidationResult(false, false, 0, 0, 0, double.NaN, double.NaN);
        }

        var transforms = new Dictionary<int, (double[] Matrix, double[] Inverse)>();
        int invalidMatrixCount = 0;
        foreach (LithTechSkeletonNode node in nodes)
        {
            double[] matrix = node.BindMatrix.ToArray();
            if (!TryInvertAffine(matrix, out double[] inverse))
            {
                invalidMatrixCount++;
                continue;
            }

            transforms[node.Index] = (matrix, inverse);
        }

        int sampleCount = 0;
        int residualWeightSampleCount = 0;
        double maxError = 0.0;
        double errorSum = 0.0;
        foreach (LithTechMesh mesh in document.Meshes)
        {
            if (!mesh.HasBoneWeights || !mesh.HasBoneIndices)
            {
                continue;
            }

            for (int vertexIndex = 0; vertexIndex < mesh.Vertices.Count; vertexIndex++)
            {
                LithTechVertexWeights weights = mesh.BoneWeights![vertexIndex];
                LithTechVertexBoneIndices indices = mesh.BoneIndices![vertexIndex];
                var weighted = new LithTechVector3(0, 0, 0);
                double totalWeight = 0.0;
                int[] boneIndices = [indices.First, indices.Second, indices.Third, indices.Fourth];
                double[] influenceWeights = [weights.First, weights.Second, weights.Third, Math.Max(0.0, 1.0 - weights.Sum)];
                if (indices.Fourth != 255 && influenceWeights[3] > 0.000001)
                {
                    residualWeightSampleCount++;
                }

                for (int influenceIndex = 0; influenceIndex < boneIndices.Length; influenceIndex++)
                {
                    int boneIndex = boneIndices[influenceIndex];
                    double influenceWeight = influenceWeights[influenceIndex];
                    if (boneIndex == 255 || influenceWeight <= 0.0 || !transforms.TryGetValue(boneIndex, out (double[] Matrix, double[] Inverse) transform))
                    {
                        continue;
                    }

                    LithTechVector3 local = TransformPoint(transform.Inverse, mesh.Vertices[vertexIndex]);
                    LithTechVector3 rebound = TransformPoint(transform.Matrix, local);
                    weighted = new LithTechVector3(
                        weighted.X + rebound.X * influenceWeight,
                        weighted.Y + rebound.Y * influenceWeight,
                        weighted.Z + rebound.Z * influenceWeight);
                    totalWeight += influenceWeight;
                }

                if (totalWeight <= 0.000001)
                {
                    continue;
                }

                LithTechVector3 original = mesh.Vertices[vertexIndex];
                double error = Math.Sqrt(
                    Math.Pow(weighted.X - original.X, 2) +
                    Math.Pow(weighted.Y - original.Y, 2) +
                    Math.Pow(weighted.Z - original.Z, 2));
                sampleCount++;
                maxError = Math.Max(maxError, error);
                errorSum += error;
            }
        }

        bool passed = sampleCount > 0 && invalidMatrixCount == 0 && maxError <= 0.001;
        return new BindPoseValidationResult(
            sampleCount > 0,
            passed,
            sampleCount,
            invalidMatrixCount,
            residualWeightSampleCount,
            maxError,
            sampleCount > 0 ? errorSum / sampleCount : double.NaN);
    }

    private static bool TryInvertAffine(IReadOnlyList<double> matrix, out double[] inverse)
    {
        inverse = Array.Empty<double>();
        if (matrix.Count != 16)
        {
            return false;
        }

        double a = matrix[0], b = matrix[1], c = matrix[2];
        double d = matrix[4], e = matrix[5], f = matrix[6];
        double g = matrix[8], h = matrix[9], i = matrix[10];
        double determinant = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g);
        if (Math.Abs(determinant) < 1e-8)
        {
            return false;
        }

        double inv = 1.0 / determinant;
        double r00 = (e * i - f * h) * inv;
        double r01 = (c * h - b * i) * inv;
        double r02 = (b * f - c * e) * inv;
        double r10 = (f * g - d * i) * inv;
        double r11 = (a * i - c * g) * inv;
        double r12 = (c * d - a * f) * inv;
        double r20 = (d * h - e * g) * inv;
        double r21 = (b * g - a * h) * inv;
        double r22 = (a * e - b * d) * inv;
        double tx = matrix[3], ty = matrix[7], tz = matrix[11];
        inverse =
        [
            r00, r01, r02, -(r00 * tx + r01 * ty + r02 * tz),
            r10, r11, r12, -(r10 * tx + r11 * ty + r12 * tz),
            r20, r21, r22, -(r20 * tx + r21 * ty + r22 * tz),
            0, 0, 0, 1
        ];
        return true;
    }

    private static LithTechVector3 TransformPoint(IReadOnlyList<double> matrix, LithTechVector3 point)
    {
        return new LithTechVector3(
            matrix[0] * point.X + matrix[1] * point.Y + matrix[2] * point.Z + matrix[3],
            matrix[4] * point.X + matrix[5] * point.Y + matrix[6] * point.Z + matrix[7],
            matrix[8] * point.X + matrix[9] * point.Y + matrix[10] * point.Z + matrix[11]);
    }

    private static object BuildMeshReport(LithTechMesh mesh)
    {
        (LithTechVector3 Min, LithTechVector3 Max) bounds = GetBounds(mesh.Vertices);
        var normalLengths = (mesh.Normals ?? [])
            .Select(normal => Math.Sqrt(normal.X * normal.X + normal.Y * normal.Y + normal.Z * normal.Z))
            .ToArray();
        var weightSums = (mesh.BoneWeights ?? []).Select(weight => weight.Sum).ToArray();
        return new
        {
            name = mesh.Name,
            vertex_count = mesh.Vertices.Count,
            triangle_count = mesh.TriangleIndices.Count / 3,
            uv_count = mesh.TextureCoordinates?.Count ?? 0,
            has_uv = mesh.HasTextureCoordinates,
            normal_count = mesh.Normals?.Count ?? 0,
            has_normals = mesh.HasNormals,
            normal_length = Summarize(normalLengths),
            weight_count = mesh.BoneWeights?.Count ?? 0,
            has_weights = mesh.HasBoneWeights,
            weight_sum = Summarize(weightSums),
            texture_path = mesh.TexturePath,
            material_hints = mesh.MaterialHints ?? [],
            bounds = new
            {
                min = new[] { bounds.Min.X, bounds.Min.Y, bounds.Min.Z },
                max = new[] { bounds.Max.X, bounds.Max.Y, bounds.Max.Z }
            }
        };
    }

    private static object? Summarize(IReadOnlyList<double> values)
    {
        if (values.Count == 0)
        {
            return null;
        }

        return new
        {
            min = values.Min(),
            max = values.Max(),
            average = values.Average(),
            count = values.Count
        };
    }

    private static (LithTechVector3 Min, LithTechVector3 Max) GetBounds(IReadOnlyList<LithTechVector3> vertices)
    {
        if (vertices.Count == 0)
        {
            return (new LithTechVector3(0, 0, 0), new LithTechVector3(0, 0, 0));
        }

        return (
            new LithTechVector3(vertices.Min(vertex => vertex.X), vertices.Min(vertex => vertex.Y), vertices.Min(vertex => vertex.Z)),
            new LithTechVector3(vertices.Max(vertex => vertex.X), vertices.Max(vertex => vertex.Y), vertices.Max(vertex => vertex.Z)));
    }

    private static bool IsFinite(double value) => !double.IsNaN(value) && !double.IsInfinity(value);
}
