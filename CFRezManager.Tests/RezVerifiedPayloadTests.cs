using System.IO;
using System.Security.Cryptography;
using CFRezManager;
using Xunit;

namespace CFRezManager.Tests;

public sealed class RezVerifiedPayloadTests : IDisposable
{
    private readonly string _root;

    public RezVerifiedPayloadTests()
    {
        _root = Path.Combine(Path.GetTempPath(), "cfrez-n05c-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(_root);
    }

    public void Dispose()
    {
        try
        {
            Directory.Delete(_root, recursive: true);
        }
        catch
        {
        }
    }

    [Fact]
    public void MainRangeLegalButWrongBytesUsesNumberedPart()
    {
        string index = Path.Combine(_root, "rf017.rez");
        byte[] good = "GOOD"u8.ToArray();
        SyntheticRez.Write(index, [
            new SyntheticRezFile("PLAYERVIEW/gun.dtx", good, Time: 8, Offset: 400, InIndex: true, WritePart: true)
        ]);
        byte[] blob = File.ReadAllBytes(index);
        "BAD!"u8.CopyTo(blob.AsSpan(400));
        File.WriteAllBytes(index, blob);

        RezArchive archive = new RezArchiveReader().Read(index);
        RezFileNode file = RezVerifiedPayloadReader.FindFile(archive, "PLAYERVIEW/gun.dtx");
        RezVerifiedPayload payload = RezVerifiedPayloadReader.Read(archive, file);
        Assert.Equal(good, payload.Data);
        Assert.Equal("numbered_part", payload.Routing);
        Assert.Contains("_8", Path.GetFileName(payload.PayloadFile), StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public void PayloadBeyondMainFileIsKeptAndReadFromPart()
    {
        string index = Path.Combine(_root, "rf017.rez");
        byte[] good = "GOOD"u8.ToArray();
        SyntheticRez.Write(index, [
            new SyntheticRezFile("PLAYERVIEW/gun.dtx", good, Time: 8, Offset: 800, InIndex: false, WritePart: true)
        ]);
        Assert.True(new FileInfo(index).Length < 800);

        RezArchive archive = new RezArchiveReader().Read(index);
        Assert.Equal(1, archive.FileCount);
        RezFileNode file = RezVerifiedPayloadReader.FindFile(archive, "PLAYERVIEW/gun.dtx");
        string dest = Path.Combine(_root, "out", "PLAYERVIEW", "gun.dtx");
        RezArchiveReader.ExtractFile(archive, file, dest);
        Assert.Equal(good, File.ReadAllBytes(dest));
    }

    [Fact]
    public void MissingTruncatedAndWrongHashPartsFail()
    {
        string index = Path.Combine(_root, "rf017.rez");
        SyntheticRez.Write(index, [
            new SyntheticRezFile("PLAYERVIEW/gun.dtx", "GOOD"u8.ToArray(), Time: 8, Offset: 400, InIndex: false, WritePart: true)
        ]);
        string part = Path.Combine(_root, "rf017_8.rez");
        RezArchive archive = new RezArchiveReader().Read(index);
        RezFileNode file = RezVerifiedPayloadReader.FindFile(archive, "PLAYERVIEW/gun.dtx");

        File.WriteAllBytes(part, "NOPE"u8.ToArray());
        Assert.Throws<InvalidDataException>(() => RezVerifiedPayloadReader.Read(archive, file));

        File.WriteAllBytes(part, "G"u8.ToArray());
        Assert.Throws<InvalidDataException>(() => RezVerifiedPayloadReader.Read(archive, file));

        File.Delete(part);
        Assert.Throws<InvalidDataException>(() => RezVerifiedPayloadReader.Read(archive, file));
    }

    [Fact]
    public void TimestampWithoutPartUsesMainFile()
    {
        string index = Path.Combine(_root, "rf017.rez");
        byte[] main = "MAIN"u8.ToArray();
        SyntheticRez.Write(index, [
            new SyntheticRezFile("root.dtx", main, Time: 1_700_000_000, Offset: 400, InIndex: true)
        ]);
        RezArchive archive = new RezArchiveReader().Read(index);
        RezVerifiedPayload payload = RezVerifiedPayloadReader.Read(
            archive,
            RezVerifiedPayloadReader.FindFile(archive, "root.dtx"));
        Assert.Equal("main_file", payload.Routing);
        Assert.Equal(main, payload.Data);
    }

    [Fact]
    public void TwoMatchingCandidatesAreAmbiguous()
    {
        string index = Path.Combine(_root, "rf017.rez");
        byte[] good = "GOOD"u8.ToArray();
        SyntheticRez.Write(index, [
            new SyntheticRezFile("PLAYERVIEW/gun.dtx", good, Time: 8, Offset: 400, InIndex: true, WritePart: true)
        ]);
        RezArchive archive = new RezArchiveReader().Read(index);
        Assert.Throws<InvalidDataException>(() =>
            RezVerifiedPayloadReader.Read(archive, RezVerifiedPayloadReader.FindFile(archive, "PLAYERVIEW/gun.dtx")));
    }

    [Fact]
    public void MissingMd5DoesNotGuessNumberedPart()
    {
        string index = Path.Combine(_root, "rf017.rez");
        RezFileNode file = SyntheticRez.Node("PLAYERVIEW/gun.dtx", 0, 4, 8, "not-an-md5");
        File.WriteAllBytes(index, "BAD!"u8.ToArray());
        File.WriteAllBytes(Path.Combine(_root, "rf017_8.rez"), "GOOD"u8.ToArray());
        Assert.Throws<InvalidDataException>(() => RezVerifiedPayloadReader.Read(index, file));
    }

    [Fact]
    public void DeepPathsKeepParentDirectories()
    {
        string index = Path.Combine(_root, "rf017.rez");
        SyntheticRez.Write(index, [
            new SyntheticRezFile("PLAYERVIEW/gun.dtx", "PVPV"u8.ToArray(), Time: 0, Offset: 500, InIndex: true),
            new SyntheticRezFile("WEAPONS/gun.dtx", "QVQV"u8.ToArray(), Time: 0, Offset: 504, InIndex: true)
        ]);
        RezArchive archive = new RezArchiveReader().Read(index);
        string destRoot = Path.Combine(_root, "extract");
        foreach (RezFileNode file in RezVerifiedPayloadReader.EnumerateFiles(archive.Root))
        {
            RezArchiveReader.ExtractFile(archive, file, Path.Combine(destRoot, file.FullPath.Replace('/', Path.DirectorySeparatorChar)));
        }

        Assert.Equal("PVPV"u8.ToArray(), File.ReadAllBytes(Path.Combine(destRoot, "PLAYERVIEW", "gun.dtx")));
        Assert.Equal("QVQV"u8.ToArray(), File.ReadAllBytes(Path.Combine(destRoot, "WEAPONS", "gun.dtx")));
    }

    [Fact]
    public void DirectoryCacheColdAndHotAgreeAndIgnoreLegacyVersion()
    {
        string index = Path.Combine(_root, "rf017.rez");
        SyntheticRez.Write(index, [
            new SyntheticRezFile("PLAYERVIEW/gun.dtx", "GOOD"u8.ToArray(), Time: 8, Offset: 800, InIndex: false, WritePart: true)
        ]);
        var reader = new RezArchiveReader();
        RezArchive cold = reader.Read(index);
        RezArchive hot = reader.Read(index);
        Assert.Equal(1, cold.FileCount);
        Assert.Equal(1, hot.FileCount);
        Assert.Equal(
            RezVerifiedPayloadReader.FindFile(cold, "PLAYERVIEW/gun.dtx").Md5,
            RezVerifiedPayloadReader.FindFile(hot, "PLAYERVIEW/gun.dtx").Md5);
    }

    [Fact]
    public void ThumbnailCacheKeyChangesWhenNumberedPartChanges()
    {
        string index = Path.Combine(_root, "rf017.rez");
        SyntheticRez.Write(index, [
            new SyntheticRezFile("PLAYERVIEW/gun.dtx", "GOOD"u8.ToArray(), Time: 8, Offset: 400, InIndex: false, WritePart: true)
        ]);
        RezArchive archive = new RezArchiveReader().Read(index);
        RezFileNode file = RezVerifiedPayloadReader.FindFile(archive, "PLAYERVIEW/gun.dtx");
        var item = new ExplorerItem
        {
            Name = file.Name,
            Kind = ExplorerItemKind.RezFile,
            Archive = archive,
            ArchiveFile = file
        };
        Assert.True(ThumbnailDiskCache.TryBuildCacheKey(item, out string? before));
        File.WriteAllBytes(Path.Combine(_root, "rf017_8.rez"), "GOOD!"u8.ToArray());
        Assert.True(ThumbnailDiskCache.TryBuildCacheKey(item, out string? after));
        Assert.False(string.Equals(before, after, StringComparison.Ordinal));
    }

    [Fact]
    public void NumberedPartFilesAreDetectedBesideAnIndex()
    {
        string index = Path.Combine(_root, "rf017.rez");
        SyntheticRez.Write(index, [
            new SyntheticRezFile("PLAYERVIEW/gun.dtx", "GOOD"u8.ToArray(), Time: 8, Offset: 400, InIndex: false, WritePart: true)
        ]);
        Assert.True(RezVerifiedPayloadReader.IsNumberedPartFile(Path.Combine(_root, "rf017_8.rez")));
        Assert.False(RezVerifiedPayloadReader.IsNumberedPartFile(index));
        string orphan = Path.Combine(_root, "orphan_8.rez");
        File.WriteAllBytes(orphan, "x"u8.ToArray());
        Assert.False(RezVerifiedPayloadReader.IsNumberedPartFile(orphan));
    }
}
