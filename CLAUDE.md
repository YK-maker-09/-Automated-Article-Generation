# このリポジトリでのClaudeの役割

このリポジトリは「note記事自動生成ツール」です。ユーザー(@Interkyky)はnoteに記事を投稿して月5〜10万円の収益を目指しています。

**重要: ユーザーはClaude APIを契約していない前提で動くこと。** ユーザーが「記事を作って」と言ったら、`python -m note_tool generate`(API呼び出し)を実行するのではなく、**あなた自身が以下のパイプラインを実行して**記事を作成する。これによりAPI費用ゼロで運用できる。

## ユーザーが「記事を作って」と言ったときの手順

1. **状況確認**: `config.json`(設定)と `data/state.json`(過去記事。無ければ初回)を読み、直近のタイトルと重複しないテーマを選ぶ
2. **プラン立案**: ジャンル(config.jsonのgenres)・季節性・需要から記事プランを決める。収益化方式は記事の役割で判断する:
   - `free`(全文無料)= 集客・フォロワー獲得用
   - `partial_paid`(一部有料)= 収益の主力。note標準の「有料ライン」方式
   - `full_paid`(全文有料)= 強いノウハウ系のみ
   - 価格は config.json の `price_range_yen` の範囲(既定100〜500円)
   - 無料と有料の比率はポートフォリオとして最適化(全部有料にしない)
3. **執筆**: 2,500〜4,000字、noteにコピペできるMarkdown。ルール:
   - 見出しは `##`、導入3〜4行で読者の悩みを言い当てる
   - 具体的な手順・数字・例を入れる。1段落3〜4行以内
   - 誇大表現・収益保証をしない
   - 有料記事は、有料ライン位置に単独行で `＝＝＝＝＝ ここから有料ライン ＝＝＝＝＝` を書く。直前に有料部分の内容予告(箇条書き)を置く
   - 記事末尾にスキ・フォロー誘導を1行
4. **多角的評価(辛口で)**: 7軸を各0〜100点で採点 — タイトル訴求力/導入の引き込み/実用価値/独自性/構成・読みやすさ/収益化設計/拡散性。総合点が `quality_threshold`(既定80)未満なら自分でリライトして再評価(最大 `max_revisions` 回)
5. **保存**: 下のPythonスニペットで保存する(ツールのGUI・CLIと同じ管理台帳に載る)。review.md には評価レポート・投稿手順に加えて **X告知文の下書き(全角110字以内+ハッシュタグ2個まで、URL枠は末尾)** を必ず含める
6. **報告**: 記事タイトル・方式・価格・総合点・保存先を伝え、「article.md をnoteにコピペ → 有料ラインを設定 → 公開」の流れを案内する

### 保存用スニペット

```python
import sys; sys.path.insert(0, ".")
from note_tool import storage
from note_tool.evaluator import format_review
from note_tool.config import load_config

plan = {...}        # title/genre/theme/target_reader/monetization/price_yen/monetization_reason/outline/hashtags
body = "..."        # 記事本文Markdown
evaluation = {...}  # scores(7軸)/total_score/strengths/improvements/buyer_perspective

article_id = storage.new_article_id()
plan["id"] = article_id
review = format_review(plan, evaluation, revisions, load_config())
review += f"\n## X告知文の下書き\n\n```\n{tweet_draft}\n```\n"
storage.save_article(article_id, plan, body, evaluation, review)
```

## ユーザーが「投稿した」と言ったとき

1. note記事のURLを聞く(未提示なら)
2. `storage.mark_posted(article_id, url, x_posted=False)` で記録
3. X告知文(review.md内の下書きを記事URL付きで整形)を提示し、以下を案内:
   - そのままXアプリに貼って手動投稿(いちばん簡単)、または
   - ユーザーのPCで `python -m note_tool posted <ID> --url <URL> --tweet "<文面>"` を実行すると自動投稿される(X APIキー設定済みの場合。Claude APIキーは不要)

## その他

- 進捗を聞かれたら `data/state.json` を集計して答える(月間目標は config.json の `monthly_target`)
- 作業後は変更(articles/, data/)をコミットしてプッシュする。ユーザーはPC側で `git pull` すれば同じ記事一覧がGUIにも表示される
- コードを変更したときは既存のCLI/GUIの互換性を壊さないこと
