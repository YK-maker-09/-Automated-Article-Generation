"""記事本文の生成とリライト。"""

from .claude_client import ClaudeClient
from .storage import PAID_MARKER

SYSTEM = """あなたはnote(note.com)で人気の実力派ライターです。
読者の悩みに寄り添い、具体的で実践的な内容を、読みやすい文章で書きます。

執筆ルール:
- 全体で2,500〜4,000字程度。noteにそのままコピペできるMarkdownで書く
- 見出しは「##」、小見出しは「###」を使う(noteのエディタで見出しに変換される)
- 導入(最初の3〜4行)で読者の悩みを言い当て、続きを読む理由を作る
- 抽象論ではなく、具体的な手順・数字・例を入れる
- 適度に改行し、1段落は3〜4行以内。箇条書きも活用する
- 誇大表現や断定できない収益保証はしない(信頼を損なうため)
- 記事の最後に、次の行動を促す一言(フォロー・スキ・関連記事への誘導)を入れる

有料記事の場合:
- 有料ラインの位置に、単独の行として正確に「{marker}」と書く
- 無料部分だけで「読んでよかった」と思わせつつ、有料部分に核心のノウハウ・具体的手順・テンプレートなどの明確な価値を置く
- 有料ライン直前に、有料部分で何が得られるかを箇条書きで予告する(購入の後押し)"""


def _plan_summary(plan: dict) -> str:
    monetization_label = {
        "free": "全文無料",
        "partial_paid": f"一部有料(有料ライン方式・{plan['price_yen']}円)",
        "full_paid": f"全文有料(冒頭のみ無料・{plan['price_yen']}円)",
    }[plan["monetization"]]
    outline = "\n".join(f"- {h}" for h in plan["outline"])
    return f"""タイトル: {plan["title"]}
ジャンル: {plan["genre"]}
テーマ: {plan["theme"]}
想定読者: {plan["target_reader"]}
収益化方式: {monetization_label}
方式の意図: {plan["monetization_reason"]}
構成案:
{outline}"""


def write_article(client: ClaudeClient, plan: dict) -> str:
    prompt = f"""以下のプランに沿ってnote記事の本文を書いてください。

{_plan_summary(plan)}

出力は記事本文のみ(タイトル行「# タイトル」から始める)。前置きや説明は不要です。"""
    return client.generate_text(SYSTEM.format(marker=PAID_MARKER), prompt)


def revise_article(client: ClaudeClient, plan: dict, body: str, evaluation: dict) -> str:
    problems = "\n".join(f"- {p}" for p in evaluation["improvements"])
    prompt = f"""以下のnote記事を、評価で指摘された問題点を解消するようにリライトしてください。

## 記事プラン
{_plan_summary(plan)}

## 指摘された問題点
{problems}

## 現在の本文
{body}

良い部分は残しつつ問題点だけを的確に直してください。
出力はリライト後の記事本文のみ(タイトル行から始める)。"""
    return client.generate_text(SYSTEM.format(marker=PAID_MARKER), prompt)
