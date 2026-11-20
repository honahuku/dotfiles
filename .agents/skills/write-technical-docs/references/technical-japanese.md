# 技術日本語の表記規約とprh検査

## 技術日本語規約

Kubernetes日本語翻訳ガイドを主参照とし、JTF日本語標準スタイルガイドを補助参照とする。一般的な文章表現はyomiyasuが担当するため、ここでは技術文書で使う表記規約だけを扱う。

- 句読点は「、」と「。」を使う。和文の句読点として半角のカンマとピリオドを使わない
- 漢字、ひらがな、カタカナは全角、数字とアルファベットは半角で表記する。半角カタカナは使わない
- 列挙には読点「、」を使う
- Kubernetesのリソース名と固有の技術用語は、公式用語集やAPIリソースの表記を優先する。Pod、Service、Deployment、CronJobなどは不用意に翻訳しない
- KubernetesのNodeリソースを指さない一般名詞は「ノード」と書く
- `cron job`は`cronジョブ`、`CronJob`はリソース名として`CronJob`と書く
- `interface`は「インターフェース」、`proxy`は「プロキシ」、`quota`は「クォータ」と書く
- カタカナ語の長音は、Kubernetes日本語翻訳ガイドの規則に従う。`-er`、`-or`、`-ar`、`-cy`、`-gy`で終わる語は長音を付け、`-ear`、`-eer`、`-re`、`-ty`、`-dy`、`-ry`で終わる語は長音を付けない。「コンテナ」は例外として長音を付けない

参照

- [Kubernetesのドキュメントを翻訳する](https://kubernetes.io/ja/docs/contribute/localization/)
- [JTF日本語標準スタイルガイド](https://www.jtf.jp/jp/style_guide/pdf/jtf_style_guide.pdf)


## 専用prh検査

技術文書を編集した場合だけ、yomiyasuによる調整後に次のコマンドを明示的に実行する。通常の文章編集、hook、pre-commitでは実行しない。

```sh
npx --yes --package prh -- prh --rules ~/.agents/prh/rules-technical-ja.yml <対象ファイル>
```

専用ルールには、明確な表記ゆれ、長音、半角カタカナ、全角と半角、機械的に判定できる句読点だけを置く。文脈が必要な文体、括弧、英日間の空白、コードブロックやURLの解釈はprhで判定しない。検出結果は自動修正せず、対象箇所がコードや固有名詞でないことを確認してから修正する。
