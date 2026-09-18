# 神经网络史话

### 从感知机到 ChatGPT

1957 年，康奈尔大学的实验室里，一个心理学家造出了一台只会做一件事的机器：在一张纸上划一条线，把东西分成两堆。

七十年后，那个替我们写文案、翻外语、看照片、写代码、陪人闲扯的东西，顺着血统往上数，祖宗就是它。

这本书讲的就是这条线怎么长成了后来那副模样——它被宣判过两次死刑，被扔进过垃圾桶，被主流学界冷落了将近三十年；然后它赢了，而且不是靠哪一个天才灵光一闪赢的。

**在线阅读：<https://terie412.github.io/qtc-llm-story/>**

全书 33 节，正文约 2.8 万字。

## 文件

- `神经网络史话.md` —— 正文源码
- `神经网络史话.pdf` —— 排版后的 PDF
- `mkdocs.yml` + `build/` —— 生成在线版与 PDF 的脚本

## 本地构建

```bash
python build/md2web.py          # 把正文拆成 33 章，生成 docs/
python build/md2pdf.py          # 生成 HTML 与 PDF（需要 Chrome 或 Edge）
python build/publish.py         # 构建并发布站点到 gh-pages
```

`docs/` 和 `site/` 都是生成物，不入库。

## 许可

MIT
