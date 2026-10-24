# Git上のKubernetes manifest差分を検証する

## 比較対象と目的

Git上の変更前後をそれぞれ展開し、実際に生成される全リソースの差分を示す。valuesや共通baseの小さな編集でも、複数の環境・リソースへ影響するため、ソースファイルのdiffだけで判断しない。全件抽出と意味ごとの分類を分ける理由、列挙と表記は[共通の表示規則](infrastructure-diff-results.md)に従う。

既定はGit上の比較とし、稼働クラスターには接続しない。Gitから消えた定義は`destroy`として列挙するが、実リソースが削除されることや適用順は断定しない。実際の削除はデプロイ方式やprune設定等に依存する。APIの既定値、admissionによる変換、実環境との差分は検証範囲に含めない。

## 生成と比較

1. PRのHEADと比較元のSHAを記録する。PR自身の変更はmerge-baseとHEADで比較し、CIが別のbase SHAやマージ結果を使っていれば、その比較条件も区別する。未コミット差分を対象にする場合は明示する。元のcheckoutを切り替えず、`apply-git-strategy`に従って比較用worktreeを用意する。
2. 既存CIの比較対象・生成方法・ログ・artifactを読む。Git同士のdiffかクラスターとのdiffかを確認し、後者をGit差分の根拠にしない。省略されたコメントだけで全件確認済みとしない。
3. 変更したbase、component、values、patch、生成入力を参照する全overlay・環境を追う。変更ファイルの直近ディレクトリだけに限定しない。比較元・比較先の対象の和集合を使い、新設・廃止されたoverlayも含める。
4. 対象SHAのCIに完全なGit差分または前後の生成物があれば利用する。なければ、許可されたstandaloneの`kustomize build`、必要に応じてHelm展開で前後を生成する。実行前に入力と呼び出すコマンドを読み、`kubectl`・AWS CLI・任意コード実行を伴うラッパーやpluginを使わない。この比較は、別途必須のCIやschema・policy検査の代替にはしない。禁止CLIの必須CI結果が不足する場合は、既存の停止条件を維持する。
5. 前後で生成ツールの版、引数、Helm chart・依存先の条件をそろえる。CIと版が異なる場合は、CIと同等の検証とは報告しない。必要なツール・依存先が使えない場合や、生成が失敗した場合は、対象とエラーを示して未検証とする。生成失敗を空のmanifestとして比較しない。前後のどちらかに対象が存在しない場合だけ、新設・廃止として扱う。
6. 生成物をYAMLとして読み、各リソースを`API group / kind / namespace / name`で対応付ける。API versionは比較する属性として残す。namespaceの未指定を勝手に`default`へ補完しない。List形式はitemsのリソースを列挙する。同一識別子の重複や識別子不足は、上書きで隠さずエラーにする。
7. 前後の識別子の和集合から`add`・`change`・`destroy`を全件抽出する。コメント、YAML文書順、マップキー順による差は除いてよいが、配列を一律に並べ替えたり、フィールドを根拠なく除外したりしない。名前やnamespaceの変更を、推測で同一リソースの`change`へまとめない。生成名のハッシュ変更も、旧定義の`destroy`と新定義の`add`を残す。
8. 全件抽出後に意味ごとに分類し、各リソースの属性の前後を`diff`ブロック等で示す。機密値は伏せてもリソースと操作は省かない。環境・overlayごとの件数を全件一覧と照合し、比較SHA、生成コマンド・版、CIまたは生成物の根拠、未検証範囲を対応付ける。既存のワークスルー、評価、approve判断、コメント候補に加えて提示する。

## 表示例

以下は架空のリソースを使った例である。

- dev / namespace `sample`
  - HTTPS入口の切り替え（PR本文のSummaryに基づく）
    - `gateway.networking.k8s.io/Gateway/sample/public`：change。証明書参照の前後をdiffで示す。
    - `networking.gke.io/GCPGatewayPolicy/sample/current`：add。適用先Gatewayと設定を示す。
    - `networking.gke.io/GCPGatewayPolicy/sample/legacy`：**destroy**。Gitから消える旧定義を示す。
  - 集計：1 to add、1 to change、**1 to destroy**。
