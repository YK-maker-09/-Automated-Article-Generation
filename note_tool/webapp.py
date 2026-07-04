"""ブラウザGUI(ローカルWebアプリ)。`python -m note_tool gui` で起動する。"""

import json
import threading
import webbrowser
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from . import config as config_module
from . import storage
from .claude_client import ClaudeClient
from .pipeline import generate_articles
from .x_poster import compose_tweet, post_tweet, x_credentials_available


class GenerationJob:
    """バックグラウンドで走る記事生成ジョブ(同時実行は1つまで)。"""

    def __init__(self):
        self.lock = threading.Lock()
        self.reset()

    def reset(self):
        self.running = False
        self.done = False
        self.error = None
        self.log_lines: list[str] = []
        self.results: list[dict] = []

    def log(self, line: str):
        with self.lock:
            self.log_lines.append(line)

    def start(self, config: dict, count: int, theme: str | None) -> bool:
        with self.lock:
            if self.running:
                return False
            self.reset()
            self.running = True
        threading.Thread(target=self._run, args=(config, count, theme), daemon=True).start()
        return True

    def _run(self, config: dict, count: int, theme: str | None):
        try:
            self.results = generate_articles(config, count, theme, log=self.log)
            self.log("🎉 すべての記事の生成が完了しました。「記事一覧」から確認してください。")
        except Exception as e:  # noqa: BLE001 - GUIにエラーを表示する
            self.error = f"{type(e).__name__}: {e}"
            self.log(f"✘ エラーが発生しました: {self.error}")
        finally:
            with self.lock:
                self.running = False
                self.done = True

    def snapshot(self) -> dict:
        with self.lock:
            return {
                "running": self.running,
                "done": self.done,
                "error": self.error,
                "log": list(self.log_lines),
                "results": list(self.results),
            }


job = GenerationJob()
app = Flask(__name__)


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/state")
def api_state():
    config = config_module.load_config()
    month = datetime.now().strftime("%Y-%m")
    monthly = storage.list_articles(month)
    posted = [a for a in monthly if a["status"] == "posted"]
    paid_posted = [a for a in posted if a["monetization"] != "free"]
    return jsonify({
        "config": config,
        "month": month,
        "monthly_generated": len(monthly),
        "monthly_posted": len(posted),
        "paid_posted_count": len(paid_posted),
        "paid_price_total": sum(a["price_yen"] for a in paid_posted),
        "x_configured": x_credentials_available(),
        "articles": list(reversed(storage.list_articles())),
    })


@app.post("/api/generate")
def api_generate():
    data = request.get_json(force=True)
    count = max(1, min(int(data.get("count", 1)), 10))
    theme = (data.get("theme") or "").strip() or None
    if not job.start(config_module.load_config(), count, theme):
        return jsonify({"error": "生成ジョブが既に実行中です"}), 409
    return jsonify({"ok": True})


@app.get("/api/job")
def api_job():
    return jsonify(job.snapshot())


@app.get("/api/article/<article_id>")
def api_article(article_id: str):
    article = storage.get_article(article_id)
    if not article:
        return jsonify({"error": "記事が見つかりません"}), 404
    article_dir = Path(article["dir"])
    meta = json.loads((article_dir / "meta.json").read_text(encoding="utf-8"))
    return jsonify({
        "meta": meta,
        "article_md": (article_dir / "article.md").read_text(encoding="utf-8"),
        "review_md": (article_dir / "review.md").read_text(encoding="utf-8"),
    })


@app.post("/api/tweet")
def api_tweet():
    """告知ツイート文面を生成して返す(投稿はしない)。"""
    data = request.get_json(force=True)
    article = storage.get_article(data["id"])
    if not article:
        return jsonify({"error": "記事が見つかりません"}), 404
    meta = json.loads((Path(article["dir"]) / "meta.json").read_text(encoding="utf-8"))
    config = config_module.load_config()
    try:
        tweet = compose_tweet(ClaudeClient(config["model"]), meta, data["url"].strip())
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": f"ツイート生成に失敗しました: {e}"}), 500
    return jsonify({"tweet": tweet})


@app.post("/api/posted")
def api_posted():
    """投稿済みとして記録し、必要ならXに投稿する。tweet は編集済み文面をそのまま使う。"""
    data = request.get_json(force=True)
    article_id = data["id"]
    if not storage.get_article(article_id):
        return jsonify({"error": "記事が見つかりません"}), 404

    x_posted = False
    tweet_url = None
    if data.get("post_to_x"):
        if not x_credentials_available():
            return jsonify({"error": "X APIキーが未設定です(.env を確認してください)"}), 400
        try:
            tweet_url = post_tweet(data["tweet"])
            x_posted = True
        except Exception as e:  # noqa: BLE001
            return jsonify({"error": f"Xへの投稿に失敗しました: {e}"}), 500

    storage.mark_posted(article_id, data["url"].strip(), x_posted)
    return jsonify({"ok": True, "x_posted": x_posted, "tweet_url": tweet_url})


@app.post("/api/config")
def api_config():
    updates = request.get_json(force=True)
    config = config_module.load_config()
    unknown = [k for k in updates if k not in config]
    if unknown:
        return jsonify({"error": f"不明な設定キー: {', '.join(unknown)}"}), 400
    config.update(updates)
    config_module.save_config(config)
    return jsonify({"ok": True, "config": config})


def run_gui(host: str = "127.0.0.1", port: int = 8787, open_browser: bool = True):
    url = f"http://{host}:{port}"
    print(f"🌐 GUIを起動しました: {url}(終了は Ctrl+C)")
    if open_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    app.run(host=host, port=port, debug=False)
