"""Tkinter GUI for the Lindamood Truck Ticket Pipeline.

This version keeps the window compact, makes the Run/Cancel buttons
always visible via a sticky bottom action bar, and shows FULL input/output
paths without manual truncation. The path entries auto-scroll so the tail
(filename) stays visible in tight layouts. State persists to a JSON file
in the user's home directory.
"""
from __future__ import annotations

import json
import os
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

import yaml

from doctr_process import pipeline

STATE_FILE = Path.home() / ".lindamood_ticket_pipeline.json"
ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT_DIR / "configs" / "config.yaml"


class ToolTip:
    """Simple hover tooltip for a widget."""

    def __init__(self, widget: tk.Widget, text: str = "") -> None:
        self.widget = widget
        self.text = text
        self._tw: tk.Toplevel | None = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, _evt: tk.Event) -> None:
        if self._tw or not self.text:
            return
        x = self.widget.winfo_rootx() + 18
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 10
        tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        ttk.Label(tw, text=self.text, relief="solid", borderwidth=1, padding=(4, 2)).pack()
        self._tw = tw

    def _hide(self, _evt: tk.Event) -> None:
        if self._tw is not None:
            self._tw.destroy()
            self._tw = None


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Lindamood Truck Ticket Pipeline")
        # Keep roughly same size as your screenshot
        self.geometry("820x480")
        self.minsize(520, 360)

        # Load persisted state
        self.state_data = self._load_state()

        # Tk variables & state
        self.input_full = self.state_data.get("input_path", "")
        self.output_full = self.state_data.get("output_dir", "")
        self.input_var = tk.StringVar()
        self.output_var = tk.StringVar()

        self.engine_var = tk.StringVar(value=self.state_data.get("ocr_engine", "doctr"))
        self.orient_var = tk.StringVar(value=self.state_data.get("orientation", "tesseract"))
        self.run_type_var = tk.StringVar(value=self.state_data.get("run_type", "initial"))
        outputs = set(self.state_data.get("outputs", []))
        self.output_vars = {
            "csv": tk.BooleanVar(value="csv" in outputs),
            "excel": tk.BooleanVar(value="excel" in outputs),
            "vendor_pdf": tk.BooleanVar(value="vendor_pdf" in outputs),
            "vendor_tiff": tk.BooleanVar(value="vendor_tiff" in outputs),
            "combined_pdf": tk.BooleanVar(value="combined_pdf" in outputs),
            "sharepoint": tk.BooleanVar(value="sharepoint" in outputs),
        }
        self.status_var = tk.StringVar(value="Ready…")

        # Build UI
        self._build_ui()
        self._bind_shortcuts()
        self._refresh_path_displays()
        self._validate()
        self.after(120, self._set_initial_focus)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---------- State ----------
    def _load_state(self) -> dict:
        try:
            with STATE_FILE.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_state(self) -> None:
        data = {
            "input_path": self.input_full,
            "output_dir": self.output_full,
            "ocr_engine": self.engine_var.get(),
            "orientation": self.orient_var.get(),
            "run_type": self.run_type_var.get(),
            "outputs": [name for name, var in self.output_vars.items() if var.get()],
        }
        try:
            with STATE_FILE.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def _load_cfg(self) -> dict:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        return {}

    def _save_cfg(self, cfg: dict) -> None:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            yaml.safe_dump(cfg, f)

    # ---------- UI ----------
    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        main = ttk.Frame(self)
        main.grid(row=0, column=0, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(0, weight=1)  # scrollable content
        main.rowconfigure(1, weight=0)  # status row
        main.rowconfigure(2, weight=0)  # action bar

        # Scrollable content area
        self.content_canvas = tk.Canvas(main, highlightthickness=0)
        self.content_canvas.grid(row=0, column=0, sticky="nsew")
        vsb = ttk.Scrollbar(main, orient="vertical", command=self.content_canvas.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        self.content_canvas.configure(yscrollcommand=vsb.set)

        self.scroll_frame = ttk.Frame(self.content_canvas)
        self._scroll_window = self.content_canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: self.content_canvas.configure(scrollregion=self.content_canvas.bbox("all")),
        )
        self.content_canvas.bind(
            "<Configure>",
            lambda e: self.content_canvas.itemconfig(self._scroll_window, width=e.width),
        )
        # Mouse wheel
        self.content_canvas.bind_all("<MouseWheel>", self._on_mousewheel)  # Windows/mac
        self.content_canvas.bind_all("<Button-4>", self._on_mousewheel)    # Linux up
        self.content_canvas.bind_all("<Button-5>", self._on_mousewheel)    # Linux down

        # Title
        row = 0
        ttk.Label(
            self.scroll_frame,
            text="Lindamood Truck Ticket Pipeline",
            font=("Segoe UI", 12, "bold"),
        ).grid(row=row, column=0, sticky="w", padx=10, pady=(10, 4))
        row += 1
        ttk.Separator(self.scroll_frame).grid(row=row, column=0, sticky="ew", padx=10)
        row += 1

        # Paths
        paths = ttk.LabelFrame(self.scroll_frame, text="Paths", padding=(10, 8))
        paths.grid(row=row, column=0, sticky="ew", padx=10, pady=8)
        paths.columnconfigure(0, weight=1)

        self.input_entry = ttk.Entry(paths, textvariable=self.input_var, state="readonly")
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6), pady=(0, 4))
        ttk.Button(paths, text="File", command=self._browse_file).grid(row=0, column=1, padx=(0, 6), pady=(0, 4))
        ttk.Button(paths, text="Folder", command=self._browse_folder).grid(row=0, column=2, pady=(0, 4))

        self.output_entry = ttk.Entry(paths, textvariable=self.output_var, state="readonly")
        self.output_entry.grid(row=1, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(paths, text="Browse", command=self._browse_output_dir).grid(row=1, column=1, columnspan=2, sticky="w")

        # Tooltips on full paths
        self.input_tip = ToolTip(self.input_entry, self.input_full)
        self.output_tip = ToolTip(self.output_entry, self.output_full)

        # When the variables change or the entries resize, snap view to the end so the tail is visible
        self.input_var.trace_add("write", lambda *_: self._snap_to_end(self.input_entry))
        self.output_var.trace_add("write", lambda *_: self._snap_to_end(self.output_entry))
        self.input_entry.bind("<Configure>", lambda _e: self._snap_to_end(self.input_entry))
        self.output_entry.bind("<Configure>", lambda _e: self._snap_to_end(self.output_entry))

        row += 1

        # Options
        opts = ttk.LabelFrame(self.scroll_frame, text="Options", padding=(10, 8))
        opts.grid(row=row, column=0, sticky="ew", padx=10, pady=8)
        opts.columnconfigure(1, weight=1)

        ttk.Label(opts, text="OCR Engine:").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Combobox(opts, textvariable=self.engine_var, values=["doctr", "tesseract"], state="readonly").grid(
            row=0, column=1, sticky="ew", pady=2
        )

        ttk.Label(opts, text="Orientation:").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Combobox(opts, textvariable=self.orient_var, values=["tesseract", "doctr", "none"], state="readonly").grid(
            row=1, column=1, sticky="ew", pady=2
        )

        ttk.Label(opts, text="Run Type:").grid(row=2, column=0, sticky="w", pady=2)
        ttk.Combobox(opts, textvariable=self.run_type_var, values=["initial", "re-run"], state="readonly").grid(
            row=2, column=1, sticky="ew", pady=2
        )

        row += 1

        # Outputs
        outs = ttk.LabelFrame(self.scroll_frame, text="Outputs", padding=(10, 8))
        outs.grid(row=row, column=0, sticky="ew", padx=10, pady=8)
        outs.columnconfigure(0, weight=1)
        outs.columnconfigure(1, weight=1)

        ttk.Checkbutton(outs, text="CSV", variable=self.output_vars["csv"]).grid(row=0, column=0, sticky="w", pady=2)
        ttk.Checkbutton(outs, text="Excel", variable=self.output_vars["excel"]).grid(row=0, column=1, sticky="w", pady=2)
        ttk.Checkbutton(outs, text="Vendor PDF", variable=self.output_vars["vendor_pdf"]).grid(row=1, column=0, sticky="w", pady=2)
        ttk.Checkbutton(outs, text="Vendor TIFF", variable=self.output_vars["vendor_tiff"]).grid(row=1, column=1, sticky="w", pady=2)
        ttk.Checkbutton(outs, text="Combined PDF", variable=self.output_vars["combined_pdf"]).grid(row=2, column=0, sticky="w", pady=2)
        ttk.Checkbutton(outs, text="SharePoint", variable=self.output_vars["sharepoint"]).grid(row=2, column=1, sticky="w", pady=2)

        # Status row (above action bar)
        ttk.Label(main, textvariable=self.status_var, anchor="w").grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(4, 2))

        # Action bar (sticky bottom)
        action = ttk.Frame(main, padding=(10, 5))
        action.grid(row=2, column=0, columnspan=2, sticky="ew")
        action.columnconfigure(0, weight=1)  # spacer pushes buttons right

        self.cancel_btn = ttk.Button(action, text="Cancel", command=self._on_cancel)
        self.cancel_btn.grid(row=0, column=1, padx=(0, 6))
        self.run_btn = ttk.Button(action, text="Run", command=self._on_run, state="disabled")
        self.run_btn.grid(row=0, column=2)

    # ---------- Helpers ----------
    def _bind_shortcuts(self) -> None:
        self.bind("<Control-Return>", lambda _e: self._on_run())
        self.bind("<Escape>", lambda _e: self._on_cancel())

    def _on_mousewheel(self, event: tk.Event) -> None:
        # Windows/Mac send event.delta, Linux sends Button-4/5 with num
        if getattr(event, "num", None) == 5 or getattr(event, "delta", 0) < 0:
            self.content_canvas.yview_scroll(1, "units")
        elif getattr(event, "num", None) == 4 or getattr(event, "delta", 0) > 0:
            self.content_canvas.yview_scroll(-1, "units")

    def _snap_to_end(self, entry: ttk.Entry) -> None:
        try:
            entry.icursor("end")
            entry.xview_moveto(1.0)
        except tk.TclError:
            pass

    def _refresh_path_displays(self) -> None:
        # Show FULL paths; keep tooltips synced; snap view so filename tail is visible
        self.input_var.set(self.input_full or "")
        self.output_var.set(self.output_full or "")
        self.input_tip.text = self.input_full
        self.output_tip.text = self.output_full
        self._snap_to_end(self.input_entry)
        self._snap_to_end(self.output_entry)
        self._validate()

    # ---------- Browsers ----------
    def _browse_file(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Documents", "*.pdf *.tif *.tiff *.jpg *.jpeg *.png")])
        if path:
            self.input_full = path
            self._refresh_path_displays()

    def _browse_folder(self) -> None:
        path = filedialog.askdirectory()
        if path:
            self.input_full = path
            self._refresh_path_displays()

    def _browse_output_dir(self) -> None:
        path = filedialog.askdirectory()
        if path:
            self.output_full = path
            self._refresh_path_displays()

    # ---------- Validation / Run ----------
    def _set_initial_focus(self) -> None:
        if not self.input_full:
            self.focus_set()
            return self.input_entry.focus_set()
        if not self.output_full:
            return self.output_entry.focus_set()
        return self.run_btn.focus_set()

    def _validate(self, *_: object) -> bool:
        msg = "Ready…"
        ok = True
        if not self.input_full:
            msg = "Select an input path"
            ok = False
        elif not os.path.exists(self.input_full):
            msg = "Input path not found"
            ok = False
        elif not self.output_full:
            msg = "Select an output directory"
            ok = False
        self.run_btn.config(state=("normal" if ok else "disabled"))
        self.status_var.set(msg)
        return ok

    def _on_run(self) -> None:
        if not self._validate():
            return
        self._save_state()

        cfg = self._load_cfg()
        path = self.input_full
        if os.path.isdir(path):
            cfg["input_dir"] = path
            cfg["batch_mode"] = True
            cfg.pop("input_pdf", None)
        else:
            cfg["input_pdf"] = path
            cfg["batch_mode"] = False
            cfg.pop("input_dir", None)
        cfg["output_dir"] = self.output_full
        cfg["ocr_engine"] = self.engine_var.get()
        cfg["orientation_check"] = self.orient_var.get()
        cfg["run_type"] = self.run_type_var.get()
        outputs = [name for name, var in self.output_vars.items() if var.get() and name != "combined_pdf"]
        cfg["output_format"] = outputs
        cfg["combined_pdf"] = self.output_vars["combined_pdf"].get()
        self._save_cfg(cfg)

        self.status_var.set("Running…")
        self.run_btn.config(state="disabled")
        self.config(cursor="wait")

        def task() -> None:
            try:
                pipeline.run_pipeline(CONFIG_PATH)
                msg = "Done"
            except Exception as exc:  # pragma: no cover - best effort UI error
                msg = f"Error: {exc}"
            self.after(0, lambda: self._run_done(msg))

        threading.Thread(target=task, daemon=True).start()

    def _run_done(self, msg: str = "Ready…") -> None:
        self.status_var.set(msg)
        self.run_btn.config(state="normal")
        self.config(cursor="")

    def _on_cancel(self) -> None:
        self._on_close()

    def _on_close(self) -> None:
        self._save_state()
        self.destroy()


def main() -> None:
    App().mainloop()


if __name__ == "__main__":
    main()
