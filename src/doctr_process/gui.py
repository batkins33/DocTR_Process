"""Tkinter GUI for the Lindamood Truck Ticket Pipeline.

This module provides a very small placeholder implementation of the GUI
application.  The previous revision attempted to call instance methods on
``self`` at class definition time which resulted in a ``NameError`` when the
module was executed.  The class is now structured correctly and the helper
functions live as instance methods.

The methods defined here are intentionally lightweight so the file can be
imported without errors.  They can be expanded in the future to provide a full
user interface.
"""

from __future__ import annotations

import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk

import yaml

from doctr_process.logging_setup import set_gui_log_widget

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
    """Placeholder application class.

    The layout and behaviour are intentionally minimal.  The goal is to provide
    a valid ``Tk`` application object so that the module can be executed and
    extended without raising errors.
    """

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

        # Finish initial setup
        self._build_ui()
        self._bind_shortcuts()
        self._refresh_path_displays()
        self._validate()
        self.after(120, self._set_initial_focus)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    # UI helpers
    def _build_ui(self) -> None:
        """Construct widgets.  Placeholder to avoid errors."""
        pass

    def _bind_shortcuts(self) -> None:
        """Bind keyboard shortcuts.  Placeholder."""
        pass

    def _refresh_path_displays(self) -> None:
        """Update any path entry widgets.  Placeholder."""
        self.input_var.set(self.input_full)
        self.output_var.set(self.output_full)

    def _validate(self, *_: object) -> bool:
        """Validate user input.  Placeholder always returning ``True``."""
        return True

    def _set_initial_focus(self) -> None:
        """Set initial focus when the window opens."""
        self.focus_set()

    def _on_close(self) -> None:
        """Persist state and close the window."""
        self._save_state()
        self.destroy()

    # ------------------------------------------------------------------
    # State helpers
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


if __name__ == "__main__":  # pragma: no cover - manual invocation
    App().mainloop()

