"""X(旧Twitter)への告知ツイート生成・投稿。"""

import os

TWEET_SCHEMA = {
    "type": "object",
    "properties": {"tweet": {"type": "string"}},
    "required": ["tweet"],
    "additionalProperties": False,
}

SYSTEM = """あなたはXでの記事宣伝が得意なSNSマーケターです。
ブログ記事の公開を告知するツイートを書きます。

ルール:
- 本文は全角110字以内(URLとハッシュタグを足しても文字数制限に収まるように)
- 1行目でターゲットの興味を掴む(悩みの言い当て・意外な事実・数字など)
- 記事を読むメリットを1つに絞って伝える
- 宣伝臭を抑え、フォロワーとの会話のようなトーンで
- 絵文字は0〜2個まで
- ハッシュタグは2個まで
- URLは含めない(こちらで末尾に追加する)"""


def compose_tweet(client, meta: dict, note_url: str) -> str:
    plan = meta.get("plan", meta)
    monetization = {
        "free": "全文無料",
        "partial_paid": f"一部有料({meta.get('price_yen', 0)}円)",
        "full_paid": f"有料記事({meta.get('price_yen', 0)}円)",
    }.get(meta["monetization"], "無料")
    hashtags = " ".join(plan.get("hashtags", [])[:2])

    prompt = f"""公開したnote記事の告知ツイート本文を書いてください。

- 記事タイトル: {meta["title"]}
- ジャンル: {meta.get("genre", "")}
- 想定読者: {plan.get("target_reader", "")}
- 記事の要点: {plan.get("theme", "")}
- 公開形態: {monetization}
- 使えるハッシュタグ: {hashtags}"""

    result = client.generate_json(SYSTEM, prompt, TWEET_SCHEMA, max_tokens=2000)
    return f"{result['tweet'].strip()}\n\n{note_url}"


def x_credentials_available() -> bool:
    return all(
        os.environ.get(key)
        for key in ("X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET")
    )


def post_tweet(text: str) -> str:
    """ツイートを投稿し、ツイートURLを返す。"""
    import tweepy

    client = tweepy.Client(
        consumer_key=os.environ["X_API_KEY"],
        consumer_secret=os.environ["X_API_SECRET"],
        access_token=os.environ["X_ACCESS_TOKEN"],
        access_token_secret=os.environ["X_ACCESS_TOKEN_SECRET"],
    )
    response = client.create_tweet(text=text)
    tweet_id = response.data["id"]
    return f"https://x.com/Interkyky/status/{tweet_id}"
