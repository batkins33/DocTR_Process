import os

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import logging
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

import yaml

# --- Config Setup ---
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "configs.yaml")

DEFAULT_CONFIG = """\
cache_file: null
keyword_file: ocr_keywords.xlsx
ocr_back_pages: false
output_format: pdf
poppler_path: C:/Poppler/poppler-24.08.0/Library/bin
preprocess:
  grayscale: false
  rotate: true
rename_original: true
source_path:
template_dir: template_dir
template_threshold: 0.85
two_page_scan: false
use_template_fallback: false
"""

if not os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "w") as f:
        f.write(DEFAULT_CONFIG)


def load_config():
    with open(CONFIG_PATH, "r") as file:
        return yaml.safe_load(file)


def save_config(config):
    with open(CONFIG_PATH, "w") as file:
        yaml.dump(config, file)


# --- Threaded Run Handler ---
def threaded_gui_run():
    config = load_config()
    config["source_path"] = selected_path.get()
    config["output_format"] = output_format.get()
    config["preprocess"]["grayscale"] = grayscale.get()
    config["preprocess"]["rotate"] = rotate.get()
    config["two_page_scan"] = two_page_scan.get()
    config["rename_original"] = rename_original.get()
    config["ocr_back_pages"] = ocr_back_pages.get()
    save_config(config)

    run_btn.config(state="disabled")
    status_label.config(text="🟢 Processing...")
    progress["value"] = 0
    progress.update_idletasks()

    def threaded_run():
        try:
            from processor.run import run_input, run_comparison_mode
            def gui_progress(idx, total):
                percent = int(idx / total * 100)
                progress["value"] = percent
                progress.update_idletasks()
            if compare_mode.get():
                run_comparison_mode(selected_path.get(), config)
            else:
                run_input(selected_path.get(), config, progress_callback=gui_progress)
            status_label.config(text="✅ Done!")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            status_label.config(text="❌ Error")
        finally:
            run_btn.config(state="normal")

    threading.Thread(target=threaded_run).start()


# --- GUI ---
def launch_gui():
    logging.basicConfig(level=logging.INFO)
    root = tk.Tk()
    root.title("Lindamood Truck Ticket Sorter")
    root.geometry("600x600")
    root.configure(bg="#F5F5F5")

    global selected_path, output_format, rename_original, rotate
    global two_page_scan, ocr_back_pages, grayscale, compare_mode
    global run_btn, status_label, progress

    selected_path = tk.StringVar()
    output_format = tk.StringVar(value="pdf")
    rename_original = tk.BooleanVar(value=True)
    rotate = tk.BooleanVar(value=True)
    two_page_scan = tk.BooleanVar(value=False)
    ocr_back_pages = tk.BooleanVar(value=False)
    grayscale = tk.BooleanVar(value=False)
    compare_mode = tk.BooleanVar(value=False)

    def browse_file():
        file_paths = filedialog.askopenfilenames(
            filetypes=[("Documents", "*.pdf *.tif *.tiff *.jpg *.jpeg *.png")]
        )
        if file_paths:
            joined_paths = ";".join(file_paths)
            selected_path.set(joined_paths)

    def browse_folder():
        folder = filedialog.askdirectory()
        if folder:
            selected_path.set(folder)

    # 🔷 Header
    tk.Label(root, text="Lindamood Truck Ticket Sorter",
             font=("Segoe UI", 16, "bold"), fg="white", bg="#2599d5",
             padx=10, pady=10).pack(fill="x")

    # 📁 Path selection
    path_frame = tk.Frame(root, bg="#F5F5F5")
    path_frame.pack(pady=50)
    tk.Entry(path_frame, textvariable=selected_path, width=55).pack(side=tk.LEFT)
    tk.Button(path_frame, text="📄 File", command=browse_file).pack(side=tk.LEFT, padx=10)
    tk.Button(path_frame, text="📁 Folder", command=browse_folder).pack(side=tk.LEFT)

    # ⚙️ Settings
    settings_frame = tk.Frame(root, bg="#F5F5F5")
    settings_frame.pack(pady=20)

    options = [
        ("Rename Original File", rename_original),
        ("Rotate", rotate),
        ("Two-Page Scan (Front/Back)", two_page_scan),
        ("OCR Back Pages", ocr_back_pages),
        ("Grayscale", grayscale),
        ("Compare OCR Engines (Benchmark Mode)", compare_mode),
    ]

    for idx, (text, var) in enumerate(options):
        tk.Checkbutton(settings_frame, text=text, variable=var, bg="#F5F5F5").grid(row=idx, column=0, sticky="w")

    tk.Label(settings_frame, text="Output Format:", bg="#F5F5F5").grid(row=6, column=0, sticky="w")
    format_combo = ttk.Combobox(settings_frame, textvariable=output_format, values=["pdf", "tif"], width=10)
    format_combo.grid(row=6, column=1, padx=10)

    # 🔄 Progress
    progress = ttk.Progressbar(root, mode="determinate", maximum=100)
    progress.pack(pady=5)
    status_label = tk.Label(root, text="", font=("Segoe UI", 9), bg="#F5F5F5")
    status_label.pack(pady=2)

    # 🚀 Run Button
    run_btn = tk.Button(
        root,
        text="🚀 Run Sorter",
        command=threaded_gui_run,
        bg="#2599d5", fg="white", activebackground="#002244", activeforeground="white",
        font=("Segoe UI", 10, "bold"), padx=10, pady=5
    )
    run_btn.pack(pady=20)

    root.mainloop()


if __name__ == "__main__":
    launch_gui()
