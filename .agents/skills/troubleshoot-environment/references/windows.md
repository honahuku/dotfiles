# WindowsとPowerShellの環境調査

Windows上で直接作業するときに読む。CLIの実行、権限昇格、編集は共通の操作制約を優先し、この資料を追加の実行許可として扱わない。

以下のルールは、Windows上で直接コマンドを実行するときだけ適用する。

### 過去のPython実行環境

過去のWindows環境では、グローバルの`python`がMicrosoft Storeのアプリ実行エイリアスを指し、`py`もサンドボックス内で使えない場合があった。この環境では、許可されたPython実行にCodex同梱の実行ファイルを使う方法を優先していた。

同梱Pythonの配置先は次の形式だった。現在の実体は実機で確認する。

`<ユーザープロファイル>\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`

許可されたPython例外の調査で必要な場合にだけ、次の形式を参考にする。

```powershell
& '<ユーザープロファイル>\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
```

### GitHub CLIの実行

GitHub CLIの`gh`を使う場合は、`sandbox_permissions: "require_escalated"`で権限昇格を要求し、Codexのサンドボックス外で実行する。サンドボックス内ではホストのGitHub認証情報を読めず、マシン上で認証済みでもコマンドが失敗する場合がある。

サンドボックス内で再認証するよりも、必要な`gh`コマンドについて簡潔な理由を添えて権限昇格を要求する方法を優先する。`prefix_rule`は、具体的に繰り返す操作に合う場合だけ、範囲を狭く指定する。

### ファイル編集で失敗した場合

Windows上のCodexでは、Windowsのサンドボックスの問題により、`apply_patch`が編集前に失敗する場合がある。特に、`workspace-write`、`unelevated`の制限付きトークン、複数の書き込み可能なルートを使う構成で起こりやすい。

関連するエラーメッセージには、次のものがある。

- `failed to prepare windows sandbox wrapper`は、Windowsサンドボックスのラッパーを準備できないことを示す。
- `windows unelevated restricted-token sandbox cannot enforce split writable root sets directly`は、非昇格の制限付きトークンでは、分かれた書き込み可能なルートを直接制御できないことを示す。
- `refusing to run unsandboxed`は、サンドボックス外での実行を拒否したことを示す。

この理由で`apply_patch`が失敗した場合は、再試行を繰り返さない。通常のテキスト編集では、次の順で代わりの方法を試す。

1. 統一差分を`git apply --check`で検証し、成功したら`git apply`で適用する。Gitが使える場合は、未追跡ファイルにも適用できる。作業ツリーだけを対象にするなら、Gitリポジトリ外でも使える。
2. `git apply`が適さない場合は、共通の操作制約で作成・実行が許可されたスクリプトだけを使う。対象文字列が想定どおりに現れることを確認してから、完全一致で置き換える。書き込み後にファイルを読み直すか、差分を確認する。許可された方法がなければ、`references/manual-handoff.md`に従って本人操作を案内する。
3. 単純でない編集では、PowerShellの正規表現による広範囲な置換を避ける。`Set-Content`は文字コードやCRLF・LFを変えたり、末尾に不要な空行を追加したりする場合があるため、編集後は`git diff`、`git diff --check`などで確認する。

編集は依頼されたファイルに限定し、変更を最小限にする。代わりの方法で作業領域の外に書き込む必要がある場合は、簡潔な理由を添えて権限昇格を要求する。

コミットメッセージを書くときは、OSにかかわらず`apply-git-strategy`の`references/naming.md`に従う。
