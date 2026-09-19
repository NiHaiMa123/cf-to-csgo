using System.Collections;
using System.Reflection;
using System.Text.Json;

if (args.Length != 3)
{
    Console.Error.WriteLine("usage: P5T02ModelReader <CFRezManager.dll> <raw-ltb> <output-json>");
    return 2;
}

string assemblyPath = Path.GetFullPath(args[0]);
string inputPath = Path.GetFullPath(args[1]);
string outputPath = Path.GetFullPath(args[2]);
Assembly assembly = Assembly.LoadFrom(assemblyPath);
Type decoderType = assembly.GetType("CFRezManager.LithTechModelDecoder", throwOnError: true)!;
MethodInfo decodeMethod = decoderType
    .GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static)
    .Single(method => method.Name == "TryDecode" && method.GetParameters().Length == 5);

byte[] rawBytes = File.ReadAllBytes(inputPath);
object?[] callArguments = [rawBytes, Path.GetFileNameWithoutExtension(inputPath) + ".LTB", "ltb", null, null];
bool decoded = (bool)(decodeMethod.Invoke(null, callArguments) ?? false);
if (!decoded || callArguments[3] is null)
{
    Console.Error.WriteLine(Convert.ToString(callArguments[4]) ?? "LTB decode failed");
    return 1;
}

object document = callArguments[3]!;
object? meshesObject = Get(document, "Meshes");
var meshes = new List<object>();
if (meshesObject is IEnumerable meshEnumerable)
{
    foreach (object mesh in meshEnumerable)
    {
        meshes.Add(new
        {
            name = Convert.ToString(Get(mesh, "Name")) ?? "",
            vertices = Enumerate(Get(mesh, "Vertices"), vector => new[] { Number(Get(vector, "X")), Number(Get(vector, "Y")), Number(Get(vector, "Z")) }),
            triangle_indices = Enumerate(Get(mesh, "TriangleIndices"), value => Convert.ToInt32(value)),
            texture_coordinates = EnumerateNullable(Get(mesh, "TextureCoordinates"), vector => new[] { Number(Get(vector, "X")), Number(Get(vector, "Y")) }),
            texture_path = Get(mesh, "TexturePath"),
            material_hints = EnumerateNullable(Get(mesh, "MaterialHints"), value => Convert.ToString(value) ?? ""),
            normals = EnumerateNullable(Get(mesh, "Normals"), vector => new[] { Number(Get(vector, "X")), Number(Get(vector, "Y")), Number(Get(vector, "Z")) })
        });
    }
}

var result = new
{
    name = Convert.ToString(Get(document, "Name")) ?? "",
    storage_description = Convert.ToString(Get(document, "StorageDescription")) ?? "",
    source_byte_count = Convert.ToInt32(Get(document, "SourceByteCount")),
    decoded_byte_count = Convert.ToInt32(Get(document, "DecodedByteCount")),
    vertex_count = Convert.ToInt32(Get(document, "VertexCount")),
    triangle_count = Convert.ToInt32(Get(document, "TriangleCount")),
    meshes
};

Directory.CreateDirectory(Path.GetDirectoryName(outputPath)!);
File.WriteAllText(outputPath, JsonSerializer.Serialize(result, new JsonSerializerOptions { WriteIndented = false }));
return 0;

static object? Get(object? value, string propertyName) => value?.GetType().GetProperty(propertyName)?.GetValue(value);

static double Number(object? value) => Convert.ToDouble(value, System.Globalization.CultureInfo.InvariantCulture);

static List<T> Enumerate<T>(object? value, Func<object, T> selector)
{
    var result = new List<T>();
    if (value is IEnumerable enumerable)
    {
        foreach (object item in enumerable)
        {
            result.Add(selector(item));
        }
    }

    return result;
}

static List<T>? EnumerateNullable<T>(object? value, Func<object, T> selector)
{
    return value is null ? null : Enumerate(value, selector);
}
