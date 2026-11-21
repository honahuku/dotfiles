---
name: troubleshoot-environment
description: コマンドが見つからない（command not found）、CLI・認証・PATH・alias・関数・シェル初期化・サンドボックスの不具合、設定が反映されない・起動エラーが出る環境の診断と修正後の再検証、セッションへ添付・提示された任意ファイルやWindows・WSL間のファイルの参照不一致、ユーザーと実行環境が異なる場合、hook拒否や、不可逆な操作の明示許可が必要なときに使う。
---

# 環境・CLIの不具合調査

失敗した操作、実行環境、終了コードとエラーを確認し、症状に合う資料だけを読む。禁止操作の代行や、制限を迂回する実行は行わない。

修正後は、症状が出た操作と環境に合わせて再検証し、関連するエラー出力・ログ・画面メッセージが解消したか確認する。終了コード0や別の簡易起動だけを根拠に解決と判断しない。元の症状を再現する操作ができない場合は、未確認の範囲を明示する。

| 症状・操作 | 資料 |
| --- | --- |
| hook拒否・不可逆操作の明示許可・手動編集の依頼 | `references/manual-handoff.md` |
| サンドボックス内の通信・認証・権限エラー | `references/sandbox.md` |
| tasks・gh・aquaの実体・ロック・認証 | `references/cli-auth-and-locks.md` |
| Codexの設定と実際の権限の不一致 | `references/codex.md` |
| セッションへ添付・提示された任意ファイルやWindows・WSL間のファイルの参照失敗、Windows・PowerShellの認証や編集の失敗 | `references/windows.md` |
| WSL から Android 実機を ADB で扱う、USB 接続・`usbipd-win`・Windows 版 `adb.exe` の確認 | `references/android-adb-wsl.md` |
| コマンドが見つからない、本人とalias・関数が異なる、.bashrc・.profileの読み込み不備 | `references/shell-initialization-and-cli-paths.md` |
| Google Cloud project IDが不明 | `references/google-cloud-project-id.md` |
| allowパターンと引用符の不一致 | `references/bash-allow-quote-variants.md` |
| timeout・断続的なエラーなど分散システムの障害 | `references/distributed-failure-investigation.md` |

本人に操作を依頼する場合は、`references/manual-operations.md`も確認し、実行済みの準備と未実行の本人操作を分ける。本人操作を依頼した後は、その完了報告を待って確認する。
