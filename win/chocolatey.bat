chcp 65001

echo.
echo このバッチは必ず管理者権限で実行してください。
echo.
echo Chocolateyのインストールを行います。
echo.

@"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command "iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))" && SET "PATH=%PATH%;%ALLUSERSPROFILE%\chocolatey\bin"

echo.
echo Chocolateyのバージョン確認を行います。
echo.

chocolatey -v

echo.
echo 各ソフトウェアのインストール処理を行います。
echo.

powershell -Command "Get-AppxPackage *spotify* | Remove-AppxPackage"

cinst -y 7zip.install googlechrome google-drive-file-stream bitwarden eartrumpet skype foxitreader powershell-core everything audacity handbrake aimp slack sublimetext3.app vlc gimp git vscode discord googlejapaneseinput bind-toolsonly scrcpy adb f.lux notepadplusplus.install bitwarden-cli line unifying vnc-viewer awscli etcher sdcard-formatter obs-studio pandoc drawio firefox psping portqry voicemeeter-banana.install audio-router garmin-express speccy freefilesync mousewithoutborders adobe-creative-cloud equalizerapo kindle spotify edgedeflector inkscape screentogif speedtest nmap

start ms-windows-store:
echo ストアにマイクロソフトアカウントでログインしてください。ログインが完了したら任意のキーを押してください。
pause > NUL

winget install --accept-package-agreements "Drawboard PDF"
winget install --accept-package-agreements "Amazon Prime Video for Windows"
winget install --accept-package-agreements "Monitorian"
winget install --accept-package-agreements "Microsoft PowerToys"
winget install --accept-package-agreements "Windows Terminal"
winget install --accept-package-agreements "Spotify"
winget install --accept-package-agreements "Zoom"
winget install --accept-package-agreements "Netflix"
winget install --accept-package-agreements "Amazon Kindle"
winget install --accept-package-agreements "TaskbarX"

echo powershell-coreはpowershell ver7のことです。win10に標準でインストールされているpowershellはver5です。
echo.
echo Notepad++(64bit)をメモ帳と置き換えします。

reg add "HKLM\Software\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\notepad.exe" /v "Debugger" /t REG_SZ /d "\"%ProgramFiles%\Notepad++\notepad++.exe\" -notepadStyleCmdline -z" /f

echo CapsキーをCtrlに割り当てます

reg add "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Keyboard Layout" /v "Scancode Map" /t reg_binary /d 

echo.
echo Ctrl+Alt+Delキーでロックを解除する設定を無効化します。
echo.
echo ポリシーからDisableCADを削除します。
echo.

reg delete "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /f /v DisableCAD

netplwiz

echo ユーザーアカウントの設定ウィンドウが開くので、詳細設定タブ→セキュリティーで保護されたサインイン→ユーザーが必ず...のチェックを外してください。
pause

echo Windowsのロック画面を無効化します

reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows\Personalization" /f /v "NoLockScreen" /t reg_dword /d 1

echo.
echo Chocolateyを用いたソフトウェアのインストールを完了しました。
echo.

timeout 15