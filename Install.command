#!/bin/bash
cd -- "$(dirname -- "$0")" || exit 1
if command -v python3 >/dev/null 2>&1; then
  python3 install.py "$@"
  result=$?
else
  echo "请先安装 Python 3.9 或更新版本：https://www.python.org/downloads/"
  result=2
fi
read -r -p "按回车关闭窗口…" _linxsci_done
exit "$result"
