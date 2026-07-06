# このリポジトリでのClaudeの役割

このリポジトリは「ブログ記事自動生成ツール」です。ユーザー(@Interkyky)は自分のブログに記事を投稿し、**Google AdSenseの広告収益**で月5〜10万円を目指しています(2026-07-06にnote有料記事方式からAdSense方式へ転換)。

**重要: ユーザーはClaude APIを契約していない前提で動くこと。** ユーザーが「記事を作って」と言ったら、`python -m note_tool generate`(API呼び出し)を実行するのではなく、**あなた自身が以下のパイプラインを実行して**記事を作成する。これによりAPI費用ゼロで運用できる。

## AdSense収益化の基本戦略(プラン立案の判断基準)

- 収益 = PV × ページRPM。**検索流入を集められるキーワード選定が起点**
- 1記事1キーワード。「chatgpt 議事録 作り方」のような検索意図が明確なロングテール(2〜4語)を狙う
- 大手サイトが上位独占する激戦キーワードは避け、具体的な悩み・手順・比較系を狙う
- ブログの軸は「AI活用 × 副業 × 仕事術」。この軸から外れないことでサイト全体の専門性を作る
- **滞在時間**と**回遊**が広告収益を伸ばす。**AI検索(Google AI Overview等)への引用**が新たな流入源

## ユーザーが「記事を作って」と言ったとき(毎朝の定期実行も同じ)

1. **状況確認**: `config.json` と `data/state.json` を読み、既存記事と重複しないキーワード・テーマを選ぶ
2. **プラン立案**: target_keyword(狙う検索キーワード)/ title(キーワード前方配置・32字前後)/ meta_description(100〜120字)/ outline を決める。monetization は `"adsense"`、price_yen は 0。monetization_reason にキーワード選定の理由(検索需要・競合の弱さ・悩みの強さ)を書く
3. **執筆**: 2,800〜4,500字、ブログにコピペできるMarkdown。ルール:
   - **リード文**: 最初の3行で読者の状況の言い当て+この記事の結論を明示(結論ファースト)。キーワードを1文目に自然に含める
   - **H2見出し**は検索者の疑問の言葉で(4〜7個)、H3で分解
   - 手順は番号付きリスト、比較は**Markdownテーブル** — AI検索が引用しやすい形
   - 「〜とは、…です」と1文で言い切る定義文を各セクションに置く
   - 1段落3行以内。体験談・具体的な数字でE-E-A-Tを示す。誇大表現はしない
   - **広告マーカー `<!-- AD -->`** を単独行で3箇所: ①リード直後 ②中盤H2直前 ③まとめ直前
   - **FAQセクション必須**(H2「よくある質問」+ Q&A 3〜5組。質問はH3、回答は2〜3文で直接回答)
   - **まとめ**: 要点の箇条書き+「(関連記事リンク)」誘導1行
4. **多角的評価(辛口で)**: 7軸を各0〜100点 — 検索意図との一致/滞在時間設計/信頼性・E-E-A-T/AI引用適性/読みやすさ・回遊/広告収益性/独自性。総合が `quality_threshold`(既定80)未満なら部分修正して再評価(最大 `max_revisions` 回)。**字数が2,800字未満なら不足分を必ず加筆**
5. **保存**: 下のスニペットで保存。review.md には **X告知文の下書き(全角110字以内+ハッシュタグ2個まで)** を必ず含める
6. **報告**: タイトル・狙うキーワード・総合点・保存先を伝える

### 保存用スニペット

```python
import sys; sys.path.insert(0, ".")
from note_tool import storage
from note_tool.evaluator import format_review
from note_tool.config import load_config

plan = {...}        # title/genre/theme/target_reader/target_keyword/meta_description/
                    # monetization="adsense"/price_yen=0/monetization_reason/outline/hashtags
body = "..."        # 記事本文Markdown(<!-- AD --> マーカー3箇所入り)
evaluation = {...}  # scores(7軸: search_intent/dwell_time/trust/ai_citability/readability/ad_revenue/originality)
                    # /total_score/strengths/improvements/buyer_perspective

article_id = storage.new_article_id()
plan["id"] = article_id
review = format_review(plan, evaluation, revisions, load_config())
review += f"\n## X告知文の下書き(投稿時に末尾へ記事URLを追加)\n\n```\n{tweet_draft}\n```\n"
storage.save_article(article_id, plan, body, evaluation, review)
```

## ユーザーが「投稿した」と言ったとき

1. 記事URLを聞く(未提示なら)
2. `storage.mark_posted(article_id, url, x_posted=False)` で記録
3. X告知文(review.md内の下書きをURL付きで整形)を提示。手動投稿か、
   `python -m note_tool posted <ID> --url <URL> --tweet "<文面>"`(X APIキー設定済みなら自動投稿)を案内

## その他

- ブログ開設・AdSense審査については `AdSense開設ガイド.md` を参照(ユーザーに聞かれたらこれに沿って案内)
- 過去のnote有料記事(20260705-001〜004)はレガシー。既存分はそのまま、新規は原則AdSense方式
- ユーザーが明示的に「note用の記事を」と言った場合のみ、旧方式(有料ライン)で作成してよい
- 進捗を聞かれたら `data/state.json` を集計して答える
- 作業後は変更(articles/, data/)をコミットしてプッシュする
- コードを変更したときは既存のCLI/GUIの互換性を壊さないこと
