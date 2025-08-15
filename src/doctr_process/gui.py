# Tkinter GUI for the Lindamood Truck Ticket Pipeline.
#
# This module provides a very small placeholder implementation of the GUI
# application.  The previous revision attempted to call instance methods on
# ``self`` at class definition time which resulted in a ``NameError`` when the
# module was executed.  The class is now structured correctly and the helper
# functions live as instance methods.
#
# The methods defined here are intentionally lightweight so the file can be
# imported without errors.  They can be expanded in the future to provide a full
# user interface.
#

from __future__ import annotations

import json
import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog

import yaml

from doctr_process.path_utils import normalize_single_path
from pipeline import run_pipeline

# Module-level variables
STATE_FILE = Path.home() / ".doctr_gui_state.json"  # Or use .lindamood_ticket_pipeline.json if preferred
CONFIG_PATH = Path("configs/config.yaml")


def get_repo_root():
    """Get repository root directory."""
    return Path(__file__).parent.parent.parent


def set_gui_log_widget(widget):
    """Set the GUI log widget for logging output."""
    pass  # Placeholder implementation


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Lindamood Truck Ticket Pipeline")
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

        # Build UI and bind events
        self._build_ui()
        self._bind_shortcuts()
        self._refresh_path_displays()
        self._validate()
        self.after(120, self._set_initial_focus)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        """Build the complete UI."""
        # Main container
        container = ttk.Frame(self, padding=12)
        container.pack(fill="both", expand=True)

        # Configure grid weights
        container.columnconfigure(1, weight=1)

        # Build UI sections
        self._build_paths_section(container)
        self._build_options_section(container)
        self._build_outputs_section(container)
        self._build_controls_section(container)

    def _build_paths_section(self, parent):
        """Build the paths input section."""
        paths = ttk.LabelFrame(parent, text="Paths")
        paths.pack(fill="x", pady=(0, 8))
        paths.columnconfigure(0, weight=1)

        # Input path
        self.input_entry = ttk.Entry(paths, textvariable=self.input_var)
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=(8, 6), pady=(6, 4))
        ttk.Button(paths, text="File", command=self._browse_file).grid(row=0, column=1, padx=(0, 6), pady=(6, 4))
        ttk.Button(paths, text="Folder", command=self._browse_folder).grid(row=0, column=2, padx=(0, 8), pady=(6, 4))

        # Output path
        self.output_entry = ttk.Entry(paths, textvariable=self.output_var)
        self.output_entry.grid(row=1, column=0, sticky="ew", padx=(8, 6), pady=(0, 8))
        ttk.Button(paths, text="Output Dir", command=self._browse_output_dir).grid(row=1, column=1, columnspan=2,
                                                                                   padx=(0, 8), pady=(0, 8))

    def _build_options_section(self, parent):
        """Build the options section."""
        opts = ttk.LabelFrame(parent, text="Options")
        opts.pack(fill="x", pady=(0, 8))

        ttk.Label(opts, text="OCR Engine:").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        ttk.Combobox(opts, textvariable=self.engine_var, values=["doctr", "tesseract", "easyocr"],
                     state="readonly").grid(row=0, column=1, sticky="w", padx=(0, 8), pady=6)

        ttk.Label(opts, text="Orientation:").grid(row=1, column=0, sticky="w", padx=8, pady=6)
        ttk.Combobox(opts, textvariable=self.orient_var, values=["tesseract", "doctr", "none"], state="readonly").grid(
            row=1, column=1, sticky="w", padx=(0, 8), pady=6)

        ttk.Label(opts, text="Run Type:").grid(row=2, column=0, sticky="w", padx=8, pady=6)
        ttk.Combobox(opts, textvariable=self.run_type_var, values=["initial", "validation"], state="readonly").grid(
            row=2, column=1, sticky="w", padx=(0, 8), pady=6)

    def _build_outputs_section(self, parent):
        """Build the outputs section."""
        fmt = ttk.LabelFrame(parent, text="Outputs")
        fmt.pack(fill="x", pady=(0, 8))

        ttk.Checkbutton(fmt, text="CSV", variable=self.output_vars["csv"]).grid(row=0, column=0, sticky="w", padx=8,
                                                                                pady=6)
        ttk.Checkbutton(fmt, text="Excel", variable=self.output_vars["excel"]).grid(row=0, column=1, sticky="w", padx=8,
                                                                                    pady=6)
        ttk.Checkbutton(fmt, text="Vendor PDF", variable=self.output_vars["vendor_pdf"]).grid(row=1, column=0,
                                                                                              sticky="w", padx=8,
                                                                                              pady=6)
        ttk.Checkbutton(fmt, text="Vendor TIFF", variable=self.output_vars["vendor_tiff"]).grid(row=1, column=1,
                                                                                                sticky="w", padx=8,
                                                                                                pady=6)
        ttk.Checkbutton(fmt, text="SharePoint", variable=self.output_vars["sharepoint"]).grid(row=2, column=0,
                                                                                              sticky="w", padx=8,
                                                                                              pady=6)
        ttk.Checkbutton(fmt, text="Combined PDF", variable=self.output_vars["combined_pdf"]).grid(row=2, column=1,
                                                                                                  sticky="w", padx=8,
                                                                                                  pady=6)

    def _build_controls_section(self, parent):
        """Build the controls section."""
        controls = ttk.Frame(parent)
        controls.pack(fill="x", pady=12)
        controls.columnconfigure(0, weight=1)

        self.run_btn = ttk.Button(controls, text="Run Pipeline", command=self._on_run)
        self.run_btn.pack()

        ttk.Label(parent, textvariable=self.status_var).pack(pady=(0, 6))

    def _bind_shortcuts(self):
        """Bind keyboard shortcuts."""
        self.bind("<Control-Return>", lambda e: self._on_run())

    def _refresh_path_displays(self):
        """Update the path display variables."""
        self.input_var.set(self.input_full)
        self.output_var.set(self.output_full)
        self._validate()

    def _run_done(self, msg):
        """Handle completion of pipeline run."""
        self.status_var.set(msg)
        self.run_btn.config(state="normal")
        self.config(cursor="")

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

    # ---------- Browsers ----------
    def _browse_file(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Documents", "*.pdf *.tif *.tiff *.jpg *.jpeg *.png")])
        if path:
            self.input_full = str(path)  # Ensure string
            self._refresh_path_displays()

    def _browse_folder(self) -> None:
        path = filedialog.askdirectory()
        if path:
            self.input_full = str(path)  # Ensure string
            self._refresh_path_displays()

    def _browse_output_dir(self) -> None:
        path = filedialog.askdirectory()
        if path:
            self.output_full = str(path)  # Ensure string
            self._refresh_path_displays()

    # ---------- Validation / Run ----------
    def _set_initial_focus(self) -> None:
        """Set initial focus to input field."""
        if hasattr(self, 'input_entry'):
            self.input_entry.focus_set()

    def _validate(self, *_: object) -> bool:
        """Validate current input state."""
        valid = bool(self.input_full and self.output_full)
        if hasattr(self, 'run_btn'):
            self.run_btn.config(state="normal" if valid else "disabled")
        return valid

    def _on_run(self) -> None:
        """Execute the pipeline."""
        if not self._validate():
            return

        self._save_state()
        cfg = self._load_cfg()

        try:
            src = normalize_single_path(self.input_full)
            is_dir = False
        except Exception as exc:
            p = Path(str(self.input_full)).expanduser()
            if p.exists() and p.is_dir():
                src = p
                is_dir = True
            else:
                self.status_var.set(str(exc))
                return

        try:
            out_dir = Path(self.output_full).expanduser()
            if not out_dir.exists() or not out_dir.is_dir():
                raise TypeError(f"Not a directory: {out_dir}")
        except Exception as exc:
                            src = str(src)  # Ensure string
                            is_dir = False
            return

        if is_dir:
            cfg["input_dir"] = str(src)

            cfg["batch_mode"] = True
            cfg.pop("input_pdf", None)
        else:
            cfg["input_pdf"] = str(src)
            cfg["batch_mode"] = False
            cfg.pop("input_dir", None)

        cfg["output_dir"] = str(out_dir)

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
                run_pipeline(CONFIG_PATH)
                msg = "Done"
            except Exception as exc:
                msg = f"Error: {exc}"
            self.after(0, lambda: self._run_done(msg))

        threading.Thread(target=task, daemon=True).start()

    def _on_close(self) -> None:
        self._save_state()
        self.destroy()


def main():
    """Main entry point for the GUI application."""
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
