# このリポジトリでのClaudeの役割

このリポジトリは「AdSenseブログ記事自動生成ツール」です。ユーザー(@Interkyky)は自分のブログに記事を投稿し、**Google AdSenseの広告収益**で月5〜10万円を目指しています。**1日10記事・月300記事**ペースで運用します(noteでの販売は廃止済み。新規記事はすべてAdSense方式)。

**重要: ユーザーはClaude APIを契約していない前提で動くこと。** 記事生成は `python -m note_tool generate`(API呼び出し)ではなく、**あなた自身が以下のパイプラインを実行して**作成する。これによりAPI費用ゼロで運用できる。

## AdSense収益化の基本戦略(プラン立案の判断基準)

- 収益 = PV × ページRPM。**検索流入を集められるキーワード選定が起点**
- 1記事1キーワード。「chatgpt 議事録 作り方」のような検索意図が明確なロングテール(2〜4語)を狙う
- **広告単価(CPC)の高いカテゴリを優先する(7〜8割)**: 転職・キャリア/副業とお金(確定申告・税金・開業)/資格・スクール・学習/通信・ビジネスサービス比較(格安SIM・回線・会計ソフト等)。残り2〜3割は集客用のAI活用・仕事術系
- **YMYLの断定禁止**: 医療の診断・特定銘柄の投資推奨・法律判断は書かない。税金等は「一般的な手順+国税庁など公式への誘導」に留める
- 大手が上位独占する激戦キーワードは避け、具体的な悩み・手順・比較系を狙う
- **滞在時間**と**回遊**、**AI検索(Google AI Overview等)への引用されやすさ**を常に設計に織り込む

## 記事1本の生成パイプライン(毎時の定期実行も「記事を作って」も同じ)

1. **状況確認**: `config.json` と `data/state.json` を読み、既存記事とキーワード・テーマが重複しないようにする(300本規模になるため、タイトルだけでなく狙うキーワードの重複・共食いに注意)
2. **需要の実データ確認(必須)**: 候補キーワードを2〜3個立て、**WebSearch で実際に検索して裏取りする**。判断基準:
   - **需要があるか**(検索結果・関連記事が豊富か)
   - **勝てるか**(検索上位10件が大手・公式・銀行・大手メディアで独占されていたら新規ブログでは勝てない → そのキーワードは捨てる。上位に個人ブログ・note が混じっていれば勝てる余地あり)
   - **YMYL回避**(医療・投資・法律の断定はしない。税金は一般手順+公式誘導まで)
   - 検索で得た**具体的な数字・事実**(相場・時間・条件など)を本文に反映して精度と信頼性を上げる
   - 勝てないと判断したら候補を差し替える。review.md に確認結果(検索語・競合状況・採用理由)を残す
3. **プラン立案**: target_keyword / title(キーワード前方配置・32字前後)/ meta_description(100〜120字)/ outline。monetization は `"adsense"`、price_yen は 0。monetization_reason にキーワード選定理由(検索需要・競合の弱さ・CPC水準)を書く
3. **執筆**: 2,800〜4,500字、ブログにコピペできるMarkdown:
   - **リード文**: 最初の3行で状況の言い当て+結論(結論ファースト)。キーワードを1文目に自然に含める
   - **H2は検索者の疑問の言葉**(4〜7個)、H3で分解。手順は番号リスト、比較は**表**
   - 「〜とは、…です」の定義文を各セクションに置く。1段落3行以内。体験談・数字でE-E-A-T。誇大表現禁止
   - **`<!-- AD -->` を単独行で3箇所**: ①リード直後 ②中盤H2直前 ③まとめ直前
   - **FAQ必須**(H2「よくある質問」+Q&A 3〜5組。質問はH3、回答2〜3文)
   - **まとめ**: 要点箇条書き+「(関連記事リンク)」誘導1行
4. **多角的評価(辛口)**: 7軸各0〜100点 — search_intent / dwell_time / trust / ai_citability / readability / ad_revenue / originality。総合80点未満または2,800字未満なら部分修正して再評価(最大2回)
5. **保存**: 下のスニペット。review.md に **X告知文の下書き(全角110字以内+ハッシュタグ2個まで)** と、state.json から選んだ**内部リンク候補の過去記事1〜2本**を含める
6. **報告**: タイトル・キーワード・総合点・進捗(x/300)

### 保存用スニペット

```python
import sys; sys.path.insert(0, ".")
from note_tool import storage
from note_tool.evaluator import format_review
from note_tool.config import load_config

plan = {...}        # title/genre/theme/target_reader/target_keyword/meta_description/
                    # monetization="adsense"/price_yen=0/monetization_reason/outline/hashtags
body = "..."        # 記事本文Markdown(<!-- AD --> マーカー3箇所入り)
evaluation = {...}  # scores(7軸)/total_score/strengths/improvements/buyer_perspective

article_id = storage.new_article_id()
plan["id"] = article_id
review = format_review(plan, evaluation, revisions, load_config())
review += f"\n## 内部リンク候補\n\n- {関連過去記事のタイトル}\n"
review += f"\n## X告知文の下書き(投稿時に末尾へ記事URLを追加)\n\n```\n{tweet_draft}\n```\n"
storage.save_article(article_id, plan, body, evaluation, review)
# save_article は article.md と一緒に、Bloggerにそのまま貼れる article.html も自動生成する
# (article.html は htmlize.py が生成: 先頭タイトルH1は本文に出さず、全要素に行間styleを付与して
#  どのブログテーマでも文字が重ならないようにする。本文Markdownは必ず「# タイトル」から始めること)
```

## レイアウトの注意(重要)

- ユーザーは Blogger に **article.html** を「HTMLビュー」で貼る。タイトルは本文に出さず、ブログのタイトル欄に入れる(二重表示・行間崩れを防ぐため)。この処理は htmlize.py が自動で行うので、本文Markdownは通常どおり「# タイトル」から書いてよい
- review.md にはタイトルを「最終チェックシート:」抜きの生のタイトルで明示すること(取り違え防止)

## 定期実行時の通知ポリシー(1日10回動くため)

- **SendUserFile**(article.md + review.md)は毎回行う(status=proactive)
- **PushNotification は使い分ける**: その日の1本目=「本日の生成開始」/ 10本目=「本日10本完了」のサマリーのみ。2〜9本目は通知しない(data/state.json の当日件数で判断)
- エラーで完了できない場合は必ず PushNotification で知らせる

## ユーザーが「投稿した」と言ったとき

1. 記事URLを聞く(未提示なら)→ `storage.mark_posted(article_id, url, x_posted=False)` で記録
2. X告知文(review.md内の下書きをURL付きで整形)を提示。手動投稿か `python -m note_tool posted <ID> --url <URL> --tweet "<文面>"` を案内

## その他

- ブログ開設・AdSense審査は `AdSense開設ガイド.md` に沿って案内する
- 過去のnote用記事(20260705-001〜004)はレガシーとして台帳に残っているだけ。新規は常にAdSense方式
- 進捗を聞かれたら `data/state.json` を集計(月間目標は config.json の `monthly_target`=300)
- 作業後は変更(articles/, data/)をコミットして claude/note-article-generator-jz7mqt へプッシュ
- コード変更時は既存CLI/GUIの互換性を壊さないこと
