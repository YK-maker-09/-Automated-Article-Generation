"""記事生成パイプライン(プラン→執筆→評価→リライト→保存)。CLIとGUIの両方から使う。"""

from . import storage
from .claude_client import ClaudeClient
from .evaluator import evaluate_article, format_review
from .planner import plan_articles
from .writer import revise_article, write_article

MONETIZATION_LABEL = {
    "free": "無料",
    "partial_paid": "一部有料",
    "full_paid": "全文有料",
}


def generate_articles(config: dict, count: int, theme: str | None = None, log=print) -> list[dict]:
    """記事を count 本生成して保存し、保存結果のリストを返す。log は進捗表示用コールバック。"""
    client = ClaudeClient(config["model"])

    log(f"▶ 記事プランを立案中({count}本)...")
    plans = plan_articles(client, config, count, storage.recent_titles(), theme)

    results = []
    for i, plan in enumerate(plans, 1):
        article_id = storage.new_article_id()
        plan["id"] = article_id
        label = MONETIZATION_LABEL[plan["monetization"]]
        if plan["monetization"] != "free":
            label += f" {plan['price_yen']}円"
        log(f"[{i}/{len(plans)}] {plan['title']}({label})")

        log("  ✎ 本文を執筆中...")
        body = write_article(client, plan)

        log("  ⚖ 多角的評価を実行中...")
        evaluation = evaluate_article(client, plan, body)
        revisions = 0
        while (
            evaluation["total_score"] < config["quality_threshold"]
            and revisions < config["max_revisions"]
        ):
            revisions += 1
            log(f"  ↻ スコア {evaluation['total_score']} 点 → リライト {revisions} 回目...")
            body = revise_article(client, plan, body, evaluation)
            evaluation = evaluate_article(client, plan, body)

        review_md = format_review(plan, evaluation, revisions, config)
        article_dir = storage.save_article(article_id, plan, body, evaluation, review_md)
        log(f"  ✔ 完成(総合 {evaluation['total_score']} 点)")
        results.append({
            "id": article_id,
            "title": plan["title"],
            "score": evaluation["total_score"],
            "dir": str(article_dir),
        })
    return results
