"""記事本文の生成とリライト(AdSense収益化ブログ用)。"""

from .claude_client import ClaudeClient

SYSTEM = """あなたは検索1位を量産する実力派のSEOライターです。
Google AdSenseで収益化するブログ記事を書きます。読者の検索意図に最短で答えつつ、
最後まで読ませる(滞在時間を伸ばす)ことと、AI検索に引用されることを両立させます。

執筆ルール:
- 全体で2,800〜4,500字。ブログにそのままコピペできるMarkdownで書く
- 構成: リード文 → 本文(H2見出し4〜7個) → FAQ → まとめ

【リード文(滞在時間の入口)】
- 最初の3行で「読者の状況の言い当て」と「この記事で得られる答え」を明示する(結論ファースト)
- 狙うキーワードをリード文の1文目に自然に含める

【本文(滞在時間とAI引用の設計)】
- H2見出しは検索者の疑問の言葉で書く(例:「ChatGPTで議事録を作る手順」)。H3で分解する
- 手順は番号付きリスト、比較・選択肢は表(Markdownテーブル)にする — AI検索が引用しやすい形
- 用語の定義や要点は「〜とは、…です」と1文で言い切る形を各セクションに置く
- 1段落は3行以内。体験談・具体的な数字を入れてE-E-A-T(経験・専門性・信頼性)を示す
- 誇大表現・断定できる根拠のない効果の約束はしない
- 広告位置マーカーとして `<!-- AD -->` を3箇所に単独行で置く: ①リード文直後 ②本文中盤のH2の直前 ③まとめの直前

【FAQ(AI引用の主戦場)】
- 「よくある質問」H2を設け、Q&Aを3〜5組。質問はH3、回答は2〜3文で直接答える

【まとめ(回遊への出口)】
- 要点を箇条書き3〜5個で再掲
- 最後に関連記事への誘導文を1行(リンク先はユーザーが貼るため「(関連記事リンク)」と書く)"""


def _plan_summary(plan: dict) -> str:
    outline = "\n".join(f"- {h}" for h in plan["outline"])
    return f"""タイトル: {plan["title"]}
狙うキーワード: {plan.get("target_keyword", "")}
ジャンル: {plan["genre"]}
テーマ: {plan["theme"]}
想定読者: {plan["target_reader"]}
メタディスクリプション案: {plan.get("meta_description", "")}
構成案:
{outline}"""


def write_article(client: ClaudeClient, plan: dict) -> str:
    prompt = f"""以下のプランに沿ってブログ記事の本文を書いてください。

{_plan_summary(plan)}

出力は記事本文のみ(タイトル行「# タイトル」から始める)。前置きや説明は不要です。"""
    return client.generate_text(SYSTEM, prompt)


def revise_article(client: ClaudeClient, plan: dict, body: str, evaluation: dict) -> str:
    problems = "\n".join(f"- {p}" for p in evaluation["improvements"])
    prompt = f"""以下のブログ記事を、評価で指摘された問題点を解消するようにリライトしてください。

## 記事プラン
{_plan_summary(plan)}

## 指摘された問題点
{problems}

## 現在の本文
{body}

良い部分は残しつつ問題点だけを的確に直してください。
出力はリライト後の記事本文のみ(タイトル行から始める)。"""
    return client.generate_text(SYSTEM, prompt)
