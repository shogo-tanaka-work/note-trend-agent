import time
import random
from datetime import datetime

import httpx

from scorer import Article

BASE_URL = "https://note.com/api"
DEFAULT_DELAY = (1.0, 3.0)  # (min, max) seconds


def _delay() -> None:
    time.sleep(random.uniform(*DEFAULT_DELAY))


def _parse_datetime(s: str) -> datetime:
    # note API returns ISO 8601 format: "2024-01-15T12:34:56.000+09:00"
    return datetime.fromisoformat(s)


def search_notes(keyword: str, per_page: int = 20) -> list[dict]:
    """キーワードで記事を検索し、生のレスポンスデータを返す。"""
    url = f"{BASE_URL}/v3/searches"
    params = {"context": "note", "q": keyword, "per": per_page}

    with httpx.Client(timeout=10.0) as client:
        response = client.get(url, params=params)
        response.raise_for_status()

    data = response.json()
    return data.get("data", {}).get("notes", {}).get("contents", [])


def get_creator(creator_id: str) -> dict:
    """クリエイター情報（フォロワー数など）を取得する。"""
    url = f"{BASE_URL}/v2/creators/{creator_id}"

    with httpx.Client(timeout=10.0) as client:
        response = client.get(url)
        response.raise_for_status()

    return response.json().get("data", {})


def fetch_articles(keywords: list[str], per_keyword: int = 20) -> list[Article]:
    """
    複数キーワードで検索し、クリエイター情報を補完した Article リストを返す。
    note_id で重複除去済み。
    """
    seen: set[str] = set()
    articles: list[Article] = []

    for keyword in keywords:
        raw_notes = search_notes(keyword, per_page=per_keyword)
        _delay()

        for note in raw_notes:
            note_id = str(note.get("id", ""))
            if note_id in seen:
                continue
            seen.add(note_id)

            creator = note.get("user", {})
            creator_id = creator.get("urlname", "")

            # クリエイター詳細（フォロワー数）を取得
            try:
                creator_detail = get_creator(creator_id)
                followers = creator_detail.get("followerCount", 0)
                _delay()
            except Exception:
                followers = 0

            published_str = note.get("publishAt") or note.get("updatedAt", "")
            try:
                published_at = _parse_datetime(published_str)
            except (ValueError, TypeError):
                published_at = datetime.now()

            articles.append(
                Article(
                    note_id=note_id,
                    title=note.get("name", ""),
                    url=f"https://note.com/{creator_id}/n/{note.get('key', '')}",
                    published_at=published_at,
                    likes=note.get("likeCount", 0),
                    comments=note.get("commentCount", 0),
                    is_paid=note.get("canRead") is False,
                    creator_followers=followers,
                    body_preview=note.get("body", "")[:300],
                )
            )

    return articles
