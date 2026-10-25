# Terraformのplan結果を省略せず示す

## 目的

planと説明を読み手が照合できるように、対象の全リソースを示す。透明性の目的、グルーピング、操作名と強調は[共通の表示規則](infrastructure-diff-results.md)に従う。

## 列挙と照合

1. 対象HEADのCIまたはHCP Terraformのrunにあるplan全文を、環境・stackごとに読む。コメントで省略されていれば元のログ、artifact、またはHCP Terraformのrunのplanを取得する。全文を取得できない場合は、未確認の範囲を明示し、既存の停止条件に従う。推測で一覧を埋めたり、全件確認済みと書いたりしない。
2. planのadd・change・destroy対象を、完全なリソースアドレスと操作種別で一件ずつ列挙する。moduleのパス、`count`の添字、`for_each`のキーを残す。
3. 各リソースに何が変わるかを添える。replaceは一件にまとめてよいが、addとdestroyの両方を明記し、planに示された順序も記す。機密値やknown after applyは、その旨を示して推測しない。秘密情報を開示する必要はない。
4. 環境・stackごとに、列挙した操作がplanの`to add`・`to change`・`to destroy`の集計と一致するか照合する。replaceはaddとdestroyの両方に数える。不一致を解消するまで完全な一覧として提示しない。集計に含まれない読み取りや移動等がplanに示されていれば、それらも操作を区別して列挙する。差分のない環境は0 to add、0 to change、0 to destroyと明記し、全リソースの再掲は不要である。
5. 環境・stack、対象HEAD、参照したCI planまたはHCP Terraformのrunのplanへのリンクを一覧に対応付ける。HCP Terraformでplanを確認した場合は、そのrunの該当planを開けるリンクを示す。両方を参照した場合は両方を添えるが、未確認のリンクを推測で作らない。コード差分にない変更や今回の目的と関係しない差分も、planに出ていれば省かない。

## 表示例

以下は架空のリソースを使った例である。

- staging
  - ベースイメージ更新（PR本文のSummaryに基づく）
    - `module.images.aws_imagebuilder_image_recipe.this`：replace＝1 to add・**1 to destroy**。新版を先に作成。`version`は`1.0.0`から`1.0.1`へ変更し、`parent_image`も変更するが値は機密扱いで未確認。
    - `module.images.aws_imagebuilder_image_pipeline.this`：change。`image_recipe_arn`を新レシピへ更新。ARNはknown after apply。
  - 集計：1 to add、1 to change、**1 to destroy**。対象HEADと、参照したCI planまたはHCP Terraformのrunのplanへのリンクを添える。
