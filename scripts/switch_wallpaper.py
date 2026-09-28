# -*- coding: utf-8 -*-
"""
AutoWall 壁纸快捷切换（便携版）
用法:
  python switch_wallpaper.py --list
  python switch_wallpaper.py --switch 6|星瞳
  python switch_wallpaper.py --random
  python switch_wallpaper.py --back
  python switch_wallpaper.py --now
路径配置（二选一）:
  1. 本文件顶部常量；2. 环境变量 WALLPAPER_VIDEOS / WALLPAPER_APPLY_PS1
"""
import argparse
import os
import random
import re
import subprocess
import sys

VIDEOS_HERE = os.environ.get(
    "WALLPAPER_VIDEOS", r"D:\Tools\AutoWall\AutoWall\VideosHere")
APPLY_PS1 = os.environ.get(
    "WALLPAPER_APPLY_PS1",
    r"C:\path\to\apply_wallpaper.ps1")  # TODO: 改为你的 apply_wallpaper.ps1 路径
HISTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".last_wallpaper")
EXTS = (".mp4", ".webm", ".mov", ".mkv", ".gif")


def list_wallpapers():
    if not os.path.isdir(VIDEOS_HERE):
        sys.exit("壁纸池不存在: %s" % VIDEOS_HERE)
    return sorted(f for f in os.listdir(VIDEOS_HERE) if f.lower().endswith(EXTS))


def pick(items, kw):
    if not items:
        return None
    low = kw.lower()
    matches = [f for f in items if low in f.lower()]
    if not matches:
        return None
    exact = [f for f in matches if f.lower() == low]
    return exact[0] if exact else matches[0]


def resolve(items, kw):
    """纯数字 -> --list 编号；否则文件名模糊匹配"""
    if kw.strip().isdigit():
        idx = int(kw.strip())
        if 1 <= idx <= len(items):
            return items[idx - 1]
        return None
    return pick(items, kw)


def apply(name):
    src = os.path.join(VIDEOS_HERE, name)
    if not os.path.isfile(src):
        sys.exit("文件不存在: %s" % src)
    cur = current_name()
    if cur and os.path.normcase(cur) != os.path.normcase(name):
        with open(HISTORY, "w", encoding="utf-8") as f:
            f.write(cur)
    # 源已在池内：不加 -Copy（避免自复制报错）
    cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
           "-File", APPLY_PS1, "-Video", src]
    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=180)
    out = (r.stdout or "") + (r.stderr or "")
    keep = [ln for ln in out.splitlines()
            if any(k in ln for k in ("playing", "hwdec", "memory", "CPU",
                                     "DONE", "ERROR", "default wallpaper"))]
    for ln in keep:
        print(ln)
    return "DONE" in out and "ERROR" not in out


def current_name():
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name='mpv.exe'\" | ForEach-Object { $_.CommandLine }"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
        for line in (r.stdout or "").splitlines():
            m = re.search(r"VideosHere[\\/]([^\"\s]+\.(?:mp4|webm|mov|mkv|gif))", line)
            if m:
                return m.group(1)
    except Exception:
        pass
    return None


def main():
    ap = argparse.ArgumentParser(description="AutoWall 壁纸快捷切换")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--switch", metavar="KW")
    ap.add_argument("--random", action="store_true")
    ap.add_argument("--now", action="store_true")
    ap.add_argument("--back", action="store_true")
    a = ap.parse_args()

    if a.list:
        items = list_wallpapers()
        if not items:
            sys.exit("壁纸池为空")
        for i, f in enumerate(items, 1):
            print("%2d. %s" % (i, f))
        return
    if a.now:
        cur = current_name()
        print("当前壁纸:", cur if cur else "（未检测到 mpv 播放）")
        return

    target = None
    if a.back:
        if os.path.isfile(HISTORY):
            with open(HISTORY, "r", encoding="utf-8") as f:
                target = f.read().strip()
        if not target:
            sys.exit("没有历史记录")
    elif a.switch:
        items = list_wallpapers()
        target = resolve(items, a.switch)
        if not target:
            if a.switch.strip().isdigit():
                sys.exit("编号 %s 超出范围（共 %d 张）。可用 --list 查看" % (a.switch, len(items)))
            sys.exit("没有匹配 '%s' 的壁纸。可用 --list 查看" % a.switch)
    elif a.random:
        items = list_wallpapers()
        if not items:
            sys.exit("壁纸池为空")
        target = random.choice(items)
    else:
        ap.print_help()
        return

    cur = current_name()
    if cur and os.path.normcase(cur) == os.path.normcase(target):
        print("当前已经是这张壁纸: %s" % target)
        return
    print("切换到: %s" % target)
    if not apply(target):
        sys.exit("切换失败，请检查 apply_wallpaper.ps1 输出")


if __name__ == "__main__":
    main()
