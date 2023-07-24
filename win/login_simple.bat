@echo off
chcp 65001

whoami /priv | find "SeDebugPrivilege" > nul
if %errorlevel% neq 0 (
　powershell -command start-process "./login_simple.bat" -verb runas
　echo 管理者権限がありません。管理者権限で実行します
 timeout 2
　exit
)
echo 管理者権限に自動で昇格できました。

if %ERRORLEVEL% equ 0 (
  echo 管理者権限で実行しています。
) else (
  echo 管理者権限で実行していません。
  exit
)

echo.
echo Ctrl+Alt+Delキーでロックを解除する設定を無効化します。
echo.
echo ポリシーからDisableCADを削除します。
echo.
reg delete "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /f /v DisableCAD

echo Windowsのロック画面を無効化します

@echo on
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows\Personalization" /f /v "NoLockScreen" /t reg_dword /d 1
timeout 2