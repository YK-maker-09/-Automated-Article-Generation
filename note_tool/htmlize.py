"""記事Markdownを、ブログ(Blogger/WordPressのHTMLビュー)に貼れるHTMLへ変換する。

外部パッケージに依存しない軽量コンバータ。当ツールが生成する記事の範囲
(見出し/段落/箇条書き/番号リスト/表/太字/インラインコード/コードブロック/
引用/<!-- AD --> マーカー)をカバーする。

レイアウト方針:
- 先頭のH1(記事タイトル)は出力しない。タイトルはブログの「タイトル欄」に入れるため、
  本文に入れると二重表示になり、テーマによっては行間が詰まって重なる。
- 見出し・段落・表などに行間と余白をインラインstyleで明示指定し、
  どのブログテーマに貼っても文字が重ならないようにする。
"""

import html
import re

_BOLD = re.compile(r"\*\*(.+?)\*\*")
_CODE = re.compile(r"`([^`]+?)`")

# どのテーマでも崩れないよう、要素ごとに行間・余白を明示する
S_H2 = "margin:1.8em 0 0.6em;line-height:1.5;font-size:1.35em;font-weight:bold;"
S_H3 = "margin:1.4em 0 0.5em;line-height:1.5;font-size:1.12em;font-weight:bold;"
S_P = "margin:0 0 1em;line-height:1.9;"
S_UL = "margin:0 0 1.2em 1.4em;line-height:1.9;padding:0;"
S_LI = "margin:0.35em 0;"
S_TABLE = "border-collapse:collapse;width:100%;margin:1em 0;"
S_TH = "border:1px solid #ccc;padding:8px 10px;text-align:left;background:#f4f4f4;"
S_TD = "border:1px solid #ccc;padding:8px 10px;text-align:left;"
S_PRE = "background:#f5f5f5;padding:12px 14px;border-radius:6px;overflow-x:auto;line-height:1.6;margin:1em 0;"
S_QUOTE = "margin:1em 0;padding:0.5em 1em;border-left:4px solid #ccc;color:#555;line-height:1.9;"
S_WRAP = "line-height:1.9;font-size:16px;"


def _inline(text: str) -> str:
    out = []
    last = 0
    for m in _CODE.finditer(text):
        out.append(_bold_escape(text[last:m.start()]))
        out.append(f'<code style="background:#eee;padding:1px 4px;border-radius:3px;">{html.escape(m.group(1))}</code>')
        last = m.end()
    out.append(_bold_escape(text[last:]))
    return "".join(out)


def _bold_escape(text: str) -> str:
    esc = html.escape(text)
    return _BOLD.sub(r"<strong>\1</strong>", esc)


def markdown_to_html(md: str) -> str:
    lines = md.split("\n")
    out: list[str] = []
    i = 0
    n = len(lines)
    seen_h1 = False

    para: list[str] = []

    def close_para(buf: list[str]):
        if buf:
            out.append(f'<p style="{S_P}">{"<br>".join(_inline(b) for b in buf)}</p>')
            buf.clear()

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if stripped == "<!-- AD -->":
            close_para(para)
            out.append("<!-- 広告ユニットをここに配置 -->")
            i += 1
            continue

        if stripped.startswith("```"):
            close_para(para)
            i += 1
            code = []
            while i < n and not lines[i].strip().startswith("```"):
                code.append(html.escape(lines[i]))
                i += 1
            i += 1
            out.append(f'<pre style="{S_PRE}"><code>' + "\n".join(code) + "</code></pre>")
            continue

        m = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if m:
            close_para(para)
            level = len(m.group(1))
            text = m.group(2)
            if level == 1 and not seen_h1:
                # 先頭のタイトルH1は本文に出さない(ブログのタイトル欄に入れるため)
                seen_h1 = True
                i += 1
                continue
            style = S_H2 if level <= 2 else S_H3
            tag = "h2" if level <= 2 else "h3"
            out.append(f'<{tag} style="{style}">{_inline(text)}</{tag}>')
            i += 1
            continue

        if stripped.startswith("|") and i + 1 < n and re.match(r"^\|?[\s:|-]+\|?$", lines[i + 1].strip()) and "-" in lines[i + 1]:
            close_para(para)
            header = _split_row(stripped)
            i += 2
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append(_split_row(lines[i].strip()))
                i += 1
            thead = "".join(f'<th style="{S_TH}">{_inline(c)}</th>' for c in header)
            body = ""
            for r in rows:
                body += "<tr>" + "".join(f'<td style="{S_TD}">{_inline(c)}</td>' for c in r) + "</tr>"
            out.append(
                f'<div style="overflow-x:auto;"><table style="{S_TABLE}">'
                f"<thead><tr>{thead}</tr></thead><tbody>{body}</tbody></table></div>"
            )
            continue

        if re.match(r"^\d+\.\s+", stripped):
            close_para(para)
            items = []
            while i < n and re.match(r"^\d+\.\s+", lines[i].strip()):
                items.append(re.sub(r"^\d+\.\s+", "", lines[i].strip()))
                i += 1
            lis = "".join(f'<li style="{S_LI}">{_inline(it)}</li>' for it in items)
            out.append(f'<ol style="{S_UL}">{lis}</ol>')
            continue

        if re.match(r"^[-*]\s+", stripped):
            close_para(para)
            items = []
            while i < n and re.match(r"^[-*]\s+", lines[i].strip()):
                items.append(re.sub(r"^[-*]\s+", "", lines[i].strip()))
                i += 1
            lis = "".join(f'<li style="{S_LI}">{_inline(it)}</li>' for it in items)
            out.append(f'<ul style="{S_UL}">{lis}</ul>')
            continue

        if stripped.startswith(">"):
            close_para(para)
            quote = []
            while i < n and lines[i].strip().startswith(">"):
                quote.append(re.sub(r"^>\s?", "", lines[i].strip()))
                i += 1
            out.append(f'<blockquote style="{S_QUOTE}">' + "<br>".join(_inline(q) for q in quote) + "</blockquote>")
            continue

        if stripped == "":
            close_para(para)
            i += 1
            continue

        para.append(stripped)
        i += 1

    close_para(para)
    inner = "\n".join(out)
    return f'<div style="{S_WRAP}">\n{inner}\n</div>\n'


def _split_row(row: str) -> list[str]:
    return [c.strip() for c in row.strip().strip("|").split("|")]
