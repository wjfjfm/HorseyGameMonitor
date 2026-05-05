# -*- coding: utf-8 -*-
"""
赛马数据分析软件
time1=1线/测试时间, time2=2线, time3=3线, time4=4线, fall_time=摔倒时间
"""

import csv
import os
import time
import zipfile
from datetime import datetime
from tkinter import ttk, messagebox, filedialog
import tkinter as tk

HORSES_FILE = "horses.csv"
RECORDS_FILE = "records.csv"


def init_csv():
    if not os.path.exists(HORSES_FILE):
        with open(HORSES_FILE, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "name", "father_id", "mother_id", "added_date", "hidden"])
    if not os.path.exists(RECORDS_FILE):
        with open(RECORDS_FILE, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow([
                "record_id", "horse_id", "horse_name", "date", "mode",
                "time1", "time2", "time3", "time4", "fall_time", "rank"
            ])


def read_horses():
    horses = []
    if not os.path.exists(HORSES_FILE):
        return horses
    with open(HORSES_FILE, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            horses.append(row)
    return horses


def add_horse(name, father_id="", mother_id=""):
    horses = read_horses()
    new_id = 1
    if horses:
        new_id = max(int(h["id"]) for h in horses) + 1
    with open(HORSES_FILE, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([new_id, name, father_id, mother_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "0"])
    return new_id


def edit_horse(horse_id, name, father_id="", mother_id=""):
    horses = read_horses()
    for h in horses:
        if h["id"] == str(horse_id):
            h["name"] = name
            h["father_id"] = father_id
            h["mother_id"] = mother_id
            break
    with open(HORSES_FILE, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "father_id", "mother_id", "added_date", "hidden"])
        for h in horses:
            writer.writerow([h["id"], h["name"], h.get("father_id", ""), h.get("mother_id", ""), h["added_date"], h.get("hidden", "0")])


def read_records():
    records = []
    if not os.path.exists(RECORDS_FILE):
        return records
    with open(RECORDS_FILE, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    return records


def get_horse_records(horse_id):
    return [r for r in read_records() if r["horse_id"] == str(horse_id)]


def toggle_hidden(horse_id):
    horses = read_horses()
    for h in horses:
        if h["id"] == str(horse_id):
            h["hidden"] = "0" if h.get("hidden", "0") == "1" else "1"
            break
    with open(HORSES_FILE, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "father_id", "mother_id", "added_date", "hidden"])
        for h in horses:
            writer.writerow([h["id"], h["name"], h.get("father_id", ""), h.get("mother_id", ""), h["added_date"], h.get("hidden", "0")])


def add_record(horse_id, horse_name, mode, time1, time2, time3,
               time4, fall_time, rank=""):
    records = read_records()
    new_id = 1
    if records:
        new_id = max(int(r["record_id"]) for r in records) + 1
    with open(RECORDS_FILE, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            new_id, horse_id, horse_name,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"), mode,
            time1, time2, time3, time4, fall_time,
            rank
        ])


def _avg(values):
    if not values:
        return "-"
    return f"{sum(values)/len(values):.2f}"


def _pf(s):
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def calc_stats(horse_id):
    all_recs = get_horse_records(horse_id)
    test_recs = [r for r in all_recs if r.get("mode", "") == "test"]
    race_recs = [r for r in all_recs if r.get("mode", "") == "race"]
    race_recs += [r for r in all_recs if r.get("mode", "") == ""]

    # 测试赛：time1 平均值
    test_completed = [r for r in test_recs if r.get("time1", "") != ""]
    tt = [_pf(r.get("time1", "")) for r in test_completed]
    tt = [v for v in tt if v is not None]
    test_avg = _avg(tt)
    test_count = len(tt)

    total = len(race_recs)
    if total == 0:
        return {
            "test_avg": test_avg, "test_count": test_count,
            "t1_avg": "-", "t1_count": 0,
            "t2_avg": "-", "t2_count": 0,
            "t3_avg": "-", "t3_count": 0,
            "t4_avg": "-", "t4_count": 0,
            "wins": 0, "total": 0, "win_rate": "-",
            "falls": 0, "avg_fall_time": "-", "fall_count": 0,
            "avg_rank": "-", "rank_count": 0
        }

    fell_recs = [r for r in race_recs if r.get("fall_time", "") != ""]

    t1_vals = [v for v in [_pf(r["time1"]) for r in race_recs] if v is not None]
    t1_avg = _avg(t1_vals)
    t1_count = len(t1_vals)

    t2_vals = [v for v in [_pf(r["time2"]) for r in race_recs] if v is not None]
    t2_avg = _avg(t2_vals)
    t2_count = len(t2_vals)

    t3_vals = [_pf(r["time3"]) for r in race_recs if r["time3"]]
    t3_vals = [v for v in t3_vals if v is not None]
    t3_avg = _avg(t3_vals)
    t3_count = len(t3_vals)

    t4_vals = [_pf(r["time4"]) for r in race_recs if r["time4"]]
    t4_vals = [v for v in t4_vals if v is not None]
    t4_avg = _avg(t4_vals)
    t4_count = len(t4_vals)

    wins = sum(1 for r in race_recs if r.get("rank", "") == "1")
    win_rate = f"{wins/total*100:.1f}%"
    falls = len(fell_recs)

    # 逐条确定最终时间，计算摔倒期望 = 总跑动时间 / 摔倒次数
    # 测试记录和正赛记录都纳入
    final_times = []
    fall_count = 0
    for r in all_recs:
        if r.get("fall_time", ""):
            t = _pf(r["fall_time"])
            if t is not None:
                final_times.append(t)
                fall_count += 1
        else:
            last_time = None
            for key in ["time4", "time3", "time2", "time1"]:
                v = _pf(r.get(key, ""))
                if v is not None:
                    last_time = v
                    break
            if last_time is not None:
                final_times.append(last_time)

    total_time = sum(final_times)
    if len(final_times) == 0:
        avg_fall = "-"
    else:
        avg_fall = f"{total_time / (fall_count + 0.5):.2f}"

    ranks = [_pf(r.get("rank", "")) for r in race_recs if r.get("rank", "")]
    avg_rank = _avg(ranks)
    rank_count = len(ranks)

    return {
        "test_avg": test_avg, "test_count": test_count,
        "t1_avg": t1_avg, "t1_count": t1_count,
        "t2_avg": t2_avg, "t2_count": t2_count,
        "t3_avg": t3_avg, "t3_count": t3_count,
        "t4_avg": t4_avg, "t4_count": t4_count,
        "wins": wins, "total": total, "win_rate": win_rate,
        "falls": falls, "avg_fall_time": avg_fall, "fall_count": fall_count,
        "avg_rank": avg_rank, "rank_count": rank_count
    }


class TimerWidget(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.elapsed = 0.0
        self.running = False
        self.start_timestamp = 0

        self.lbl_time = ttk.Label(self, text="0.00", font=("Courier New", 30, "bold"))
        self.lbl_time.pack(pady=8)

        btn = ttk.Frame(self)
        btn.pack(pady=5)

        self.btn_toggle = ttk.Button(btn, text="开始", command=self.toggle, width=8)
        self.btn_toggle.pack(side="left", padx=4)

        ttk.Button(btn, text="归零", command=self.reset, width=8).pack(side="left", padx=4)

        self.btn_edit = ttk.Button(btn, text="编辑时间", command=self._edit_dialog, width=10, state="normal")
        self.btn_edit.pack(side="left", padx=4)

    def toggle(self):
        self.start() if not self.running else self.pause()

    def start(self):
        if not self.running:
            self.running = True
            self.start_timestamp = time.time() - self.elapsed
            self.btn_toggle.config(text="暂停")
            self.btn_edit.config(state="disabled")
            self._update()

    def pause(self):
        if self.running:
            self.running = False
            self.elapsed = time.time() - self.start_timestamp
            self.btn_toggle.config(text="开始")
            self.btn_edit.config(state="normal")
            self.lbl_time.config(text=self._fmt(self.elapsed))

    def reset(self):
        self.running = False
        self.elapsed = 0.0
        self.start_timestamp = 0
        self.lbl_time.config(text=self._fmt(0))
        self.btn_toggle.config(text="开始")
        self.btn_edit.config(state="normal")

    def get_elapsed(self):
        if self.running:
            return time.time() - self.start_timestamp
        return self.elapsed

    def set_elapsed(self, seconds):
        self.elapsed = max(0.0, seconds)
        if self.running:
            self.start_timestamp = time.time() - self.elapsed
        self.lbl_time.config(text=self._fmt(self.elapsed))

    def is_running(self):
        return self.running

    def _update(self):
        if not self.running:
            return
        self.lbl_time.config(text=self._fmt(self.get_elapsed()))
        self.after(50, self._update)

    def _fmt(self, sec):
        return f"{sec:.2f}"

    def _edit_dialog(self):
        top = tk.Toplevel(self)
        top.title("编辑时间")
        top.resizable(False, False)
        top.transient(self.winfo_toplevel())
        top.grab_set()

        ttk.Label(top, text="输入时间（秒）:").pack(pady=10, padx=20)
        ent = ttk.Entry(top, width=15)
        ent.pack(pady=5, padx=20)
        ent.insert(0, f"{self.get_elapsed():.3f}")
        ent.select_range(0, "end")
        ent.focus()

        def save():
            try:
                self.set_elapsed(float(ent.get()))
                top.destroy()
            except ValueError:
                messagebox.showwarning("格式错误", "请输入数字", parent=top)

        b = ttk.Frame(top)
        b.pack(pady=10)
        ttk.Button(b, text="确定", command=save).pack(side="left", padx=5)
        ttk.Button(b, text="取消", command=top.destroy).pack(side="left", padx=5)

        top.update_idletasks()
        w, h = top.winfo_width(), top.winfo_height()
        px, py = self.winfo_toplevel().winfo_x(), self.winfo_toplevel().winfo_y()
        pw, ph = self.winfo_toplevel().winfo_width(), self.winfo_toplevel().winfo_height()
        top.geometry(f"{w}x{h}+{px + (pw - w) // 2}+{py + (ph - h) // 2}")


class TimerWindow:
    def __init__(self, parent, mode, on_save, default_horse=None):
        self.mode = mode
        self.on_save = on_save
        self.parent = parent
        self.win = tk.Toplevel(parent)
        self.win.title("测试计时" if mode == "test" else "正赛计时")
        self.win.resizable(False, False)
        self.win.transient(parent)
        self.win.grab_set()
        w, h = (420, 460) if mode == "test" else (620, 620)
        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - w) // 2
        y = parent.winfo_y() + (parent.winfo_height() - h) // 2
        self.win.geometry(f"{w}x{h}+{x}+{y}")

        sel = ttk.Frame(self.win)
        sel.pack(fill="x", pady=10, padx=15)
        ttk.Label(sel, text="选择马:").pack(side="left", padx=(0, 5))
        self.horse_var = tk.StringVar()
        self.combo = ttk.Combobox(sel, textvariable=self.horse_var, state="readonly", width=25)
        self.combo.pack(side="left")
        self._refresh_combo()
        if default_horse:
            self.horse_var.set(default_horse)

        self.timer = TimerWidget(self.win)
        self.timer.pack(pady=5)

        btn = ttk.Frame(self.win)
        btn.pack(fill="x", pady=5, padx=10)

        if mode == "test":
            ttk.Button(btn, text="记录测试", command=self._record_test_time, width=12).pack(side="left", padx=4)
            ttk.Button(btn, text="记录摔倒", command=self._record_fall, width=12).pack(side="left", padx=4)
        else:
            ttk.Button(btn, text="记录1线", command=lambda: self._fill("time1"), width=10).pack(side="left", padx=4)
            ttk.Button(btn, text="记录2线", command=lambda: self._fill("time2"), width=10).pack(side="left", padx=4)
            ttk.Button(btn, text="记录3线", command=self._record_line3, width=10).pack(side="left", padx=4)
            ttk.Button(btn, text="记录4线", command=self._record_line4, width=10).pack(side="left", padx=4)
            ttk.Button(btn, text="记录摔倒", command=self._record_fall, width=10).pack(side="left", padx=4)

        edit = ttk.LabelFrame(self.win, text="数据编辑")
        edit.pack(fill="x", padx=15, pady=10, ipady=5)

        self.entries = {}
        if mode == "test":
            row = ttk.Frame(edit)
            row.pack(fill="x", pady=5, padx=10)
            ttk.Label(row, text="测试时间 (秒):").pack(side="left", padx=(0, 5))
            e = ttk.Entry(row, width=15)
            e.pack(side="left")
            self.entries["time1"] = e
            row = ttk.Frame(edit)
            row.pack(fill="x", pady=5, padx=10)
            ttk.Label(row, text="摔倒时间 (秒):").pack(side="left", padx=(0, 5))
            e = ttk.Entry(row, width=15)
            e.pack(side="left")
            self.entries["fall_time"] = e
        else:
            for key, lbl in [("time1", "1线 (秒):"), ("time2", "2线 (秒):"),
                             ("time3", "3线 (秒):"), ("time4", "4线 (秒):")]:
                row = ttk.Frame(edit)
                row.pack(fill="x", pady=3, padx=10)
                ttk.Label(row, text=lbl).pack(side="left", padx=(0, 5))
                e = ttk.Entry(row, width=15)
                e.pack(side="left")
                self.entries[key] = e
            row = ttk.Frame(edit)
            row.pack(fill="x", pady=3, padx=10)
            ttk.Label(row, text="摔倒时间 (秒):").pack(side="left", padx=(0, 5))
            e = ttk.Entry(row, width=15)
            e.pack(side="left")
            self.entries["fall_time"] = e

            rank_row = ttk.Frame(edit)
            rank_row.pack(fill="x", pady=5, padx=10)
            ttk.Label(rank_row, text="名次:").pack(side="left", padx=(0, 5))
            self.rank_var = tk.IntVar(value=0)
            for i in range(1, 6):
                ttk.Radiobutton(rank_row, text=str(i), variable=self.rank_var, value=i).pack(side="left", padx=4)

        act = ttk.Frame(self.win)
        act.pack(pady=10)
        ttk.Button(act, text="保存记录", command=self._save).pack(side="left", padx=10)
        ttk.Button(act, text="取消", command=self.win.destroy).pack(side="left", padx=10)

    def _refresh_combo(self):
        horses = read_horses()
        self.combo["values"] = [f"{h['id']} - {h['name']}" for h in horses]
        if horses:
            self.combo.current(0)

    def _fill(self, key):
        sec = self.timer.get_elapsed()
        ent = self.entries.get(key)
        if ent:
            ent.delete(0, "end")
            ent.insert(0, f"{sec:.3f}")

    def _record_test_time(self):
        self.timer.pause()
        sec = self.timer.get_elapsed()
        ent = self.entries.get("time1")
        if ent:
            ent.delete(0, "end")
            ent.insert(0, f"{sec:.3f}")

    def _record_line3(self):
        sec = self.timer.get_elapsed()
        ent = self.entries.get("time3")
        if ent:
            ent.delete(0, "end")
            ent.insert(0, f"{sec:.3f}")

    def _record_line4(self):
        sec = self.timer.get_elapsed()
        ent = self.entries.get("time4")
        if ent:
            ent.delete(0, "end")
            ent.insert(0, f"{sec:.3f}")

    def _record_fall(self):
        sec = self.timer.get_elapsed()
        ent_fall = self.entries.get("fall_time")
        if ent_fall:
            ent_fall.delete(0, "end")
            ent_fall.insert(0, f"{sec:.3f}")
        self.rank_var.set(2)

    def _save(self):
        hs = self.horse_var.get()
        if not hs:
            messagebox.showwarning("未选择马", "请先选择一匹马", parent=self.win)
            return
        hid = hs.split(" - ")[0]
        hname = hs.split(" - ", 1)[1]
        try:
            if self.mode == "test":
                v = self.entries["time1"].get().strip()
                test_time = f"{_pf(v):.3f}" if v else ""
                ent_fall = self.entries.get("fall_time")
                fv = ent_fall.get().strip() if ent_fall else ""
                fall_time = f"{_pf(fv):.3f}" if fv else ""
                add_record(hid, hname, "test", test_time, "", "", "", "", fall_time)
            else:
                vals = {}
                for k, e in self.entries.items():
                    v = e.get().strip()
                    vals[k] = f"{_pf(v):.3f}" if v else ""
                fall_v = vals.get("fall_time", "")
                time3_v = vals.get("time3", "")
                time4_v = vals.get("time4", "")
                rank = str(self.rank_var.get()) if self.rank_var.get() > 0 else ""
                add_record(hid, hname, "race",
                           vals.get("time1", ""), vals.get("time2", ""),
                           time3_v, time4_v, fall_v,
                           rank)
        except (ValueError, TypeError):
            messagebox.showwarning("格式错误", "时间必须是数字", parent=self.win)
            return
        self.win.destroy()
        if self.on_save:
            self.on_save()


from faker import Faker
_fake = Faker()


def _get_bloodline(selected_id, horses):
    """计算选中马与其他马的血缘关系。返回 {horse_id: (type, gen)}，
    type='ancestor' 或 'descendant'，gen=代数。仅保留最近关系。"""
    horse_map = {h["id"]: h for h in horses}
    sel = str(selected_id)

    # BFS 祖先
    ancestors = {}
    queue = [(sel, 0)]
    while queue:
        cur, gen = queue.pop(0)
        if cur not in horse_map:
            continue
        h = horse_map[cur]
        for pid in [h.get("father_id", ""), h.get("mother_id", "")]:
            if pid and pid not in ancestors:
                ancestors[pid] = gen + 1
                queue.append((pid, gen + 1))

    # BFS 后代
    children_map = {}
    for h in horses:
        for pid in [h.get("father_id", ""), h.get("mother_id", "")]:
            if pid:
                children_map.setdefault(pid, []).append(h["id"])

    descendants = {}
    queue = [(sel, 0)]
    while queue:
        cur, gen = queue.pop(0)
        for cid in children_map.get(cur, []):
            if cid not in descendants:
                descendants[cid] = gen + 1
                queue.append((cid, gen + 1))

    result = {}
    for hid, gen in ancestors.items():
        result[hid] = ("ancestor", gen)
    for hid, gen in descendants.items():
        if hid not in result or gen < result[hid][1]:
            result[hid] = ("descendant", gen)
    return result


class AddHorseWindow:
    def __init__(self, parent, on_save):
        self.on_save = on_save
        self.win = tk.Toplevel(parent)
        self.win.title("添加马")
        self.win.resizable(False, False)
        self.win.transient(parent)
        self.win.grab_set()
        w, h = 380, 240
        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - w) // 2
        y = parent.winfo_y() + (parent.winfo_height() - h) // 2
        self.win.geometry(f"{w}x{h}+{x}+{y}")

        frm = ttk.Frame(self.win)
        frm.pack(padx=20, pady=15, fill="x")

        ttk.Label(frm, text="马名称:").grid(row=0, column=0, sticky="e", padx=5, pady=8)
        self.entry_name = ttk.Entry(frm, width=18)
        self.entry_name.grid(row=0, column=1, padx=5, pady=8)
        ttk.Button(frm, text="随机", command=self._random_name, width=6).grid(row=0, column=2, padx=2, pady=8)
        ttk.Button(frm, text="复制", command=self._copy_name, width=6).grid(row=0, column=3, padx=2, pady=8)

        ttk.Label(frm, text="父亲:").grid(row=1, column=0, sticky="e", padx=5, pady=8)
        self.father_var = tk.StringVar()
        self.combo_father = ttk.Combobox(frm, textvariable=self.father_var, state="readonly", width=20)
        self.combo_father.grid(row=1, column=1, columnspan=3, padx=5, pady=8, sticky="w")

        ttk.Label(frm, text="母亲:").grid(row=2, column=0, sticky="e", padx=5, pady=8)
        self.mother_var = tk.StringVar()
        self.combo_mother = ttk.Combobox(frm, textvariable=self.mother_var, state="readonly", width=20)
        self.combo_mother.grid(row=2, column=1, columnspan=3, padx=5, pady=8, sticky="w")

        self._refresh_combos()

        btn = ttk.Frame(self.win)
        btn.pack(pady=15)
        ttk.Button(btn, text="添加", command=self._save).pack(side="left", padx=10)
        ttk.Button(btn, text="取消", command=self.win.destroy).pack(side="left", padx=10)

    def _random_name(self):
        existing = {h["name"] for h in read_horses()}
        name = _fake.first_name()
        attempts = 0
        while (name in existing or len(name) > 7) and attempts < 100:
            name = _fake.first_name()
            attempts += 1
        self.entry_name.delete(0, "end")
        self.entry_name.insert(0, name)

    def _copy_name(self):
        name = self.entry_name.get().strip()
        if name:
            self.win.clipboard_clear()
            self.win.clipboard_append(name)

    def _refresh_combos(self):
        self.parent_map = {"": ""}
        horses = [h for h in read_horses() if h.get("hidden", "0") != "1"]
        horses = sorted(horses, key=lambda h: int(h["id"]))
        vals = [""]
        for h in horses:
            display = f"{h['id']} - {h['name']}"
            vals.append(display)
            self.parent_map[display] = h["id"]
        self.combo_father["values"] = vals
        self.combo_mother["values"] = vals
        self.combo_father.current(0)
        self.combo_mother.current(0)

    def _save(self):
        name = self.entry_name.get().strip()
        if not name:
            messagebox.showwarning("输入不完整", "请填写马名称", parent=self.win)
            return
        father_id = self.parent_map.get(self.father_var.get(), "")
        mother_id = self.parent_map.get(self.mother_var.get(), "")
        add_horse(name, father_id, mother_id)
        self.win.destroy()
        if self.on_save:
            self.on_save()


class EditHorseWindow:
    def __init__(self, parent, horse_id, name, father_id, mother_id, on_save):
        self.on_save = on_save
        self.horse_id = horse_id
        self.win = tk.Toplevel(parent)
        self.win.title("编辑马")
        self.win.resizable(False, False)
        self.win.transient(parent)
        self.win.grab_set()
        w, h = 380, 240
        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - w) // 2
        y = parent.winfo_y() + (parent.winfo_height() - h) // 2
        self.win.geometry(f"{w}x{h}+{x}+{y}")

        frm = ttk.Frame(self.win)
        frm.pack(padx=20, pady=15, fill="x")

        ttk.Label(frm, text="马名称:").grid(row=0, column=0, sticky="e", padx=5, pady=8)
        self.entry_name = ttk.Entry(frm, width=18)
        self.entry_name.grid(row=0, column=1, padx=5, pady=8)
        self.entry_name.insert(0, name)
        ttk.Button(frm, text="随机", command=self._random_name, width=6).grid(row=0, column=2, padx=2, pady=8)
        ttk.Button(frm, text="复制", command=self._copy_name, width=6).grid(row=0, column=3, padx=2, pady=8)

        ttk.Label(frm, text="父亲:").grid(row=1, column=0, sticky="e", padx=5, pady=8)
        self.father_var = tk.StringVar()
        self.combo_father = ttk.Combobox(frm, textvariable=self.father_var, state="readonly", width=20)
        self.combo_father.grid(row=1, column=1, columnspan=3, padx=5, pady=8, sticky="w")

        ttk.Label(frm, text="母亲:").grid(row=2, column=0, sticky="e", padx=5, pady=8)
        self.mother_var = tk.StringVar()
        self.combo_mother = ttk.Combobox(frm, textvariable=self.mother_var, state="readonly", width=20)
        self.combo_mother.grid(row=2, column=1, columnspan=3, padx=5, pady=8, sticky="w")

        self._refresh_combos(father_id, mother_id)

        btn = ttk.Frame(self.win)
        btn.pack(pady=15)
        ttk.Button(btn, text="保存", command=self._save).pack(side="left", padx=10)
        ttk.Button(btn, text="取消", command=self.win.destroy).pack(side="left", padx=10)

    def _random_name(self):
        existing = {h["name"] for h in read_horses() if h["id"] != str(self.horse_id)}
        name = _fake.first_name()
        attempts = 0
        while (name in existing or len(name) > 7) and attempts < 100:
            name = _fake.first_name()
            attempts += 1
        self.entry_name.delete(0, "end")
        self.entry_name.insert(0, name)

    def _copy_name(self):
        name = self.entry_name.get().strip()
        if name:
            self.win.clipboard_clear()
            self.win.clipboard_append(name)

    def _refresh_combos(self, father_id="", mother_id=""):
        self.parent_map = {"": ""}
        horses = [h for h in read_horses() if h.get("hidden", "0") != "1" and h["id"] != str(self.horse_id)]
        horses = sorted(horses, key=lambda h: int(h["id"]))
        vals = [""]
        father_idx = 0
        mother_idx = 0
        for i, h in enumerate(horses, start=1):
            display = f"{h['id']} - {h['name']}"
            vals.append(display)
            self.parent_map[display] = h["id"]
            if h["id"] == str(father_id):
                father_idx = i
            if h["id"] == str(mother_id):
                mother_idx = i
        self.combo_father["values"] = vals
        self.combo_mother["values"] = vals
        self.combo_father.current(father_idx)
        self.combo_mother.current(mother_idx)

    def _save(self):
        name = self.entry_name.get().strip()
        if not name:
            messagebox.showwarning("输入不完整", "请填写马名称", parent=self.win)
            return
        father_id = self.parent_map.get(self.father_var.get(), "")
        mother_id = self.parent_map.get(self.mother_var.get(), "")
        edit_horse(self.horse_id, name, father_id, mother_id)
        self.win.destroy()
        if self.on_save:
            self.on_save()


class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("赛马数据分析")
        self.root.geometry("1100x700")
        self.root.minsize(900, 600)
        init_csv()
        self.selected_horse_id = None

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", font=("Microsoft YaHei", 10))
        style.configure("TLabel", font=("Microsoft YaHei", 10))
        style.configure("Treeview", font=("Microsoft YaHei", 9), rowheight=22)
        style.configure("Treeview.Heading", font=("Microsoft YaHei", 9, "bold"))

        top = ttk.Frame(root)
        top.pack(fill="x", padx=10, pady=8)
        ttk.Button(top, text="添加马", command=self._open_add_horse).pack(side="left", padx=(0, 10))
        self.btn_edit = ttk.Button(top, text="编辑马", command=self._edit_horse, state="disabled")
        self.btn_edit.pack(side="left", padx=(0, 10))
        self.btn_delete = ttk.Button(top, text="删除马", command=self._delete_horse, state="disabled")
        self.btn_delete.pack(side="left", padx=(0, 10))
        self.btn_test = ttk.Button(top, text="测试计时", command=lambda: self._open_timer("test"), state="disabled")
        self.btn_test.pack(side="left", padx=(0, 10))
        self.btn_race = ttk.Button(top, text="正赛计时", command=lambda: self._open_timer("race"), state="disabled")
        self.btn_race.pack(side="left", padx=(0, 10))
        ttk.Button(top, text="刷新数据", command=self._refresh_all).pack(side="left", padx=(0, 10))
        self.show_hidden_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(top, text="显示隐藏马", variable=self.show_hidden_var, command=self._refresh_table).pack(side="left", padx=(0, 10))
        self.bloodline_only_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(top, text="仅显示亲缘马", variable=self.bloodline_only_var, command=self._refresh_table).pack(side="left", padx=(0, 10))
        self.sort_state = {}

        # 数据操作下拉菜单
        menu_btn = tk.Menubutton(top, text="数据操作 ▼", relief="raised")
        menu_btn.pack(side="left", padx=(10, 0))
        menu = tk.Menu(menu_btn, tearoff=0)
        menu.add_command(label="数据导出", command=self._export_data)
        menu.add_command(label="数据导入", command=self._import_data)
        menu.add_separator()
        menu.add_command(label="清空数据", command=self._clear_all_data)
        menu_btn.config(menu=menu)

        paned = ttk.PanedWindow(root, orient="vertical")
        paned.pack(fill="both", expand=True, padx=10, pady=5)

        table_frame = ttk.LabelFrame(paned, text="马数据统计（点击行查看明细）")
        paned.add(table_frame, weight=1)

        cols = (
            "hidden", "id", "name", "father", "mother", "test_avg", "t1", "t2", "t3", "t4",
            "avg_fall_time", "avg_rank", "wins", "total", "win_rate", "falls"
        )
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        headings = {
            "id": "ID", "name": "名字", "father": "父亲", "mother": "母亲",
            "test_avg": "测试赛", "t1": "1线", "t2": "2线",
            "t3": "3线", "t4": "4线", "avg_fall_time": "摔倒期望", "avg_rank": "平均名次",
            "wins": "胜利数", "total": "参赛数", "win_rate": "胜率", "falls": "摔倒数",
            "hidden": "隐藏"
        }
        for col in cols:
            self.tree.heading(col, text=headings[col], command=lambda c=col: self._sort_by(c))
        self.tree.column("hidden", width=50, anchor="center")
        self.tree.column("id", width=40, anchor="center")
        self.tree.column("name", width=80, anchor="center")
        self.tree.column("father", width=80, anchor="center")
        self.tree.column("mother", width=80, anchor="center")
        self.tree.column("test_avg", width=110, anchor="center")
        self.tree.column("t1", width=80, anchor="center")
        self.tree.column("t2", width=80, anchor="center")
        self.tree.column("t3", width=80, anchor="center")
        self.tree.column("t4", width=80, anchor="center")
        self.tree.column("avg_fall_time", width=100, anchor="center")
        self.tree.column("avg_rank", width=80, anchor="center")
        self.tree.column("wins", width=55, anchor="center")
        self.tree.column("total", width=55, anchor="center")
        self.tree.column("win_rate", width=55, anchor="center")
        self.tree.column("falls", width=55, anchor="center")
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(xscrollcommand=hsb.set, yscrollcommand=vsb.set)
        hsb.pack(side="bottom", fill="x")
        vsb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<ButtonPress-1>", self._on_tree_click)

        # 血缘高亮颜色配置：蓝色系（祖先），粉色系（后代），越远越淡
        for gen, color in [(1, "#b3d9ff"), (2, "#ccebff"), (3, "#e0f0ff"), (4, "#f0f8ff")]:
            self.tree.tag_configure(f"anc{gen}", background=color)
        for gen, color in [(1, "#ffb3ba"), (2, "#ffd1d6"), (3, "#ffe8ea"), (4, "#fff0f2")]:
            self.tree.tag_configure(f"desc{gen}", background=color)
        self.tree.tag_configure("self_sel", background="#fff3cd")

        detail_frame = ttk.LabelFrame(paned, text="选中马记录明细")
        paned.add(detail_frame, weight=1)
        dcols = ("date", "mode", "t1", "t2", "t3", "t4", "fall_time", "rank")
        self.tree_detail = ttk.Treeview(detail_frame, columns=dcols, show="headings")
        self.tree_detail.heading("date", text="日期")
        self.tree_detail.heading("mode", text="类型")
        self.tree_detail.heading("t1", text="1线")
        self.tree_detail.heading("t2", text="2线")
        self.tree_detail.heading("t3", text="3线")
        self.tree_detail.heading("t4", text="4线")
        self.tree_detail.heading("fall_time", text="摔倒时间")
        self.tree_detail.heading("rank", text="名次")
        self.tree_detail.column("date", width=140, anchor="center")
        self.tree_detail.column("mode", width=55, anchor="center")
        self.tree_detail.column("t1", width=65, anchor="center")
        self.tree_detail.column("t2", width=65, anchor="center")
        self.tree_detail.column("t3", width=65, anchor="center")
        self.tree_detail.column("t4", width=65, anchor="center")
        self.tree_detail.column("fall_time", width=65, anchor="center")
        self.tree_detail.column("rank", width=50, anchor="center")
        self.tree_detail.tag_configure("rank1", background="#d4edda")
        self.tree_detail.tag_configure("fell", background="#f8d7da")
        dvsb = ttk.Scrollbar(detail_frame, orient="vertical", command=self.tree_detail.yview)
        self.tree_detail.configure(yscrollcommand=dvsb.set)
        dvsb.pack(side="right", fill="y")
        self.tree_detail.pack(fill="both", expand=True)
        self.lbl_hint = ttk.Label(detail_frame, text="点击上方表格中的马查看记录明细",
                                   font=("Microsoft YaHei", 10), foreground="gray")
        self.lbl_hint.place(relx=0.5, rely=0.5, anchor="center")

        self._refresh_all()

    def _refresh_all(self):
        self._refresh_table()
        self._clear_detail()

    def _refresh_table(self):
        # 记录当前选中
        prev_sel = list(self.tree.selection())

        for item in self.tree.get_children():
            self.tree.delete(item)
        show_hidden = self.show_hidden_var.get()
        bloodline_only = self.bloodline_only_var.get()

        allowed_ids = None
        if bloodline_only and prev_sel:
            selected_id = prev_sel[0]
            rels = _get_bloodline(selected_id, read_horses())
            allowed_ids = {selected_id} | set(rels.keys())

        for h in read_horses():
            hid = h["id"]
            is_hidden = h.get("hidden", "0") == "1"
            if is_hidden and not show_hidden:
                continue
            if allowed_ids is not None and hid not in allowed_ids:
                continue
            st = calc_stats(hid)
            def fmt(avg, cnt):
                return f"{avg} ({cnt})" if avg != "-" else f"- ({cnt})"
            def parent_name(pid):
                if not pid:
                    return "-"
                for ho in read_horses():
                    if ho["id"] == str(pid):
                        return ho["name"]
                return "-"
            self.tree.insert("", "end", iid=hid, values=(
                "☑" if is_hidden else "☐",
                hid,
                h["name"],
                parent_name(h.get("father_id", "")),
                parent_name(h.get("mother_id", "")),
                fmt(st["test_avg"], st["test_count"]),
                fmt(st["t1_avg"], st["t1_count"]),
                fmt(st["t2_avg"], st["t2_count"]),
                fmt(st["t3_avg"], st["t3_count"]),
                fmt(st["t4_avg"], st["t4_count"]),
                fmt(st["avg_fall_time"], st["fall_count"]),
                fmt(st["avg_rank"], st["rank_count"]),
                st["wins"], st["total"], st["win_rate"],
                st["falls"]
            ))

        # 恢复选中（如果该马仍在表格中）
        for sid in prev_sel:
            for item in self.tree.get_children():
                if item == sid:
                    self.tree.selection_set(sid)
                    break

        self._apply_bloodline()

    def _apply_bloodline(self):
        sel = self.tree.selection()
        if not sel:
            for item in self.tree.get_children():
                self.tree.item(item, tags=())
            self._update_timer_buttons()
            return
        selected_id = sel[0]
        rels = _get_bloodline(selected_id, read_horses())
        for item in self.tree.get_children():
            hid = item
            if hid == selected_id:
                self.tree.item(item, tags=("self_sel",))
            elif hid in rels:
                rtype, gen = rels[hid]
                prefix = "anc" if rtype == "ancestor" else "desc"
                tag = f"{prefix}{min(gen, 4)}"
                self.tree.item(item, tags=(tag,))
            else:
                self.tree.item(item, tags=())
        self._update_timer_buttons()

    def _update_timer_buttons(self):
        has_sel = bool(self.tree.selection())
        self.btn_edit.config(state="normal" if has_sel else "disabled")
        self.btn_delete.config(state="normal" if has_sel else "disabled")
        self.btn_test.config(state="normal" if has_sel else "disabled")
        self.btn_race.config(state="normal" if has_sel else "disabled")

    def _sort_by(self, col):
        reverse = self.sort_state.get(col, False)
        data = []
        for item in self.tree.get_children(""):
            val = self.tree.set(item, col)
            data.append((self._sort_key(val, col), item))
        data.sort(key=lambda x: x[0], reverse=reverse)
        for i, (_, item) in enumerate(data):
            self.tree.move(item, "", i)
        self.sort_state[col] = not reverse

    def _sort_key(self, val, col):
        if col == "hidden":
            return (0, 1 if val == "☑" else 0)
        if val == "-":
            return (0, float("inf"))
        try:
            if "%" in val:
                return (0, float(val.replace("%", "")))
            return (0, float(val.split()[0]))
        except (ValueError, IndexError):
            return (1, val)

    def _on_tree_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            return
        row = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)

        if row:
            if row in self.tree.selection():
                self.tree.selection_remove(row)
                self._clear_detail()
                self._apply_bloodline()
                if self.bloodline_only_var.get():
                    self._refresh_table()
            else:
                self.tree.selection_set(row)
                self._show_detail(row)
                self._apply_bloodline()
                if self.bloodline_only_var.get():
                    self._refresh_table()
            self._update_timer_buttons()

        if col == "#1" and row:  # hidden 列
            toggle_hidden(row)
            current_val = self.tree.set(row, "hidden")
            new_val = "☐" if current_val == "☑" else "☑"
            self.tree.set(row, "hidden", new_val)
            if not self.show_hidden_var.get() and new_val == "☑":
                self.tree.delete(row)
                self._clear_detail()
                self._apply_bloodline()
                self._update_timer_buttons()
            return "break"

    def _clear_detail(self):
        self.selected_horse_id = None
        for item in self.tree_detail.get_children():
            self.tree_detail.delete(item)
        self.lbl_hint.lift()
        self.lbl_hint.place(relx=0.5, rely=0.5, anchor="center")

    def _show_detail(self, horse_id):
        self.selected_horse_id = horse_id
        for item in self.tree_detail.get_children():
            self.tree_detail.delete(item)
        self.lbl_hint.place_forget()
        records = get_horse_records(horse_id)
        for r in reversed(records):
            mode_str = "测试" if r.get("mode", "") == "test" else "正赛"
            tag = ""
            if r.get("fall_time", ""):
                tag = "fell"
            elif r.get("rank", "") == "1":
                tag = "rank1"
            self.tree_detail.insert("", "end", values=(
                r["date"], mode_str,
                r["time1"] if r["time1"] else "-",
                r["time2"] if r["time2"] else "-",
                r["time3"] if r["time3"] else "-",
                r["time4"] if r["time4"] else "-",
                r.get("fall_time", "") if r.get("fall_time", "") else "-",
                r.get("rank", "") if r.get("rank", "") else "-"
            ), tags=(tag,))

    def _delete_horse(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("未选择", "请先选中一匹要删除的马")
            return
        hid = sel[0]
        hname = ""
        for h in read_horses():
            if h["id"] == hid:
                hname = h["name"]
                break

        # 自定义居中确认对话框
        top = tk.Toplevel(self.root)
        top.title("确认删除")
        top.resizable(False, False)
        top.transient(self.root)
        top.grab_set()
        w, h = 320, 130
        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - w) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - h) // 2
        top.geometry(f"{w}x{h}+{x}+{y}")

        ttk.Label(top, text=f"确定要删除马 '{hname}' 及其所有记录吗？", wraplength=280).pack(pady=15)
        btn = ttk.Frame(top)
        btn.pack(pady=10)
        result = tk.BooleanVar(value=False)
        ttk.Button(btn, text="确定", command=lambda: [result.set(True), top.destroy()]).pack(side="left", padx=10)
        ttk.Button(btn, text="取消", command=top.destroy).pack(side="left", padx=10)
        self.root.wait_window(top)
        if not result.get():
            return
        # 删除马
        horses = [h for h in read_horses() if h["id"] != hid]
        with open(HORSES_FILE, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "name", "father_id", "mother_id", "added_date", "hidden"])
            for h in horses:
                writer.writerow([h["id"], h["name"], h.get("father_id", ""), h.get("mother_id", ""), h["added_date"], h.get("hidden", "0")])
        # 删除记录
        records = [r for r in read_records() if r["horse_id"] != hid]
        with open(RECORDS_FILE, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow([
                "record_id", "horse_id", "horse_name", "date", "mode",
                "time1", "time2", "time3", "time4", "fall_time", "rank"
            ])
            for r in records:
                writer.writerow([
                    r["record_id"], r["horse_id"], r["horse_name"], r["date"], r["mode"],
                    r["time1"], r["time2"], r["time3"], r["time4"], r["fall_time"],
                    r["rank"]
                ])
        self._refresh_all()

    def _open_add_horse(self):
        AddHorseWindow(self.root, on_save=self._refresh_all)

    def _edit_horse(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("未选择", "请先选中一匹要编辑的马")
            return
        hid = sel[0]
        horse = None
        for h in read_horses():
            if h["id"] == hid:
                horse = h
                break
        if not horse:
            return
        EditHorseWindow(
            self.root,
            horse_id=hid,
            name=horse["name"],
            father_id=horse.get("father_id", ""),
            mother_id=horse.get("mother_id", ""),
            on_save=self._refresh_all
        )

    def _open_timer(self, mode):
        sel = self.tree.selection()
        if not sel:
            return
        hid = sel[0]
        default = None
        for h in read_horses():
            if h["id"] == hid:
                default = f"{h['id']} - {h['name']}"
                break
        TimerWindow(self.root, mode, on_save=self._refresh_all, default_horse=default)

    def _export_data(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"horsey_monitor_{timestamp}.zip"
        path = filedialog.asksaveasfilename(
            title="导出数据",
            defaultextension=".zip",
            initialfile=default_name,
            filetypes=[("ZIP 文件", "*.zip")],
            parent=self.root
        )
        if not path:
            return
        try:
            with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
                if os.path.exists(HORSES_FILE):
                    zf.write(HORSES_FILE, os.path.basename(HORSES_FILE))
                if os.path.exists(RECORDS_FILE):
                    zf.write(RECORDS_FILE, os.path.basename(RECORDS_FILE))
            messagebox.showinfo("导出成功", f"数据已导出到:\n{path}", parent=self.root)
        except Exception as e:
            messagebox.showerror("导出失败", str(e), parent=self.root)

    def _import_data(self):
        path = filedialog.askopenfilename(
            filetypes=[("ZIP 文件", "*.zip")],
            title="选择要导入的 ZIP 文件",
            parent=self.root
        )
        if not path:
            return
        if not messagebox.askyesno("确认导入", "导入将覆盖现有数据，确定继续？", parent=self.root):
            return
        try:
            with zipfile.ZipFile(path, "r") as zf:
                for name in zf.namelist():
                    if name == os.path.basename(HORSES_FILE):
                        zf.extract(name, ".")
                    elif name == os.path.basename(RECORDS_FILE):
                        zf.extract(name, ".")
            self._refresh_all()
            messagebox.showinfo("导入成功", "数据已导入", parent=self.root)
        except Exception as e:
            messagebox.showerror("导入失败", str(e), parent=self.root)

    def _clear_all_data(self):
        if not messagebox.askyesno("确认清空", "确定要清空所有数据吗？此操作不可恢复！", parent=self.root):
            return
        try:
            for f in [HORSES_FILE, RECORDS_FILE]:
                if os.path.exists(f):
                    os.remove(f)
            init_csv()
            self._refresh_all()
            messagebox.showinfo("清空完成", "所有数据已清空", parent=self.root)
        except Exception as e:
            messagebox.showerror("清空失败", str(e), parent=self.root)


if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()
