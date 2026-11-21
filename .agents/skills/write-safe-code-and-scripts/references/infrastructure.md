# Terraform・Kubernetes manifestの検証

## Terraform・Kubernetes manifestの検証

直接編集とmergeによる取り込みの両方に適用する。`check-command-policy`の可逆性判断に従い、hook・Makefile・タスク・ラッパーの呼び出し先も実行前に読む。

1. CI定義、呼び出す共通workflow・スクリプト、対象path・環境・実行条件を読み、今回必要な検査を特定する。workflowが存在するだけで実行済みと扱わない。
2. 利用可能な検査を、CIと同じバージョン・設定・入力でローカル実行する。Terraformは`tflint`、manifestはCIで採用されている`yamllint`・Kubeconform・OPA/`conftest`等を使う。renderが必要なら生成コマンドとCIと同じschema・policyを使う。`yq`の構文確認だけでschema・policy検査を代替しない。
3. `tfcmt`は既存CI出力の整形・報告に使うツールとして扱う。Terraform CLIを起動するwrapperとして実行せず、lint・validate・planの代わりにも扱わない。commit hookのTerraform検査は`tflint`のみとする。
4. `terraform`・`kubectl`のfmt・validate・plan・dry-run等はローカルで実行できる。CIの実行・完了状態・ログ・artifactも確認する。未pushの変更でCI実行が必要なら、検証専用CIを起動するpushを行う。apply・デプロイを起動するpush・rerun・承認は、対象と影響を示して明示許可を得てから行う。pending・skip・未実行を成功と扱わず、古いheadや別環境の成功も流用しない。
5. ローカルで使えない検査はCIで同じ検査の結果を確認する。必要な結果を取得できない場合は、不足する結果とCIの状態を示して判断を仰ぐ。無断で検査を省略・弱体化・追加インストールしない。
6. CI完了後、構文・整形・参照名等の単純な誤りは修正して必要な検査を再確認する。リソースの作成・変更・削除・置換、権限・公開範囲・停止・コスト等の差分は、対象・影響・復旧方法を示して確認する。意図しない差分を隠す修正や、許可のない実リソースへの反映は行わない。
