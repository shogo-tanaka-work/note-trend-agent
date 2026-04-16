from datetime import datetime, timedelta

from scorer import ScoredArticle, calc_scores, Article


DAYS_THRESHOLD = 14
TOP_K = 5
THEME_THRESHOLD = 0.5


def filter_recent(articles: list[Article], days: int = DAYS_THRESHOLD) -> list[Article]:
    """直近N日以内の記事のみ返す。"""
    cutoff = datetime.now() - timedelta(days=days)
    return [a for a in articles if a.published_at >= cutoff]


def score_all(articles: list[Article]) -> list[ScoredArticle]:
    return [calc_scores(a) for a in articles]


def rank(
    scored: list[ScoredArticle],
    top_k: int = TOP_K,
    theme_threshold: float = THEME_THRESHOLD,
) -> list[ScoredArticle]:
    """
    テーマ適合スコアが閾値以上の記事を、buzz / engagement 各軸で上位K件取得し
    Union + 重複除去して返す。
    """
    qualified = [s for s in scored if s.theme_score >= theme_threshold]

    top_buzz = sorted(qualified, key=lambda s: s.final_buzz, reverse=True)[:top_k]
    top_eng = sorted(qualified, key=lambda s: s.final_eng, reverse=True)[:top_k]

    seen: set[str] = set()
    result: list[ScoredArticle] = []
    for s in top_buzz + top_eng:
        if s.article.note_id not in seen:
            seen.add(s.article.note_id)
            result.append(s)

    return result
