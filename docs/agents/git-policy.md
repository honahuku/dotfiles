# Git操作とファイル削除

- コミットメッセージの説明と本文は、明示的な指示がなければ日本語にする。Conventional Commitsのtypeやscopeなど、所定の構文は維持する。

- 本人へGit操作を依頼する前に、`manual-operations.md`の「依頼前の検証提示」を適用し、実行済みの検証コマンドと結果をチャット本文に示す。

- **本人へのコミット依頼はlazygitを前提に、worktreeの絶対パスと対象ファイルを自然文で伝え、差分に基づくConventional Commits形式のコミットメッセージ案も必ず添える。コミット用のコマンドは提示しない。Git操作の依頼と、それ以外のコマンド実行依頼は分け、同じコードブロックや`&&`等で連結しない。**

- **`git rebase` は絶対に実行しない。** 履歴を整理したい場面でも rebase ではなく merge で対応できないか先に考える

- 既存の変更を勝手に破棄しない。stash・強制push・削除・履歴変更は対象と影響を確認してから行う

- `main`ブランチは元clone直下の作業ツリーに置き、`main`用worktreeは作らない。`main`への直接編集は禁止し、変更規模を問わず`main`から作成した専用ブランチのworktreeで作業する。

- mainとの競合は、作業ブランチのworktreeへmainを取り込み、そのworktree内で解消する。main上での競合解消や、そのためのmain直接編集の許可を求めない。取り込み・解消後のステージ・コミットは、それぞれの操作の許可範囲に従う。mainで既にマージが始まっていても、その作業状態を変更せず、作業ブランチ側で進める。

- Git管理下の変更と関連ファイルは、所有者や組織を問わず元のclone直下の`.worktree/<branch>`に置く。表示のためにチャットの`work/`・`outputs/`などへ複製しない。外部保存はユーザーが対象と保存先を明示した場合だけ行う。保存前と提示前は`apply-git-strategy`に従い、反映は許可範囲内のmergeで行う。既存ファイルを`cp`で直接置き換えない。Obsidianは既定の例外に従う

- **ファイル削除（実験ログ・作業結果・スクラッチ出力など、Git管理下でないものも含む）は絶対に実行しない。削除は必ずユーザー自身が行う。** `rm`・`rmdir`・`git rm`・`find -delete`はもちろん、上書きで実質消える操作も対象。`git merge`・`switch`・`checkout`・`reset`・`restore`などで作業ツリー上の既存ファイルが削除・上書きされる場合も実行しない。merge前は`git diff --name-status HEAD..<target>`で削除対象を確認する。`D`があれば、その対象・内容・参照先と削除理由を調べ、削除の必要性を判断する。削除が必要なら、許可された事前確認・準備はCoding Agentsが実行し、実行済みコマンドと実際の結果をコードブロックで示す。本人に必要な削除だけを未実行と明記して別のコードブロックで依頼し、完了報告後の確認もCoding Agentsが行う。片付け・置換・移行も同じ手順とする。**削除の代替として、Coding Agentsが独自に`mv`・trash・アーカイブ・退避ディレクトリを選んで既存物を移動し、先へ進めてはならない。** 削除手順を提示する前に管理元と標準の削除・アンインストール方法を確認し、直接削除との違いと推奨方法・理由を示す。管理ツールの削除機能も本人操作として案内できる。直接ファイル・ディレクトリを削除する場合は`rm`で示し、本人の`rm`→`trash` aliasを保持する。`/usr/bin/rm`・`/bin/rm`などの絶対パス、`rmdir`、`command rm`・`env rm`・`\rm`・`sudo rm`などaliasを迂回する指定を提示しない。ユーザーが明示的に依頼した移動・改名はこの代替禁止の対象外。共通hookの`~/.agents/hooks/command-policy.jq`で削除コマンドを拒否する。

## Git操作の許可範囲

`~/git/*`の既定は次のとおりとする。CLI・API・MCP・サブエージェントへの委譲でも同じ範囲を適用する。

| 操作 | 許可条件 |
| --- | --- |
| 状態を変更しない読み取り | 追加確認なしで実行できる |
| worktreeの準備 | `git worktree add`、それに伴う`-b`でのブランチ作成、clone専用の`info/exclude`への`/.worktree/`追記を追加確認なしで実行できる。既存worktreeの再利用確認などは`apply-git-strategy/references/worktree.md`に従う |
| ステージ | 下記の条件を満たす場合に実行できる |
| commit・push・merge・pull・fetchなど上記以外の書き込み | 本人の明示指示またはリポジトリごとの恒常的な例外が必要 |

worktreeの準備に`--force`や`-B`を使わず、既存状態を強制変更しない。許可した`info/exclude`への追記以外は、index・refs・reflog・Git hookなどへの直接書き込みで制限を迂回しない。

Git書き込みの前に、適用中の上位指示にある恒常的な例外と既定を照合する。確認できない許可を推測しない。子ディレクトリの指示や通常の実装依頼だけで許可範囲を広げない。Git操作の許可は、ファイル削除・hook迂回・apply・デプロイの禁止を解除しない。

- **ステージのみが許可されたリポジトリでは、対象worktreeの作業開始時にステージ済み差分と未解決競合がない場合に限り、`git add`を実行する。** `git status --short --branch`で対象worktreeの状態を確認し、コマンドの作業ディレクトリには対象worktreeの絶対パスを明示する（mainの状態を調べる場合だけ元clone直下を指定する）。作業内容を確認した追加・変更ファイルの明示的なパスだけを一つの`git add -- <path>...`に指定する。削除パス・ディレクトリ・glob・`-A`・`-u`・`-p`は使わない。ステージ状態はworktreeごとのindexに保存される。

- ステージ後は`git diff --cached`と`git status`で結果を確認する。ステージのみが許可されたリポジトリでは、いったんステージした後の追加ステージは禁止する。

- `status`・`log`・`show`・`diff`・`grep`・`ls-files`・`rev-parse`・`branch --list`・`tag --list`・`remote -v`・`worktree list`など、状態を変更しない検査は許可する。不明なGit操作は実行せず、本人の指示を仰ぐ。編集時は`apply-git-strategy`の作業開始手順に従う。

- Issue作成は、本人の明示指示または適用中の上位指示で恒常的に許可された対象だけを実行する。この例外をIssueの更新・close・コメント投稿や、リポジトリ作成の許可へ広げない。

- **`honahuku/*`の各リポジトリには、外部OSSをcloneしたディレクトリやGitサブモジュールを含めない。`vendor/`と`.gitmodules`はignoreし、公開前の検査でネストしたGit repoと外部repo用パスを検出する**

## ステージ操作の許可判断

ステージ操作の前に、対象リポジトリに適用される指示と、この資料の許可条件を照合する。条件を満たす`git add`は実行し、Git書き込み全般の禁止だけを理由に拒否しない。特定リポジトリやオプションの禁止を、すべてのステージ操作へ広げない。`git add -p`などの可否も対象に適用される規則で判断し、禁止を説明するときは対象と根拠を示す。

## Git書き込み前後の確認

- ブランチの変更を検査・引き渡す前は、対象ブランチのworktreeで、リポジトリに定義されたpre-commit全体を実行する。Lefthookでは`lefthook run pre-commit --no-auto-install`を使い、個別コマンドや独自に選んだファイルだけの検査で代替しない。実行前にhook定義と呼び出し先を読み、禁止された操作を含まないことを確認する。
- 検査には、本人が指定した設定または対象repoの設定を使う。別worktreeやmainの設定に差し替えない。実行したブランチ・worktree・設定元・コマンド・各検査の結果を対応させ、pre-commit全体が成功した場合だけ全体の検査成功と報告する。ステージ済み差分と未ステージ差分が異なる場合は、hookが実際に検査した範囲も明記する。

- **sandbox環境ではBashの書き込み系コマンド（`git worktree add`/`commit`/`merge`/`push`/`remove`、ファイルシステムやリモートを変更する操作）がブロックされ、実行されないまま成功したふうのダミー出力（それらしいSHAや`Fast-forward`、ファイル一覧など）を返すことがある。** 読み取り系（`git log`/`status`/`worktree list`、`grep`、`test -f`）は本物の値を返す。書き込み系は`dangerouslyDisableSandbox: true`を付けて実行し、実行後は必ず読み取りコマンド（`git log`/`status`/`rev-parse origin/main`/`test -f`）で実際に反映されたか検証してから次に進む。ダミー出力を鵜呑みにしない。commitのheredoc `-F -`はsandbox無効でもstdinが渡らず失敗することがあるため`-m`フラグを複数使う。Write/Editツールもsandboxの影響を受けることがあるので、ファイル作成後は`test -f`や`wc -c`で実在を確認する。

- **作業開始時に `git log --oneline -3` でHEADのSHAを控え、mergeの直前にもう一度確認する。確認だけを1回のツール呼び出しで行い、その結果を読んでSHAを比較してから、次の呼び出しでmergeする。検査の呼び出しに、その結果に依存する書き込みを同居させない。動いていたら、そこで止めて別セッションが何をコミットしたかを読む。** 同じリポジトリで複数のセッションが並行して動くと、同じ変更が二重にコミットされる。2026-07-31、`autocmds.lua`に同じ`require`行が2回入った状態がpushされ、後から削除するコミットが必要になった。自分の変更がすでに入っていたら、自分の側のコミットは捨てて重ねない。

- ステージは `git add <path>` でファイルを個別に指定する。`git add -A` と `git add .` は使わない。並行するセッションや手作業の変更を巻き込む。

- Terraform・Kubernetes manifestを編集・mergeで取り込んだ場合は`write-safe-code-and-scripts`のインフラ検証手順を適用し、対象headのCI結果まで確認する。commit前に既存hookと呼び出し先も読み、Terraform検査は`tflint`だけにする。`terraform`・`kubectl`を起動するhookは一時無効化や別経路のcommitで回避せず、許可された恒久修正を行う。必要なCI結果が得られない場合は停止して判断を仰ぐ。

- hookが動くGit操作（commit・mergeなど）は、1回のツール呼び出しにつき1操作だけ実行する。終了コードに加えてWarningを含む全出力を読み、`write-safe-code-and-scripts`の警告確認手順を完了してから、次のGit書き込みを別の呼び出しで行う。同じ`functions.exec`内で後続のadd・commit・pushを予約しない。TruffleHogのエラー時はAGENTS.mdの停止・報告手順に従う。

- **`git commit`の前に、対象リポジトリでlefthookのpre-commit（TruffleHogによるsecret検知）を必ず実行させる。** メインチェックアウトの`.git/hooks/pre-commit`に`LEFTHOOK_CONFIG`でメインの`lefthook.yml`の絶対パスを固定注入済みの独立リポジトリでは、worktree側に`lefthook.yml`を個別配置しなくても発動する（hooksはworktree間で共有されるがconfigはworktree自身のトップレベルからしか探索されないため、`LEFTHOOK_CONFIG`で固定する対応が必要になる）。まだこの対応をしていない独立リポジトリ（新規clone直後など）では、`lefthook.yml`（`extends: [~/.lefthook-global.yml]`のみ）をトップレベルに作成して`lefthook install`し、生成された`.git/hooks/pre-commit`の`call_lefthook()`定義の直前に`export LEFTHOOK_CONFIG="<トップレベルの絶対パス>/lefthook.yml"`を追記してから`git commit`する。`LEFTHOOK=0`や`--no-verify`でのスキップは絶対禁止のhook迂回に当たるため使わない。




## Git・GitHub CLIの実行

- `git`と`gh`は、読み取り操作を含め初回から毎回サンドボックス外で実行する。必要な実行ツールでは`sandbox_permissions: "require_escalated"`を指定し、承認手続きに従う。
- この実行方法は許可済みだが、Git操作自体の許可は広げない。リポジトリごとの操作制限を引き続き適用する。

## GitHub Issueの作成・本文更新

- 本文を書く前に、対象リポジトリの作業指示と`.github/ISSUE_TEMPLATE/`を確認し、用途に合うテンプレートを実際に読む。ローカルにない場合はGitHubから取得する。過去のIssueや記憶をテンプレート確認の代わりにしない。
- テンプレートの見出し・順序・必須項目を使って本文を組み立てる。独自の見出しへ置き換えず、詳細は該当項目の下へ整理する。空欄・省略が許される項目はテンプレートの指示に従う。
- 投稿直前に、本文を読み取ったテンプレートと照合し、見出し・順序・必須項目の欠落を確認する。CLI・API・プラグイン経由でも省略しない。テンプレートの有無や内容を確認できない場合は投稿せず、その状況を報告する。テンプレートがないと確認できた場合だけ自由形式で作成する。
- 投稿・本文更新後はIssueを再取得し、意図した本文とテンプレートの構成が反映されていることを確認してから完了を報告する。
