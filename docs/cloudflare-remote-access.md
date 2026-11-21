# 家庭内開発環境への外部アクセス

Cloudflare Tunnelを家庭内ホストから起動し、Cloudflare Accessで保護した公開ホスト名を通じてSSHとOpenCode Web UIへ接続する。スマートフォンにはcloudflaredやCloudflare One Clientを入れず、ブラウザーでAccess認証を行う。カスタムWorkerやOpenCode内蔵のリバースプロキシは使わない。

## 通信経路

```text
スマートフォン / PC
  ├─ Access認証 → SSHブラウザー端末 → Tunnel → 127.0.0.1:22
  └─ Access認証 → OpenCode Web UI → Tunnel → 127.0.0.1:49374
```

TunnelはホストからCloudflareへの発信接続を使う。インターネットから家庭内ホストへの受信ポート転送は設定しない。Accessの認証に加えて、OpenCodeの公開ホスト名ではTunnelの「Protect with Access」を有効にし、`cloudflared`側でもAccess JWTを検証する。Tunnelトークンは誰でもそのTunnelへ接続できる秘密情報のため、リポジトリに保存しない。

## Cloudflare側の設定

既存のCloudflare Accessポリシーを使い、SSH用とOpenCode用の公開アプリケーションを許可対象を絞って用意する。

- SSHの公開アプリケーションルートはSSHサービスをローカルの`localhost:22`へ向け、Accessのブラウザー端末を有効にする。接続時はAccess認証に加えて、SSHサーバーのアカウント認証も必要。
- OpenCodeの公開アプリケーションルートは`http://localhost:49374`へ向け、対応するAccessアプリケーションを先に作成する。ルートの「Protect with Access」を有効にする。
- 両方のルートで、意図したAccessアプリケーションが先に適用され、許可対象外の利用者が拒否されることを確認する。

公開ホスト名とAccessアプリケーションの設定はCloudflare側で管理し、dotfilesには含めない。ホスト名や既存ポリシーを確認できないまま、別のアプリケーションや認証ポリシーを作らない。

## ホスト側の準備

Linuxのmise設定でcloudflaredとユーザーsystemdユニットを配置する。

```sh
mise -C linux run setup
```

CloudflareダッシュボードでTunnelを作成し、そのTunnel専用のトークンを取得する。トークンをコマンドライン引数やリポジトリに置かず、次のファイルへ保存する。

```sh
install -d -m 700 ~/.config/cloudflared
install -m 600 /dev/null ~/.config/cloudflared/tunnel-token
```

`~/.config/cloudflared/tunnel-token`をエディターで開き、Tunnelトークンだけを記入する。空白や改行以外の追加内容を入れない。

Cloudflare側でSSHとOpenCodeのルート、Accessアプリケーション、OpenCodeの「Protect with Access」を確認してから、ユーザーサービスを有効化する。

```sh
systemctl --user daemon-reload
systemctl --user enable --now cloudflared-tunnel.service
```

ユーザーがログインしていない間もTunnelを維持するには、ユーザーサービスのlingerが必要。確認は`loginctl show-user "$USER" -p Linger`で行い、無効の場合はユーザーサービスを常時動作させる方法を決めてから変更する。

## 接続と検証

- CloudflareダッシュボードでTunnelがHealthyであることを確認する。
- Access未認証時と許可対象外のアカウントでは、SSH・OpenCodeのどちらも拒否されることを確認する。
- スマートフォンのブラウザーからSSH用ホスト名を開き、Access認証後にSSH端末が表示されることを確認する。
- OpenCodeサービスが`127.0.0.1:49374`で待ち受けている状態で、スマートフォンのブラウザーからOpenCode用ホスト名を開き、既存セッションを閲覧・操作できることを確認する。
- 接続できない場合は、Tunnelの状態、Cloudflare Access認証ログ、`journalctl --user -u cloudflared-tunnel.service`を確認する。Access保護を外した状態での公開は行わない。
