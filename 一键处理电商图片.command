#!/bin/zsh
cd "$(dirname "$0")"
/Users/curt/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 process_ecommerce_images.py
echo ""
echo "处理结束，可以关闭这个窗口。"
read -k 1 -s "?按任意键关闭..."
