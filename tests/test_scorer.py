import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))

from datetime import datetime, timedelta
import pytest
from scorer import Article, calc_scores


def make_article(**kwargs) -> Article:
    defaults = dict(
        note_id="test-1",
        title="テスト記事",
        url="https://note.com/test/n/abc",
        published_at=datetime.now() - timedelta(days=1),
        likes=100,
        comments=10,
        is_paid=False,
        creator_followers=1000,
    )
    defaults.update(kwargs)
    return Article(**defaults)


def test_buzz_score_decreases_with_age():
    """古い記事ほど buzz_score が低くなる。"""
    new_article = make_article(published_at=datetime.now() - timedelta(days=1))
    old_article = make_article(published_at=datetime.now() - timedelta(days=10))

    new_scored = calc_scores(new_article)
    old_scored = calc_scores(old_article)

    assert new_scored.buzz_score > old_scored.buzz_score


def test_eng_score_decreases_with_followers():
    """フォロワーが多いほど eng_score が低くなる（同じスキ数の場合）。"""
    small_creator = make_article(creator_followers=100)
    large_creator = make_article(creator_followers=100_000)

    small_scored = calc_scores(small_creator)
    large_scored = calc_scores(large_creator)

    assert small_scored.eng_score > large_scored.eng_score


def test_paid_multiplier():
    """有料記事は無料記事よりスコアが高い。"""
    free_article = make_article(is_paid=False)
    paid_article = make_article(is_paid=True)

    free_scored = calc_scores(free_article)
    paid_scored = calc_scores(paid_article)

    assert paid_scored.buzz_score > free_scored.buzz_score
    assert paid_scored.eng_score > free_scored.eng_score


def test_final_scores_with_theme():
    """theme_score を設定すると final_buzz / final_eng に反映される。"""
    article = make_article()
    scored = calc_scores(article)
    scored.theme_score = 0.8

    assert scored.final_buzz == pytest.approx(scored.buzz_score * 0.8)
    assert scored.final_eng == pytest.approx(scored.eng_score * 0.8)


def test_min_followers_floor():
    """フォロワー0でもゼロ除算にならない。"""
    article = make_article(creator_followers=0)
    scored = calc_scores(article)

    assert scored.eng_score > 0
