"""CLIエントリポイント。

使い方:
  python -m note_tool generate [-n 本数] [--theme "テーマ"]   記事を生成
  python -m note_tool list [--month YYYY-MM]                  記事一覧
  python -m note_tool status                                  今月の進捗
  python -m note_tool posted <記事ID> --url <noteのURL>       投稿記録 & X告知
  python -m note_tool config [--set key=value]                設定の確認・変更
"""

import argparse
import json
import sys
from datetime import datetime

from dotenv import load_dotenv

from . import config as config_module
from . import storage
from .claude_client import ClaudeClient
from .evaluator import evaluate_article, format_review
from .planner import plan_articles
from .writer import revise_article, write_article
from .x_poster import compose_tweet, post_tweet, x_credentials_available


def cmd_generate(args) -> None:
    config = config_module.load_config()
    client = ClaudeClient(config["model"])
    count = args.count

    remaining = _remaining_this_month(config)
    if remaining <= 0:
        print(f"⚠ 今月の目標 {config['monthly_target']} 本は達成済みです。続けて生成します。")

    print(f"▶ 記事プランを立案中({count}本)...")
    plans = plan_articles(client, config, count, storage.recent_titles(), args.theme)

    for i, plan in enumerate(plans, 1):
        article_id = storage.new_article_id()
        plan["id"] = article_id
        label = {"free": "無料", "partial_paid": f"一部有料 {plan['price_yen']}円",
                 "full_paid": f"全文有料 {plan['price_yen']}円"}[plan["monetization"]]
        print(f"\n[{i}/{len(plans)}] {plan['title']}({label})")

        print("  ✎ 本文を執筆中...")
        body = write_article(client, plan)

        print("  ⚖ 多角的評価を実行中...")
        evaluation = evaluate_article(client, plan, body)
        revisions = 0
        while (
            evaluation["total_score"] < config["quality_threshold"]
            and revisions < config["max_revisions"]
        ):
            revisions += 1
            print(f"  ↻ スコア {evaluation['total_score']} 点 → リライト {revisions} 回目...")
            body = revise_article(client, plan, body, evaluation)
            evaluation = evaluate_article(client, plan, body)

        review_md = format_review(plan, evaluation, revisions, config)
        article_dir = storage.save_article(article_id, plan, body, evaluation, review_md)
        print(f"  ✔ 完成(総合 {evaluation['total_score']} 点)→ {article_dir}")

    print("\n──────────────────────────────")
    print("次のステップ:")
    print("  1. 各記事フォルダの review.md(評価と投稿手順)を確認")
    print("  2. article.md をnoteにコピペして投稿")
    print("  3. python -m note_tool posted <記事ID> --url <noteのURL> でX告知")
    _print_status(config)


def cmd_list(args) -> None:
    articles = storage.list_articles(args.month)
    if not articles:
        print("記事がありません。まず `python -m note_tool generate` を実行してください。")
        return
    print(f"{'記事ID':<14} {'状態':<6} {'方式':<12} {'点':<4} タイトル")
    for a in articles:
        monetization = {"free": "無料", "partial_paid": f"一部有料{a['price_yen']}円",
                        "full_paid": f"全文有料{a['price_yen']}円"}[a["monetization"]]
        status = "投稿済" if a["status"] == "posted" else "下書き"
        print(f"{a['id']:<14} {status:<6} {monetization:<12} {a['score']:<4} {a['title']}")


def cmd_status(args) -> None:
    _print_status(config_module.load_config())


def cmd_posted(args) -> None:
    config = config_module.load_config()
    article = storage.get_article(args.article_id)
    if not article:
        print(f"✘ 記事ID {args.article_id} が見つかりません。`list` で確認してください。")
        sys.exit(1)

    meta_path = f"{article['dir']}/meta.json"
    with open(meta_path, encoding="utf-8") as f:
        meta = json.load(f)

    print("▶ X告知ツイートを生成中...")
    client = ClaudeClient(config["model"])
    tweet = compose_tweet(client, meta, args.url)
    print("\n─── ツイート文 ───")
    print(tweet)
    print("──────────────\n")

    x_posted = False
    if args.skip_x or args.dry_run:
        print("(X投稿はスキップしました。上の文面を手動投稿できます)")
    elif not x_credentials_available():
        print("⚠ X APIキーが未設定のため自動投稿できません(.env を確認)。上の文面を手動投稿してください。")
    else:
        tweet_url = post_tweet(tweet)
        x_posted = True
        print(f"✔ Xに投稿しました: {tweet_url}")

    if not args.dry_run:
        storage.mark_posted(args.article_id, args.url, x_posted)
        print(f"✔ 記事 {args.article_id} を投稿済みとして記録しました。")
        _print_status(config)


def cmd_config(args) -> None:
    config = config_module.load_config()
    if args.set:
        for pair in args.set:
            key, _, value = pair.partition("=")
            if key not in config:
                print(f"✘ 不明な設定キー: {key}")
                print(f"  利用可能: {', '.join(config)}")
                sys.exit(1)
            try:
                config[key] = json.loads(value)
            except json.JSONDecodeError:
                config[key] = value
            print(f"✔ {key} = {config[key]}")
        config_module.save_config(config)
    else:
        print(json.dumps(config, ensure_ascii=False, indent=2))


def _remaining_this_month(config: dict) -> int:
    month = datetime.now().strftime("%Y-%m")
    return config["monthly_target"] - len(storage.list_articles(month))


def _print_status(config: dict) -> None:
    month = datetime.now().strftime("%Y-%m")
    articles = storage.list_articles(month)
    posted = [a for a in articles if a["status"] == "posted"]
    paid_posted = [a for a in posted if a["monetization"] != "free"]
    goal_min, goal_max = config["revenue_goal_yen"]
    print(f"\n📊 {month} の進捗")
    print(f"  生成済み: {len(articles)} / {config['monthly_target']} 本(投稿済み {len(posted)} 本)")
    if paid_posted:
        total_price = sum(a["price_yen"] for a in paid_posted)
        print(f"  投稿済み有料記事: {len(paid_posted)} 本(価格合計 {total_price:,} 円)")
        for sales in (10, 30):
            print(f"    各記事が月{sales}部売れた場合の想定売上: 約 {total_price * sales:,} 円")
    print(f"  収益目標: {goal_min:,}〜{goal_max:,} 円/月")


def main() -> None:
    load_dotenv(config_module.BASE_DIR / ".env")

    parser = argparse.ArgumentParser(
        prog="note_tool", description="note記事自動生成ツール(多角的評価 & X告知つき)"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("generate", help="記事を生成する")
    p.add_argument("-n", "--count", type=int, default=1, help="生成する記事数(既定: 1)")
    p.add_argument("--theme", help="テーマを指定する(省略時はAIが判断)")
    p.set_defaults(func=cmd_generate)

    p = sub.add_parser("list", help="記事一覧を表示する")
    p.add_argument("--month", help="YYYY-MM で絞り込み")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("status", help="今月の進捗を表示する")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("posted", help="note投稿を記録し、Xに告知する")
    p.add_argument("article_id", help="記事ID(list コマンドで確認)")
    p.add_argument("--url", required=True, help="公開したnote記事のURL")
    p.add_argument("--skip-x", action="store_true", help="X投稿をスキップ(文面生成のみ)")
    p.add_argument("--dry-run", action="store_true", help="投稿・記録をせず文面だけ確認")
    p.set_defaults(func=cmd_posted)

    p = sub.add_parser("config", help="設定を確認・変更する")
    p.add_argument("--set", action="append", metavar="KEY=VALUE",
                   help="例: --set monthly_target=40(複数指定可)")
    p.set_defaults(func=cmd_config)

    args = parser.parse_args()
    args.func(args)
