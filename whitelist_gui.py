"""
whitelist_gui.py
================
Interactive GUI to pick commands for run_config.json whitelist.

Usage
-----
    python whitelist_gui.py

Dependencies
------------
    tkinter (built-in with Python on Windows)

Flow
----
    1. Parse all log files -> count unique commands
    2. Show checkbox list (command + count)
    3. User ticks commands to whitelist
    4. Click "Generate Config" -> writes run_config.json
    5. Show success + config preview
"""

import json
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

from process_network_logs import _split_into_segments, _prompt_depth


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "run_config.json")


_DEFAULT_CONFIG = {
    "logs_dir": "logs",
    "output_dir": "screenshots",
    "whitelist": []
}


def parse_logs_and_count(logs_dir="logs"):
    """Read all .txt/.log files and count commands (standalone only, depth 0)."""
    logs_path = os.path.join(SCRIPT_DIR, logs_dir)
    if not os.path.isdir(logs_path):
        return {}

    log_files = sorted(
        os.path.join(logs_path, f)
        for f in os.listdir(logs_path)
        if f.lower().endswith(('.txt', '.log')) and os.path.isfile(os.path.join(logs_path, f))
    )

    # Only count commands at prompt depth 0 (the actual executed commands, not sub-view commands)
    counts = {}
    total = 0
    for log_path in log_files:
        with open(log_path, "r", encoding="utf-8") as f:
            content = f.read()
        segments = _split_into_segments(content)
        for seg in segments:
            if _prompt_depth(seg['prompt']) == 0:
                cmd = seg['command'].strip()
                if cmd:
                    counts[cmd] = counts.get(cmd, 0) + 1
                    total += 1

    return counts, total, len(log_files)


class WhitelistDialog(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Whitelist Generator for run.py")
        self.geometry("650x550")
        self.resizable(True, True)

        # --- Header ---
        header = ttk.Frame(self, padding="10 10 10 5")
        header.pack(fill="x")
        ttk.Label(
            header,
            text="Select commands to include in run_config.json whitelist",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w")
        ttk.Label(
            header,
            text="Tick the commands you want to generate PNGs for. Prefix matching is enabled (e.g. selecting 'display' matches all display* commands)."
        ).pack(anchor="w", pady=(5, 0))

        # --- Info bar ---
        self.info_var = tk.StringVar(value="Scanning logs...")
        info = ttk.Label(header, textvariable=self.info_var, foreground="gray")
        info.pack(anchor="w", pady=(5, 0))

        # --- Scrollable checkbox list ---
        list_frame = ttk.Frame(self, padding="10 5 10 5")
        list_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(list_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        self.scrollable = ttk.Frame(canvas)

        self.scrollable.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Mousewheel scrolling
        self._bind_mousewheel(canvas, scrollbar)

        # --- Buttons ---
        btn_frame = ttk.Frame(self, padding="10 5 10 10")
        btn_frame.pack(fill="x", side="bottom")
        ttk.Button(btn_frame, text="Select All", command=self.select_all).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Deselect All", command=self.deselect_all).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Generate Config", command=self.generate_config).pack(side="right", padx=2)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side="right", padx=2)

        # --- Data ---
        self.check_vars = []  # list of (command, tk.BooleanVar)
        self.load_commands()

    def _bind_mousewheel(self, canvas, scrollbar):
        def on_mousewheel(event):
            if scrollbar.winfo_exists():
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)

    def load_commands(self):
        counts, total, files = parse_logs_and_count()
        if not counts:
            self.info_var.set(f"No .txt/.log files found in logs/")
            return

        self.info_var.set(
            f"Found {len(counts)} unique commands across {files} log file(s) "
            f"({total} total occurrences at depth 0)"
        )

        # Sort by count desc, then command
        sorted_cmds = sorted(counts.items(), key=lambda x: (-x[1], x[0]))

        for cmd, count in sorted_cmds:
            var = tk.BooleanVar(value=False)
            cb = ttk.Checkbutton(
                self.scrollable,
                text=f"{cmd}  ({count}x)",
                variable=var
            )
            cb.pack(anchor="w", padx=5, pady=1)
            self.check_vars.append((cmd, var))

    def select_all(self):
        for _, var in self.check_vars:
            var.set(True)

    def deselect_all(self):
        for _, var in self.check_vars:
            var.set(False)

    def generate_config(self):
        selected = [cmd for cmd, var in self.check_vars if var.get()]
        if not selected:
            messagebox.showwarning("No Selection", "Please select at least one command.")
            return

        # Show success dialog with only the whitelist array
        whitelist_json = json.dumps(selected, indent=2, ensure_ascii=False)
        self.show_success_dialog(whitelist_json)

    def show_success_dialog(self, whitelist_json):
        """Display the generated whitelist array for manual copying."""
        win = tk.Toplevel(self)
        win.title("Generated Whitelist")
        win.geometry("500x350")
        win.resizable(True, True)

        ttk.Label(
            win,
            text="Copy this whitelist into your run_config.json:",
            font=("Segoe UI", 10)
        ).pack(anchor="w", padx=10, pady=(10, 5))

        txt = scrolledtext.ScrolledText(win, wrap=tk.WORD, height=12, font=("Consolas", 10))
        txt.pack(fill="both", expand=True, padx=10, pady=5)
        txt.insert("1.0", whitelist_json)
        
        # Disable editing after insert
        txt.configure(state="disabled")

        # --- Toolbar with Copy button ---
        toolbar = ttk.Frame(win)
        toolbar.pack(fill="x", padx=10, pady=(0, 5))
        
        def copy_to_clipboard():
            self.clipboard_clear()
            self.clipboard_append(whitelist_json)
            self.update()  # Required on Windows to keep clipboard
            tip_label.config(text="Copied!", foreground="green")
            win.after(1500, lambda: tip_label.config(text="", foreground="black"))

        ttk.Button(toolbar, text="Copy to Clipboard", command=copy_to_clipboard).pack(side="left")
        tip_label = ttk.Label(toolbar, text="")
        tip_label.pack(side="left", padx=(10, 0))

        ttk.Button(win, text="OK", command=win.destroy).pack(pady=10)


def main():
    # Ensure tkinter is available
    try:
        import tkinter
    except ImportError:
        print("ERROR: tkinter is not available. Install it with your Python distribution.")
        sys.exit(1)

    app = WhitelistDialog()
    app.mainloop()


if __name__ == "__main__":
    main()
