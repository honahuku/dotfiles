# worktreeの準備・再利用・整理

## 作業開始

- 個人用のdotfiles・スキル・共通指示の改善依頼では、継続依頼も含め、着手前に日本時間の現在日時を取得し、`~/.agents/skills/write-agent-instructions/references/context-policy.md`の「個人用の改善に着手する時間帯」を参照する。対象作業・現在時刻・例外を照合し、対象時間ならworktree作成や編集へ進まず、Obsidianの`inbox.md`へ未完了タスクだけを記録する。前のターンの時刻や、過去に着手した事実を継続の許可にしない。
- 実際のrepoの場所と適用される指示を確認し、`~/.agents/skills/apply-git-strategy/references/git-policy.md`に従ってGit操作の許可範囲を判定する。
- worktree作成がCoding Agentsに禁止されているリポジトリでは、mainへの直接編集で代替しない。制約を報告するだけで終えず、本人が安全に実行できる場合は、確認済みのブランチ・worktree状態に合わせて必要なGit操作を案内する。本人へのコミット依頼は共通の`~/.agents/skills/apply-git-strategy/references/git-policy.md`のlazygit・依頼分離の規則に従い、worktreeの絶対パスと対象ファイルを自然文で示す。許可された事前・事後確認はCoding Agentsが行い、未コミット差分などで判断できない場合は確認済みの状態と未決事項を伝える。
- ブランチを作成する前に、既存差分、ローカル・リモートのブランチ、登録済みworktree、同じトピックのopen PRを確認する。同じトピックのブランチやopen PRがあれば、そのブランチを使う。ローカルにない場合も既存のリモートブランチを追跡し、別名の同一トピックブランチを作らない。別ブランチへの分離には本人の明示許可が必要であり、レビュー・検証・修正という作業種別の違いだけを分離理由にしない。
- 同じセッションで同じrepoに作成済みのworktreeがあれば再利用する。そのworktreeでは目的を達成できず追加作成が必要な場合だけ、既存の状態と再利用できない理由を示して本人の許可を得る。別repoでの最初の作成や、別セッションのworktreeの存在だけを理由に確認を求めない。
- `main`ブランチは元clone直下の作業ツリーに置き、`main`用worktreeは作らない。`main`への直接編集は禁止する。Obsidian vaultを除くGit管理下の編集は、同じトピックの既存ブランチのworktreeで行う。該当するブランチがない新規作業では、`main`から専用ブランチを作成する。
- 新規worktreeは、所有者や組織を問わず、元のclone直下の `<repo>/.worktree/<branch>` に置く。`/tmp`・兄弟ディレクトリ・`<repo-name>-worktrees/`には作らない。作業中のworktree内にさらに `.worktree/` を作らず、元のclone直下に並べる。**`<branch>` は`main`以外のブランチ名そのままで、省略・改変しない。** 既存worktreeは `git worktree list` で確認し、`main`以外のブランチで目的に合う場合だけ再利用する。worktreeを自動で移動・削除しない。
- リンク経由で編集する場合は、リンク先の実体と所属リポジトリを確認する。保存先を決める前に、依頼の対象ファイルが既存のGitリポジトリに属するか確認する。チャットのcwdがリポジトリ外でも、対象リポジトリ内の登録済みworktreeを使う。worktreeの登録と元のcloneとの対応は、`git -C <repo> worktree list --porcelain`と`git -C <worktree> rev-parse --show-toplevel`で確認する。
- リポジトリの文書・コード・差分・ログ・校正用の複製は、そのworktree内に保存する。表示やリンクのためにチャットの`work/`・`outputs/`や`/tmp`へ複製・書き出ししない。リポジトリを持たない独立した依頼だけ、チャット用の保存先を使う。リポジトリ外への持ち出しは、対象と保存先をユーザーが明示した場合だけ行う。チャット用ディレクトリへの案内やリンク表示の制約だけを、持ち出しの許可と解釈しない。
- worktree作成前に、`~/.agents/skills/apply-git-strategy/references/git-policy.md`の「Git操作の許可範囲」を確認する。`git -C <repo> rev-parse --path-format=absolute --git-path info/exclude`で対象を特定する。現在の内容を読み、`/.worktree/`がなければ既存内容を残して追記し、`git -C <repo> check-ignore -v .worktree/<branch>`で適用を確認する。共有の`.gitignore`とglobal ignoreは変更しない。
- Git操作は可能なら `git -C <path>` 形式で実行する。
- 削除・置換で本人操作が必要な場合も、許可された確認・準備はCoding Agentsが実行し、実行済みのコマンドと結果を示す。worktreeなど管理対象の削除では、標準の削除機能と直接削除を比較し、推奨方法と理由を示す。直接削除を選ぶ場合は`rm`で示して本人のtrash aliasを保持し、コマンド自体の絶対パス指定・`rmdir`・alias迂回を使わない。本人操作だけを別のコードブロックに分け、報告後の検証もCoding Agentsが行う。詳細は`troubleshoot-environment`の手動依頼手順に従う。
- `git rebase` は実行しない。ベースブランチの取り込みにはmergeを使う。worktreeとmainの差を手動同期で埋めず、許可されたmergeで反映する。
- **vendir syncなどのディレクトリ同期コマンドは、実行前に公式仕様またはヘルプで既存ファイルの削除・置換挙動を確認する。** スキルの同期には`~/.agents/skills/write-agent-instructions/references/context-policy.md`の同期条件を適用する。それ以外で管理対象の既存ファイルを削除する可能性がある場合は実行しない。読み取り専用のdiff機能や設定・現物から対象と必要性を判断し、必要な削除・置換は`troubleshoot-environment`に従って手動実行用コマンドを示す。実行できない理由の報告だけで終えない。
- 設定移行や競合解消では、共通指示の削除規則に従って必要性を判断し、必要な手動操作をコマンドで示す。merge時の`D`は、対象コミットの削除理由・現物・参照先・未コミット差分を調べる。本人の削除後は、対象パスが存在せず、`git status --short -- <path>`と`git diff -- <path>`が確認した削除だけであることを確かめる。`HEAD..<target>`に`D`が残ることだけで再停止しない。削除対象の実ファイルがすべて既に存在せず、保持すべき差分の破棄や追加のファイル削除を生じない場合はmergeを再開する。後続の置換・リンク作成も同じ条件で再開し、独自の退避先へ移して処理を続けない。

## タスクに対応する作業先

タスクの着手・再開、完了時の確認で、対象タスクに対応するworktreeを探す場合に使う。完了時は照合だけを行い、新規作成・切り替えへ進まない。

1. `git rev-parse --show-toplevel`と`git worktree list --porcelain`で、現在のcheckout・元のclone・main以外の登録済みworktreeを確認する。旧配置も登録情報から識別し、ディレクトリ名だけでメインworktreeを判定しない。
2. タスクIDがあれば、ディレクトリ名またはブランチ名に含まれるものを照合する。変更の有無だけで再利用を除外しない。候補が複数なら対象タスクとの対応を確認する。
3. 着手時に目的の合う作業先が見つかれば再利用する。旧配置でも自動で新規作成・移動せず、再利用するものを整理候補から除く。
4. 対応するworktreeがなくても、同じトピックの既存ブランチ・open PRがあれば、そのブランチ用のworktreeを準備する。新しいトピックのブランチ作成は「作業開始」と`references/naming.md`の条件を満たす場合だけ行う。`<repo>`は元のcloneとし、配置を指定できない自動作成ツールは使わない。
5. 準備に失敗した場合は原因を確認し、作業先が確定するまで編集しない。mainへの直接編集へ切り替えない。

## 整理候補の確認

着手時や完了時に不要なworktreeを確認する場合に使う。ファイル・worktree・ブランチの削除は本人操作とする。共有の削除規則と手動依頼の詳細は`~/.agents/skills/apply-git-strategy/references/git-policy.md`と`troubleshoot-environment`に従う。

1. main、再利用するもの、ほかのセッションで使用中のもの、使用状況が不明なものを候補から除く。
2. 各worktreeで`git -C <worktree_path> status --short`・`git -C <worktree_path> diff HEAD`・`git -C <worktree_path> log main..<branch>`を確認する。未追跡を含む作業差分や未マージコミットがあれば保持する。
3. いずれも差分がなく、使用していないことを確認できたものだけ、パスと不要と判断した理由を示す。呼び出し元のスキルに従い、通知する範囲を決める。強制削除を提案しない。
4. 本人操作を案内する場合は、事前確認・実行・事後確認を分ける。標準の`git worktree remove <worktree_path>`はディレクトリと登録をまとめて削除し、trash aliasを使う`rm -r -- <worktree_path>`はディレクトリを退避して登録を残す。復元可能な退避を優先する場合は後者を推奨し、その理由と違いを説明する。直接削除を案内する場合は本人のtrash aliasを保持する。
5. 本人による削除後は`git -C <repo> worktree prune --dry-run`で整理対象を確認する。確認した対象だけを整理できる場合に限り、本人向けに`git -C <repo> worktree prune`・`git -C <repo> branch -d <branch>`を順に示す。他の登録も巻き込む場合は一括実行を案内せず、その状態を調べる。
6. 本人の完了報告後は`git worktree list`・`git branch --list`で結果を確認する。

## 成果物を提示する前

- 今回作成・編集したファイルと、コピー・差分の書き出し先を確認する。ユーザーが外部保存を明示したファイル以外は、対象リポジトリのworktree内に収まっているか確かめる。読み取り・表示だけで足りる場合は、追加ファイルを作らない。
- 元のworktreeのファイルを直接開き、応答でもその保存場所を示す。外部保存の明示依頼がなければ、リンクの表示に制約があっても複製はせず、元のパスを本文で示す。
- リポジトリ外への誤った書き出しを見つけたら、そのファイルの提示・再利用を止める。削除はAGENTS.mdの規則に従って依頼し、削除済みと報告しない。
