# -*- coding: utf-8 -*-
"""前端增强注入脚本（中性模板，幂等）。

用途：Open-LLM-VTuber 上游 clone 下来的 index.html 是纯净版，
     本脚本把仓库自带的 desktop/frontend_patch.html 注入到 </body> 之前，
     提供状态面板 / 心情气泡 / 问候气泡 / 一键诊断 / TTS 试听。

幂等性：
  - 已存在 <script id="ai-companion-patch"> 标记 → 跳过，不重复注入；
  - 首次注入前备份原文件为 index.html.bak（仅首次）。

用法：
  python inject_frontend.py [Open-LLM-VTuber根目录]
  （不传参数时自动取仓库根下的 Open-LLM-VTuber）
"""
import os
import shutil
import sys

MARK = 'id="ai-companion-patch"'


def main():
    if len(sys.argv) > 1:
        vt_root = os.path.abspath(sys.argv[1])
    else:
        vt_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Open-LLM-VTuber')
        vt_root = os.path.normpath(vt_root)

    index_html = os.path.join(vt_root, 'frontend', 'index.html')
    if not os.path.isfile(index_html):
        print("未找到前端文件，跳过注入:", index_html)
        return 0

    patch_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend_patch.html')
    with open(patch_file, 'r', encoding='utf-8') as f:
        patch = f.read().strip()

    with open(index_html, 'r', encoding='utf-8') as f:
        html = f.read()

    if MARK in html:
        print("前端增强已注入过，跳过。")
        return 0

    bak = index_html + '.bak'
    if not os.path.isfile(bak):
        shutil.copy2(index_html, bak)
        print("已备份原文件 ->", os.path.basename(bak))

    body_end = html.rfind('</body>')
    if body_end == -1:
        print("index.html 缺少 </body>，无法注入。")
        return 1

    new_html = html[:body_end] + patch + '\n' + html[body_end:]
    with open(index_html, 'w', encoding='utf-8') as f:
        f.write(new_html)

    print("前端增强注入成功:", os.path.basename(index_html))
    return 0


if __name__ == '__main__':
    sys.exit(main())
