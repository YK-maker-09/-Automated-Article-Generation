"""設定の読み書き。config.json をプロジェクト直下に保持する。"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config.json"
ARTICLES_DIR = BASE_DIR / "articles"
STATE_PATH = BASE_DIR / "data" / "state.json"

DEFAULT_CONFIG = {
    # 月間の目標記事数(増やしたい場合はここを変更 or `config --set monthly_target=40`)
    "monthly_target": 30,
    # 記事生成に使うClaudeモデル
    "model": "claude-opus-4-8",
    # 総合スコアがこの値未満なら自動リライト(0-100)
    "quality_threshold": 80,
    # 自動リライトの最大回数
    "max_revisions": 2,
    # 月間の収益目標(円)
    "revenue_goal_yen": [50000, 100000],
    # 有料記事の価格帯(円)。AIはこの範囲で価格を提案する
    "price_range_yen": [100, 500],
    # 記事テーマの軸。AIはここから需要と収益性を見て都度選ぶ。
    # 自分の得意分野に合わせて自由に書き換えてOK
    "genres": [
        "副業・お金の増やし方",
        "AI・ChatGPT活用術",
        "仕事術・生産性向上",
        "ライフハック・習慣化",
        "SNS運用・発信ノウハウ",
        "キャリア・転職",
        "健康・メンタル管理",
    ],
    # Xアカウント(告知ツイートの文面調整に使用)
    "x_account": "@Interkyky",
}


def load_config() -> dict:
    config = dict(DEFAULT_CONFIG)
    if CONFIG_PATH.exists():
        config.update(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
    return config


def save_config(config: dict) -> None:
    CONFIG_PATH.write_text(
        json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
