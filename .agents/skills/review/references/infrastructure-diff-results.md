# インフラ差分の列挙と表示

TerraformのplanとKubernetes manifestのGit差分に共通して適用する。

## 透明性と省略しない理由

読み手が、Coding Agentsのグルーピングの判断過程をたどり、元の差分と説明を自分で照合できるようにする。透明性の担保には、資料に書かれた分類とCoding Agentsによる推測を区別し、全リソースを示すことが必要である。グルーピングによってリソースを省くと、影響範囲やdestroy対象の見落としを読み手が検出できなくなる。簡潔さや説明の重複回避を理由に、リソースを省略しない。

## グルーピングと照合

- まず全リソースの操作を抽出し、その後に分類する。環境・stackまたはoverlayの下に、変更の目的や対象システムでグループを作り、その一段下へ全リソースを箇条書きで並べる。同じ差分でも別リソースや別環境を「同様」「ほか」「など」で省かない。
- PR本文、PRコメント、コードコメントに分類やまとまりが書かれていれば、それを使う。記載がなければCoding Agentsが推測してよい。この許可は分類に限り、操作・値・実効権限を推測する許可にはしない。
- 各グループ名の直後に、根拠や判断過程が分かる短い括弧書きを必ず付ける。例えば「ベースイメージ更新（PR本文のSummaryに基づく）」や「配信基盤の更新（コードの参照関係からCoding Agentsが推測）」とする。資料に基づく場合は該当セクション、コメントへのリンク、またはファイルと行番号を示す。資料と推測を組み合わせた場合も、補った部分が分かるように書く。
- 環境・stackまたはoverlayごとに全件一覧と集計を照合する。全文の貼り付けや集計だけでリソースごとの説明を代替しない。機密値を伏せる場合も、リソースと操作は省略しない。

## 操作名と強調

操作名はTerraform・manifestとも`add`、`change`、`destroy`、`replace`をそのまま使い、日本語の操作名に置き換えない。属性によってreplaceが必要になることを表す`forces replacement`、未確定値を表す`known after apply`も英語のまま使う。元の出力にこの表示があるときに用い、根拠なくforces replacementを付けたり、機密値やmanifestに存在しない属性を勝手にknown after applyとしたりしない。

読み手がdestroyとreplaceを必要とする属性をすぐ見分けられるように、正のdestroyと、出力に現れたforces replacementを太字にする。addやchangeまで強調すると注意すべき対象が埋もれるため、それらや行全体・集計全体を太字にしない。replace自体も強調せず、含まれるdestroyの部分だけを太字にする。0 to destroyは太字にしない。diffやコードブロック内ではMarkdownの太字が表示されないため、forces replacementの強調はブロック外の属性説明に添え、元のdiffは保つ。

| 用途 | 表示 |
| --- | --- |
| 個別リソース | `resource-address`：add / change / **destroy** |
| replaceの内訳 | `resource-address`：replace＝1 to add・**1 to destroy** |
| replaceを必要とする属性 | `attribute`：旧値 → 新値（**forces replacement**） |
| destroyありの集計 | 1 to add、1 to change、**1 to destroy** |
| destroyなしの集計 | 1 to add、1 to change、0 to destroy |
| 未確定値 | `attribute`：known after apply |

Kubernetes manifestでのdestroyはGit上から定義が消えることを表す。Terraformのplanが示すdestroyや、実際のクラスター操作と混同しない。識別子が変わった別リソース同士を、見た目のためにreplaceへまとめない。
