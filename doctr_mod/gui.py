import os
import threading
import tkinter as tk
from tkinter import filedialog, ttk
from pathlib import Path

import yaml

from doctr_ocr_to_csv import run_pipeline

CONFIG_PATH = Path(__file__).with_name("config.yaml")


def load_cfg() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


def save_cfg(cfg: dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f)


def launch_gui() -> None:
    cfg = load_cfg()

    root = tk.Tk()
    root.title("Ticket OCR Pipeline")
    root.geometry("500x500")

    input_path = tk.StringVar(value=cfg.get("input_pdf") or cfg.get("input_dir") or "")
    output_dir = tk.StringVar(value=cfg.get("output_dir", "./outputs"))
    engine_var = tk.StringVar(value=cfg.get("ocr_engine", "doctr"))
    orient_var = tk.StringVar(value=cfg.get("orientation_check", "tesseract"))

    out_csv = tk.BooleanVar(value="csv" in cfg.get("output_format", []))
    out_excel = tk.BooleanVar(value="excel" in cfg.get("output_format", []))
    out_pdf = tk.BooleanVar(value="vendor_pdf" in cfg.get("output_format", []))
    out_tiff = tk.BooleanVar(value="vendor_tiff" in cfg.get("output_format", []))
    out_sp = tk.BooleanVar(value="sharepoint" in cfg.get("output_format", []))
    combined_pdf_var = tk.BooleanVar(value=cfg.get("combined_pdf", False))

    status = tk.StringVar(value="")

    def browse_file():
        path = filedialog.askopenfilename(filetypes=[("Documents", "*.pdf *.tif *.tiff *.jpg *.jpeg *.png")])
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
        status.set("Processing...")

        def task():
            try:
                run_pipeline()
                status.set("Done")
            except Exception as exc:
                status.set(f"Error: {exc}")
            finally:
                run_btn.config(state="normal")

        threading.Thread(target=task).start()

    # input selection
    frame = tk.Frame(root)
    frame.pack(pady=10)
    # Allow the input path entry to expand so long paths are visible
    tk.Entry(frame, textvariable=input_path).pack(side=tk.LEFT, fill=tk.X, expand=True)
    tk.Button(frame, text="File", command=browse_file).pack(side=tk.LEFT, padx=2)
    tk.Button(frame, text="Folder", command=browse_folder).pack(side=tk.LEFT)

    # output dir
    out_frame = tk.Frame(root)
    out_frame.pack(pady=5)
    # Allow output directory entry to expand dynamically as well
    tk.Entry(out_frame, textvariable=output_dir).pack(side=tk.LEFT, fill=tk.X, expand=True)
    tk.Button(out_frame, text="Output Dir", command=browse_output_dir).pack(side=tk.LEFT)

    # Engine and orientation
    opts_frame = tk.Frame(root)
    opts_frame.pack(pady=5)
    tk.Label(opts_frame, text="OCR Engine:").grid(row=0, column=0, sticky="w")
    ttk.Combobox(opts_frame, textvariable=engine_var, values=["doctr", "tesseract", "easyocr"], width=12).grid(row=0, column=1)
    tk.Label(opts_frame, text="Orientation:").grid(row=1, column=0, sticky="w")
    ttk.Combobox(opts_frame, textvariable=orient_var, values=["tesseract", "doctr", "none"], width=12).grid(row=1, column=1)

    # Output format checkboxes
    fmt_frame = tk.LabelFrame(root, text="Outputs")
    fmt_frame.pack(pady=10, fill="x", padx=5)
    tk.Checkbutton(fmt_frame, text="CSV", variable=out_csv).grid(row=0, column=0, sticky="w")
    tk.Checkbutton(fmt_frame, text="Excel", variable=out_excel).grid(row=0, column=1, sticky="w")
    tk.Checkbutton(fmt_frame, text="Vendor PDF", variable=out_pdf).grid(row=1, column=0, sticky="w")
    tk.Checkbutton(fmt_frame, text="Vendor TIFF", variable=out_tiff).grid(row=1, column=1, sticky="w")
    tk.Checkbutton(fmt_frame, text="SharePoint", variable=out_sp).grid(row=2, column=0, sticky="w")
    tk.Checkbutton(fmt_frame, text="Combined PDF", variable=combined_pdf_var).grid(row=2, column=1, sticky="w")

    # Run button and status
    run_btn = tk.Button(root, text="Run Pipeline", command=run_clicked)
    run_btn.pack(pady=15)
    tk.Label(root, textvariable=status).pack()

    root.mainloop()


if __name__ == "__main__":
    launch_gui()
