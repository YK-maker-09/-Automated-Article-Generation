"""記事Markdownを、ブログ(Blogger/WordPressのHTMLビュー)に貼れるHTMLへ変換する。

外部パッケージに依存しない軽量コンバータ。当ツールが生成する記事の範囲
(見出し/段落/箇条書き/番号リスト/表/太字/インラインコード/コードブロック/
引用/<!-- AD --> マーカー)をカバーする。
"""

import html
import re

_BOLD = re.compile(r"\*\*(.+?)\*\*")
_CODE = re.compile(r"`([^`]+?)`")


def _inline(text: str) -> str:
    """行内の装飾(太字・インラインコード)をHTMLに変換。先にエスケープする。"""
    out = []
    last = 0
    # インラインコードを先に退避(中身はエスケープするが装飾はしない)
    for m in _CODE.finditer(text):
        out.append(_bold_escape(text[last:m.start()]))
        out.append(f"<code>{html.escape(m.group(1))}</code>")
        last = m.end()
    out.append(_bold_escape(text[last:]))
    return "".join(out)


def _bold_escape(text: str) -> str:
    esc = html.escape(text)
    # エスケープ後に ** を <strong> へ(** は escape で変化しない)
    return _BOLD.sub(r"<strong>\1</strong>", esc)


def markdown_to_html(md: str) -> str:
    lines = md.split("\n")
    out: list[str] = []
    i = 0
    n = len(lines)

    def close_para(buf: list[str]):
        if buf:
            out.append(f"<p>{'<br>'.join(_inline(b) for b in buf)}</p>")
            buf.clear()

    para: list[str] = []

    while i < n:
        line = lines[i]
        stripped = line.strip()

        # 広告マーカー
        if stripped == "<!-- AD -->":
            close_para(para)
            out.append("<!-- 広告ユニットをここに配置 -->")
            i += 1
            continue

        # コードブロック
        if stripped.startswith("```"):
            close_para(para)
            i += 1
            code: list[str] = []
            while i < n and not lines[i].strip().startswith("```"):
                code.append(html.escape(lines[i]))
                i += 1
            i += 1  # 閉じる ```
            out.append("<pre><code>" + "\n".join(code) + "</code></pre>")
            continue

        # 見出し
        m = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if m:
            close_para(para)
            level = len(m.group(1))
            out.append(f"<h{level}>{_inline(m.group(2))}</h{level}>")
            i += 1
            continue

        # 表(| で始まり、次行が区切り行)
        if stripped.startswith("|") and i + 1 < n and re.match(r"^\|?[\s:|-]+\|?$", lines[i + 1].strip()) and "-" in lines[i + 1]:
            close_para(para)
            header = _split_row(stripped)
            i += 2  # ヘッダ行 + 区切り行
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append(_split_row(lines[i].strip()))
                i += 1
            thead = "".join(f"<th>{_inline(c)}</th>" for c in header)
            body = ""
            for r in rows:
                body += "<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in r) + "</tr>"
            out.append(
                '<table border="1" cellpadding="6" cellspacing="0">'
                f"<thead><tr>{thead}</tr></thead><tbody>{body}</tbody></table>"
            )
            continue

        # 番号付きリスト
        if re.match(r"^\d+\.\s+", stripped):
            close_para(para)
            items = []
            while i < n and re.match(r"^\d+\.\s+", lines[i].strip()):
                items.append(re.sub(r"^\d+\.\s+", "", lines[i].strip()))
                i += 1
            out.append("<ol>" + "".join(f"<li>{_inline(it)}</li>" for it in items) + "</ol>")
            continue

        # 箇条書き
        if re.match(r"^[-*]\s+", stripped):
            close_para(para)
            items = []
            while i < n and re.match(r"^[-*]\s+", lines[i].strip()):
                items.append(re.sub(r"^[-*]\s+", "", lines[i].strip()))
                i += 1
            out.append("<ul>" + "".join(f"<li>{_inline(it)}</li>" for it in items) + "</ul>")
            continue

        # 引用
        if stripped.startswith(">"):
            close_para(para)
            quote = []
            while i < n and lines[i].strip().startswith(">"):
                quote.append(re.sub(r"^>\s?", "", lines[i].strip()))
                i += 1
            out.append("<blockquote>" + "<br>".join(_inline(q) for q in quote) + "</blockquote>")
            continue

        # 空行 = 段落の区切り
        if stripped == "":
            close_para(para)
            i += 1
            continue

        # 通常の本文行
        para.append(stripped)
        i += 1

    close_para(para)
    return "\n".join(out) + "\n"


def _split_row(row: str) -> list[str]:
    return [c.strip() for c in row.strip().strip("|").split("|")]
