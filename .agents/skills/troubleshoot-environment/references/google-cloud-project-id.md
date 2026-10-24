# Google Cloudのproject IDを確認する

IDが不明な場合は、ユーザーに尋ねる前に対象リポジトリのTerraform・manifest・環境別設定を検索する。環境名から値や末尾の数字を推測しない。認証エラーとID不明を区別し、CLIが使えない場合も許可された読み取り手段を確認する。探索範囲は対象リポジトリに限定し、実行禁止のCLIは使わない。

社内プロジェクト固有の履歴が判断に必要な場合は、非公開資料`~/.agents/docs/work/context.md`の`cloud-project-id`セクションも読む。
