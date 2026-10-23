---
name: troubleshoot-environment
description: CLI・認証・PATH・alias・関数・シェル初期化・サンドボックスの不具合、ユーザーと実行環境が異なる場合、hook拒否や本人操作が必要なときに使う。
---

# 環境・CLIの不具合調査

失敗した操作、実行環境、終了コードとエラーを確認し、症状に合う資料だけを読む。禁止操作の代行や、制限を迂回する実行は行わない。

| 症状・操作 | 資料 |
| --- | --- |
| hook拒否・削除や編集など本人の操作が必要 | `references/manual-handoff.md` |
| サンドボックス内の通信・認証・権限エラー | `references/sandbox.md` |
| tasks・gh・aquaの実体・ロック・認証 | `references/cli-auth-and-locks.md` |
| Codexの設定と実際の権限の不一致 | `references/codex.md` |
| Windows・PowerShellの認証や編集の失敗 | `references/windows.md` |
| コマンドが見つからない、本人とalias・関数が異なる、.bashrc・.profileの読み込み不備 | `references/shell-initialization-and-cli-paths.md` |
| Google Cloud project IDが不明 | `references/google-cloud-project-id.md` |
| allowパターンと引用符の不一致 | `references/bash-allow-quote-variants.md` |
| timeout・断続的なエラーなど分散システムの障害 | `references/distributed-failure-investigation.md` |

本人に操作を依頼する場合は、共通の`manual-operations.md`も確認し、実行済みの準備と未実行の本人操作を分ける。本人操作を依頼した後は、その完了報告を待って確認する。共通資料は`~/.agents/docs/common/`にある。
