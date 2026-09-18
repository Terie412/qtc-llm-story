"""Markdown -> HTML -> PDF，为中文长文排版。

用法：
    python build/md2pdf.py

依赖：markdown（pip install markdown）
渲染：调用本机 Chrome 无头模式；没有 Chrome 时回退到 Edge。
"""

import io
import os
import re
import html
import subprocess
import markdown

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build")
SRC = os.path.join(ROOT, "神经网络史话.md")
HTML_OUT = os.path.join(BUILD, "神经网络史话.html")
PDF_OUT = os.path.join(ROOT, "神经网络史话.pdf")

os.makedirs(BUILD, exist_ok=True)
raw = io.open(SRC, encoding="utf-8").read()

# 书名与副标题单独抽出来排版成封面
m_title = re.search(r"^#\s+(.+)$", raw, re.M)
m_sub = re.search(r"^###\s+(.+)$", raw, re.M)
TITLE = m_title.group(1).strip() if m_title else "未命名"
SUB = m_sub.group(1).strip() if m_sub else ""

body_md = raw
if m_title:
    body_md = raw[m_title.end():]
    body_md = re.sub(r"^\s*###\s+.+$", "", body_md, count=1, flags=re.M)

md = markdown.Markdown(extensions=["tables", "toc", "sane_lists", "attr_list"])
body_html = md.convert(body_md).replace("<hr />", '<hr class="gap" />')

toc_items = []
for mt in re.finditer(r'<h2 id="([^"]+)">(.*?)</h2>', body_html):
    toc_items.append((mt.group(1), re.sub(r"<[^>]+>", "", mt.group(2))))
toc_html = "\n".join(
    f'<li><a href="#{a}">{html.escape(t)}</a></li>' for a, t in toc_items
)

COVER = f"""
<section class="cover">
  <div class="cover-inner">
    <h1 class="cover-title">{html.escape(TITLE)}</h1>
    <p class="cover-sub">{html.escape(SUB)}</p>
    <p class="cover-note">全 {len(toc_items)} 节</p>
  </div>
</section>
"""

TOC = f"""
<section class="toc">
  <h2 class="toc-title">目录</h2>
  <ol class="toc-list">
{toc_html}
  </ol>
</section>
"""

CSS = """
@page { size: A4; margin: 20mm 18mm 20mm 18mm; }
* { box-sizing: border-box; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body {
  margin: 0;
  font-family: "Microsoft YaHei", "PingFang SC", "Hiragino Sans GB", sans-serif;
  font-size: 10.8pt;
  line-height: 1.9;
  color: #1a1a1a;
  text-align: justify;
  word-break: break-word;
}
p { margin: 0 0 0.62em 0; }
strong { font-weight: 600; color: #000; }
em { font-style: normal; color: #333; }

.cover {
  height: 247mm;
  display: flex; align-items: center; justify-content: center;
  page-break-after: always;
}
.cover-inner { text-align: center; }
.cover-title {
  display: inline-block;
  font-size: 34pt; font-weight: 600;
  letter-spacing: 0.14em; margin: 0 0 12mm 0;
  color: #111; padding: 0 0 6mm 0;
}
.cover-sub { font-size: 12pt; color: #555; letter-spacing: 0.06em; margin: 0 0 26mm 0; }
.cover-note { font-size: 9.5pt; color: #888; margin: 0; }

.toc { page-break-after: always; }
.toc-title {
  font-size: 17pt; font-weight: 600; text-align: center;
  margin: 0 0 10mm 0; border: none; padding: 0;
}
.toc-list {
  list-style: none; padding: 0; margin: 0;
  columns: 2; column-gap: 12mm;
}
.toc-list li { font-size: 9.4pt; line-height: 1.75; margin-bottom: 1.6mm; break-inside: avoid; }
.toc-list a { color: #1a1a1a; text-decoration: none; }

h1 { font-size: 20pt; font-weight: 600; margin: 0 0 6mm 0;
     padding-bottom: 3mm; border-bottom: 2px solid #222; }
h2 { font-size: 15pt; font-weight: 600; margin: 11mm 0 4mm 0;
     padding-bottom: 2mm; border-bottom: 1px solid #ccc;
     page-break-after: avoid; color: #111; }
h3 { font-size: 12pt; font-weight: 600; margin: 7mm 0 3mm 0;
     page-break-after: avoid; color: #222; }
h4 { font-size: 11pt; font-weight: 600; margin: 5mm 0 2mm 0; }

table { width: 100%; border-collapse: collapse; margin: 4mm 0 6mm 0;
        font-size: 9.2pt; line-height: 1.6; page-break-inside: avoid; }
th, td { border: 1px solid #d0d0d0; padding: 1.8mm 2.6mm;
         text-align: left; vertical-align: top; }
th { background: #f2f2f2; font-weight: 600; }
tbody tr:nth-child(even) { background: #fafafa; }

blockquote { margin: 4mm 0; padding: 2mm 0 2mm 5mm;
             border-left: 2.5px solid #bbb; color: #444; }
blockquote p { margin: 0.3em 0; }

ul, ol { margin: 0.4em 0 0.8em 0; padding-left: 6mm; }
li { margin-bottom: 0.32em; }

hr.gap { border: none; height: 0; margin: 6mm 0; page-break-after: avoid; }
hr { border: none; border-top: 1px solid #ddd; margin: 6mm 0; }
"""

HTML = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<title>{html.escape(TITLE)}</title>
<style>{CSS}</style>
</head>
<body>
{COVER}
{TOC}
<main>
{body_html}
</main>
</body>
</html>
"""

io.open(HTML_OUT, "w", encoding="utf-8").write(HTML)
print("HTML:", HTML_OUT)
print("目录条目:", len(toc_items))

CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]
browser = next((c for c in CANDIDATES if os.path.exists(c)), None)
if not browser:
    raise SystemExit("没找到 Chrome 或 Edge，无法渲染 PDF")

if os.path.exists(PDF_OUT):
    os.remove(PDF_OUT)

url = "file:///" + HTML_OUT.replace("\\", "/")
res = subprocess.run(
    [
        browser,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--no-pdf-header-footer",
        "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=15000",
        f"--print-to-pdf={PDF_OUT}",
        url,
    ],
    capture_output=True,
    text=True,
    timeout=300,
)
print("exit:", res.returncode)
print("PDF:", PDF_OUT, os.path.getsize(PDF_OUT), "bytes")
