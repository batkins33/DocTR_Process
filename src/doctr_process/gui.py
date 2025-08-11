"""Tkinter GUI for executing the OCR pipeline."""

import os
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

import yaml

from src.doctr_process import pipeline

def get_repo_root() -> Path:
    """Return the absolute path to the repo root (assumes this file is at src/doctr_process/)."""
    return Path(__file__).resolve().parents[2]


# Store GUI settings alongside repository configs
CONFIG_PATH = get_repo_root() / "configs" / "config.yaml"
EXTRACTION_RULES_PATH = get_repo_root() / "configs" / "extraction_rules.yaml"


def load_cfg() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


def save_cfg(cfg: dict) -> None:
    CONFIG_PATH.parent.mkdir(
        parents=True, exist_ok=True
    )  # <-- Ensures 'configs/' exists
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

    # ---- helpers ----
    def browse_file():
        path = filedialog.askopenfilename(
            filetypes=[("Documents", "*.pdf *.tif *.tiff *.jpg *.jpeg *.png")]
        )
        if path:
            input_path.set(path)

    def browse_folder():
        path = filedialog.askdirectory()
        if path:
            input_path.set(path)

    def browse_output_dir():
        path = filedialog.askdirectory()
        if path:
            output_dir.set(path)

    def run_clicked():
        new_cfg = cfg.copy()
        path = input_path.get()
        if os.path.isdir(path):
            new_cfg["input_dir"] = path
            new_cfg["batch_mode"] = True
            new_cfg.pop("input_pdf", None)
        else:
            new_cfg["input_pdf"] = path
            new_cfg["batch_mode"] = False
            new_cfg.pop("input_dir", None)

        new_cfg["output_dir"] = output_dir.get()
        new_cfg["ocr_engine"] = engine_var.get()
        new_cfg["orientation_check"] = orient_var.get()
        new_cfg["run_type"] = run_type_var.get()

        outputs = []
        if out_csv.get():
            outputs.append("csv")
        if out_excel.get():
            outputs.append("excel")
        if out_pdf.get():
            outputs.append("vendor_pdf")
        if out_tiff.get():
            outputs.append("vendor_tiff")
        if out_sp.get():
            outputs.append("sharepoint")
        new_cfg["output_format"] = outputs
        new_cfg["combined_pdf"] = combined_pdf_var.get()

        save_cfg(new_cfg)
        run_btn.config(state="disabled")
        progress.grid()  # show while running
        progress.start(10)
        status.set("Processing...")

        def task():
            try:
                pipeline.run_pipeline()
                status.set("Done")
            except Exception as exc:
                status.set(f"Error: {exc}")
            finally:
                progress.stop()
                progress.grid_remove()
                run_btn.config(state="normal")

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
    launch_gui()
