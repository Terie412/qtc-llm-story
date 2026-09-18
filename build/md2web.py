# -*- coding: utf-8 -*-
"""把《神经网络史话》的单一 Markdown 源拆成 MkDocs 站点。

用法（在仓库根目录）：
    python build/md2web.py      # 生成 docs/
之后交给 mkdocs：
    mkdocs build                # 只出静态站到 site/
    mkdocs gh-deploy --force    # 直接推到 gh-pages 分支

源文件只有一份：神经网络史话.md。docs/ 是生成物，不入库。
站点的观感（配色、字体、版心）写在下面的 EXTRA_CSS 里，改这一处就够。
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

# ---------------------------------------------------------------------------
# 站点样式：纸与墨、标题黑体正文宋体、每行约 38 字、底栏固定在窗口底部
# ---------------------------------------------------------------------------
EXTRA_CSS = """/* ==========================================================================
   站点外观：往"书"的方向调，不改变任何结构。
   由 build/md2web.py 生成，要改样式请改那个脚本里的 EXTRA_CSS。
   ========================================================================== */

/* ---------- 1. 配色：纸与墨 ----------
   Material 把配色变量声明在 :root / [data-md-color-scheme] 上，
   这里用 body[data-md-color-scheme=...] 提高一级特异性来覆盖。 */

body {
  --book-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
    "Microsoft YaHei", "Hiragino Sans GB", sans-serif;
  --book-serif: Georgia, "Songti SC", "Source Han Serif SC",
    "Noto Serif CJK SC", "SimSun", serif;
}

body[data-md-color-scheme="default"] {
  --book-paper: #faf8f4;
  --book-paper-soft: #f3efe8;
  --book-ink: #211e1b;
  --book-ink-soft: #6c655e;
  --book-line: #e5e0d7;
  --book-accent: #2f4f6f;

  --md-default-bg-color: var(--book-paper);
  --md-default-fg-color: var(--book-ink);
  --md-default-fg-color--light: var(--book-ink-soft);
  --md-default-fg-color--lighter: #a9a29a;
  --md-default-fg-color--lightest: var(--book-line);
  --md-primary-fg-color: var(--book-paper);
  --md-primary-fg-color--light: var(--book-paper);
  --md-primary-fg-color--dark: var(--book-paper);
  --md-primary-bg-color: var(--book-ink);
  --md-accent-fg-color: var(--book-accent);
  --md-typeset-color: var(--book-ink);
  --md-typeset-a-color: var(--book-accent);
  --md-code-bg-color: var(--book-paper-soft);
  --md-footer-bg-color: var(--book-paper);
  --md-footer-bg-color--dark: var(--book-paper);
  --md-footer-fg-color: var(--book-ink-soft);
  --md-footer-fg-color--light: var(--book-ink-soft);
  --md-footer-fg-color--lighter: #a9a29a;
}

body[data-md-color-scheme="slate"] {
  --book-paper: #17191c;
  --book-paper-soft: #1f2227;
  --book-ink: #d9d5ce;
  --book-ink-soft: #918b83;
  --book-line: #2b2f35;
  --book-accent: #93b5d8;

  --md-default-bg-color: var(--book-paper);
  --md-default-fg-color: var(--book-ink);
  --md-default-fg-color--light: var(--book-ink-soft);
  --md-default-fg-color--lighter: #6f6a64;
  --md-default-fg-color--lightest: var(--book-line);
  --md-primary-fg-color: var(--book-paper);
  --md-primary-fg-color--light: var(--book-paper);
  --md-primary-fg-color--dark: var(--book-paper);
  --md-primary-bg-color: var(--book-ink);
  --md-accent-fg-color: var(--book-accent);
  --md-typeset-color: var(--book-ink);
  --md-typeset-a-color: var(--book-accent);
  --md-code-bg-color: var(--book-paper-soft);
  --md-footer-bg-color: var(--book-paper);
  --md-footer-bg-color--dark: var(--book-paper);
  --md-footer-fg-color: var(--book-ink-soft);
  --md-footer-fg-color--light: var(--book-ink-soft);
  --md-footer-fg-color--lighter: #6f6a64;
}

/* ---------- 2. 正文：标题黑体、正文宋体 ---------- */

.md-typeset {
  font-family: var(--book-serif);
  font-size: 0.88rem;
  line-height: 1.95;
  letter-spacing: 0.012em;
  text-align: justify;
  text-justify: inter-ideograph;
  hyphens: none;
}

.md-typeset p {
  margin: 0 0 1.05em;
}

.md-typeset h1,
.md-typeset h2,
.md-typeset h3,
.md-typeset h4 {
  font-family: var(--book-sans);
  font-weight: 600;
  letter-spacing: 0.03em;
}

.md-typeset h1 {
  font-size: 1.7rem;
  margin: 0 0 1.8rem;
  padding: 0;
  border: none;
  color: var(--book-ink);
}

.md-typeset h2 {
  font-size: 1.05rem;
  border: none;
  padding: 0;
}

.md-typeset strong {
  color: var(--book-ink);
  font-weight: 700;
}

/* ---------- 3. 版心：每行约 38 字，整块居中 ---------- */

.md-content__inner {
  max-width: 34rem;
  margin-inline: auto;
  padding-bottom: 2.4rem;
}

/* 每一章都是平铺的正文、没有小标题，右侧"本页目录"是空的。
   收掉它，正文才能真正落在版心正中。 */
@media screen and (min-width: 76.25em) {
  .md-sidebar--secondary {
    display: none;
  }

/* ---------- 4. 页头：不要大色块，只留一条发丝线 ---------- */

.md-header,
.md-header--shadow {
  background-color: var(--book-paper);
  color: var(--book-ink);
  box-shadow: none;
  border-bottom: 1px solid var(--book-line);
}

.md-header__title {
  font-family: var(--book-sans);
  font-weight: 600;
  letter-spacing: 0.06em;
}

/* ---------- 5. 底栏：固定在窗口底部，做得安静 ---------- */

.md-footer {
  position: sticky;
  bottom: 0;
  z-index: 3;
  background-color: var(--book-paper);
  border-top: 1px solid var(--book-line);
}

.md-footer-meta {
  background-color: transparent;
}

.md-copyright {
  font-size: 0.6rem;
  letter-spacing: 0.1em;
  opacity: 0.75;
}

/* 固定栏会占住视口底部，给左侧目录减掉这段高度，
   否则目录滚到底时最后几项会被盖住点不到 */
@media screen and (min-width: 76.25em) {
  .md-sidebar__scrollwrap {
    max-height: calc(100vh - 7rem);
  }
}

/* ---------- 6. 侧栏与导航 ---------- */

.md-nav {
  font-family: var(--book-sans);
}

/* 站名已经在页头了，侧栏顶部不必再重复一遍 */
@media screen and (min-width: 76.25em) {
  .md-nav--primary > .md-nav__title {
    display: none;
  }
}

.md-nav__link--active,
.md-nav__link--active:focus,
.md-nav__link--active:hover {
  color: var(--book-accent);
  font-weight: 600;
}

/* ---------- 7. 首页：扉页与目录 ---------- */

.md-typeset blockquote {
  border-left: 2px solid var(--book-line);
  color: var(--book-ink-soft);
  padding-left: 1.4em;
  margin: 1.4em 0;
}

.md-typeset blockquote p {
  margin: 0.35em 0;
}

.md-typeset .md-button {
  font-family: var(--book-sans);
  font-size: 0.72rem;
  letter-spacing: 0.1em;
  color: var(--book-ink);
  border: 1px solid var(--book-line);
  border-radius: 0.2rem;
  padding: 0.55em 1.4em;
}

.md-typeset .md-button:hover,
.md-typeset .md-button:focus {
  color: var(--book-accent);
  border-color: var(--book-accent);
  background-color: transparent;
}

.book-toc ol {
  columns: 2;
  column-gap: 2.6rem;
  padding-left: 1.3em;
  margin-top: 0.6em;
}

.book-toc li {
  break-inside: avoid;
  margin-bottom: 0.22em;
}

.book-toc a {
  text-decoration: none;
}

.book-toc a:hover {
  text-decoration: underline;
  text-underline-offset: 0.2em;
}

@media screen and (max-width: 44em) {
  .book-toc ol {
    columns: 1;
  }
}
"""
io.open(os.path.join(ASSETS, "extra.css"), "w", encoding="utf-8").write(EXTRA_CSS)

# ---------------------------------------------------------------------------
# 首页：扉页 + 目录
# ---------------------------------------------------------------------------
toc_lines = "\n".join(
    '%d. [%s](%s)' % (i, name, fn) for i, (fn, name) in enumerate(written, start=1)
)
n_chars = len(re.sub(r"\s", "", re.sub(r"[#*>`\[\]()\-]", "", body)))
index = """# %s

### %s

> 一部关于失败、误读与固执的历史：一条只能把东西分成两堆的线，是怎么长成会跟你说话的东西的。
>
> 全书 %d 节，正文约 %.1f 万字。

[下载 PDF 版](assets/neural-networks-story.pdf){ .md-button }

<div class="book-toc" markdown>

## 目录

%s

</div>
""" % (TITLE, SUB, len(written), n_chars / 10000.0, toc_lines)
io.open(os.path.join(DOCS, "index.md"), "w", encoding="utf-8").write(index)

# PDF 放一份到站点里，供下载
if os.path.exists(PDF):
    shutil.copyfile(PDF, os.path.join(ASSETS, "neural-networks-story.pdf"))
    pdf_note = "已复制 PDF"
else:
    pdf_note = "未找到 PDF，跳过"

print("标题:", TITLE, "/", SUB)
print("拆出章节: %d 节" % len(written))
print("正文字数(去空白):", n_chars)
print(pdf_note)
