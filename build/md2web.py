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


def split_chapter_title(name):
    """把「第十五章　高塔」拆成（章号, 章名）。

    章题分两级排版：章号小字疏排上朱砂，章名大字用墨色。
    拆不开的（没有全角空格）就整条当章名。
    """
    parts = name.split("\u3000", 1)
    if len(parts) == 2 and parts[0].strip() and parts[1].strip():
        return parts[0].strip(), parts[1].strip()
    return "", name.strip()


def first_para_dropcap(text):
    """判断开篇首段该用哪一档首字下沉。

    正文一行约 38 字，下沉字占掉一个字宽，要放下两行至少得 40 字，
    留点余量取 45。够不着的降级成一行的抬字 —— 否则浮空盒比整段还高，
    会顶到下一段，第一行莫名其妙缩进一个字。

    段尾补一行 attr_list 语法（{: .dropcap-2 }），由 attr_list 扩展
    给这个 <p> 挂上 class。
    """
    head = re.split(r"\n\s*\n", text.strip(), maxsplit=1)[0]
    plain = re.sub(r"[*`_\[\]<>]", "", head)
    return "dropcap-2" if len(plain) >= 45 else "dropcap-1"


def with_dropcap(text):
    """把首段标上首字下沉的 class，其余原样返回。"""
    parts = re.split(r"(\n\s*\n)", text.strip(), maxsplit=1)
    head = parts[0].strip()
    rest = "".join(parts[1:])
    return "%s\n{: .%s }%s" % (head, first_para_dropcap(text), rest)


# 逐章写文件。h1 用内联 HTML 拆成"章号 + 章名"两级，交给 CSS 分别上色；
# 同时写 front matter 的 title —— h1 里带了标签之后，MkDocs 自己提的标题
# 会把标签一起带进 <title>，这里显式给一个干净的。
written = []
for idx, (name, text) in enumerate(sections, start=1):
    fn = "%02d.md" % idx
    no, chap = split_chapter_title(name)
    if no:
        h1 = '# <span class="chap-no">%s</span><span class="chap-name">%s</span>' % (
            no,
            chap,
        )
    else:
        h1 = '# <span class="chap-name">%s</span>' % chap
    io.open(os.path.join(DOCS, fn), "w", encoding="utf-8").write(
        "---\ntitle: %s\n---\n\n%s\n\n%s\n"
        % (name.replace("\u3000", " "), h1, with_dropcap(text))
    )
    written.append((fn, name))


# ---------------------------------------------------------------------------
# 站点样式：纸与墨、四档墨色的明暗阶梯（正文最实，目录最虚）、
# 章题两级排版（章号朱砂 + 章名墨色）、标题黑体正文宋体、每行约 38 字、
# 左侧目录收窄贴边、底栏固定在窗口底部
# ---------------------------------------------------------------------------
EXTRA_CSS = """/* ==========================================================================
   站点外观：往"书"的方向调，不改变任何结构。
   明暗关系自上而下递减：正文 > 标题 > 页头页脚 > 左侧目录。
   正文拿最实的一档墨色，其余全部往背景里退，眼睛自然落在文字上。
   没有哪一档是纯黑或纯白。
   由 build/md2web.py 生成，要改样式请改那个脚本里的 EXTRA_CSS。
   ========================================================================== */

/* ---------- 1. 配色：纸与墨 ----------
   Material 把配色变量声明在 :root / [data-md-color-scheme] 上，
   这里用 body[data-md-color-scheme=...] 提高一级特异性来覆盖。
   四档墨色，由实到虚：book-ink（正文）→ book-ink-title（标题）
   → book-ink-soft（页头页脚）→ book-nav-ink（左侧目录）。 */

body {
  --book-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
    "Microsoft YaHei", "Hiragino Sans GB", sans-serif;
  --book-serif: Georgia, "Songti SC", "Source Han Serif SC",
    "Noto Serif CJK SC", "SimSun", serif;

  /* 左侧目录的栏宽，以及页头页脚占掉的高度（页脚实测约 3.6rem） */
  --book-nav-w: 10rem;
  --book-header-h: 2.4rem;
  --book-footer-h: 3.6rem;
}

body[data-md-color-scheme="default"] {
  --book-paper: #faf8f4;      /* 纸：回到中性，不带色相 */
  --book-paper-soft: #f2eee7;
  --book-ink: #33302b;        /* 正文：中性墨，不是纯黑 */
  --book-title-ink: #262320;  /* 首页站名：比正文深一档 */
  --book-ink-title: #4f4943;  /* 次级标题 */
  --book-ink-soft: #6c655e;   /* 页头页脚 */
  --book-nav-ink: #857e74;    /* 左侧目录：最淡 */
  --book-ink-faint: #a9a29a;
  --book-line: #e5e0d7;
  --book-accent: #a8442c;     /* 朱砂：全站唯一的彩色，只给章题和链接 */

  --md-default-bg-color: var(--book-paper);
  --md-default-fg-color: var(--book-ink);
  --md-default-fg-color--light: var(--book-ink-soft);
  --md-default-fg-color--lighter: var(--book-ink-faint);
  --md-default-fg-color--lightest: var(--book-line);
  --md-primary-fg-color: var(--book-paper);
  --md-primary-fg-color--light: var(--book-paper);
  --md-primary-fg-color--dark: var(--book-paper);
  --md-primary-bg-color: var(--book-ink-title);
  --md-accent-fg-color: var(--book-accent);
  --md-typeset-color: var(--book-ink);
  --md-typeset-a-color: var(--book-accent);
  --md-code-bg-color: var(--book-paper-soft);
  --md-footer-bg-color: var(--book-paper);
  --md-footer-bg-color--dark: var(--book-paper);
  --md-footer-fg-color: var(--book-ink-soft);
  --md-footer-fg-color--light: var(--book-ink-soft);
  --md-footer-fg-color--lighter: var(--book-ink-faint);
}

body[data-md-color-scheme="slate"] {
  --book-paper: #17191c;      /* 纸：回到中性 */
  --book-paper-soft: #1f2227;
  --book-ink: #d2cec7;        /* 正文：中性墨，不是纯白 */
  --book-title-ink: #e4e1da;  /* 首页站名：比正文亮一档 */
  --book-ink-title: #b3ada4;
  --book-ink-soft: #918b83;
  --book-nav-ink: #7e7871;
  --book-ink-faint: #6f6a64;
  --book-line: #2b2f35;
  --book-accent: #d4866b;     /* 朱砂在暗底上的对应值 */

  --md-default-bg-color: var(--book-paper);
  --md-default-fg-color: var(--book-ink);
  --md-default-fg-color--light: var(--book-ink-soft);
  --md-default-fg-color--lighter: var(--book-ink-faint);
  --md-default-fg-color--lightest: var(--book-line);
  --md-primary-fg-color: var(--book-paper);
  --md-primary-fg-color--light: var(--book-paper);
  --md-primary-fg-color--dark: var(--book-paper);
  --md-primary-bg-color: var(--book-ink-title);
  --md-accent-fg-color: var(--book-accent);
  --md-typeset-color: var(--book-ink);
  --md-typeset-a-color: var(--book-accent);
  --md-code-bg-color: var(--book-paper-soft);
  --md-footer-bg-color: var(--book-paper);
  --md-footer-bg-color--dark: var(--book-paper);
  --md-footer-fg-color: var(--book-ink-soft);
  --md-footer-fg-color--light: var(--book-ink-soft);
  --md-footer-fg-color--lighter: var(--book-ink-faint);
}

/* Material 的 indigo 深色预设把 --md-typeset-a-color 写死在
   [data-md-color-scheme][data-md-color-primary] 两级属性选择器里，
   比上面 body[data-md-color-scheme=...] 那一层高一级，会把正文链接和
   当前章节的蓝色抢成 #5488e8。这里用同级的写法把它拉回我们自己的强调色。 */
body[data-md-color-scheme][data-md-color-primary] {
  --md-typeset-a-color: var(--book-accent);
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
  margin: 0 0 2rem;
  padding: 0;
  border: none;
  color: var(--book-title-ink);
}

/* 章题分两级：章号小字疏排、后面拖一条通栏引线；章名大字、上朱砂。
   标题是全页唯一带色的字，翻页时一眼认得出"新的一章从这里起"。
   章号由 build/md2web.py 的 split_chapter_title() 拆出来。 */
.md-typeset h1 .chap-no {
  display: flex;
  align-items: center;
  font-size: 0.6rem;
  font-weight: 500;
  letter-spacing: 0.4em;
  color: var(--book-accent);
  margin-bottom: 0.55rem;
}

/* 序号引线：从章号一直拖到版心右缘，把标题压成一块"章节起首" */
.md-typeset h1 .chap-no::after {
  content: "";
  flex: 1 1 auto;
  height: 1px;
  margin-left: 0.8rem;
  background-color: var(--book-line);
}

.md-typeset h1 .chap-name {
  color: var(--book-accent);
}

/* 首页那个是站名不是章题，保持墨色，下面补一道朱砂短横当题花 */
.md-typeset h1 .book-title::after {
  content: "";
  display: block;
  width: 2rem;
  height: 2px;
  margin-top: 1.15rem;
  background-color: var(--book-accent);
}

/* 首字下沉。分两档，class 由 build/md2web.py 的 with_dropcap() 按
   首段够不够两行挂上，改版心宽度或字号得回头看那个阈值。

   两行档：字号是算出来的，不是试出来的。正文 0.88rem / 行高 1.95，
   两行 = 2 × 1.95em；下沉字用 line-height:1，字号就得等于 3.9em，
   浮空盒正好压住两行，第三行才回左边。 */
.md-typeset h1 + p.dropcap-2::first-letter {
  float: left;
  font-family: var(--book-serif);
  font-size: 3.9em;
  line-height: 1;
  margin: -0.08em 0.1em 0 0;
  color: var(--book-accent);
}

/* 一行档：开篇是短句时用。字号压在行高以内，不越界顶到下一段 */
.md-typeset h1 + p.dropcap-1::first-letter {
  float: left;
  font-family: var(--book-serif);
  font-size: 1.85em;
  line-height: 1;
  margin: 0.12em 0.06em 0 0;
  color: var(--book-accent);
}

.md-typeset h2 {
  font-size: 1.05rem;
  border: none;
  padding: 0;
  color: var(--book-ink-title);
}

/* 二级标题前面一小道朱砂横，跟章题的引线同一个记号 */
.md-typeset h2::before {
  content: "";
  display: inline-block;
  width: 1.1rem;
  height: 2px;
  margin-right: 0.55rem;
  margin-bottom: 0.14rem;
  background-color: var(--book-accent);
  vertical-align: middle;
}

.md-typeset strong {
  color: var(--book-ink);
  font-weight: 700;
}

/* ---------- 3. 版心：每行约 38 字，整块居中 ---------- */

/* 网格铺满整屏：页头页脚贴边，左侧目录贴左，正文单独居中。
   目录脱离文档流（见第 6 节）之后不再占列宽，
   正文的居中才不会被它推向一侧。 */
.md-grid {
  max-width: 100%;
}

.md-content__inner {
  /* 窄窗口下留出左右各 1rem 的呼吸，别贴着屏幕边 */
  max-width: min(34rem, 100% - 2rem);
  margin-inline: auto;
  padding-bottom: 2.4rem;
}

/* Material 给正文左右各塞了 1.2rem 的边距，选择器带 [dir] 和 :not()，
   特异性到 5 级，普通写法压不过它，正文会被钉在左侧。
   这里用同样长的选择器把那两条边距还原成 auto，版心才落在屏幕正中。 */
[dir="ltr"] .md-sidebar--primary:not([hidden]) ~ .md-content > .md-content__inner,
[dir="rtl"] .md-sidebar--primary:not([hidden]) ~ .md-content > .md-content__inner,
[dir="ltr"] .md-sidebar--secondary:not([hidden]) ~ .md-content > .md-content__inner,
[dir="rtl"] .md-sidebar--secondary:not([hidden]) ~ .md-content > .md-content__inner {
  margin-left: auto;
  margin-right: auto;
}

/* ---------- 4. 页头：不要大色块，只留一条发丝线 ---------- */

.md-header,
.md-header--shadow {
  background-color: var(--book-paper);
  color: var(--book-ink-title);
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

/* 目录栏的高度由第 6 节按页头页脚扣好，这里不再单独限高 */

/* ---------- 6. 左侧目录：收窄、贴住窗口左边缘、退到背景里 ---------- */

.md-nav {
  font-family: var(--book-sans);
}

/* 目录只是索引，不是读物：字形和行距都收一档，
   颜色压到最淡的一档，让视觉重量整体让给正文。 */
.md-nav--primary .md-nav__link {
  color: var(--book-nav-ink);
  font-size: 0.64rem;
  line-height: 1.45;
  margin-top: 0.28em;
  transition: color 125ms;
}

.md-nav--primary .md-nav__link:hover,
.md-nav--primary .md-nav__link:focus {
  color: var(--book-ink-title);
}

/* 当前章节。写法要带上 .md-nav--primary 才够特异性，
   否则会被上面的目录底色盖掉，也会被 Material indigo 调色板里的
   --md-accent-fg-color 抢走（那条规则是 [属性][属性] 两级）。 */
.md-nav--primary .md-nav__link--active,
.md-nav--primary .md-nav__link--active:focus,
.md-nav--primary .md-nav__link--active:hover {
  color: var(--book-accent);
  font-weight: 600;
}

@media screen and (min-width: 1220px) {
  /* 站名已经在页头了，侧栏顶部不必再重复一遍 */
  .md-nav--primary > .md-nav__title {
    display: none;
  }

  /* 目录固定在窗口最左侧的一条窄栏里。
     关键是 position:fixed —— 它一脱流，下面 .md-content 就吃掉整行宽度，
     版心才能真正落在屏幕正中，而不是被目录推得偏右。 */
  .md-sidebar--primary {
    position: fixed;
    top: var(--book-header-h);
    left: 0;
    width: var(--book-nav-w);
    /* 高度写明，不用 top+bottom 拉伸：abspos 的 flex 容器在 Chrome 里
       会退回按内容定高，底栏上方会空出一条。 */
    height: calc(100vh - var(--book-header-h) - var(--book-footer-h));
    z-index: 2;
    display: flex;
    flex-direction: column;
    padding: 1.4rem 0 0.4rem 1rem;
    overflow: hidden;
  }

  /* 在窄栏里自己滚，滚到最后一项也不会被底栏盖住 */
  .md-sidebar--primary .md-sidebar__scrollwrap {
    flex: 1 1 auto;
    min-height: 0;
    height: auto;
    max-height: none;
    margin: 0;
    padding-right: 0.5rem;
  }

  /* Material 靠 padding-right:calc(100% - 11.5rem) 把导航压到 11.5rem 宽，
     侧栏一变窄这条算式就失效了，直接归零让目录铺满栏宽。 */
  .md-sidebar--primary .md-sidebar__inner {
    padding: 0;
  }

  /* 目录脱流之后，正文列独占整行 */
  .md-main__inner {
    display: block;
  }
}

/* 每一章都是平铺的正文、没有小标题（章节拆分时就已经把 ## 切走了），
   右侧"本页目录"永远是空的，任何宽度下都收掉，别白占一列。
   坑：Material 用 .md-sidebar--secondary:not([hidden]) 显示右栏，特异性两级，
   所以这里必须写成 .md-sidebar.md-sidebar--secondary 才压得过它。 */
.md-sidebar.md-sidebar--secondary {
  display: none;
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

/* 目录条目里的章号也上朱砂，跟章题是同一种记号 */
.book-toc .toc-no {
  color: var(--book-accent);
  margin-right: 0.5em;
}

.book-toc a:hover {
  text-decoration: underline;
  text-underline-offset: 0.2em;
}

@media screen and (max-width: 704px) {
  .book-toc ol {
    columns: 1;
  }
}
"""
io.open(os.path.join(ASSETS, "extra.css"), "w", encoding="utf-8").write(EXTRA_CSS)

# ---------------------------------------------------------------------------
# 首页：扉页 + 目录
# ---------------------------------------------------------------------------
def toc_label(name):
    """首页目录里的条目：章号上朱砂，章名跟着走墨色。

    这里用行内 HTML，链接文字里的 <span> 会被 Markdown 原样保留。
    """
    no, chap = split_chapter_title(name)
    if no:
        return '<span class="toc-no">%s</span>%s' % (no, chap)
    return chap


toc_lines = "\n".join(
    "%d. [%s](%s)" % (i, toc_label(name), fn)
    for i, (fn, name) in enumerate(written, start=1)
)
n_chars = len(re.sub(r"\s", "", re.sub(r"[#*>`\[\]()\-]", "", body)))
index = """# <span class="book-title">%s</span>

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
