"""記事プランの立案。狙うキーワード・タイトル・構成をAIが判断する(AdSense収益化ブログ用)。"""

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
                    "target_keyword": {"type": "string"},
                    "meta_description": {"type": "string"},
                    "monetization": {
                        "type": "string",
                        "enum": ["adsense"],
                    },
                    "price_yen": {"type": "integer"},
                    "monetization_reason": {"type": "string"},
                    "outline": {"type": "array", "items": {"type": "string"}},
                    "hashtags": {"type": "array", "items": {"type": "string"}},
                },
                "required": [
                    "title", "genre", "theme", "target_reader", "target_keyword",
                    "meta_description", "monetization", "price_yen",
                    "monetization_reason", "outline", "hashtags",
                ],
                "additionalProperties": False,
            },
        }
    },
    "required": ["articles"],
    "additionalProperties": False,
}

SYSTEM = """あなたはGoogle AdSenseで収益を上げるブログのコンテンツ戦略家です。
AdSense収益の構造を熟知しています:
- 収益 = PV × ページRPM。まずPV(検索流入)を集められるテーマ選定がすべての起点
- 検索流入は「検索意図が明確なロングテールキーワード」(3語程度の組み合わせ)を1記事1キーワードで狙う
- 大手サイトが上位を独占する激戦キーワードは避け、具体的な悩み・手順系を狙う
- 滞在時間とページ回遊が伸びるほど広告収益は上がる
- GoogleのAI Overview等のAI検索に引用されると新しい流入源になる(結論ファースト・構造化が有利)
- 読者の役に立たない記事はAdSense審査・SEOの両方で不利になる
- 広告単価(CPC)はカテゴリで大きく違う。転職・副業とお金(税金等)・資格/スクール・通信/ビジネスサービス比較は高単価。日常雑記・エンタメは低単価
- ただしYMYL(医療の診断・投資の推奨・法律判断)は断定を避け、一般的な情報+公式情報への誘導に留める

あなたの仕事は、検索需要から逆算して「今書くべき記事」と「狙うキーワード」を決めることです。
高単価カテゴリを7〜8割、集客用のAI活用系を2〜3割の比率で選定してください。
monetization は原則 "adsense"、price_yen は 0 とし、
monetization_reason にはキーワード選定の理由(検索需要・競合の弱さ・読者の悩みの強さ)を書いてください。"""


def plan_articles(
    client: ClaudeClient,
    config: dict,
    count: int,
    recent_titles: list[str],
    user_theme: str | None = None,
) -> list[dict]:
    genres = "、".join(config["genres"])
    recent = "\n".join(f"- {t}" for t in recent_titles) or "(まだ記事なし)"

    theme_instruction = (
        f"今回はユーザー指定のテーマ「{user_theme}」で書きます。このテーマで検索需要のあるキーワードを設定してください。"
        if user_theme
        else f"テーマは以下のジャンル群から、検索需要・競合の弱さ・季節性を考えて選んでください:\n{genres}"
    )

    prompt = f"""AdSense収益化ブログの記事プランを{count}本分、立ててください。

## 運用の前提
- 月間目標: 記事{config["monthly_target"]}本。検索流入の積み上げでPVを育てる
- 同一ブログ内の記事なので、テーマの一貫性(AI活用・副業・仕事術が軸)も意識する
- 今日の日付や季節性も考慮すること

## テーマ選定
{theme_instruction}

## 重複回避(既存の記事タイトル)
{recent}

## 各記事に必ず含めること
- target_keyword: 狙う検索キーワード(例:「chatgpt 議事録 作り方」のような2〜4語)
- title: キーワードを前方に含む32字前後のタイトル(クリックしたくなる具体性)
- meta_description: 100〜120字。検索結果でクリックさせる要約
- outline: 見出し構成案(6〜9項目)。読者の検索意図に最短で答える順序。FAQセクションを必ず含める
- hashtags: X告知用ハッシュタグ(2〜4個、#付き)"""

    result = client.generate_json(SYSTEM, prompt, PLAN_SCHEMA, max_tokens=16000)
    return result["articles"][:count]
