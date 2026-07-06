"""記事ファイルと進捗状態(state.json)の保存・読み込み。"""

import json
import re
from datetime import datetime
from pathlib import Path

from .config import ARTICLES_DIR, STATE_PATH


def _load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {"articles": []}


def _save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def list_articles(month: str | None = None) -> list[dict]:
    """記事一覧。month は 'YYYY-MM' 形式で絞り込み。"""
    articles = _load_state()["articles"]
    if month:
        articles = [a for a in articles if a["created_at"].startswith(month)]
    return articles


def get_article(article_id: str) -> dict | None:
    for a in _load_state()["articles"]:
        if a["id"] == article_id:
            return a
    return None


def recent_titles(limit: int = 60) -> list[str]:
    """テーマ重複を避けるために直近の記事タイトルを返す。"""
    return [a["title"] for a in _load_state()["articles"][-limit:]]


def new_article_id() -> str:
    today = datetime.now().strftime("%Y%m%d")
    seq = sum(1 for a in _load_state()["articles"] if a["id"].startswith(today)) + 1
    return f"{today}-{seq:03d}"


def save_article(
    article_id: str,
    plan: dict,
    body: str,
    evaluation: dict,
    review_md: str,
) -> Path:
    """記事本文・メタ情報・評価レポートを保存し、state に登録する。"""
    month_dir = ARTICLES_DIR / datetime.now().strftime("%Y-%m")
    slug = re.sub(r"[^\w\-]", "", plan["title"].replace(" ", "-"))[:30] or "article"
    article_dir = month_dir / f"{article_id}_{slug}"
    article_dir.mkdir(parents=True, exist_ok=True)

    (article_dir / "article.md").write_text(body, encoding="utf-8")
    # ブログのHTMLビューにそのまま貼れるHTML版も出力(見出し・表が反映される)
    from .htmlize import markdown_to_html
    (article_dir / "article.html").write_text(markdown_to_html(body), encoding="utf-8")
    (article_dir / "review.md").write_text(review_md, encoding="utf-8")
    meta = {
        "id": article_id,
        "title": plan["title"],
        "genre": plan["genre"],
        "monetization": plan["monetization"],
        "price_yen": plan.get("price_yen", 0),
        "score": evaluation["total_score"],
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "status": "draft",  # draft -> posted
        "note_url": None,
        "x_posted": False,
        "dir": str(article_dir),
    }
    (article_dir / "meta.json").write_text(
        json.dumps({**meta, "plan": plan, "evaluation": evaluation},
                   ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    state = _load_state()
    state["articles"].append(meta)
    _save_state(state)
    return article_dir


def mark_posted(article_id: str, note_url: str, x_posted: bool) -> dict:
    state = _load_state()
    for a in state["articles"]:
        if a["id"] == article_id:
            a["status"] = "posted"
            a["note_url"] = note_url
            a["x_posted"] = x_posted
            _save_state(state)
            return a
    raise KeyError(f"記事ID {article_id} が見つかりません")
