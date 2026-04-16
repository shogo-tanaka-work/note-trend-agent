from dataclasses import dataclass
from datetime import datetime


@dataclass
class Article:
    note_id: str
    title: str
    url: str
    published_at: datetime
    likes: int
    comments: int
    is_paid: bool
    creator_followers: int
    body_preview: str = ""

    @property
    def days_since_published(self) -> float:
        delta = datetime.now() - self.published_at
        return max(delta.days + delta.seconds / 86400, 0.5)


@dataclass
class ScoredArticle:
    article: Article
    buzz_score: float
    eng_score: float
    theme_score: float = 1.0

    @property
    def final_buzz(self) -> float:
        return self.buzz_score * self.theme_score

    @property
    def final_eng(self) -> float:
        return self.eng_score * self.theme_score


PAID_MULTIPLIER = 1.2
COMMENT_WEIGHT = 2
MIN_FOLLOWERS = 100


def calc_scores(article: Article) -> ScoredArticle:
    days = article.days_since_published
    engagement = article.likes + article.comments * COMMENT_WEIGHT
    paid = PAID_MULTIPLIER if article.is_paid else 1.0

    buzz_score = (engagement / days) * paid
    eng_score = (engagement / max(article.creator_followers, MIN_FOLLOWERS)) * paid

    return ScoredArticle(article=article, buzz_score=buzz_score, eng_score=eng_score)
