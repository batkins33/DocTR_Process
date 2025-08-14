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
from .logging_setup import set_gui_log_widget

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
    def _build_ui(self):
        # Minimal placeholder UI to avoid errors
        # You should add your full UI layout here
        pass
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

        # ---- Log panel ----
        from tkinter.scrolledtext import ScrolledText
        log_frame = tk.Frame(self)
        log_frame.pack(side="bottom", fill="both")
        st = ScrolledText(log_frame, height=12, state="disabled")
        st.pack(fill="both", expand=True)
        set_gui_log_widget(st)
        import logging
        logging.getLogger(__name__).info("GUI log panel attached")

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


def launch_gui() -> None:
    cfg = load_cfg()

    root = tk.Tk()
    root.title("Lindamood Truck Ticket Pipeline")  # <- rename
    root.geometry("820x440")  # <- friendlier default
    root.minsize(720, 360)  # <- keeps layout from collapsing

    # Optional: gentle DPI bump (comment out if it looks too big on your screen)
    try:
        root.tk.call("tk", "scaling", 1.15)
    except tk.TclError:
        pass

    # ttk styling (light, clean)
    style = ttk.Style(root)
    # style.theme_use("clam")  # uncomment if you prefer 'clam' over Windows native
    style.configure("TLabel", padding=(0, 2))
    style.configure("TButton", padding=(10, 6))
    style.configure("TLabelframe", padding=(10, 8))
    style.configure("TLabelframe.Label", padding=(4, 0))

    # wrap the family in braces; without this, Tk splits on the space and misreads "UI" as the size
    root.option_add("*Font", "{Segoe UI} 10")

    # ---- state ----
    input_path = tk.StringVar(value=cfg.get("input_pdf") or cfg.get("input_dir") or "")
    output_dir = tk.StringVar(value=cfg.get("output_dir", "./outputs"))
    engine_var = tk.StringVar(value=cfg.get("ocr_engine", "doctr"))
    orient_var = tk.StringVar(value=cfg.get("orientation_check", "tesseract"))
    run_type_var = tk.StringVar(value=cfg.get("run_type", "initial"))

    out_csv = tk.BooleanVar(value="csv" in cfg.get("output_format", []))
    out_excel = tk.BooleanVar(value="excel" in cfg.get("output_format", []))
    out_pdf = tk.BooleanVar(value="vendor_pdf" in cfg.get("output_format", []))
    out_tiff = tk.BooleanVar(value="vendor_tiff" in cfg.get("output_format", []))
    out_sp = tk.BooleanVar(value="sharepoint" in cfg.get("output_format", []))
    combined_pdf_var = tk.BooleanVar(value=cfg.get("combined_pdf", False))
    status = tk.StringVar(value="")

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

    # ---- layout scaffold (responsive) ----
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    container = ttk.Frame(root, padding=12)
    container.grid(row=0, column=0, sticky="nsew")
    # only column 1 stretches (the text entries)
    for c in (0, 1, 2, 3):
        container.columnconfigure(c, weight=0)
    container.columnconfigure(1, weight=1)

    # ---- (optional) brand header ----
    # Drop a PNG at <repo_root>/branding/lindamood_logo.png to show it.
    logo_path = get_repo_root() / "branding" / "lindamood_logo.png"
    if logo_path.exists():
        logo_img = tk.PhotoImage(file=str(logo_path))
        ttk.Label(container, image=logo_img).grid(
            row=0, column=0, sticky="w", pady=(0, 6)
        )
        container.logo_img = logo_img
        ttk.Label(
            container,
            text="Lindamood Truck Ticket Pipeline",
            font=("Segoe UI", 12, "bold"),  # <- three elements
        ).grid(row=0, column=1, columnspan=3, sticky="w", pady=(2, 6))
        row_offset = 1
    else:
        ttk.Label(
            container,
            text="Lindamood Truck Ticket Pipeline",
            font=("Segoe UI", 12, "bold"),  # <- three elements here too
        ).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 6))
        row_offset = 1

    # ---- Paths group ----
    paths = ttk.LabelFrame(container, text="Paths")
    paths.grid(row=row_offset, column=0, columnspan=4, sticky="ew", pady=(0, 8))
    paths.columnconfigure(0, weight=1)  # entry expands

    # Input path row
    in_entry = ttk.Entry(paths, textvariable=input_path)
    in_entry.grid(row=0, column=0, sticky="ew", padx=(8, 6), pady=(6, 4))
    ttk.Button(paths, text="File", command=browse_file).grid(
        row=0, column=1, padx=(0, 6), pady=(6, 4)
    )
    ttk.Button(paths, text="Folder", command=browse_folder).grid(
        row=0, column=2, padx=(0, 8), pady=(6, 4)
    )

    # Snap view to the end of the path so long paths show the tail
    def _snap_to_end(*_):
        try:
            in_entry.icursor("end")
            in_entry.xview_moveto(1.0)
        except tk.TclError:
            pass

    input_path.trace_add("write", _snap_to_end)

    # Output dir row
    out_entry = ttk.Entry(paths, textvariable=output_dir)
    out_entry.grid(row=1, column=0, sticky="ew", padx=(8, 6), pady=(0, 8))
    ttk.Button(paths, text="Output Dir", command=browse_output_dir).grid(
        row=1, column=1, columnspan=2, padx=(0, 8), pady=(0, 8), sticky="w"
    )

    # ---- Options group ----
    opts = ttk.LabelFrame(container, text="Options")
    opts.grid(row=row_offset + 1, column=0, columnspan=4, sticky="ew")
    for c in (0, 1, 2, 3):
        opts.columnconfigure(c, weight=0)
    opts.columnconfigure(1, weight=1)  # leave room if labels vary

    ttk.Label(opts, text="OCR Engine:").grid(
        row=0, column=0, sticky="w", padx=8, pady=6
    )
    ttk.Combobox(
        opts,
        textvariable=engine_var,
        values=["doctr", "tesseract", "easyocr"],
        width=18,
        state="readonly",
    ).grid(row=0, column=1, sticky="w", padx=(0, 8), pady=6)

    ttk.Label(opts, text="Orientation:").grid(
        row=1, column=0, sticky="w", padx=8, pady=6
    )
    ttk.Combobox(
        opts,
        textvariable=orient_var,
        values=["tesseract", "doctr", "none"],
        width=18,
        state="readonly",
    ).grid(row=1, column=1, sticky="w", padx=(0, 8), pady=6)

    ttk.Label(opts, text="Run Type:").grid(
        row=2, column=0, sticky="w", padx=8, pady=(6, 10)
    )
    ttk.Combobox(
        opts,
        textvariable=run_type_var,
        values=["initial", "validation"],
        width=18,
        state="readonly",
    ).grid(row=2, column=1, sticky="w", padx=(0, 8), pady=(6, 10))

    # ---- Outputs group ----
    fmt = ttk.LabelFrame(container, text="Outputs")
    fmt.grid(row=row_offset + 2, column=0, columnspan=4, sticky="ew", pady=(8, 0))
    for c in (0, 1):
        fmt.columnconfigure(c, weight=1)  # let the grid breathe horizontally

    ttk.Checkbutton(fmt, text="CSV", variable=out_csv).grid(
        row=0, column=0, sticky="w", padx=8, pady=6
    )
    ttk.Checkbutton(fmt, text="Excel", variable=out_excel).grid(
        row=0, column=1, sticky="w", padx=8, pady=6
    )
    ttk.Checkbutton(fmt, text="Vendor PDF", variable=out_pdf).grid(
        row=1, column=0, sticky="w", padx=8, pady=6
    )
    ttk.Checkbutton(fmt, text="Vendor TIFF", variable=out_tiff).grid(
        row=1, column=1, sticky="w", padx=8, pady=6
    )
    ttk.Checkbutton(fmt, text="SharePoint", variable=out_sp).grid(
        row=2, column=0, sticky="w", padx=8, pady=(6, 10)
    )
    ttk.Checkbutton(fmt, text="Combined PDF", variable=combined_pdf_var).grid(
        row=2, column=1, sticky="w", padx=8, pady=(6, 10)
    )

    # ---- Controls & status ----
    controls = ttk.Frame(container)
    controls.grid(row=row_offset + 3, column=0, columnspan=4, sticky="ew", pady=12)
    controls.columnconfigure(0, weight=1)
    controls.columnconfigure(1, weight=0)
    controls.columnconfigure(2, weight=1)

    run_btn = ttk.Button(controls, text="Run Pipeline", command=run_clicked)
    run_btn.grid(row=0, column=1, padx=8)

    progress = ttk.Progressbar(controls, mode="indeterminate", length=220)
    progress.grid(row=1, column=1, pady=(8, 0))
    progress.grid_remove()  # hidden until used

    ttk.Label(container, textvariable=status).grid(
        row=row_offset + 4, column=0, columnspan=4, sticky="w", pady=(0, 6)
    )

    root.mainloop()


if __name__ == "__main__":
    App().mainloop()
