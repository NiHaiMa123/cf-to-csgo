using System.IO;

namespace CFRezManager;

public partial class App : System.Windows.Application
{
    protected override void OnStartup(System.Windows.StartupEventArgs e)
    {
        base.OnStartup(e);

        ShutdownMode = System.Windows.ShutdownMode.OnMainWindowClose;
        if (e.Args.Length >= 3 && e.Args[0] == "--extract-all")
        {
            ShutdownMode = System.Windows.ShutdownMode.OnExplicitShutdown;
            int extractAllCode = ExtractTool.Run(e.Args[1], e.Args[2]);
            Shutdown(extractAllCode);
            return;
        }

        if (e.Args.Length >= 4 &&
            (string.Equals(e.Args[0], "--extract-file", StringComparison.OrdinalIgnoreCase) ||
             string.Equals(e.Args[0], "extract-file", StringComparison.OrdinalIgnoreCase)))
        {
            ShutdownMode = System.Windows.ShutdownMode.OnExplicitShutdown;
            int extractFileCode = ExtractTool.ExtractOne(e.Args[1], e.Args[2], e.Args[3]);
            Shutdown(extractFileCode);
            return;
        }

        if (e.Args.Length >= 3 &&
            (string.Equals(e.Args[0], "--read-hash", StringComparison.OrdinalIgnoreCase) ||
             string.Equals(e.Args[0], "read-hash", StringComparison.OrdinalIgnoreCase)))
        {
            ShutdownMode = System.Windows.ShutdownMode.OnExplicitShutdown;
            int hashCode = ExtractTool.PrintHash(e.Args[1], e.Args[2]);
            Shutdown(hashCode);
            return;
        }

        if (LithTechObjExportCommand.IsInvocation(e.Args))
        {
            ShutdownMode = System.Windows.ShutdownMode.OnExplicitShutdown;
            int exitCode = LithTechObjExportCommand.Run(e.Args);
            Shutdown(exitCode);
            return;
        }

        if (LithTechInspectCommand.IsInvocation(e.Args))
        {
            ShutdownMode = System.Windows.ShutdownMode.OnExplicitShutdown;
            int exitCode = LithTechInspectCommand.Run(e.Args);
            Shutdown(exitCode);
            return;
        }

        if (CfgScanCommand.IsInvocation(e.Args))
        {
            ShutdownMode = System.Windows.ShutdownMode.OnExplicitShutdown;
            int exitCode = CfgScanCommand.Run(e.Args);
            Shutdown(exitCode);
            return;
        }

        if (CfgDecodeCommand.IsInvocation(e.Args))
        {
            ShutdownMode = System.Windows.ShutdownMode.OnExplicitShutdown;
            int exitCode = CfgDecodeCommand.Run(e.Args);
            Shutdown(exitCode);
            return;
        }

        if (ImageDecodeCommand.IsInvocation(e.Args))
        {
            ShutdownMode = System.Windows.ShutdownMode.OnExplicitShutdown;
            int exitCode = ImageDecodeCommand.Run(e.Args);
            Shutdown(exitCode);
            return;
        }

        if (PreviewTool.IsPreviewInvocation(e.Args))
        {
            LocalizedText.UseSavedLanguage();
            ThemeManager.ApplySavedTheme();
            string? errorMessage = null;
            if (PreviewTool.TryGetPreviewPath(e.Args, out string previewPath) &&
                PreviewTool.TryCreateWindow(previewPath, out System.Windows.Window? previewWindow, out errorMessage) &&
                previewWindow is not null)
            {
                MainWindow = previewWindow;
                previewWindow.Show();
            }
            else
            {
                System.Windows.MessageBox.Show(
                    errorMessage ?? LocalizedText.T("PreviewUnsupportedFile"),
                    LocalizedText.T("PreviewFailedTitle"),
                    System.Windows.MessageBoxButton.OK,
                    System.Windows.MessageBoxImage.Information);
                Shutdown(1);
            }

            return;
        }

        LocalizedText.UseSavedLanguage();
        ThemeManager.ApplySavedTheme();
        ThumbnailDiskCache.TryClearLegacyCache();

        var mainWindow = new MainWindow();
        MainWindow = mainWindow;
        mainWindow.Show();
    }
}

public static class ExtractTool
{
    public static int Run(string cfPath, string outPath)
    {
        try
        {
            var files = System.IO.Directory.GetFiles(cfPath, "*.rez", System.IO.SearchOption.AllDirectories);
            var reader = new RezArchiveReader();
            foreach (var file in files)
            {
                if (RezVerifiedPayloadReader.IsNumberedPartFile(file))
                {
                    System.Console.WriteLine($"Skipping numbered part {file}");
                    continue;
                }

                System.Console.WriteLine($"Extracting {file}...");
                var archive = reader.Read(file);
                EnsureUniqueLogicalPaths(archive);
                ExtractNode(archive, archive.Root, System.IO.Path.Combine(outPath, System.IO.Path.GetFileNameWithoutExtension(file)));
            }

            return 0;
        }
        catch (Exception ex)
        {
            System.Console.Error.WriteLine(ex.Message);
            return 1;
        }
    }

    public static int ExtractOne(string archivePath, string logicalPath, string destinationPath)
    {
        try
        {
            var reader = new RezArchiveReader();
            RezArchive archive = reader.Read(System.IO.Path.GetFullPath(archivePath));
            RezFileNode file = RezVerifiedPayloadReader.FindFile(archive, logicalPath);
            RezArchiveReader.ExtractFile(archive, file, System.IO.Path.GetFullPath(destinationPath));
            System.Console.WriteLine($"Extracted {file.FullPath}");
            System.Console.WriteLine($"Output: {System.IO.Path.GetFullPath(destinationPath)}");
            return 0;
        }
        catch (Exception ex)
        {
            System.Console.Error.WriteLine(ex.Message);
            return 1;
        }
    }

    public static int PrintHash(string archivePath, string logicalPath)
    {
        try
        {
            var reader = new RezArchiveReader();
            RezArchive archive = reader.Read(System.IO.Path.GetFullPath(archivePath));
            RezFileNode file = RezVerifiedPayloadReader.FindFile(archive, logicalPath);
            RezVerifiedPayload payload = RezVerifiedPayloadReader.Read(archive, file);
            System.Console.WriteLine($"logical_path={payload.LogicalPath}");
            System.Console.WriteLine($"payload_file={payload.PayloadFile}");
            System.Console.WriteLine($"routing={payload.Routing}");
            System.Console.WriteLine($"sha256={payload.Sha256}");
            System.Console.WriteLine($"md5={payload.DirectoryMd5}");
            System.Console.WriteLine($"size={payload.Size}");
            return 0;
        }
        catch (Exception ex)
        {
            System.Console.Error.WriteLine(ex.Message);
            return 1;
        }
    }

    private static void ExtractNode(RezArchive archive, RezDirectoryNode dir, string currentOutPath)
    {
        foreach (var child in dir.Children)
        {
            if (child is RezDirectoryNode childDir)
            {
                ExtractNode(archive, childDir, System.IO.Path.Combine(currentOutPath, childDir.Name));
            }
            else if (child is RezFileNode childFile)
            {
                string outFilePath = System.IO.Path.Combine(currentOutPath, childFile.Name);
                RezArchiveReader.ExtractFile(archive, childFile, outFilePath);
            }
        }
    }

    private static void EnsureUniqueLogicalPaths(RezArchive archive)
    {
        var duplicates = RezVerifiedPayloadReader.EnumerateFiles(archive.Root)
            .GroupBy(file => file.FullPath.Replace('\\', '/'), StringComparer.OrdinalIgnoreCase)
            .Where(group => group.Count() > 1)
            .Select(group => group.Key)
            .ToList();
        if (duplicates.Count > 0)
        {
            throw new InvalidDataException($"Duplicate logical path in archive: {duplicates[0]}");
        }
    }
}
