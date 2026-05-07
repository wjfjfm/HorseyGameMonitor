# -*- coding: utf-8 -*-
"""
赛马数据分析软件 — 记录与统计分离的列系统
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
RECORD_SCHEMA_FILE = "record_schema.csv"
STAT_SCHEMA_FILE = "stat_schema.csv"


def init_csv():
    if not os.path.exists(HORSES_FILE):
        with open(HORSES_FILE, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "name", "father_id", "mother_id", "added_date", "hidden"])


def init_record_schema():
    if not os.path.exists(RECORD_SCHEMA_FILE):
        with open(RECORD_SCHEMA_FILE, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["col_id", "name", "type", "params", "order"])
            writer.writerow(["col_1", "1线", "time", "", "1"])
            writer.writerow(["col_2", "2线", "time", "", "2"])
            writer.writerow(["col_3", "3线", "time", "", "3"])
            writer.writerow(["col_4", "4线", "time", "", "4"])
            writer.writerow(["col_5", "摔倒", "time", "", "5"])
            writer.writerow(["col_6", "获胜", "bool", "", "6"])


def init_stat_schema():
    if not os.path.exists(STAT_SCHEMA_FILE):
        with open(STAT_SCHEMA_FILE, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["stat_id", "name", "source_col", "stat_type", "order"])
            writer.writerow(["stat_1", "1线平均", "col_1", "avg", "1"])
            writer.writerow(["stat_2", "2线平均", "col_2", "avg", "2"])
            writer.writerow(["stat_3", "3线平均", "col_3", "avg", "3"])
            writer.writerow(["stat_4", "4线平均", "col_4", "avg", "4"])
            writer.writerow(["stat_5", "摔倒平均", "col_5", "avg", "5"])
            writer.writerow(["stat_6", "获胜率", "col_6", "avg", "6"])


def ensure_records_header():
    record_schema = read_record_schema()
    schema_ids = [c["col_id"] for c in record_schema]
    header = ["record_id", "horse_id", "horse_name", "date"] + schema_ids
    if not os.path.exists(RECORDS_FILE):
        with open(RECORDS_FILE, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(header)
        return
    with open(RECORDS_FILE, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        records = list(reader)
    if fieldnames == header:
        return
    legacy_map = {
        "time1": "col_1", "time2": "col_2", "time3": "col_3", "time4": "col_4",
        "fall_time": "col_5", "rank": "col_6",
    }
    rev_map = {v: k for k, v in legacy_map.items()}
    with open(RECORDS_FILE, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for r in records:
            row = [r.get("record_id", ""), r.get("horse_id", ""),
                   r.get("horse_name", ""), r.get("date", "")]
            for cid in schema_ids:
                legacy_key = rev_map.get(cid)
                if legacy_key and legacy_key in fieldnames:
                    val = r.get(legacy_key, "")
                else:
                    val = r.get(cid, "")
                row.append(val)
            writer.writerow(row)


def migrate_schema():
    old_schema = "schema.csv"
    if os.path.exists(old_schema) and not os.path.exists(RECORD_SCHEMA_FILE):
        import shutil
        shutil.copy2(old_schema, RECORD_SCHEMA_FILE)


# ---------- Record Schema ----------

def read_record_schema():
    if not os.path.exists(RECORD_SCHEMA_FILE):
        init_record_schema()
    schema = []
    with open(RECORD_SCHEMA_FILE, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            schema.append({
                "col_id": row["col_id"],
                "name": row["name"],
                "type": row["type"],
                "params": row.get("params", ""),
                "order": int(row.get("order", 0))
            })
    schema.sort(key=lambda x: x["order"])
    return schema


def save_record_schema(schema):
    with open(RECORD_SCHEMA_FILE, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["col_id", "name", "type", "params", "order"])
        for c in schema:
            writer.writerow([c["col_id"], c["name"], c["type"], c.get("params", ""), c["order"]])


def next_record_col_id(schema):
    max_num = 0
    for c in schema:
        try:
            num = int(c["col_id"].replace("col_", ""))
            if num > max_num:
                max_num = num
        except ValueError:
            pass
    return f"col_{max_num + 1}"


def delete_record_column(col_id):
    schema = read_record_schema()
    schema = [c for c in schema if c["col_id"] != col_id]
    for i, c in enumerate(schema, start=1):
        c["order"] = i
    save_record_schema(schema)

    stat_schema = read_stat_schema()
    stat_schema = [s for s in stat_schema if s["source_col"] != col_id]
    for i, s in enumerate(stat_schema, start=1):
        s["order"] = i
    save_stat_schema(stat_schema)

    records = read_records()
    schema_ids = [c["col_id"] for c in schema]
    with open(RECORDS_FILE, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["record_id", "horse_id", "horse_name", "date"] + schema_ids)
        for r in records:
            row = [r["record_id"], r["horse_id"], r["horse_name"], r["date"]]
            for cid in schema_ids:
                row.append(r.get(cid, ""))
            writer.writerow(row)


# ---------- Stat Schema ----------

def read_stat_schema():
    if not os.path.exists(STAT_SCHEMA_FILE):
        init_stat_schema()
    schema = []
    with open(STAT_SCHEMA_FILE, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            schema.append({
                "stat_id": row["stat_id"],
                "name": row["name"],
                "source_col": row["source_col"],
                "stat_type": row["stat_type"],
                "order": int(row.get("order", 0))
            })
    schema.sort(key=lambda x: x["order"])
    return schema


def save_stat_schema(schema):
    with open(STAT_SCHEMA_FILE, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["stat_id", "name", "source_col", "stat_type", "order"])
        for s in schema:
            writer.writerow([s["stat_id"], s["name"], s["source_col"], s["stat_type"], s["order"]])


def next_stat_col_id(schema):
    max_num = 0
    for s in schema:
        try:
            num = int(s["stat_id"].replace("stat_", ""))
            if num > max_num:
                max_num = num
        except ValueError:
            pass
    return f"stat_{max_num + 1}"


def delete_stat_column(stat_id):
    schema = read_stat_schema()
    schema = [s for s in schema if s["stat_id"] != stat_id]
    for i, s in enumerate(schema, start=1):
        s["order"] = i
    save_stat_schema(schema)


# ---------- Horses ----------

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
        writer.writerow([new_id, name, father_id, mother_id,
                         datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "0"])
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
            writer.writerow([h["id"], h["name"], h.get("father_id", ""),
                             h.get("mother_id", ""), h["added_date"], h.get("hidden", "0")])


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
            writer.writerow([h["id"], h["name"], h.get("father_id", ""),
                             h.get("mother_id", ""), h["added_date"], h.get("hidden", "0")])


# ---------- Records ----------

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


def add_record(horse_id, horse_name, values):
    records = read_records()
    new_id = 1
    if records:
        new_id = max(int(r["record_id"]) for r in records) + 1
    record_schema = read_record_schema()
    schema_ids = [c["col_id"] for c in record_schema]
    row = [new_id, horse_id, horse_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
    for cid in schema_ids:
        row.append(values.get(cid, ""))
    with open(RECORDS_FILE, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(row)


def update_record(record_id, values):
    records = read_records()
    record_schema = read_record_schema()
    schema_ids = [c["col_id"] for c in record_schema]
    header = ["record_id", "horse_id", "horse_name", "date"] + schema_ids
    for r in records:
        if r["record_id"] == str(record_id):
            for cid in schema_ids:
                r[cid] = values.get(cid, "")
            break
    with open(RECORDS_FILE, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for r in records:
            row = [r["record_id"], r["horse_id"], r["horse_name"], r["date"]]
            for cid in schema_ids:
                row.append(r.get(cid, ""))
            writer.writerow(row)


# ---------- 统计与验证 ----------

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
    record_schema = read_record_schema()
    result = {}
    for c in record_schema:
        cid = c["col_id"]
        vals = [_pf(r.get(cid, "")) for r in all_recs if r.get(cid, "")]
        vals = [v for v in vals if v is not None]
        count = len(vals)
        result[cid] = {
            "count": count,
            "avg": _avg(vals),
            "max": f"{max(vals):.2f}" if vals else "-",
            "min": f"{min(vals):.2f}" if vals else "-",
            "sum": f"{sum(vals):.2f}" if vals else "-",
        }
    return result


def validate_value(value, col_type, params):
    if value == "" or value is None:
        return True
    v = _pf(value)
    if v is None:
        return False
    if col_type == "range":
        parts = params.split(",")
        if len(parts) != 2:
            return False
        try:
            min_v, max_v = int(parts[0]), int(parts[1])
        except ValueError:
            return False
        if v != int(v):
            return False
        vi = int(v)
        if vi < min_v or vi > max_v:
            return False
    elif col_type == "bool":
        if v not in (0, 1):
            return False
    return True


def format_display(value, col_type):
    if value == "" or value is None:
        return "-"
    if col_type == "bool":
        return "✓" if str(value) in ("1", "1.0") else ""
    return str(value)


# ---------- TimerWidget ----------

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


# ---------- RecordWindow（添加/修改记录） ----------

class RecordWindow:
    def __init__(self, parent, on_save=None, default_horse=None, edit_record=None):
        self.on_save = on_save
        self.edit_record = edit_record
        self.parent = parent
        self.win = tk.Toplevel(parent)
        self.win.title("修改记录" if edit_record else "添加记录")
        self.win.resizable(False, False)
        self.win.transient(parent)
        self.win.grab_set()

        self.record_schema = read_record_schema()

        time_cols = [c for c in self.record_schema if c["type"] == "time"]
        other_cols = [c for c in self.record_schema if c["type"] != "time"]
        if edit_record:
            h = 180 + len(self.record_schema) * 45
        else:
            h = 420 + len(time_cols) * 30 + len(other_cols) * 45
        w = 620
        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - w) // 2
        y = parent.winfo_y() + (parent.winfo_height() - h) // 2
        self.win.geometry(f"{w}x{h}+{x}+{y}")

        if edit_record:
            info = ttk.Frame(self.win)
            info.pack(fill="x", pady=10, padx=15)
            ttk.Label(info, text=f"马: {edit_record.get('horse_name', '')}").pack(side="left", padx=(0, 15))
            ttk.Label(info, text=f"日期: {edit_record.get('date', '')}").pack(side="left")
        else:
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

        edit = ttk.LabelFrame(self.win, text="数据编辑")
        edit.pack(fill="x", padx=15, pady=10, ipady=5)

        self.entries = {}
        self.bool_vars = {}

        for c in self.record_schema:
            cid = c["col_id"]
            ctype = c["type"]
            name = c["name"]
            params = c.get("params", "")
            raw_val = edit_record.get(cid, "") if edit_record else ""

            row = ttk.Frame(edit)
            row.pack(fill="x", pady=3, padx=10)
            ttk.Label(row, text=f"{name}:").pack(side="left", padx=(0, 5))

            if ctype == "time":
                e = ttk.Entry(row, width=15)
                e.pack(side="left")
                if edit_record:
                    display_val = "" if raw_val == "" or raw_val is None else format_display(raw_val, "time")
                    e.insert(0, display_val)
                    ttk.Button(row, text="清空",
                               command=lambda cid=cid: self._clear_time(cid),
                               width=6).pack(side="left", padx=(5, 0))
                else:
                    ttk.Button(row, text="录入时间",
                               command=lambda cid=cid: self._fill_time(cid),
                               width=8).pack(side="left", padx=(5, 0))
                    ttk.Button(row, text="清空",
                               command=lambda cid=cid: self._clear_time(cid),
                               width=6).pack(side="left", padx=(2, 0))
                self.entries[cid] = e

            elif ctype == "range":
                parts = params.split(",")
                if len(parts) == 2:
                    try:
                        min_v, max_v = int(parts[0]), int(parts[1])
                    except ValueError:
                        min_v, max_v = 0, 10
                else:
                    min_v, max_v = 0, 10
                spin = tk.Spinbox(row, from_=min_v, to=max_v, width=10, justify="center")
                spin.pack(side="left")
                if edit_record:
                    display_val = "" if raw_val == "" or raw_val is None else format_display(raw_val, "range")
                    spin.delete(0, "end")
                    spin.insert(0, display_val)
                self.entries[cid] = spin
                ttk.Label(row, text=f"  (整数 {min_v}-{max_v})", foreground="gray").pack(side="left")

            elif ctype == "bool":
                var = tk.BooleanVar(value=(raw_val.strip() == "1") if edit_record else False)
                cb = ttk.Checkbutton(row, text="", variable=var)
                cb.pack(side="left")
                self.bool_vars[cid] = var
                e = ttk.Entry(row, width=5)
                e.insert(0, "0")
                e.pack_forget()
                self.entries[cid] = e

        act = ttk.Frame(self.win)
        act.pack(pady=10)
        ttk.Button(act, text="保存", command=self._save).pack(side="left", padx=10)
        ttk.Button(act, text="取消", command=self.win.destroy).pack(side="left", padx=10)

    def _refresh_combo(self):
        horses = read_horses()
        self.combo["values"] = [f"{h['id']} - {h['name']}" for h in horses]
        if horses:
            self.combo.current(0)

    def _fill_time(self, col_id):
        sec = self.timer.get_elapsed()
        ent = self.entries.get(col_id)
        if ent:
            ent.delete(0, "end")
            ent.insert(0, f"{sec:.3f}")

    def _clear_time(self, col_id):
        ent = self.entries.get(col_id)
        if ent:
            ent.delete(0, "end")

    def _save(self):
        values = {}
        for c in self.record_schema:
            cid = c["col_id"]
            ctype = c["type"]
            params = c.get("params", "")

            if ctype == "bool":
                val = "1" if self.bool_vars.get(cid, tk.BooleanVar()).get() else "0"
            else:
                ent = self.entries.get(cid)
                val = ent.get().strip() if ent else ""

            if val:
                if not validate_value(val, ctype, params):
                    messagebox.showwarning("格式错误",
                        f"'{c['name']}' 的值 '{val}' 不符合类型 {ctype} 的要求",
                        parent=self.win)
                    return
                v = _pf(val)
                if v is not None:
                    if ctype == "bool" or ctype == "range":
                        val = str(int(v))
                    else:
                        val = f"{v:.3f}"
            values[cid] = val

        if self.edit_record:
            update_record(self.edit_record["record_id"], values)
        else:
            hs = self.horse_var.get()
            if not hs:
                messagebox.showwarning("未选择马", "请先选择一匹马", parent=self.win)
                return
            hid = hs.split(" - ")[0]
            hname = hs.split(" - ", 1)[1]
            add_record(hid, hname, values)

        self.win.destroy()
        if self.on_save:
            self.on_save()


from faker import Faker
_fake = Faker()


def _get_bloodline(selected_id, horses):
    horse_map = {h["id"]: h for h in horses}
    sel = str(selected_id)

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


# ---------- AddHorseWindow / EditHorseWindow ----------

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


# ---------- RecordSchemaManagerWindow ----------

class RecordSchemaManagerWindow:
    def __init__(self, parent, on_save):
        self.on_save = on_save
        self.win = tk.Toplevel(parent)
        self.win.title("记录管理")
        self.win.resizable(False, False)
        self.win.transient(parent)
        self.win.grab_set()
        w, h = 600, 420
        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - w) // 2
        y = parent.winfo_y() + (parent.winfo_height() - h) // 2
        self.win.geometry(f"{w}x{h}+{x}+{y}")

        frm = ttk.Frame(self.win)
        frm.pack(fill="both", expand=True, padx=15, pady=10)

        cols = ("order", "col_id", "name", "type", "params")
        self.tree = ttk.Treeview(frm, columns=cols, show="headings", height=10)
        self.tree.heading("order", text="顺序")
        self.tree.heading("col_id", text="列ID")
        self.tree.heading("name", text="名称")
        self.tree.heading("type", text="类型")
        self.tree.heading("params", text="参数")
        self.tree.column("order", width=50, anchor="center")
        self.tree.column("col_id", width=70, anchor="center")
        self.tree.column("name", width=120, anchor="center")
        self.tree.column("type", width=80, anchor="center")
        self.tree.column("params", width=100, anchor="center")
        vsb = ttk.Scrollbar(frm, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)

        btn = ttk.Frame(self.win)
        btn.pack(fill="x", padx=15, pady=10)
        ttk.Button(btn, text="上移", command=self._move_up).pack(side="left", padx=4)
        ttk.Button(btn, text="下移", command=self._move_down).pack(side="left", padx=4)
        ttk.Button(btn, text="添加列", command=self._add_col).pack(side="left", padx=4)
        ttk.Button(btn, text="编辑列", command=self._edit_col).pack(side="left", padx=4)
        ttk.Button(btn, text="删除列", command=self._del_col).pack(side="left", padx=4)
        ttk.Button(btn, text="关闭", command=self.win.destroy).pack(side="right", padx=4)

        self._refresh()

    def _refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        schema = read_record_schema()
        for c in schema:
            self.tree.insert("", "end", iid=c["col_id"], values=(
                c["order"], c["col_id"], c["name"], c["type"], c.get("params", "")
            ))

    def _selected_col(self):
        sel = self.tree.selection()
        if not sel:
            return None
        cid = sel[0]
        for c in read_record_schema():
            if c["col_id"] == cid:
                return c
        return None

    def _move_up(self):
        c = self._selected_col()
        if not c or c["order"] <= 1:
            return
        schema = read_record_schema()
        for sc in schema:
            if sc["order"] == c["order"] - 1:
                sc["order"] += 1
            elif sc["col_id"] == c["col_id"]:
                sc["order"] -= 1
        save_record_schema(schema)
        self._refresh()

    def _move_down(self):
        c = self._selected_col()
        if not c:
            return
        schema = read_record_schema()
        max_order = max(s["order"] for s in schema)
        if c["order"] >= max_order:
            return
        for sc in schema:
            if sc["order"] == c["order"] + 1:
                sc["order"] -= 1
            elif sc["col_id"] == c["col_id"]:
                sc["order"] += 1
        save_record_schema(schema)
        self._refresh()

    def _add_col(self):
        self._open_edit_dialog("添加记录列", None)

    def _edit_col(self):
        c = self._selected_col()
        if not c:
            messagebox.showwarning("未选择", "请先选择一列", parent=self.win)
            return
        self._open_edit_dialog("编辑记录列", c)

    def _del_col(self):
        c = self._selected_col()
        if not c:
            messagebox.showwarning("未选择", "请先选择一列", parent=self.win)
            return
        if not messagebox.askyesno("确认删除", f"确定删除列 '{c['name']}' 吗？\n该列及其所有统计列、历史数据将被清除！", parent=self.win):
            return
        delete_record_column(c["col_id"])
        self._refresh()
        if self.on_save:
            self.on_save()

    def _open_edit_dialog(self, title, col_data):
        top = tk.Toplevel(self.win)
        top.title(title)
        top.resizable(False, False)
        top.transient(self.win)
        top.grab_set()
        w, h = 360, 300
        self.win.update_idletasks()
        x = self.win.winfo_x() + (self.win.winfo_width() - w) // 2
        y = self.win.winfo_y() + (self.win.winfo_height() - h) // 2
        top.geometry(f"{w}x{h}+{x}+{y}")

        frm = ttk.Frame(top)
        frm.pack(padx=20, pady=15, fill="x")

        ttk.Label(frm, text="名称:").grid(row=0, column=0, sticky="e", padx=5, pady=8)
        entry_name = ttk.Entry(frm, width=20)
        entry_name.grid(row=0, column=1, padx=5, pady=8)

        ttk.Label(frm, text="类型:").grid(row=1, column=0, sticky="e", padx=5, pady=8)
        type_var = tk.StringVar(value="time")
        combo_type = ttk.Combobox(frm, textvariable=type_var, state="readonly", width=18,
                                   values=["time", "range", "bool"])
        combo_type.grid(row=1, column=1, padx=5, pady=8)
        combo_type.current(0)

        ttk.Label(frm, text="参数:").grid(row=2, column=0, sticky="e", padx=5, pady=8)
        entry_params = ttk.Entry(frm, width=20)
        entry_params.grid(row=2, column=1, padx=5, pady=8)
        ttk.Label(frm, text="range 类型填: min,max", foreground="gray").grid(row=3, column=0, columnspan=2)
        ttk.Label(frm, text="time/bool 留空", foreground="gray").grid(row=4, column=0, columnspan=2)

        if col_data:
            entry_name.insert(0, col_data["name"])
            type_var.set(col_data["type"])
            entry_params.insert(0, col_data.get("params", ""))

        def save():
            name = entry_name.get().strip()
            if not name:
                messagebox.showwarning("输入不完整", "请填写列名称", parent=top)
                return
            ctype = type_var.get()
            params = entry_params.get().strip()
            if ctype == "range":
                parts = params.split(",")
                if len(parts) != 2:
                    messagebox.showwarning("参数错误", "range 类型参数格式为: min,max", parent=top)
                    return
                try:
                    int(parts[0]), int(parts[1])
                except ValueError:
                    messagebox.showwarning("参数错误", "range 范围的 min,max 必须是整数", parent=top)
                    return

            schema = read_record_schema()
            existing_names = {c["name"] for c in schema if (not col_data or c["col_id"] != col_data["col_id"])}
            if name in existing_names:
                messagebox.showwarning("名称重复", "该列名称已存在", parent=top)
                return

            if col_data:
                for c in schema:
                    if c["col_id"] == col_data["col_id"]:
                        c["name"] = name
                        c["type"] = ctype
                        c["params"] = params
                        break
            else:
                new_id = next_record_col_id(schema)
                new_order = max((c["order"] for c in schema), default=0) + 1
                schema.append({
                    "col_id": new_id, "name": name, "type": ctype,
                    "params": params, "order": new_order
                })
            schema.sort(key=lambda x: x["order"])
            save_record_schema(schema)
            ensure_records_header()
            top.destroy()
            self._refresh()
            if self.on_save:
                self.on_save()

        btn = ttk.Frame(top)
        btn.pack(pady=15)
        ttk.Button(btn, text="保存", command=save).pack(side="left", padx=10)
        ttk.Button(btn, text="取消", command=top.destroy).pack(side="left", padx=10)


# ---------- StatSchemaManagerWindow ----------

class StatSchemaManagerWindow:
    def __init__(self, parent, on_save):
        self.on_save = on_save
        self.win = tk.Toplevel(parent)
        self.win.title("统计管理")
        self.win.resizable(False, False)
        self.win.transient(parent)
        self.win.grab_set()
        w, h = 600, 420
        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - w) // 2
        y = parent.winfo_y() + (parent.winfo_height() - h) // 2
        self.win.geometry(f"{w}x{h}+{x}+{y}")

        frm = ttk.Frame(self.win)
        frm.pack(fill="both", expand=True, padx=15, pady=10)

        cols = ("order", "stat_id", "name", "source", "stat_type")
        self.tree = ttk.Treeview(frm, columns=cols, show="headings", height=10)
        self.tree.heading("order", text="顺序")
        self.tree.heading("stat_id", text="统计ID")
        self.tree.heading("name", text="名称")
        self.tree.heading("source", text="来源列")
        self.tree.heading("stat_type", text="统计方式")
        self.tree.column("order", width=50, anchor="center")
        self.tree.column("stat_id", width=70, anchor="center")
        self.tree.column("name", width=140, anchor="center")
        self.tree.column("source", width=100, anchor="center")
        self.tree.column("stat_type", width=80, anchor="center")
        vsb = ttk.Scrollbar(frm, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)

        btn = ttk.Frame(self.win)
        btn.pack(fill="x", padx=15, pady=10)
        ttk.Button(btn, text="上移", command=self._move_up).pack(side="left", padx=4)
        ttk.Button(btn, text="下移", command=self._move_down).pack(side="left", padx=4)
        ttk.Button(btn, text="添加统计列", command=self._add_col).pack(side="left", padx=4)
        ttk.Button(btn, text="编辑统计列", command=self._edit_col).pack(side="left", padx=4)
        ttk.Button(btn, text="删除统计列", command=self._del_col).pack(side="left", padx=4)
        ttk.Button(btn, text="关闭", command=self.win.destroy).pack(side="right", padx=4)

        self._refresh()

    def _refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        schema = read_stat_schema()
        record_schema = read_record_schema()
        col_map = {c["col_id"]: c["name"] for c in record_schema}
        for s in schema:
            source_name = col_map.get(s["source_col"], s["source_col"])
            self.tree.insert("", "end", iid=s["stat_id"], values=(
                s["order"], s["stat_id"], s["name"], source_name, s["stat_type"]
            ))

    def _selected(self):
        sel = self.tree.selection()
        if not sel:
            return None
        sid = sel[0]
        for s in read_stat_schema():
            if s["stat_id"] == sid:
                return s
        return None

    def _move_up(self):
        s = self._selected()
        if not s or s["order"] <= 1:
            return
        schema = read_stat_schema()
        for sc in schema:
            if sc["order"] == s["order"] - 1:
                sc["order"] += 1
            elif sc["stat_id"] == s["stat_id"]:
                sc["order"] -= 1
        save_stat_schema(schema)
        self._refresh()

    def _move_down(self):
        s = self._selected()
        if not s:
            return
        schema = read_stat_schema()
        max_order = max(s["order"] for s in schema)
        if s["order"] >= max_order:
            return
        for sc in schema:
            if sc["order"] == s["order"] + 1:
                sc["order"] -= 1
            elif sc["stat_id"] == s["stat_id"]:
                sc["order"] += 1
        save_stat_schema(schema)
        self._refresh()

    def _add_col(self):
        self._open_edit_dialog("添加统计列", None)

    def _edit_col(self):
        s = self._selected()
        if not s:
            messagebox.showwarning("未选择", "请先选择一列", parent=self.win)
            return
        self._open_edit_dialog("编辑统计列", s)

    def _del_col(self):
        s = self._selected()
        if not s:
            messagebox.showwarning("未选择", "请先选择一列", parent=self.win)
            return
        if not messagebox.askyesno("确认删除", f"确定删除统计列 '{s['name']}' 吗？", parent=self.win):
            return
        delete_stat_column(s["stat_id"])
        self._refresh()
        if self.on_save:
            self.on_save()

    def _open_edit_dialog(self, title, stat_data):
        top = tk.Toplevel(self.win)
        top.title(title)
        top.resizable(False, False)
        top.transient(self.win)
        top.grab_set()
        w, h = 360, 260
        self.win.update_idletasks()
        x = self.win.winfo_x() + (self.win.winfo_width() - w) // 2
        y = self.win.winfo_y() + (self.win.winfo_height() - h) // 2
        top.geometry(f"{w}x{h}+{x}+{y}")

        frm = ttk.Frame(top)
        frm.pack(padx=20, pady=15, fill="x")

        ttk.Label(frm, text="名称:").grid(row=0, column=0, sticky="e", padx=5, pady=8)
        entry_name = ttk.Entry(frm, width=20)
        entry_name.grid(row=0, column=1, padx=5, pady=8)

        ttk.Label(frm, text="来源列:").grid(row=1, column=0, sticky="e", padx=5, pady=8)
        source_var = tk.StringVar()
        combo_source = ttk.Combobox(frm, textvariable=source_var, state="readonly", width=18)
        record_schema = read_record_schema()
        source_vals = [f"{c['col_id']} - {c['name']}" for c in record_schema]
        source_map = {f"{c['col_id']} - {c['name']}": c["col_id"] for c in record_schema}
        combo_source["values"] = source_vals
        combo_source.grid(row=1, column=1, padx=5, pady=8)
        if source_vals:
            combo_source.current(0)

        ttk.Label(frm, text="统计方式:").grid(row=2, column=0, sticky="e", padx=5, pady=8)
        stat_var = tk.StringVar(value="avg")
        combo_stat = ttk.Combobox(frm, textvariable=stat_var, state="readonly", width=18,
                                   values=["avg", "max", "min", "sum"])
        combo_stat.grid(row=2, column=1, padx=5, pady=8)
        combo_stat.current(0)

        if stat_data:
            entry_name.insert(0, stat_data["name"])
            source_key = None
            for k, v in source_map.items():
                if v == stat_data["source_col"]:
                    source_key = k
                    break
            if source_key:
                source_var.set(source_key)
            stat_var.set(stat_data["stat_type"])

        def save():
            name = entry_name.get().strip()
            if not name:
                messagebox.showwarning("输入不完整", "请填写统计列名称", parent=top)
                return
            source_col = source_map.get(source_var.get(), "")
            if not source_col:
                messagebox.showwarning("未选择", "请选择来源列", parent=top)
                return
            stype = stat_var.get()

            schema = read_stat_schema()
            existing_names = {s["name"] for s in schema if (not stat_data or s["stat_id"] != stat_data["stat_id"])}
            if name in existing_names:
                messagebox.showwarning("名称重复", "该统计列名称已存在", parent=top)
                return

            if stat_data:
                for s in schema:
                    if s["stat_id"] == stat_data["stat_id"]:
                        s["name"] = name
                        s["source_col"] = source_col
                        s["stat_type"] = stype
                        break
            else:
                new_id = next_stat_col_id(schema)
                new_order = max((s["order"] for s in schema), default=0) + 1
                schema.append({
                    "stat_id": new_id, "name": name, "source_col": source_col,
                    "stat_type": stype, "order": new_order
                })
            schema.sort(key=lambda x: x["order"])
            save_stat_schema(schema)
            top.destroy()
            self._refresh()
            if self.on_save:
                self.on_save()

        btn = ttk.Frame(top)
        btn.pack(pady=15)
        ttk.Button(btn, text="保存", command=save).pack(side="left", padx=10)
        ttk.Button(btn, text="取消", command=top.destroy).pack(side="left", padx=10)


# ---------- MainApp ----------

class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("赛马数据分析")
        self.root.geometry("1200x750")
        self.root.minsize(1000, 650)
        init_csv()
        migrate_schema()
        init_record_schema()
        init_stat_schema()
        ensure_records_header()
        self.selected_horse_id = None

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", font=("Microsoft YaHei", 10))
        style.configure("TLabel", font=("Microsoft YaHei", 10))
        style.configure("Treeview", font=("Microsoft YaHei", 9), rowheight=22)
        style.configure("Treeview.Heading", font=("Microsoft YaHei", 9, "bold"))

        top = ttk.Frame(root)
        top.pack(fill="x", padx=10, pady=8)

        # 核心操作
        ttk.Button(top, text="添加马", command=self._open_add_horse).pack(side="left", padx=(0, 10))

        ttk.Frame(top, width=20).pack(side="left")

        # 操作菜单（编辑/删除，依赖选中马）
        self.menu_op = tk.Menubutton(top, text="马管理 ▼", relief="raised", state="disabled")
        self.menu_op.pack(side="left", padx=(0, 10))
        op_menu = tk.Menu(self.menu_op, tearoff=0)
        op_menu.add_command(label="编辑马", command=self._edit_horse)
        op_menu.add_command(label="删除马", command=self._delete_horse)
        self.menu_op.config(menu=op_menu)

        # 配置菜单
        menu_cfg = tk.Menubutton(top, text="数据管理 ▼", relief="raised")
        menu_cfg.pack(side="left", padx=(0, 10))
        cfg_menu = tk.Menu(menu_cfg, tearoff=0)
        cfg_menu.add_command(label="记录管理", command=self._open_record_manager)
        cfg_menu.add_command(label="统计管理", command=self._open_stat_manager)
        cfg_menu.add_separator()
        cfg_menu.add_command(label="刷新数据", command=self._refresh_all)
        menu_cfg.config(menu=cfg_menu)

        self.show_hidden_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(top, text="显示隐藏马", variable=self.show_hidden_var, command=self._refresh_table).pack(side="left", padx=(0, 10))
        self.bloodline_only_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(top, text="仅显示亲缘马", variable=self.bloodline_only_var, command=self._refresh_table).pack(side="left", padx=(0, 10))
        self.sort_state = {}

        # 数据菜单
        menu_data = tk.Menubutton(top, text="数据 ▼", relief="raised")
        menu_data.pack(side="right", padx=(10, 0))
        data_menu = tk.Menu(menu_data, tearoff=0)
        data_menu.add_command(label="数据导出", command=self._export_data)
        data_menu.add_command(label="数据导入", command=self._import_data)
        data_menu.add_separator()
        data_menu.add_command(label="清空数据", command=self._clear_all_data)
        menu_data.config(menu=data_menu)

        paned = ttk.PanedWindow(root, orient="vertical")
        paned.pack(fill="both", expand=True, padx=10, pady=5)

        table_frame = ttk.LabelFrame(paned, text="马数据统计（点击行查看明细）")
        paned.add(table_frame, weight=1)

        self._build_main_tree(table_frame)

        detail_frame = ttk.LabelFrame(paned, text="选中马记录明细")
        paned.add(detail_frame, weight=1)

        self.detail_btn_frame = ttk.Frame(detail_frame)
        self.detail_btn_frame.pack(fill="x", padx=5, pady=2)
        self.btn_add_record = ttk.Button(self.detail_btn_frame, text="添加记录", command=self._open_timer)
        self.btn_add_record.pack(side="left", padx=2)
        self.btn_add_record.config(state="disabled")
        self.btn_edit_record = ttk.Button(self.detail_btn_frame, text="修改记录", command=self._edit_record)
        self.btn_edit_record.pack(side="left", padx=2)
        self.btn_edit_record.config(state="disabled")

        self._build_detail_tree(detail_frame)
        self.lbl_hint = ttk.Label(detail_frame, text="点击上方表格中的马查看记录明细\n双击记录可直接修改",
                                   font=("Microsoft YaHei", 10), foreground="gray")
        self.lbl_hint.place(relx=0.5, rely=0.5, anchor="center")

        self._refresh_all()

    def _build_main_tree(self, parent):
        stat_schema = read_stat_schema()
        base_cols = ["hidden", "id", "name", "father", "mother", "shared"]
        stat_cols = [s["stat_id"] for s in stat_schema]
        cols = base_cols + stat_cols

        self.tree = ttk.Treeview(parent, columns=cols, show="headings")
        headings = {
            "hidden": "隐藏", "id": "ID", "name": "名字",
            "father": "父亲", "mother": "母亲", "shared": "共子"
        }
        for s in stat_schema:
            headings[s["stat_id"]] = s["name"]
        for col in cols:
            self.tree.heading(col, text=headings.get(col, col), command=lambda c=col: self._sort_by(c))

        self.tree.column("hidden", width=50, anchor="center")
        self.tree.column("id", width=40, anchor="center")
        self.tree.column("name", width=90, anchor="center")
        self.tree.column("father", width=80, anchor="center")
        self.tree.column("mother", width=80, anchor="center")
        self.tree.column("shared", width=35, anchor="center")
        for s in stat_schema:
            self.tree.column(s["stat_id"], width=110, anchor="center")

        hsb = ttk.Scrollbar(parent, orient="horizontal", command=self.tree.xview)
        vsb = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        self.tree.configure(xscrollcommand=hsb.set, yscrollcommand=vsb.set)
        hsb.pack(side="bottom", fill="x")
        vsb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<ButtonPress-1>", self._on_tree_click)

        for gen, color in [(1, "#b3d9ff"), (2, "#ccebff"), (3, "#e0f0ff"), (4, "#f0f8ff")]:
            self.tree.tag_configure(f"anc{gen}", background=color)
        for gen, color in [(1, "#ffb3ba"), (2, "#ffd1d6"), (3, "#ffe8ea"), (4, "#fff0f2")]:
            self.tree.tag_configure(f"desc{gen}", background=color)
        self.tree.tag_configure("self_sel", background="#fff3cd")

    def _build_detail_tree(self, parent):
        record_schema = read_record_schema()
        dcols = ["date"] + [c["col_id"] for c in record_schema]
        self.tree_detail = ttk.Treeview(parent, columns=dcols, show="headings")
        self.tree_detail.heading("date", text="日期")
        for c in record_schema:
            self.tree_detail.heading(c["col_id"], text=c["name"])
        self.tree_detail.column("date", width=140, anchor="center")
        for c in record_schema:
            self.tree_detail.column(c["col_id"], width=85, anchor="center")
        dvsb = ttk.Scrollbar(parent, orient="vertical", command=self.tree_detail.yview)
        self.tree_detail.configure(yscrollcommand=dvsb.set)
        dvsb.pack(side="right", fill="y")
        self.tree_detail.pack(fill="both", expand=True)
        self.tree_detail.bind("<Double-1>", self._on_detail_double_click)
        self.tree_detail.bind("<<TreeviewSelect>>", self._on_detail_select)

    def _refresh_all(self):
        self._rebuild_trees()
        self._refresh_table()
        self._clear_detail()

    def _rebuild_trees(self):
        prev_sel = list(self.tree.selection())

        self.tree.pack_forget()
        for sb in [w for w in self.tree.master.winfo_children() if isinstance(w, ttk.Scrollbar)]:
            sb.destroy()
        self.tree.destroy()
        self._build_main_tree(self.tree.master)

        self.tree_detail.pack_forget()
        for sb in [w for w in self.tree_detail.master.winfo_children() if isinstance(w, ttk.Scrollbar)]:
            sb.destroy()
        self.tree_detail.destroy()
        self._build_detail_tree(self.tree_detail.master)
        self.lbl_hint.lift()
        self.lbl_hint.place(relx=0.5, rely=0.5, anchor="center")

        for sid in prev_sel:
            for item in self.tree.get_children():
                if item == sid:
                    self.tree.selection_set(sid)
                    break

    def _refresh_table(self):
        prev_sel = list(self.tree.selection())
        for item in self.tree.get_children():
            self.tree.delete(item)
        show_hidden = self.show_hidden_var.get()
        bloodline_only = self.bloodline_only_var.get()
        stat_schema = read_stat_schema()

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

            def fmt_stat(val, count):
                if val != "-" and val is not None:
                    return f"{val} ({count})"
                return f"- ({count})" if count else "-"
            def parent_name(pid):
                if not pid:
                    return "-"
                for ho in read_horses():
                    if ho["id"] == str(pid):
                        return ho["name"]
                return "-"

            values = [
                "☑" if is_hidden else "☐",
                hid, h["name"],
                parent_name(h.get("father_id", "")),
                parent_name(h.get("mother_id", "")),
                "",
            ]
            for s in stat_schema:
                source = s["source_col"]
                stat_type = s["stat_type"]
                val = st[source].get(stat_type, "-")
                count = st[source]["count"]
                values.append(fmt_stat(val, count))
            self.tree.insert("", "end", iid=hid, values=values)

        for sid in prev_sel:
            for item in self.tree.get_children():
                if item == sid:
                    self.tree.selection_set(sid)
                    break
        self._apply_bloodline()

    def _apply_bloodline(self):
        sel = self.tree.selection()
        if not sel:
            horses = read_horses()
            for item in self.tree.get_children():
                self.tree.item(item, tags=())
                hid = item
                count = sum(1 for h in horses if hid in {h.get("father_id",""), h.get("mother_id","")})
                self.tree.set(item, "shared", f"({count})" if count else "")
            self._update_action_buttons()
            return
        selected_id = sel[0]
        rels = _get_bloodline(selected_id, read_horses())
        horses = read_horses()
        for item in self.tree.get_children():
            hid = item
            shared = sum(1 for h in horses
                         if selected_id in {h.get("father_id",""), h.get("mother_id","")}
                         and hid in {h.get("father_id",""), h.get("mother_id","")})
            self.tree.set(item, "shared", f"({shared})" if shared else "")
            if hid == selected_id:
                self.tree.item(item, tags=("self_sel",))
            elif hid in rels:
                rtype, gen = rels[hid]
                prefix = "anc" if rtype == "ancestor" else "desc"
                tag = f"{prefix}{min(gen, 4)}"
                self.tree.item(item, tags=(tag,))
            else:
                self.tree.item(item, tags=())
        self._update_action_buttons()

    def _update_action_buttons(self):
        has_sel = bool(self.tree.selection())
        self.menu_op.config(state="normal" if has_sel else "disabled")

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
            self._update_action_buttons()

        if col == "#1" and row:
            toggle_hidden(row)
            current_val = self.tree.set(row, "hidden")
            new_val = "☐" if current_val == "☑" else "☑"
            self.tree.set(row, "hidden", new_val)
            if not self.show_hidden_var.get() and new_val == "☑":
                self.tree.delete(row)
                self._clear_detail()
                self._apply_bloodline()
                self._update_action_buttons()
        return "break"

    def _clear_detail(self):
        self.selected_horse_id = None
        for item in self.tree_detail.get_children():
            self.tree_detail.delete(item)
        self.lbl_hint.lift()
        self.lbl_hint.place(relx=0.5, rely=0.5, anchor="center")
        self.btn_add_record.config(state="disabled")
        self.btn_edit_record.config(state="disabled")

    def _on_detail_select(self, event=None):
        sel = self.tree_detail.selection()
        if sel:
            self.btn_edit_record.config(state="normal")
        else:
            self.btn_edit_record.config(state="disabled")

    def _on_detail_double_click(self, event):
        row = self.tree_detail.identify_row(event.y)
        if row:
            self._edit_record(record_id=row)

    def _edit_record(self, record_id=None):
        if record_id is None:
            sel = self.tree_detail.selection()
            if not sel:
                messagebox.showwarning("未选择", "请先选中一条记录", parent=self.root)
                return
            record_id = sel[0]
        records = read_records()
        record = None
        for r in records:
            if r["record_id"] == str(record_id):
                record = r
                break
        if not record:
            messagebox.showwarning("未找到", "记录不存在", parent=self.root)
            return
        RecordWindow(self.root, on_save=self._refresh_all, edit_record=record)

    def _show_detail(self, horse_id):
        self.selected_horse_id = horse_id
        for item in self.tree_detail.get_children():
            self.tree_detail.delete(item)
        self.lbl_hint.place_forget()
        records = get_horse_records(horse_id)
        record_schema = read_record_schema()
        for r in reversed(records):
            values = [r["date"]]
            for c in record_schema:
                cid = c["col_id"]
                values.append(format_display(r.get(cid, ""), c["type"]))
            self.tree_detail.insert("", "end", iid=r["record_id"], values=values)
        self.btn_add_record.config(state="normal")
        self.btn_edit_record.config(state="disabled")

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

        horses = [h for h in read_horses() if h["id"] != hid]
        with open(HORSES_FILE, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "name", "father_id", "mother_id", "added_date", "hidden"])
            for h in horses:
                writer.writerow([h["id"], h["name"], h.get("father_id", ""),
                                 h.get("mother_id", ""), h["added_date"], h.get("hidden", "0")])

        record_schema = read_record_schema()
        schema_ids = [c["col_id"] for c in record_schema]
        records = [r for r in read_records() if r["horse_id"] != hid]
        with open(RECORDS_FILE, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["record_id", "horse_id", "horse_name", "date"] + schema_ids)
            for r in records:
                row = [r["record_id"], r["horse_id"], r["horse_name"], r["date"]]
                for cid in schema_ids:
                    row.append(r.get(cid, ""))
                writer.writerow(row)
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
            self.root, horse_id=hid, name=horse["name"],
            father_id=horse.get("father_id", ""),
            mother_id=horse.get("mother_id", ""),
            on_save=self._refresh_all
        )

    def _open_timer(self):
        sel = self.tree.selection()
        if not sel:
            return
        hid = sel[0]
        default = None
        for h in read_horses():
            if h["id"] == hid:
                default = f"{h['id']} - {h['name']}"
                break
        RecordWindow(self.root, on_save=self._refresh_all, default_horse=default)

    def _open_record_manager(self):
        RecordSchemaManagerWindow(self.root, on_save=self._refresh_all)

    def _open_stat_manager(self):
        StatSchemaManagerWindow(self.root, on_save=self._refresh_all)

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
                for f in [HORSES_FILE, RECORDS_FILE, RECORD_SCHEMA_FILE, STAT_SCHEMA_FILE]:
                    if os.path.exists(f):
                        zf.write(f, os.path.basename(f))
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
                    if name in (os.path.basename(HORSES_FILE), os.path.basename(RECORDS_FILE),
                                os.path.basename(RECORD_SCHEMA_FILE), os.path.basename(STAT_SCHEMA_FILE)):
                        zf.extract(name, ".")
            ensure_records_header()
            self._refresh_all()
            messagebox.showinfo("导入成功", "数据已导入", parent=self.root)
        except Exception as e:
            messagebox.showerror("导入失败", str(e), parent=self.root)

    def _clear_all_data(self):
        if not messagebox.askyesno("确认清空", "确定要清空所有数据吗？此操作不可恢复！", parent=self.root):
            return
        try:
            for f in [HORSES_FILE, RECORDS_FILE, RECORD_SCHEMA_FILE, STAT_SCHEMA_FILE]:
                if os.path.exists(f):
                    os.remove(f)
            init_csv()
            init_record_schema()
            init_stat_schema()
            ensure_records_header()
            self._refresh_all()
            messagebox.showinfo("清空完成", "所有数据已清空", parent=self.root)
        except Exception as e:
            messagebox.showerror("清空失败", str(e), parent=self.root)


if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()
