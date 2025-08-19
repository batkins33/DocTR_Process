# Tkinter GUI for the Lindamood Truck Ticket Pipeline.

from __future__ import annotations

import json
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog

import yaml

from doctr_process.pipeline import run_pipeline
from doctr_process.utils.resources import as_path


# Module-level variables
STATE_FILE = Path.home() / ".doctr_gui_state.json"

# Get config path using context manager
with as_path("config.yaml") as config_path:
    CONFIG_PATH = Path(config_path)

def set_gui_log_widget(widget):
    """Set the GUI log widget for logging output."""
    pass  # Placeholder implementation


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Lindamood Truck Ticket Pipeline")
        self.geometry("1000x600")
        self.minsize(800, 480)

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

        # Build UI and bind events
        self._build_ui()
        
        # ---- Log panel ----
        from tkinter.scrolledtext import ScrolledText

        log_frame = tk.Frame(self)
        log_frame.pack(side="bottom", fill="both", expand=True)
        st = ScrolledText(log_frame, height=8, state="disabled")
        st.pack(fill="both", expand=True)
        set_gui_log_widget(st)
        import logging
        logging.getLogger(__name__).info("GUI log panel attached")
        self._bind_shortcuts()
        self._refresh_path_displays()
        self._validate()
        self.after(120, self._set_initial_focus)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        """Build the complete UI."""
        # Main container
        container = ttk.Frame(self, padding=12)
        container.pack(fill="x", side="top")

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
        self._create_tooltip(self.input_entry, lambda: self.input_full)
        ttk.Button(paths, text="File", command=self._browse_file).grid(row=0, column=1, padx=(0, 6), pady=(6, 4))
        ttk.Button(paths, text="Folder", command=self._browse_folder).grid(row=0, column=2, padx=(0, 8), pady=(6, 4))

        # Output path
        self.output_entry = ttk.Entry(paths, textvariable=self.output_var)
        self.output_entry.grid(row=1, column=0, sticky="ew", padx=(8, 6), pady=(0, 8))
        self._create_tooltip(self.output_entry, lambda: self.output_full)
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

    def _create_tooltip(self, widget, text_func):
        """Create tooltip for widget showing full path."""
        def on_enter(event):
            text = text_func()
            if text and len(text) > 50:
                tooltip = tk.Toplevel()
                tooltip.wm_overrideredirect(True)
                tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
                label = tk.Label(tooltip, text=text, background="lightyellow", relief="solid", borderwidth=1)
                label.pack()
                widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

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
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        if CONFIG_PATH.exists():
            with open(str(CONFIG_PATH), "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                # yaml.safe_load can return None (e.g. empty file) or a non-dict
                # Ensure we always return a dict so callers can safely assign keys
                if data is None:
                    return {}
                if not isinstance(data, dict):
                    return {}
                return data
        return {}

    def _save_cfg(self, cfg: dict) -> None:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(str(CONFIG_PATH), "w", encoding="utf-8") as f:
            yaml.safe_dump(cfg, f)

    # ---------- Browsers ----------
    def _browse_file(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Documents", "*.pdf *.tif *.tiff *.jpg *.jpeg *.png")])
        if path:
            self.input_full = str(path)
            self._refresh_path_displays()

    def _browse_folder(self) -> None:
        path = filedialog.askdirectory()
        if path:
            self.input_full = str(path)
            self._refresh_path_displays()

    def _browse_output_dir(self) -> None:
        path = filedialog.askdirectory()
        if path:
            try:
                # Auto-create the directory if it doesn't exist
                Path(path).mkdir(parents=True, exist_ok=True)
                self.output_full = str(path)
                self._refresh_path_displays()
            except Exception as e:
                self.status_var.set(f"Cannot create output directory: {e}")

    # ---------- Validation / Run ----------
    def _set_initial_focus(self) -> None:
        """Set initial focus to input field."""
        if hasattr(self, 'input_entry'):
            self.input_entry.focus_set()

    def _validate(self, *_: object) -> bool:
        """Validate current input state."""
        input_valid = bool(self.input_full)
        output_valid = bool(self.output_full)
        
        # Check if input exists
        if input_valid:
            try:
                input_path = Path(self.input_full).expanduser().resolve()
                input_valid = input_path.exists()
            except:
                input_valid = False
        
        valid = input_valid and output_valid
        if hasattr(self, 'run_btn'):
            self.run_btn.config(state="normal" if valid else "disabled")
        return valid

    def _on_run(self) -> None:
        """Execute the pipeline."""
        if not self._validate():
            return

        self._save_state()
        cfg = self._load_cfg()

        # Handle input path
        try:
            p = Path(str(self.input_full)).expanduser().resolve()
            if not p.exists():
                self.status_var.set(f"Input path does not exist: {p}")
                return
            src = str(p)
            is_dir = p.is_dir()
        except Exception as exc:
            self.status_var.set(f"Invalid input path: {exc}")
            return

        # Handle output path
        try:
            out_dir = Path(self.output_full).expanduser().resolve()
            out_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            self.status_var.set(f"Cannot create output directory: {exc}")
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
                run_pipeline(str(CONFIG_PATH))
                msg = "Done"
            except Exception as exc:
                import traceback
                error_details = traceback.format_exc()
                print(f"Pipeline error: {error_details}")
                msg = f"Error: {exc}"
            self.after(0, lambda: self._run_done(msg))

        threading.Thread(target=task, daemon=True).start()

    def _on_close(self) -> None:
        self._save_state()
        self.destroy()


def main():
    """Main entry point for the GUI application."""
    import signal
    
    app = App()
    
    def signal_handler(signum, frame):
        """Handle shutdown signals gracefully."""
        app._on_close()
        sys.exit(0)
    
    # Register signal handlers for clean shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        app.mainloop()
    except KeyboardInterrupt:
        app._on_close()


if __name__ == "__main__":
    main()