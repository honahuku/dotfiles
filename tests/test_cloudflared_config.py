"""Cloudflare TunnelのLinuxユーザーサービス設定を検証する。"""

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "linux" / "systemd" / "user" / "cloudflared-tunnel.service"


def test_cloudflared_service_reads_token_from_file():
    service = SERVICE.read_text(encoding="utf-8")

    assert "run --token-file %h/.config/cloudflared/tunnel-token" in service
    assert "TUNNEL_TOKEN" not in service
    assert "Restart=on-failure" in service


def test_linux_mise_deploys_tunnel_service():
    config = tomllib.loads((ROOT / "linux" / "mise.toml").read_text(encoding="utf-8"))

    assert (
        config["dotfiles"]["~/.config/systemd/user/cloudflared-tunnel.service"]
        == "systemd/user/cloudflared-tunnel.service"
    )


def test_aqua_pins_cloudflared_from_official_registry():
    aqua = (ROOT / "aqua.yaml").read_text(encoding="utf-8")

    assert "name: cloudflare/cloudflared@2026.11.1" in aqua
