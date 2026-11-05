"""Minimal Windows operator desktop for simulation-only sequence execution.

Tkinter (Python standard library) is a *temporary operator front end* for
the vertical slice, not a native LabVIEW front panel. Real LabVIEW function
VIs may be selected as its decision backend via the working gRPC MCP server.
"""
from __future__ import annotations

import asyncio
import queue
import threading
from pathlib import Path

from .core import project_root
from .sequence_mvp import PLAN_FILE, load_plan, run_file, save_results


def launch(exe: Path | None = None, native_dir: Path | None = None) -> None:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    root = tk.Tk()
    root.title("Universal Sequence Executor — SIMULATION ONLY")
    root.geometry("960x660")
    root.minsize(780, 540)
    q: queue.Queue = queue.Queue()
    stopping = threading.Event()
    pausing = threading.Event()
    current_path = PLAN_FILE
    running = False

    toolbar = ttk.Frame(root, padding=(12, 12, 12, 8))
    toolbar.pack(fill="x")
    ttk.Label(toolbar, text="Universal Executor / Simulation",
              font=("Segoe UI", 16, "bold")).pack(side="left")
    status = tk.StringVar(value="IDLE — No physical I/O")
    ttk.Label(root, textvariable=status, padding=(12, 2)).pack(anchor="w")

    columns = ("number", "name", "status")
    tree = ttk.Treeview(root, columns=columns, show="headings", height=9)
    for name, label, width in (("number", "#", 50),
                               ("name", "Sequence Step", 520),
                               ("status", "State", 150)):
        tree.heading(name, text=label)
        tree.column(name, width=width, anchor="w" if name == "name" else "center")
    tree.pack(fill="both", expand=True, padx=12, pady=8)
    progress = ttk.Progressbar(root, mode="determinate")
    progress.pack(fill="x", padx=12)
    log = tk.Text(root, height=11, wrap="word", font=("Consolas", 10), state="disabled")
    log.pack(fill="both", expand=True, padx=12, pady=8)
    footer = ttk.Frame(root, padding=12)
    footer.pack(fill="x")
    mode = tk.StringVar(value="grpc" if (exe and native_dir) else "mock")
    ttk.Label(footer, text="Decision backend:").pack(side="left")
    if exe and native_dir:
        ttk.Radiobutton(footer, text="Native LabVIEW utility VIs", variable=mode,
                        value="grpc").pack(side="left")
        ttk.Radiobutton(footer, text="Python mock", variable=mode,
                        value="mock").pack(side="left")
    else:
        ttk.Label(footer, text="Python mock (not native verification)").pack(side="left")

    def append(text: str) -> None:
        log.configure(state="normal")
        log.insert("end", text + "\n")
        log.see("end")
        log.configure(state="disabled")

    def fill(path: Path) -> None:
        plan = load_plan(path)
        tree.delete(*tree.get_children())
        for n, step in enumerate(plan.steps, 1):
            tree.insert("", "end", iid=str(n), values=(n, step.name, "PENDING"))
        progress.configure(maximum=len(plan.steps), value=0)
        status.set(f"READY — {plan.name} — SIMULATION ONLY")
        append(f"Loaded {len(plan.steps)} steps from {path}")

    def load_click() -> None:
        nonlocal current_path
        if running:
            return
        name = filedialog.askopenfilename(title="Open simulation sequence JSON",
                                          filetypes=[("JSON", "*.json")])
        if not name:
            return
        try:
            fill(Path(name))
            current_path = Path(name)
        except Exception as exc:
            messagebox.showerror("Invalid sequence", str(exc))

    def start_click() -> None:
        nonlocal running
        if running:
            return
        try:
            load_plan(current_path)
        except Exception as exc:
            messagebox.showerror("Invalid sequence", str(exc))
            return
        stopping.clear()
        pausing.clear()
        running = True
        start_btn.configure(state="disabled")
        load_btn.configure(state="disabled")
        pause_btn.configure(state="normal", text="Pause")
        stop_btn.configure(state="normal")
        for iid in tree.get_children():
            tree.set(iid, "status", "PENDING")
        progress.configure(value=0)
        status.set("RUNNING — SIMULATION ONLY")
        append(f"Start {current_path} using backend {mode.get()}")

        def worker() -> None:
            try:
                result = asyncio.run(run_file(
                    current_path, backend=mode.get(), exe=exe, vi_dir=native_dir,
                    stop=stopping, pause=pausing, delay_s=0.04,
                    emit=lambda event: q.put(("event", event))))
                report, events = save_results(result)
                q.put(("done", result, str(report), str(events)))
            except Exception as exc:
                q.put(("error", f"{type(exc).__name__}: {exc}"))

        threading.Thread(target=worker, name="SimulationSequenceRun",
                         daemon=True).start()

    def pause_click() -> None:
        if not running:
            return
        if pausing.is_set():
            pausing.clear()
            pause_btn.configure(text="Pause")
            status.set("RUNNING — SIMULATION ONLY")
            append("Operator RESUME")
        else:
            pausing.set()
            pause_btn.configure(text="Resume")
            status.set("PAUSED — SIMULATION ONLY")
            append("Operator PAUSE")

    def stop_click() -> None:
        if running:
            stopping.set()
            pausing.clear()
            status.set("STOP REQUESTED")
            append("Operator STOP requested")

    def reset() -> None:
        nonlocal running
        running = False
        load_btn.configure(state="normal")
        start_btn.configure(state="normal")
        pause_btn.configure(state="disabled", text="Pause")
        stop_btn.configure(state="disabled")

    def poll() -> None:
        try:
            while True:
                row = q.get_nowait()
                if row[0] == "event":
                    e = row[1]
                    if e["type"] == "SAMPLE":
                        status.set(f"Step {e['step_index']} | {e['actual_bar']:.2f} bar"
                                   f" → {e['target_bar']:.2f} bar [SIM]")
                    elif e["type"] == "STEP_STARTED":
                        tree.set(str(e["step_index"]), "status", "RUNNING")
                        append(f"Step {e['step_index']} START: {e['step_name']}")
                    elif e["type"] == "STEP_FINISHED":
                        tree.set(str(e["step_index"]), "status", e["status"])
                        progress.step(1)
                        append(f"Step {e['step_index']} {e['status']}")
                    elif e["type"] == "RUN_ERROR":
                        append(f"ERROR: {e.get('detail', 'Unknown')}")
                elif row[0] == "done":
                    result, report, events = row[1:]
                    status.set(f"{result['status']} — {result['backend']} — SIMULATION ONLY")
                    append(f"Run {result['status']}. Saved {report} and {events}")
                    reset()
                elif row[0] == "error":
                    status.set("ERROR")
                    append("Run error: " + row[1])
                    reset()
        except queue.Empty:
            pass
        root.after(75, poll)

    load_btn = ttk.Button(footer, text="Load JSON", command=load_click)
    load_btn.pack(side="right", padx=4)
    stop_btn = ttk.Button(footer, text="Stop", command=stop_click, state="disabled")
    stop_btn.pack(side="right", padx=4)
    pause_btn = ttk.Button(footer, text="Pause", command=pause_click, state="disabled")
    pause_btn.pack(side="right", padx=4)
    start_btn = ttk.Button(footer, text="Start", command=start_click)
    start_btn.pack(side="right", padx=4)

    def close() -> None:
        if running:
            stopping.set()
            pausing.clear()
            messagebox.showinfo("Stopping", "Stop requested. Close after the run terminates.")
            return
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", close)
    fill(current_path)
    root.after(75, poll)
    root.mainloop()
