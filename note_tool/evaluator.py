"""記事の多角的評価。7つの観点でスコアリングし、改善点を抽出する。"""

from .claude_client import ClaudeClient

AXES = [
    ("title_appeal", "タイトル訴求力(クリックしたくなるか)"),
    ("hook", "導入の引き込み(最初の数行で続きを読みたくなるか)"),
    ("practical_value", "実用価値(読者が行動に移せる具体性があるか)"),
    ("originality", "独自性(他のnote記事との差別化)"),
    ("readability", "構成・読みやすさ(見出し・段落・リズム)"),
    ("monetization_design", "収益化設計(無料部分の引きと有料部分の価値。無料記事なら集客・導線設計)"),
    ("shareability", "拡散性(SNSでシェア・スキされやすいか)"),
]

EVAL_SCHEMA = {
    "type": "object",
    "properties": {
        "scores": {
            "type": "object",
            "properties": {key: {"type": "integer"} for key, _ in AXES},
            "required": [key for key, _ in AXES],
            "additionalProperties": False,
        },
        "total_score": {"type": "integer"},
        "strengths": {"type": "array", "items": {"type": "string"}},
        "improvements": {"type": "array", "items": {"type": "string"}},
        "buyer_perspective": {"type": "string"},
    },
    "required": ["scores", "total_score", "strengths", "improvements", "buyer_perspective"],
    "additionalProperties": False,
}

SYSTEM = """あなたはnote(note.com)のコンテンツを専門とする辛口の編集者兼マーケターです。
「この記事は本当に読まれるか?有料部分は本当に買われるか?」という
読者・購入者の視点で、忖度なく厳しく評価します。
甘い点数をつけると書き手のためになりません。80点は「自信を持って公開できる水準」です。"""


def evaluate_article(client: ClaudeClient, plan: dict, body: str) -> dict:
    axes_desc = "\n".join(f"- {key}: {desc}" for key, desc in AXES)
    prompt = f"""以下のnote記事を多角的に評価してください。

## 記事の狙い
- タイトル: {plan["title"]}
- 想定読者: {plan["target_reader"]}
- 収益化方式: {plan["monetization"]}(価格: {plan.get("price_yen", 0)}円)

## 評価軸(各0〜100点)
{axes_desc}

## 記事本文
{body}

total_score は7軸の重み付き総合点(0〜100)。
improvements にはリライトでそのまま使える具体的な改善指示を書いてください。
buyer_perspective には「自分が読者ならこの記事(有料部分)にお金を払うか、なぜか」を率直に書いてください。"""
    return client.generate_json(SYSTEM, prompt, EVAL_SCHEMA, max_tokens=8000)


def format_review(plan: dict, evaluation: dict, revisions: int, config: dict) -> str:
    """最終チェック用の評価レポート(review.md)を組み立てる。"""
    monetization_label = {
        "free": "全文無料",
        "partial_paid": f"一部有料(有料ライン方式)/ 価格 {plan['price_yen']}円",
        "full_paid": f"全文有料(冒頭のみ無料)/ 価格 {plan['price_yen']}円",
    }[plan["monetization"]]

    scores = "\n".join(
        f"| {desc} | {evaluation['scores'][key]} |" for key, desc in AXES
    )
    strengths = "\n".join(f"- {s}" for s in evaluation["strengths"])
    improvements = "\n".join(f"- {s}" for s in evaluation["improvements"]) or "- なし"
    hashtags = " ".join(plan["hashtags"])

    steps = [
        "`article.md` の中身を全選択してコピー",
        "noteの新規記事作成画面に貼り付け(見出し・箇条書きは自動反映されます)",
        "タイトルと本文を最終確認(誤字・固有名詞・数字は特に注意)",
    ]
    if plan["monetization"] in ("partial_paid", "full_paid"):
        steps += [
            f"公開設定で「有料」を選び、価格を **{plan['price_yen']}円** に設定",
            "有料ラインを本文中の「＝＝＝＝＝ ここから有料ライン ＝＝＝＝＝」の位置に設定し、そのマーカー行自体は削除",
        ]
    steps += [f"ハッシュタグ: {hashtags}", "公開!"]
    steps_md = "\n".join(f"{i}. {s}" for i, s in enumerate(steps, 1))

    return f"""# 最終チェックシート: {plan["title"]}

## 収益化方式
**{monetization_label}**

判断理由: {plan["monetization_reason"]}

## AI評価(総合 {evaluation["total_score"]} 点 / 合格基準 {config["quality_threshold"]} 点 / リライト {revisions} 回)

| 評価軸 | 点数 |
|---|---|
{scores}

### 強み
{strengths}

### 残っている改善余地(必要ならご自身で微調整)
{improvements}

### 購入者視点の率直な感想
{evaluation["buyer_perspective"]}

## note投稿手順
{steps_md}

## 投稿が終わったら
以下のコマンドでX(@Interkyky)への告知が自動投稿されます:

```
python -m note_tool posted {plan.get("id", "<記事ID>")} --url <公開したnoteのURL>
```
"""
