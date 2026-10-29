# コミットの整理・委譲と個人設定の反映

## コミットの整理

コミットの整理を行う場合は、リポジトリの操作制限と対象・影響を先に確認する。force pushは禁止。どうしても必要なら手順をユーザーに示して。許可された操作だけを行う。

## 既存PRへの変更とpush

- 着手時に`gh pr view <番号> --repo <owner/repo> --json headRefName,headRefOid,url`で既存PRのheadを取得し、`git worktree list --porcelain`と照合して同じブランチのworktreeを使う。同じトピックの既存PRがある場合、別ブランチ・worktreeは本人が明示した場合だけ作る。名前が似ているworktreeを代用しない。
- push直前にPRのheadとローカルHEAD・push先のremote/refを再照合する。PRのheadブランチをpush先に明示し、不一致があればpushせず原因を確認する。対象worktreeに未コミット変更がある、またはリモートより遅れている場合も、それを理由に別ブランチを作らない。
- push後は`gh pr view`で対象PRの`headRefName`と`headRefOid`がpushしたブランチ・SHAに一致することを確認する。別ブランチへのpush成功や`ls-remote`の一致だけで「PRへ反映済み」と報告しない。

## コミット操作の委譲

委譲先にも同じGit操作の制限を適用する。

次のどれかに当たったら実行を止めて呼び出し元へ報告する。自分で判断して先へ進まない。

- 渡された入力が欠けている、またはメッセージの文面を自分で考える必要がある
- 対象ファイル以外の差分が作業ツリーに混ざっている
- 渡されたSHAからHEADが動いている
- mergeがfast-forwardにならない、コンフリクトが出た、pushが拒否された

## スキルと個人設定

- 個人用hook設定を置く前に`git ls-files -- <path>`で追跡状態を確認する。`info/exclude`は追跡済みファイルの変更を除外しない。共有の`lefthook.yml`へ個人設定を追記せず、exclude済みの`lefthook-local.yml`などのローカル設定口を使う。commit・merge前の差分確認では、個人用設定の混入も確認する。
- 編集先の確認は`worktree.md`の「作業開始」に従う。コミット前に差分と追跡対象を確認する。
- スキルの言語と外部取得物の扱いは、`write-agent-instructions`の「言語・外部取得物・反映」に従う。
- リポジトリ固有の自動コミット・反映方針は、このスキルの`references/`一覧から該当する補足資料を確認し、公開側のGit操作の許可条件と照合する。補足資料がなければ公開側の既定を適用し、恒常許可を推測しない。
