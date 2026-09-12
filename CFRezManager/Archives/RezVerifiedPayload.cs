using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;

namespace CFRezManager;

public sealed record RezPayloadCandidateCheck(
    string Path,
    long Length,
    bool RangeOk,
    int? ActualBytes,
    string? Md5,
    bool Md5Match);

public sealed record RezVerifiedPayload(
    byte[] Data,
    string LogicalPath,
    string IndexArchive,
    string PayloadFile,
    int LegacyTimeField,
    int Offset,
    int Size,
    string DirectoryMd5,
    string Sha256,
    IReadOnlyList<RezPayloadCandidateCheck> CandidateChecks,
    string Routing);

public static class RezVerifiedPayloadReader
{
    public const int DefaultMaxBytes = 64 * 1024 * 1024;
    private static readonly Regex NumberedPartName = new(
        @"^(?<stem>.+)_(?<part>[0-9]+)(?<suffix>\.[^.]+)$",
        RegexOptions.IgnoreCase | RegexOptions.CultureInvariant | RegexOptions.Compiled);
    private static readonly Regex Md5Hex = new(
        "^[0-9a-f]{32}$",
        RegexOptions.CultureInvariant | RegexOptions.Compiled);

    public static bool IsCompleteDirectoryMd5(string? value)
    {
        return !string.IsNullOrWhiteSpace(value) && Md5Hex.IsMatch(value.Trim().ToLowerInvariant());
    }

    public static bool IsNumberedPartFile(string filePath)
    {
        string name = System.IO.Path.GetFileName(filePath);
        Match match = NumberedPartName.Match(name);
        if (!match.Success)
        {
            return false;
        }

        string directory = System.IO.Path.GetDirectoryName(System.IO.Path.GetFullPath(filePath)) ?? string.Empty;
        if (!Directory.Exists(directory))
        {
            return false;
        }

        string siblingName = match.Groups["stem"].Value + match.Groups["suffix"].Value;
        return Directory.EnumerateFiles(directory)
            .Count(path => string.Equals(System.IO.Path.GetFileName(path), siblingName, StringComparison.OrdinalIgnoreCase)) == 1;
    }

    public static string NumberedPartFileName(string indexPath, int part)
    {
        return $"{System.IO.Path.GetFileNameWithoutExtension(indexPath)}_{part}{System.IO.Path.GetExtension(indexPath)}";
    }

    public static IReadOnlyList<string> ListCandidatePaths(string indexPath, int part)
    {
        string indexFullPath = System.IO.Path.GetFullPath(indexPath);
        var candidates = new List<string> { indexFullPath };
        if (part <= 0)
        {
            return candidates;
        }

        string directory = System.IO.Path.GetDirectoryName(indexFullPath) ?? string.Empty;
        if (!Directory.Exists(directory))
        {
            return candidates;
        }

        string name = NumberedPartFileName(indexFullPath, part);
        List<string> siblings = Directory.EnumerateFiles(directory)
            .Where(path => string.Equals(System.IO.Path.GetFileName(path), name, StringComparison.OrdinalIgnoreCase))
            .Select(System.IO.Path.GetFullPath)
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .ToList();
        if (siblings.Count > 1)
        {
            throw new InvalidDataException("Ambiguous numbered-part filename");
        }

        candidates.AddRange(siblings);
        return candidates;
    }

    public static RezVerifiedPayload Read(RezArchive archive, RezFileNode file, int maxBytes = DefaultMaxBytes)
    {
        ArgumentNullException.ThrowIfNull(archive);
        return Read(archive.FilePath, file, maxBytes);
    }

    public static RezVerifiedPayload Read(string indexPath, RezFileNode file, int maxBytes = DefaultMaxBytes)
    {
        ArgumentNullException.ThrowIfNull(file);
        if (file.DataOffset < 0 || file.Size < 0 || file.Size > maxBytes)
        {
            throw new InvalidDataException("Invalid or oversized payload range");
        }

        string expected = (file.Md5 ?? string.Empty).Trim().ToLowerInvariant();
        if (!IsCompleteDirectoryMd5(expected))
        {
            return ReadUnverifiedMainFile(indexPath, file, maxBytes);
        }

        IReadOnlyList<string> candidates = ListCandidatePaths(indexPath, file.Time);
        var attempts = new List<RezPayloadCandidateCheck>();
        var matches = new List<(string Path, byte[] Data)>();
        foreach (string candidate in candidates)
        {
            var info = new FileInfo(candidate);
            long length = info.Exists ? info.Length : 0;
            bool rangeOk = info.Exists && file.DataOffset + (long)file.Size <= length;
            if (!rangeOk)
            {
                attempts.Add(new RezPayloadCandidateCheck(candidate, length, false, null, null, false));
                continue;
            }

            byte[] data = ReadExactRange(candidate, file.DataOffset, file.Size);
            string actual = Convert.ToHexString(MD5.HashData(data)).ToLowerInvariant();
            bool md5Match = data.Length == file.Size && actual == expected;
            attempts.Add(new RezPayloadCandidateCheck(candidate, length, true, data.Length, actual, md5Match));
            if (md5Match)
            {
                matches.Add((candidate, data));
            }
        }

        if (matches.Count != 1)
        {
            throw new InvalidDataException(
                $"Expected one MD5-verified payload candidate, found {matches.Count}: {FormatAttempts(attempts)}");
        }

        (string source, byte[] payload) = matches[0];
        string indexFullPath = System.IO.Path.GetFullPath(indexPath);
        return new RezVerifiedPayload(
            payload,
            file.FullPath,
            indexFullPath,
            source,
            file.Time,
            file.DataOffset,
            file.Size,
            expected,
            Convert.ToHexString(SHA256.HashData(payload)).ToLowerInvariant(),
            attempts,
            string.Equals(source, indexFullPath, StringComparison.OrdinalIgnoreCase) ? "main_file" : "numbered_part");
    }

    public static byte[] ReadBytes(RezArchive archive, RezFileNode file, int maxBytes = DefaultMaxBytes)
    {
        return Read(archive, file, maxBytes).Data;
    }

    public static byte[] ReadPrefix(RezArchive archive, RezFileNode file, int prefixBytes, int maxBytes = DefaultMaxBytes)
    {
        byte[] data = ReadBytes(archive, file, maxBytes);
        if (prefixBytes >= data.Length)
        {
            return data;
        }

        return data.AsSpan(0, Math.Max(0, prefixBytes)).ToArray();
    }

    public static bool TryRead(RezArchive archive, RezFileNode file, int maxBytes, out byte[]? data)
    {
        data = null;
        try
        {
            if (archive is null || file is null || file.Size < 0 || file.Size > maxBytes)
            {
                return false;
            }

            data = ReadBytes(archive, file, maxBytes);
            return true;
        }
        catch
        {
            data = null;
            return false;
        }
    }

    public static IEnumerable<RezFileNode> EnumerateFiles(RezDirectoryNode node)
    {
        foreach (RezNode child in node.Children)
        {
            if (child is RezFileNode file)
            {
                yield return file;
            }
            else if (child is RezDirectoryNode directory)
            {
                foreach (RezFileNode nested in EnumerateFiles(directory))
                {
                    yield return nested;
                }
            }
        }
    }

    public static RezFileNode FindFile(RezArchive archive, string logicalPath)
    {
        string wanted = logicalPath.Replace('\\', '/').Trim('/');
        List<RezFileNode> matches = EnumerateFiles(archive.Root)
            .Where(file =>
            {
                string full = file.FullPath.Replace('\\', '/').Trim('/');
                return string.Equals(full, wanted, StringComparison.OrdinalIgnoreCase) ||
                       full.EndsWith("/" + wanted, StringComparison.OrdinalIgnoreCase);
            })
            .ToList();
        if (matches.Count != 1)
        {
            throw new InvalidDataException($"Expected one logical path '{logicalPath}', found {matches.Count}");
        }

        return matches[0];
    }

    private static RezVerifiedPayload ReadUnverifiedMainFile(string indexPath, RezFileNode file, int maxBytes)
    {
        if (file.Time > 0 && ListCandidatePaths(indexPath, file.Time).Count > 1)
        {
            throw new InvalidDataException("A complete directory MD5 is required");
        }

        string indexFullPath = System.IO.Path.GetFullPath(indexPath);
        var info = new FileInfo(indexFullPath);
        if (!info.Exists || file.DataOffset + (long)file.Size > info.Length || file.Size > maxBytes)
        {
            throw new InvalidDataException("A complete directory MD5 is required");
        }

        byte[] data = ReadExactRange(indexFullPath, file.DataOffset, file.Size);
        return new RezVerifiedPayload(
            data,
            file.FullPath,
            indexFullPath,
            indexFullPath,
            file.Time,
            file.DataOffset,
            file.Size,
            string.Empty,
            Convert.ToHexString(SHA256.HashData(data)).ToLowerInvariant(),
            [
                new RezPayloadCandidateCheck(indexFullPath, info.Length, true, data.Length, null, false)
            ],
            "unverified_main_file");
    }

    private static byte[] ReadExactRange(string path, int offset, int size)
    {
        byte[] data = new byte[size];
        using FileStream source = File.OpenRead(path);
        source.Position = offset;
        source.ReadExactly(data);
        return data;
    }

    private static string FormatAttempts(IReadOnlyList<RezPayloadCandidateCheck> attempts)
    {
        var builder = new StringBuilder();
        builder.Append('[');
        for (int i = 0; i < attempts.Count; i++)
        {
            if (i > 0)
            {
                builder.Append(", ");
            }

            RezPayloadCandidateCheck attempt = attempts[i];
            builder.Append('{')
                .Append("path=").Append(attempt.Path)
                .Append(", range_ok=").Append(attempt.RangeOk)
                .Append(", md5_match=").Append(attempt.Md5Match)
                .Append('}');
        }

        builder.Append(']');
        return builder.ToString();
    }
}
