import json

from openai import OpenAI

from scorer import ScoredArticle

JUDGE_MODEL = "gpt-5-mini"
NOTIFY_MODEL = "gpt-5-mini"

THEME_SYSTEM_PROMPT = """\
あなたはnote記事がターゲットテーマに合致するかを判定します。

ターゲットテーマ:
- 生成AI × 組織導入・展開
- 経営 × 生成AI
- AI活用の実践・事例
- LLM・Claude・ChatGPT の業務活用

タイトルと冒頭文から適合度を 0.0〜1.0 のfloatで判定してください。
- 1.0: テーマに完全に合致
- 0.5: 部分的に関連
- 0.0: テーマと無関係

必ず以下のJSON形式のみで返してください:
{"theme_score": 0.85}
"""


def judge_theme(scored: ScoredArticle, client: OpenAI) -> float:
    """記事のテーマ適合スコア（0.0〜1.0）を返す。"""
    a = scored.article
    user_content = f"タイトル: {a.title}\n冒頭: {a.body_preview}"

    message = client.chat.completions.create(
        model=JUDGE_MODEL,
        max_completion_tokens=4096,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": THEME_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
    )

    try:
        result = json.loads(message.choices[0].message.content)
        return float(result.get("theme_score", 0.0))
    except (json.JSONDecodeError, IndexError, KeyError, ValueError):
        return 0.0


def batch_judge_themes(
    articles: list[ScoredArticle], client: OpenAI
) -> list[ScoredArticle]:
    """候補記事リストにテーマ適合スコアを付与して返す。"""
    results = []
    for scored in articles:
        score = judge_theme(scored, client)
        scored.theme_score = score
        results.append(scored)
    return results


def generate_summary(scored: ScoredArticle, client: OpenAI) -> str:
    """Discord/Slack 通知用の1〜2文サマリーを生成する。"""
    a = scored.article
    prompt = f"""\
記事タイトル: {a.title}
冒頭: {a.body_preview}
スキ数: {a.likes} / フォロワー数: {a.creator_followers}

この記事を1〜2文で要約し、「なぜ今注目か」を添えてください。
Discord通知向けの簡潔な文体（です・ます不要）で。
"""
    message = client.chat.completions.create(
        model=NOTIFY_MODEL,
        max_completion_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.choices[0].message.content.strip()
