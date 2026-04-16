import os

import httpx

from scorer import ScoredArticle


def _build_message(scored: ScoredArticle, summary: str) -> str:
    a = scored.article
    paid_label = "💰有料" if a.is_paid else ""
    return (
        f"**{a.title}** {paid_label}\n"
        f"{summary}\n"
        f"スキ {a.likes} / フォロワー {a.creator_followers:,}\n"
        f"{a.url}"
    )


def post_discord(messages: list[str], webhook_url: str | None = None) -> None:
    url = webhook_url or os.environ["DISCORD_WEBHOOK_URL"]
    header = "📰 **noteトレンド記事** （本日のピックアップ）\n━━━━━━━━━━━━━━━━"
    body = "\n\n".join(messages)
    payload = {"content": f"{header}\n\n{body}"}

    with httpx.Client(timeout=10.0) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()


def post_slack(messages: list[str], webhook_url: str | None = None) -> None:
    url = webhook_url or os.environ.get("SLACK_WEBHOOK_URL")
    if not url:
        return
    header = ":newspaper: *noteトレンド記事*（本日のピックアップ）"
    body = "\n\n".join(messages)
    payload = {"text": f"{header}\n\n{body}"}

    with httpx.Client(timeout=10.0) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()
