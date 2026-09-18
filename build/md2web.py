# -*- coding: utf-8 -*-
"""把《神经网络史话》的单一 Markdown 源拆成 MkDocs 站点。

用法（在仓库根目录）：
    python build/md2web.py      # 生成 docs/
之后交给 mkdocs：
    mkdocs build                # 只出静态站到 site/
    mkdocs gh-deploy --force    # 直接推到 gh-pages 分支

源文件只有一份：神经网络史话.md。docs/ 是生成物，不入库。
"""

import io
import os
import re
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "神经网络史话.md")
PDF = os.path.join(ROOT, "神经网络史话.pdf")
DOCS = os.path.join(ROOT, "docs")
ASSETS = os.path.join(DOCS, "assets")

os.makedirs(ASSETS, exist_ok=True)

raw = io.open(SRC, encoding="utf-8").read()

m_title = re.search(r"^#\s+(.+)$", raw, re.M)
m_sub = re.search(r"^###\s+(.+)$", raw, re.M)
TITLE = m_title.group(1).strip()
SUB = m_sub.group(1).strip()

body = raw[m_title.end():]
body = re.sub(r"^\s*###\s+.+$", "", body, count=1, flags=re.M)

# 按二级标题切章
chunks = re.split(r"^##\s+(.+?)\s*$", body, flags=re.M)
lead, pairs = chunks[0], chunks[1:]
sections = []
for i in range(0, len(pairs) - 1, 2):
    name = pairs[i].strip()
    text = pairs[i + 1].strip()
    text = re.sub(r"^-{3,}\s*$", "", text, flags=re.M).strip()
    sections.append((name, text))

# 逐章写文件
written = []
for idx, (name, text) in enumerate(sections, start=1):
    fn = "%02d.md" % idx
    io.open(os.path.join(DOCS, fn), "w", encoding="utf-8").write(
        "# %s\n\n%s\n" % (name, text)
    )
    written.append((fn, name))

# 首页
toc_lines = "\n".join(
    '%d. [%s](%s)' % (i, name, fn) for i, (fn, name) in enumerate(written, start=1)
)
n_chars = len(re.sub(r"\s", "", re.sub(r"[#*>`\[\]()\-]", "", body)))
index = """# %s

## %s

一部关于失败、误读与固执的历史：一条只能把东西分成两堆的线，是怎么长成会跟你说话的东西的。

全书 %d 节，正文约 %.1f 万字。左侧目录可直接翻章，右上角可以切换深色模式，顶部搜索框能全文检索。

[下载 PDF 版](assets/neural-networks-story.pdf){ .md-button .md-button--primary }

---

## 目录

%s
""" % (TITLE, SUB, len(written), n_chars / 10000.0, toc_lines)
io.open(os.path.join(DOCS, "index.md"), "w", encoding="utf-8").write(index)
print("正文字数(去空白):", n_chars)

# 站点自定义样式：把底部信息栏固定在窗口底部
EXTRA_CSS = """/* 底部信息栏固定在窗口底部，正文滚动时它不动 */
.md-footer {
  position: sticky;
  bottom: 0;
  z-index: 3;
}

/* 固定栏会占住视口底部，给左侧目录减掉这段高度，
   否则目录滚到底时最后几项会被盖住点不到 */
@media screen and (min-width: 76.25em) {
  .md-sidebar__scrollwrap {
    max-height: calc(100vh - 7rem);
  }
}
"""
io.open(os.path.join(ASSETS, "extra.css"), "w", encoding="utf-8").write(EXTRA_CSS)

# PDF 放一份到站点里，供下载
if os.path.exists(PDF):
    shutil.copyfile(PDF, os.path.join(ASSETS, "neural-networks-story.pdf"))
    pdf_note = "已复制 PDF"
else:
    pdf_note = "未找到 PDF，跳过"

print("标题:", TITLE, "/", SUB)
print("拆出章节: %d 节" % len(written))
for fn, name in written:
    print("   ", fn, name)
print(pdf_note)
