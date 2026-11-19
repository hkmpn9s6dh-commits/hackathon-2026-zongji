#!/usr/bin/env bash
# 《总机》一条命令从零到交付物 —— clone 里也照样能跑。
#
#   bash verify.sh            # 全流程：字体子集 → 图版 → 音轨 → 渲染 → 字幕 → 断言
#   bash verify.sh --quick    # 用已有成片只跑断言
#
# 依赖：python(含 numpy/Pillow)、ffmpeg/ffprobe、edge-tts、可访问网络（配音）
set -u
cd "$(dirname "$0")"

PY=python
command -v python >/dev/null 2>&1 || PY=py
if ! "$PY" -c "import numpy, PIL" >/dev/null 2>&1; then
  if py -3 -c "import numpy, PIL" >/dev/null 2>&1; then PY="py -3"; else
    echo "缺 numpy / Pillow"; exit 2
  fi
fi

rc=0
step() { printf '\n=== %s ===\n' "$1"; }

if [ "${1:-}" != "--quick" ]; then
  step "1/6 字体子集（随包带字体；只核对不生成时用 --check）"
  $PY scripts/subset_fonts.py || { echo "字体子集失败"; rc=1; }

  step "2/6 图版处理"
  $PY scripts/plates.py || { echo "图版失败"; rc=1; }

  step "3/6 音轨"
  $PY scripts/audio.py || { echo "音轨失败"; rc=1; }

  step "4/6 渲染 + 拼接 + 混流"
  $PY scripts/build_film.py --skip-plates --skip-audio --jobs 4 || { echo "渲染失败"; rc=1; }
fi

step "5/6 字幕"
$PY scripts/make_srt.py || rc=1

step "6/6 断言"
$PY scripts/verify.py || rc=1

echo
if [ $rc -eq 0 ]; then echo "全部通过"; else echo "有失败项"; fi
exit $rc
