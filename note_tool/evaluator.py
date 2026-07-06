"""記事の多角的評価。7つの観点でスコアリングし、改善点を抽出する。

注意: このモジュールはAPI不要の運用(CLAUDE.mdの保存スニペット)からも import される。
anthropic パッケージへの依存を持ち込まないよう、ClaudeClient は関数内で遅延importする。
"""

# AdSense収益化(ブログ記事)用の評価軸
AXES = [
    ("search_intent", "検索意図との一致(狙ったキーワードの答えに最短で到達できるか)"),
    ("dwell_time", "滞在時間設計(導入の引き込み・見出しの引き・飽きさせない構成)"),
    ("trust", "信頼性・E-E-A-T(体験・根拠・正直さ・過度な断定の回避)"),
    ("ai_citability", "AI引用適性(結論ファースト・FAQ・定義や手順の構造化=AI検索に引用されやすいか)"),
    ("readability", "読みやすさ・回遊(表・箇条書き・段落の短さ・内部リンクの置き場)"),
    ("ad_revenue", "広告収益性(PVが見込めるテーマ選定と広告配置スペースの確保)"),
    ("originality", "独自性(検索上位の記事と同じ内容の焼き直しになっていないか)"),
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

SYSTEM = """あなたはSEO・AdSense収益化ブログを専門とする辛口の編集者兼SEOコンサルタントです。
「この記事は検索から人が来るか?最後まで読まれるか?AI検索(GoogleのAI Overview等)に引用されるか?」
という視点で、忖度なく厳しく評価します。
甘い点数をつけると書き手のためになりません。80点は「自信を持って公開できる水準」です。"""

MONETIZATION_LABEL = {
    "adsense": "広告収益(Google AdSense)",
    "free": "全文無料",
    "partial_paid": "一部有料(有料ライン方式)",
    "full_paid": "全文有料(冒頭のみ無料)",
}


def evaluate_article(client, plan: dict, body: str) -> dict:
    axes_desc = "\n".join(f"- {key}: {desc}" for key, desc in AXES)
    prompt = f"""以下のブログ記事(AdSense収益化)を多角的に評価してください。

## 記事の狙い
- タイトル: {plan["title"]}
- 狙うキーワード: {plan.get("target_keyword", "")}
- 想定読者: {plan["target_reader"]}

## 評価軸(各0〜100点)
{axes_desc}

## 記事本文
{body}

total_score は7軸の重み付き総合点(0〜100)。
improvements にはリライトでそのまま使える具体的な改善指示を書いてください。
buyer_perspective には「検索でこの記事に来た読者として、最後まで読むか・またこのブログに来たいか」を率直に書いてください。"""
    return client.generate_json(SYSTEM, prompt, EVAL_SCHEMA, max_tokens=8000)


def format_review(plan: dict, evaluation: dict, revisions: int, config: dict) -> str:
    """最終チェック用の評価レポート(review.md)を組み立てる。"""
    label = MONETIZATION_LABEL.get(plan.get("monetization", "adsense"), "広告収益(Google AdSense)")

    scores = "\n".join(
        f"| {desc} | {evaluation['scores'].get(key, '-')} |" for key, desc in AXES
    )
    strengths = "\n".join(f"- {s}" for s in evaluation["strengths"])
    improvements = "\n".join(f"- {s}" for s in evaluation["improvements"]) or "- なし"
    hashtags = " ".join(plan.get("hashtags", []))

    steps = [
        "ブログ(Blogger)の投稿画面で、ペンのアイコンから **「HTML ビュー」に切り替える**",
        "**`article.html`**(.md ではなく .html)の中身を全選択してコピーし、本文に貼り付け → 「作成ビュー」に戻す",
        "上の『ブログのタイトル欄に入れる文字』を、Blogger の **タイトル欄** に貼り付け(本文にタイトルは含まれていません)",
        f"メタディスクリプションに「{plan.get('meta_description', '')}」を設定(オプション→検索向け説明)",
        "本文中の `<!-- 広告ユニットをここに配置 -->` の位置に広告を配置(合格前は空欄でOK)",
        "パーマリンクを英語スラッグに変更して公開",
        f"X告知(下記の下書きを使用)/ 推奨タグ: {hashtags}",
    ]
    extra = f"""
## ブログのタイトル欄に入れる文字(これをコピーしてください)

```
{plan["title"]}
```

## SEO情報
- 狙うキーワード: **{plan.get("target_keyword", "")}**
- メタディスクリプション案: {plan.get("meta_description", "")}
"""
    steps_md = "\n".join(f"{i}. {s}" for i, s in enumerate(steps, 1))

    return f"""# 最終チェックシート: {plan["title"]}

## 収益化方式
**{label}**

判断理由: {plan["monetization_reason"]}
{extra}
## AI評価(総合 {evaluation["total_score"]} 点 / 合格基準 {config["quality_threshold"]} 点 / リライト {revisions} 回)

| 評価軸 | 点数 |
|---|---|
{scores}

### 強み
{strengths}

### 残っている改善余地(必要ならご自身で微調整)
{improvements}

### 読者視点の率直な感想
{evaluation["buyer_perspective"]}

## 投稿手順
{steps_md}
"""
