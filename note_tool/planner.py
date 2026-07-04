"""記事プランの立案。テーマ・タイトル・収益化方式(有料ライン等)をAIが判断する。"""

from .claude_client import ClaudeClient

PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "articles": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "genre": {"type": "string"},
                    "theme": {"type": "string"},
                    "target_reader": {"type": "string"},
                    "monetization": {
                        "type": "string",
                        "enum": ["free", "partial_paid", "full_paid"],
                    },
                    "price_yen": {"type": "integer"},
                    "monetization_reason": {"type": "string"},
                    "outline": {"type": "array", "items": {"type": "string"}},
                    "hashtags": {"type": "array", "items": {"type": "string"}},
                },
                "required": [
                    "title", "genre", "theme", "target_reader", "monetization",
                    "price_yen", "monetization_reason", "outline", "hashtags",
                ],
                "additionalProperties": False,
            },
        }
    },
    "required": ["articles"],
    "additionalProperties": False,
}

SYSTEM = """あなたはnote(note.com)で収益を上げるコンテンツ戦略のプロフェッショナルです。
noteの収益化の仕組みを熟知しています:
- note標準の課金は「有料記事」方式。記事の途中に有料ラインを設定し、そこから先は購入者のみ読める(いわゆる「ここから先は有料です」)
- 無料記事はフォロワー獲得・信頼構築・有料記事への導線として機能する
- 売れる価格帯は100〜500円が中心。実績が積み上がるまでは低価格で購入ハードルを下げる
- 無料と有料のバランスが重要(無料だけでは収益ゼロ、有料だけではフォロワーが増えない)

あなたの仕事は、収益目標から逆算して「今書くべき記事」のプランを立てることです。
各記事について、無料にするか・一部有料(有料ライン設置)にするか・全文有料にするかを、
その記事の役割(集客か収益化か)を考えて判断し、理由も説明してください。"""


def plan_articles(
    client: ClaudeClient,
    config: dict,
    count: int,
    recent_titles: list[str],
    user_theme: str | None = None,
) -> list[dict]:
    goal_min, goal_max = config["revenue_goal_yen"]
    price_min, price_max = config["price_range_yen"]
    genres = "、".join(config["genres"])
    recent = "\n".join(f"- {t}" for t in recent_titles) or "(まだ記事なし)"

    theme_instruction = (
        f"今回はユーザー指定のテーマ「{user_theme}」で書きます。このテーマでプランを立ててください。"
        if user_theme
        else f"テーマは以下のジャンル群から、今の時期の需要・トレンド・収益性を考えて選んでください:\n{genres}"
    )

    prompt = f"""noteの記事プランを{count}本分、立ててください。

## 運用の前提
- 月間目標: 記事{config["monthly_target"]}本、収益{goal_min:,}〜{goal_max:,}円
- 有料記事の価格帯: {price_min}〜{price_max}円(無料記事は price_yen を 0 に)
- 今日の日付や季節性も考慮すること

## テーマ選定
{theme_instruction}

## 重複回避(直近の記事タイトル)
{recent}

## 各記事に必ず含めること
- title: 思わずクリックしたくなる具体的なタイトル(数字や具体性を入れる)
- monetization: free(全文無料・集客用)/ partial_paid(途中から有料・note標準の有料ライン方式)/ full_paid(冒頭以外ほぼ有料)
- monetization_reason: なぜその方式にしたのか(収益戦略上の役割)
- outline: 見出しレベルの構成案(5〜8項目)。partial_paid の場合はどの見出しから有料にするかを outline 内に「★ここから有料」と明記
- hashtags: noteとXで使うハッシュタグ(3〜5個、#付き)

複数本のときは、無料と有料の比率もポートフォリオとして最適になるように配分してください。"""

    result = client.generate_json(SYSTEM, prompt, PLAN_SCHEMA, max_tokens=16000)
    return result["articles"][:count]
