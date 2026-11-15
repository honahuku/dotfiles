# WSL から Android 実機を ADB で扱う

WSL で Android アプリをビルドし、USB 接続した実機へ ADB でインストールするときの確認手順。Windows 版 `adb.exe` を使う構成と、`usbipd-win` で USB デバイスを WSL へ渡して Linux 版 `adb` を使う構成を扱う。

## 推奨構成

Android SDK、JDK、Gradle、ソースコードは WSL 側に置く。USB 接続と ADB サーバーは Windows 版 Platform-Tools に任せ、WSL から `adb.exe` を呼び出す。

```text
WSL: ./gradlew assembleDebug
  -> Windows: adb.exe install -r <APK>
  -> Android 実機
```

`adb.exe` が PATH にあれば、WSL で次を実行する。

```bash
adb.exe devices -l
adb.exe get-state
adb.exe install -r /path/to/app-debug.apk
```

PATH に反映されていない場合は、Windows の新しいターミナルを開いて PATH を再読込する。見つからない場合は Windows で `where adb.exe` を実行して Platform-Tools の実体を確認し、その絶対パスを WSL から呼ぶ。

```bash
<Windows版Platform-Toolsの絶対パス>/adb.exe devices -l
```

実機側では開発者向けオプションと USB デバッグを有効にし、表示された RSA 認証を許可する。`adb devices` の状態が `device` になれば接続済みである。`unauthorized` の場合は端末の認証ダイアログを確認する。

## WSL へ USB を転送する場合

Windows に `usbipd-win` を導入し、管理者 PowerShell で対象端末を共有する。`BUSID` は `usbipd list` の実際の値に置き換える。

```powershell
usbipd list
usbipd bind --busid <BUSID>
```

通常権限の PowerShell または WSL から、共有済みデバイスを WSL に接続する。

```powershell
usbipd attach --wsl --busid <BUSID>
```

WSL 側で Linux 版 ADB を使う場合は、`adb devices -l` を実行する。ADB サーバーのポート競合や権限エラーが出る場合は、Windows 版 `adb.exe` と Linux 版 `adb` を同時に使わず、どちらか一方の ADB サーバーを使う。

## ビルドからインストールまで

```bash
./gradlew assembleDebug
adb.exe install -r "$(wslpath -w "$PWD/app/build/outputs/apk/debug/app-debug.apk")"
```

APK の場所はプロジェクトのモジュール構成に合わせて変更する。`adb.exe devices -l` で `device` を確認してからインストールする。

## 切り分け

- `adb.exe` が見つからない: 新しい WSL セッションを開き、`command -v adb.exe` と `where.exe adb.exe` を確認する。
- 一覧が空: USB デバッグ、端末の認証ダイアログ、USB 接続モード、ケーブル、`usbipd list` の BUSID と接続状態を確認する。
- `unauthorized`: 端末で RSA 認証を許可し、必要なら USB デバッグの認証を取り消して再接続する。
- Linux 版 `adb` がサーバー起動時に失敗: Windows 版 `adb.exe` に切り替えるか、競合している ADB サーバーを一方に統一する。
