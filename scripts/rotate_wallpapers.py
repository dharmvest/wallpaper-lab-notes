# -*- coding: utf-8 -*-
"""
AutoWall 指定壁纸轮换（便携版）
用法:
  python rotate_wallpapers.py --set "6,9"    配置轮换名单（编号对应 --list 序号）
  python rotate_wallpapers.py --once         切到名单中的下一张
  python rotate_wallpapers.py --show / --stop
调度建议:
  系统定时任务最小间隔 1 小时；30 分钟级轮换用 Windows 计划任务:
  Register-ScheduledTask -Trigger (New-ScheduledTaskTrigger -Once -At <now+2min> `
    -RepetitionInterval (New-TimeSpan -Minutes 30)) -Action <python rotate_wallpapers.py --once>
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import switch_wallpaper as sw  # noqa: E402

CFG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rotate_config.json")
ST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rotate_state.json")


def load_cfg():
    if not os.path.isfile(CFG):
        return None
    with open(CFG, "r", encoding="utf-8") as f:
        return json.load(f)


def load_st():
    if not os.path.isfile(ST):
        return {"idx": 0}
    with open(ST, "r", encoding="utf-8") as f:
        return json.load(f)


def save_st(idx):
    with open(ST, "w", encoding="utf-8") as f:
        json.dump({"idx": idx}, f, ensure_ascii=False)


def id_to_name(items, num):
    return items[num - 1] if 1 <= num <= len(items) else None


def do_set(ids_text):
    ids = [int(x.strip()) for x in ids_text.split(",") if x.strip().isdigit()]
    if not ids:
        sys.exit("无效编号列表: %s" % ids_text)
    items = sw.list_wallpapers()
    for n in ids:
        if not id_to_name(items, n):
            sys.exit("编号 %d 超出范围（共 %d 张）" % (n, len(items)))
    with open(CFG, "w", encoding="utf-8") as f:
        json.dump({"ids": ids}, f, ensure_ascii=False)
    cur = sw.current_name()
    pos = next((i for i, n in enumerate(ids)
                if cur and os.path.normcase(id_to_name(items, n)) == os.path.normcase(cur)), None)
    save_st((pos + 1) % len(ids) if pos is not None else 0)
    print("轮换配置已保存: ids=%s 当前=%s" % (ids, cur or "未知"))


def do_once():
    cfg = load_cfg()
    if not cfg or not cfg.get("ids"):
        sys.exit('未配置轮换名单，请先 --set "6,9"')
    ids = cfg["ids"]
    items = sw.list_wallpapers()
    st = load_st()
    i = st.get("idx", 0) % len(ids)
    name = id_to_name(items, ids[i])
    if not name:
        sys.exit("编号 %d 超出范围" % ids[i])
    print("轮换到: %s" % name)
    if sw.apply(name):
        save_st((i + 1) % len(ids))
        print("下次将切到编号 %d" % ids[(i + 1) % len(ids)])
    else:
        sys.exit("切换失败，状态未推进")


def do_show():
    cfg = load_cfg()
    st = load_st()
    items = sw.list_wallpapers()
    if not cfg or not cfg.get("ids"):
        print("未配置轮换。用法: --set \"6,9\"")
        return
    ids = cfg["ids"]
    names = [id_to_name(items, n) for n in ids]
    i = st.get("idx", 0) % len(ids)
    print("轮换名单: %s" % ", ".join("#%d %s" % (n, nm) for n, nm in zip(ids, names)))
    print("下一次: #%d %s" % (ids[i], names[i]))


def do_stop():
    for p in (CFG, ST):
        if os.path.isfile(p):
            os.remove(p)
    print("轮换已停止（配置已清除）")


def main():
    ap = argparse.ArgumentParser(description="AutoWall 指定壁纸轮换")
    ap.add_argument("--set", metavar="IDS", help='如 "6,9"')
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--stop", action="store_true")
    a = ap.parse_args()
    if a.set:
        do_set(a.set)
    elif a.once:
        do_once()
    elif a.show:
        do_show()
    elif a.stop:
        do_stop()
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
