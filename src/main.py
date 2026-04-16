import os
import sys

from openai import OpenAI
from dotenv import load_dotenv

from fetcher import fetch_articles
from ranker import filter_recent, score_all, rank
from llm_judge import batch_judge_themes, generate_summary
from notifier import post_discord, post_slack, _build_message

load_dotenv()

KEYWORDS = [
    "生成AI", "LLM",
    "ChatGPT", "Codex", "Gemini", "Claude", "Claude Code", 
    "AI活用", "組織変革", "経営 AI", "マーケティング AI",
]


def run(dry_run: bool = False) -> None:
    print(f"[1/5] note API からデータ取得中... キーワード数: {len(KEYWORDS)}")
    articles = fetch_articles(KEYWORDS, per_keyword=20)
    print(f"      取得件数: {len(articles)}")

    print("[2/5] 直近14日フィルター + スコア計算...")
    recent = filter_recent(articles, days=14)
    scored = score_all(recent)
    print(f"      候補件数: {len(scored)}")

    print("[3/5] GPT-4o-mini でテーマ適合性を判定中...")
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    scored = batch_judge_themes(scored, client)

    print("[4/5] ランキング（buzz / engagement 各軸上位5件）...")
    top = rank(scored, top_k=5, theme_threshold=0.5)
    print(f"      通知対象: {len(top)} 件")

    print("[5/5] 通知文生成...")
    messages = []
    for s in top:
        summary = generate_summary(s, client)
        messages.append(_build_message(s, summary))
        print(f"  - {s.article.title[:40]}...")

    if dry_run:
        print("\n--- DRY RUN: 通知内容プレビュー ---")
        for m in messages:
            print(m)
            print("---")
        return

    if os.environ.get("DISCORD_WEBHOOK_URL"):
        post_discord(messages)
        print("Discord に送信しました")

    if os.environ.get("SLACK_WEBHOOK_URL"):
        post_slack(messages)
        print("Slack に送信しました")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    run(dry_run=dry_run)
