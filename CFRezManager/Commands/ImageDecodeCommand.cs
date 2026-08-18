using System.IO;

namespace CFRezManager;

internal static class ImageDecodeCommand
{
    public static bool IsInvocation(string[] args)
    {
        return args.Length > 0 &&
               (string.Equals(args[0], "--decode-image", StringComparison.OrdinalIgnoreCase) ||
                string.Equals(args[0], "decode-image", StringComparison.OrdinalIgnoreCase));
    }

    public static int Run(string[] args)
    {
        try
        {
            if (args.Length != 3)
            {
                throw new InvalidOperationException("Usage: --decode-image <input> <output.png>");
            }

            string input = Path.GetFullPath(args[1]);
            string output = Path.GetFullPath(args[2]);
            if (!File.Exists(input))
            {
                throw new FileNotFoundException("Image input does not exist.", input);
            }

            string extension = Path.GetExtension(input).TrimStart('.');
            byte[] data = File.ReadAllBytes(input);
            if (!DecodedImageExporter.TryWritePng(data, extension, output))
            {
                throw new InvalidDataException($"Unsupported or malformed {extension.ToUpperInvariant()} image: {input}");
            }

            Console.WriteLine($"Decoded image: {input}");
            Console.WriteLine($"Output: {output}");
            return 0;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine(ex.Message);
            return 1;
        }
    }
}
