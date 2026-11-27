import os
import re
import html
import subprocess

md_path = "docs/guia_apresentacao_av3.md"
html_path = "docs/guia_apresentacao_av3.html"
pdf_path = "docs/guia_apresentacao_av3.pdf"

with open(md_path, "r", encoding="utf-8") as f:
    md = f.read()

header = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Guia de Defesa e Apresentação - AV3</title>
<style>
    @page {
        margin: 15mm;
        size: A4 portrait;
    }
    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        color: #1a202c;
        line-height: 1.5;
        font-size: 10.5pt;
    }
    h1 {
        color: #1b4d3e;
        border-bottom: 2px solid #2e7d32;
        padding-bottom: 6px;
        font-size: 18pt;
        margin-top: 0;
    }
    h2 {
        color: #2e7d32;
        border-bottom: 1px solid #e2e8f0;
        padding-bottom: 4px;
        margin-top: 20px;
        font-size: 14pt;
        page-break-after: avoid;
    }
    h3 {
        color: #2d3748;
        font-size: 11.5pt;
        margin-top: 14px;
        margin-bottom: 4px;
        page-break-after: avoid;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 12px 0;
        font-size: 9.5pt;
    }
    th, td {
        border: 1px solid #cbd5e0;
        padding: 6px 8px;
        text-align: left;
    }
    th {
        background-color: #f7fafc;
        color: #2d3748;
        font-weight: 600;
    }
    tr:nth-child(even) {
        background-color: #f8fafc;
    }
    blockquote {
        border-left: 4px solid #38a169;
        background-color: #f0fff4;
        margin: 8px 0;
        padding: 8px 12px;
        color: #22543d;
        border-radius: 4px;
        font-style: italic;
    }
    code {
        background-color: #edf2f7;
        padding: 2px 4px;
        border-radius: 4px;
        font-family: 'Consolas', 'Courier New', monospace;
        font-size: 9pt;
        color: #c53030;
    }
    pre {
        background-color: #1a202c;
        color: #edf2f7;
        padding: 10px;
        border-radius: 6px;
        font-family: 'Consolas', monospace;
        font-size: 8.5pt;
        overflow-x: auto;
    }
    pre code {
        background-color: transparent;
        color: inherit;
        padding: 0;
    }
    hr {
        border: 0;
        height: 1px;
        background: #e2e8f0;
        margin: 16px 0;
    }
    ul, ol {
        padding-left: 18px;
        margin-top: 4px;
        margin-bottom: 4px;
    }
    li {
        margin-bottom: 3px;
    }
    p {
        margin-top: 4px;
        margin-bottom: 6px;
    }
</style>
</head>
<body>
"""

html_body = []
lines = md.split("\n")
in_table = False
in_code = False

for line in lines:
    if line.startswith("```"):
        if in_code:
            html_body.append("</pre>")
            in_code = False
        else:
            in_code = True
            html_body.append("<pre><code>")
        continue
    if in_code:
        html_body.append(html.escape(line))
        continue

    if line.startswith("|") and line.endswith("|"):
        if not in_table:
            html_body.append("<table>")
            in_table = True
            cells = [c.strip() for c in line.split("|")[1:-1]]
            html_body.append("<tr>" + "".join(f"<th>{html.escape(c)}</th>" for c in cells) + "</tr>")
            continue
        elif "---" in line:
            continue
        else:
            cells = [c.strip() for c in line.split("|")[1:-1]]
            formatted_cells = []
            for c in cells:
                c_esc = html.escape(c)
                c_esc = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", c_esc)
                c_esc = re.sub(r"`(.*?)`", r"<code>\1</code>", c_esc)
                formatted_cells.append(c_esc)
            html_body.append("<tr>" + "".join(f"<td>{c}</td>" for c in formatted_cells) + "</tr>")
            continue
    else:
        if in_table:
            html_body.append("</table>")
            in_table = False

    if line.startswith(">"):
        content = html.escape(line[1:].strip())
        content = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", content)
        content = re.sub(r"\*(.*?)\*", r"<em>\1</em>", content)
        content = re.sub(r"`(.*?)`", r"<code>\1</code>", content)
        html_body.append(f"<blockquote>{content}</blockquote>")
        continue

    if line.startswith("# "):
        html_body.append(f"<h1>{html.escape(line[2:])}</h1>")
        continue
    elif line.startswith("## "):
        html_body.append(f"<h2>{html.escape(line[3:])}</h2>")
        continue
    elif line.startswith("### "):
        html_body.append(f"<h3>{html.escape(line[4:])}</h3>")
        continue
    elif line.startswith("---"):
        html_body.append("<hr>")
        continue

    if line.startswith("* ") or line.startswith("- "):
        content = html.escape(line[2:].strip())
        content = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", content)
        content = re.sub(r"\*(.*?)\*", r"<em>\1</em>", content)
        content = re.sub(r"`(.*?)`", r"<code>\1</code>", content)
        content = re.sub(r"\[(.*?)\]\((.*?)\)", r'<a href="\2">\1</a>', content)
        html_body.append(f"<ul><li>{content}</li></ul>")
        continue

    if line.strip():
        content = html.escape(line.strip())
        content = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", content)
        content = re.sub(r"\*(.*?)\*", r"<em>\1</em>", content)
        content = re.sub(r"`(.*?)`", r"<code>\1</code>", content)
        content = re.sub(r"\[(.*?)\]\((.*?)\)", r'<a href="\2">\1</a>', content)
        html_body.append(f"<p>{content}</p>")

if in_table:
    html_body.append("</table>")
if in_code:
    html_body.append("</pre>")

full_html = header + "\n".join(html_body) + "\n</body></html>"

with open(html_path, "w", encoding="utf-8") as f:
    f.write(full_html)

print("HTML generated successfully.")
