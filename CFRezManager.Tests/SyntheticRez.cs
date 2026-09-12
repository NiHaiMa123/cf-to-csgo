using System.Buffers.Binary;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using CFRezManager;

namespace CFRezManager.Tests;

internal sealed record SyntheticRezFile(
    string FullPath,
    byte[] Data,
    int Time,
    int Offset,
    bool InIndex = true,
    bool WritePart = false,
    string? Md5 = null);

internal static class SyntheticRez
{
    private const int HeaderSize = 168;
    private static readonly Encoding Text = Encoding.ASCII;

    public static string Write(string indexPath, IReadOnlyList<SyntheticRezFile> files)
    {
        string directory = Path.GetDirectoryName(Path.GetFullPath(indexPath))!;
        Directory.CreateDirectory(directory);

        var grouped = new Dictionary<string, List<SyntheticRezFile>>(StringComparer.OrdinalIgnoreCase);
        foreach (SyntheticRezFile file in files)
        {
            string logical = file.FullPath.Replace('\\', '/').Trim('/');
            int slash = logical.LastIndexOf('/');
            string parent = slash < 0 ? "" : logical[..slash];
            if (!grouped.TryGetValue(parent, out List<SyntheticRezFile>? list))
            {
                list = [];
                grouped[parent] = list;
            }

            list.Add(file with { FullPath = logical });
        }

        List<string> directories = grouped.Keys.Where(name => name.Length > 0).ToList();
        Dictionary<string, byte[]> dirPlain = directories.ToDictionary(
            name => name,
            name => EncodeFiles(grouped[name]));
        byte[] rootFilesPlain = grouped.TryGetValue("", out List<SyntheticRezFile>? rootFiles)
            ? EncodeFiles(rootFiles)
            : [];

        int rootPos = HeaderSize;
        int cursor = rootPos;
        byte[] placeholderRoot = Concat(directories.Select(name => DirEntry(name, 0, dirPlain[name].Length)), rootFilesPlain);
        cursor += placeholderRoot.Length;
        var dirOffsets = new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase);
        foreach (string name in directories)
        {
            dirOffsets[name] = cursor;
            cursor += dirPlain[name].Length;
        }

        byte[] rootPlain = Concat(directories.Select(name => DirEntry(name, dirOffsets[name], dirPlain[name].Length)), rootFilesPlain);
        int indexEnd = cursor;
        foreach (SyntheticRezFile file in files)
        {
            if (file.InIndex)
            {
                indexEnd = Math.Max(indexEnd, file.Offset + file.Data.Length);
            }
        }

        byte[] blob = new byte[indexEnd];
        Header(rootPos, rootPlain.Length).CopyTo(blob, 0);
        WriteEncoded(blob, rootPos, rootPlain);
        foreach (string name in directories)
        {
            WriteEncoded(blob, dirOffsets[name], dirPlain[name]);
        }

        foreach (SyntheticRezFile file in files)
        {
            if (file.InIndex)
            {
                file.Data.CopyTo(blob, file.Offset);
            }
        }

        File.WriteAllBytes(indexPath, blob);

        var parts = new Dictionary<int, byte[]>();
        foreach (SyntheticRezFile file in files)
        {
            bool writePart = file.WritePart || !file.InIndex;
            if (!writePart)
            {
                continue;
            }

            int end = file.Offset + file.Data.Length;
            if (!parts.TryGetValue(file.Time, out byte[]? partBlob) || partBlob.Length < end)
            {
                byte[] grown = new byte[end];
                if (partBlob is not null)
                {
                    partBlob.CopyTo(grown, 0);
                }

                partBlob = grown;
                parts[file.Time] = partBlob;
            }

            file.Data.CopyTo(partBlob, file.Offset);
        }

        foreach ((int part, byte[] partBlob) in parts)
        {
            string partPath = Path.Combine(
                directory,
                $"{Path.GetFileNameWithoutExtension(indexPath)}_{part}{Path.GetExtension(indexPath)}");
            File.WriteAllBytes(partPath, partBlob);
        }

        return Path.GetFullPath(indexPath);
    }

    public static RezFileNode Node(string fullPath, int offset, int size, int time, string md5)
    {
        string name = Path.GetFileName(fullPath.Replace('/', Path.DirectorySeparatorChar));
        string extension = Path.GetExtension(name).TrimStart('.');
        return new RezFileNode(name, fullPath.Replace('\\', '/'), extension, offset, size, time, 1, md5);
    }

    private static byte[] EncodeFiles(IEnumerable<SyntheticRezFile> files)
    {
        using var stream = new MemoryStream();
        foreach (SyntheticRezFile file in files)
        {
            string name = file.FullPath.Replace('\\', '/');
            string fileName = name[(name.LastIndexOf('/') + 1)..];
            string stem = Path.GetFileNameWithoutExtension(fileName);
            string extension = Path.GetExtension(fileName).TrimStart('.');
            string md5 = file.Md5 ?? Convert.ToHexString(MD5.HashData(file.Data)).ToLowerInvariant();
            stream.Write(FileEntry(stem, extension, file.Offset, file.Data.Length, file.Time, md5));
        }

        return stream.ToArray();
    }

    private static byte[] FileEntry(string stem, string extension, int offset, int size, int time, string md5)
    {
        using var stream = new MemoryStream();
        using var writer = new BinaryWriter(stream, Text, leaveOpen: true);
        writer.Write(0);
        writer.Write(offset);
        writer.Write(size);
        writer.Write(time);
        writer.Write(1);
        byte[] ext = new byte[4];
        byte[] extBytes = Text.GetBytes(extension);
        for (int i = 0; i < extBytes.Length && i < 4; i++)
        {
            ext[i] = extBytes[extBytes.Length - 1 - i];
        }

        writer.Write(ext);
        writer.Write(0);
        byte[] nameBytes = Text.GetBytes(stem);
        writer.Write(nameBytes.Length);
        writer.Write(nameBytes);
        writer.Write((short)0);
        writer.Write(Text.GetBytes(md5.PadRight(32, '\0')[..32]));
        return stream.ToArray();
    }

    private static byte[] DirEntry(string name, int tableOffset, int tableSize)
    {
        using var stream = new MemoryStream();
        using var writer = new BinaryWriter(stream, Text, leaveOpen: true);
        writer.Write(1);
        writer.Write(tableOffset);
        writer.Write(tableSize);
        writer.Write(0);
        byte[] nameBytes = Text.GetBytes(name);
        writer.Write(nameBytes.Length);
        writer.Write(nameBytes);
        writer.Write((byte)0);
        return stream.ToArray();
    }

    private static byte[] Header(int rootPos, int rootSize)
    {
        byte[] header = new byte[HeaderSize];
        header[0] = 0x0D;
        header[1] = 0x0A;
        header[62] = 0x0D;
        header[63] = 0x0A;
        header[124] = 0x0D;
        header[125] = 0x0A;
        header[126] = 0x1A;
        BinaryPrimitives.WriteInt32LittleEndian(header.AsSpan(127, 4), 1);
        BinaryPrimitives.WriteInt32LittleEndian(header.AsSpan(131, 4), rootPos);
        BinaryPrimitives.WriteInt32LittleEndian(header.AsSpan(135, 4), rootSize);
        return header;
    }

    private static void WriteEncoded(byte[] destination, int offset, byte[] plain)
    {
        byte[] encoded = (byte[])plain.Clone();
        RezCrypto.Encode(encoded, offset);
        encoded.CopyTo(destination, offset);
    }

    private static byte[] Concat(IEnumerable<byte[]> parts, byte[] extra)
    {
        using var stream = new MemoryStream();
        foreach (byte[] part in parts)
        {
            stream.Write(part);
        }

        stream.Write(extra);
        return stream.ToArray();
    }
}
