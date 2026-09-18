# -*- coding: utf-8 -*-
"""手动发布在线版站点（在 qtc-llm-story 仓库里运行）。

用法：
    python build/publish.py            # 有确认提示
    python build/publish.py --dry-run  # 只构建本地站点，不推送
    python build/publish.py --yes      # 跳过确认

它做三件事：拆章 → 构建站点 → 推到 gh-pages 分支。
不会自动触发，只有你手动运行才会更新线上。
"""

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENV_PY = r"C:\Users\pc\.workbuddy\binaries\python\envs\default\Scripts\python.exe"
URL = "https://terie412.github.io/qtc-llm-story/"

argv = sys.argv[1:]
dry = "--dry-run" in argv
assume_yes = "--yes" in argv

mkdocs_python = VENV_PY if os.path.exists(VENV_PY) else sys.executable


def run(cmd, **kw):
    print("$", " ".join(cmd) if isinstance(cmd, list) else cmd)
    return subprocess.run(cmd, cwd=ROOT, **kw).returncode


if not dry and not assume_yes:
    ans = input("确认把当前内容发布到 %s 吗？[y/N] " % URL).strip().lower()
    if ans not in ("y", "yes"):
        print("已取消。")
        raise SystemExit(0)

if run([sys.executable, os.path.join(ROOT, "build", "md2web.py")]) != 0:
    raise SystemExit("拆章失败")
if run([mkdocs_python, "-m", "mkdocs", "build", "--strict"]) != 0:
    raise SystemExit("构建失败")

if dry:
    print("\n[dry-run] 站点已构建到 site/，未推送。")
    raise SystemExit(0)

if run([mkdocs_python, "-m", "mkdocs", "gh-deploy", "--force"]) != 0:
    raise SystemExit("推送失败")

print("\n已发布： %s" % URL)
print("GitHub 通常要几十秒才会刷新，国内访问可能更慢。")
