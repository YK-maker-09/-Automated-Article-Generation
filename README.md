# ブログ記事自動生成ツール(Google AdSense収益化)

自分のブログに投稿する記事を **AIが多角的に分析・評価しながら自動生成** し、**Google AdSenseの広告収益**を狙うツールです。**1日10記事(月300記事)** の自動生成体制で運用します。

## できること

| 機能 | 内容 |
|---|---|
| キーワード選定 | 検索需要のあるロングテールキーワードをAIが選定。**広告単価の高いカテゴリ(転職/副業とお金/資格・学習/サービス比較)を優先** |
| 記事生成 | 2,800〜4,500字のブログ用Markdown。**結論ファーストのリード・疑問形見出し・比較表・FAQ**で滞在時間とAI検索(AI Overview等)への引用されやすさを最適化 |
| 広告配置支援 | 最適な広告位置に `<!-- AD -->` マーカーを3箇所自動挿入 |
| SEO情報出力 | メタディスクリプション・狙うキーワード・内部リンク候補を毎回出力 |
| 多角的評価 | 検索意図/滞在時間/E-E-A-T/AI引用適性/読みやすさ/広告収益性/独自性 の7軸で辛口採点。80点未満は自動リライト |
| X告知 | 記事ごとに告知文の下書きを出力。X APIキーがあれば自動投稿も可 |
| 管理 | GUI・CLIで記事一覧・進捗(x/300)を管理 |

## 運用のしかた(2通り)

### A. Coworkの定期実行(標準・費用ゼロ)

Coworkに登録済みのルーティンが **毎日6時〜15時(JST)に1時間おきに1本、計10本** を自動生成し、チャットに article.md + review.md を届けます。Claude APIは使いません。

あなたの作業は「ブログに貼り付けて公開」だけ。詳細は **`運用手順.md`** を参照。

### B. GUI/CLI(Claude APIチャージ時のみ)

```bash
pip install -r requirements.txt
cp .env.example .env   # ANTHROPIC_API_KEY を記入
python -m note_tool gui        # ブラウザGUI
python -m note_tool generate   # CLIで1本生成
```

## ブログとAdSenseの準備

**AdSenseは自分のブログが必要です**(WordPress推奨/無料ならBlogger)。開設〜審査申請〜広告配置〜収益の現実的な見通しまで **`AdSense開設ガイド.md`** にまとめています。

> ⚠️ 収益の目安: AdSenseは1,000PVあたり200〜500円程度。月5万円には月10〜25万PVが必要で、新規ブログの検索流入が育つには3〜6ヶ月かかります。アフィリエイト併用・X流入での補強を推奨します(ガイド参照)。

## 主なコマンド

```bash
python -m note_tool list                        # 記事一覧
python -m note_tool status                      # 今月の進捗
python -m note_tool posted <ID> --url <記事URL> --tweet "<告知文>"   # 投稿記録+X告知(Claude API不要)
python -m note_tool config --set monthly_target=300                  # 設定変更
```

## ファイル構成

```
note_tool/            ツール本体(planner/writer/evaluator/x_poster/cli/webapp)
CLAUDE.md             Cowork自動生成のパイプライン定義
AdSense開設ガイド.md   ブログ開設〜審査〜広告配置ガイド
運用手順.md            毎日の運用フロー
config.json           設定(目標本数・ジャンル・合格基準など)
articles/             生成された記事(article.md / review.md / meta.json)
data/state.json       管理台帳
```
