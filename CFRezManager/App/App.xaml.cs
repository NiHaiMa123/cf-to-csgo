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
            ExtractTool.Run(e.Args[1], e.Args[2]);
            Shutdown(0);
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
    public static void Run(string cfPath, string outPath)
    {
        var files = System.IO.Directory.GetFiles(cfPath, "*.rez", System.IO.SearchOption.AllDirectories);
        var reader = new RezArchiveReader();
        foreach (var file in files)
        {
            System.Console.WriteLine($"Extracting {file}...");
            var archive = reader.Read(file);
            ExtractNode(archive, archive.Root, System.IO.Path.Combine(outPath, System.IO.Path.GetFileNameWithoutExtension(file)));
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
}
