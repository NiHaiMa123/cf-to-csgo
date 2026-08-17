' 启动 GSI 语音联动机器人（静默后台运行）。
' 用脚本自身所在目录定位 gsi_voice_bot.py，任意位置双击均可运行。
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "python """ & scriptDir & "\gsi_voice_bot.py""", 0, False
