#!/usr/bin/env bash
# ミニPC セットアップスクリプト
# 実行: sudo bash deploy/setup.sh <username>
# 例:   sudo bash deploy/setup.sh ubuntu
set -euo pipefail

REPO_URL="https://github.com/shogo-tanaka-work/note-trend-agent.git"
INSTALL_DIR="/opt/note-trend-agent"
SERVICE_USER="${1:?使用するユーザー名を引数で指定してください (例: ubuntu)}"

# ── 1. リポジトリのクローン or アップデート ──────────────────────────────
if [ -d "$INSTALL_DIR/.git" ]; then
  echo "[1/5] リポジトリを更新..."
  git -C "$INSTALL_DIR" pull --ff-only
else
  echo "[1/5] リポジトリをクローン..."
  git clone "$REPO_URL" "$INSTALL_DIR"
fi
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"

# ── 2. Python 仮想環境と依存パッケージ ──────────────────────────────────
echo "[2/5] 仮想環境を構築..."
sudo -u "$SERVICE_USER" python3 -m venv "$INSTALL_DIR/.venv"
sudo -u "$SERVICE_USER" "$INSTALL_DIR/.venv/bin/pip" install -q -r "$INSTALL_DIR/requirements.txt"

# ── 3. .env ファイルの確認 ───────────────────────────────────────────────
if [ ! -f "$INSTALL_DIR/.env" ]; then
  echo "[3/5] .env ファイルを作成（値を手動で設定してください）..."
  cat > "$INSTALL_DIR/.env" <<'EOF'
OPENAI_API_KEY=sk-...
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
EOF
  chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/.env"
  chmod 600 "$INSTALL_DIR/.env"
  echo "    → $INSTALL_DIR/.env を編集してから再実行してください"
  exit 1
else
  echo "[3/5] .env 確認済み"
fi

# ── 4. systemd ユニットのインストール ────────────────────────────────────
echo "[4/5] systemd ユニットをインストール..."
# テンプレートユニット (@) を使ってユーザー名をパラメータとして渡す
sed "s/%i/$SERVICE_USER/g" "$INSTALL_DIR/deploy/note-agent.service" \
  > "/etc/systemd/system/note-agent@.service"
cp "$INSTALL_DIR/deploy/note-agent.timer" \
  "/etc/systemd/system/note-agent@.timer"

systemctl daemon-reload
systemctl enable --now "note-agent@${SERVICE_USER}.timer"

echo ""
echo "[5/5] 完了!"
echo "  タイマー状態: systemctl status note-agent@${SERVICE_USER}.timer"
echo "  手動実行:     systemctl start note-agent@${SERVICE_USER}.service"
echo "  ログ確認:     journalctl -u note-agent@${SERVICE_USER}.service -f"
