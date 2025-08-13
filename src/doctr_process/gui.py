"""Modern Tkinter GUI for the OCR pipeline.

Implements a fixed bottom action bar with a scrollable content area so the
Run button remains visible even on small screens.
"""

from __future__ import annotations

import json
import os
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk
from typing import Callable

CONFIG_FILE = Path.home() / ".lindamood_ticket_pipeline.json"


def _truncate(path: str, maxlen: int = 60) -> str:
    """Return a truncated version of *path* with an ellipsis if needed."""
    return path if len(path) <= maxlen else f"...{path[-(maxlen - 3):]}"


class ToolTip:
    """Very small tooltip implementation."""

    def __init__(self, widget: tk.Widget, textfunc: Callable[[], str]) -> None:
        self.widget = widget
        self.textfunc = textfunc
        self.tip: tk.Toplevel | None = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, _event=None) -> None:  # pragma: no cover - UI behaviour
        if self.tip:
            return
        text = self.textfunc()
        if not text:
            return
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry("+%d+%d" % (self.widget.winfo_pointerx() + 10, self.widget.winfo_pointery() + 10))
        label = ttk.Label(self.tip, text=text, relief="solid", borderwidth=1)
        label.pack(ipadx=4, ipady=2)

    def hide(self, _event=None) -> None:  # pragma: no cover - UI behaviour
        if self.tip:
            self.tip.destroy()
            self.tip = None


def create_tooltip(widget: tk.Widget, textfunc: Callable[[], str]) -> None:
    ToolTip(widget, textfunc)


class App(tk.Tk):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Lindamood Truck Ticket Pipeline")
        self.geometry("820x440")
        self.minsize(640, 360)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.state: dict[str, object] = {}
        self.load_state()

        self.build_ui()
        self.bind_shortcuts()
        self.validate()
        self.focus_initial()

    # ------------------------------------------------------------------
    # state persistence
    def load_state(self) -> None:
        if CONFIG_FILE.exists():
            try:
                self.state = json.loads(CONFIG_FILE.read_text())
            except json.JSONDecodeError:
                self.state = {}

    def save_state(self) -> None:
        data = {
            "input_path": self.input_path.get(),
            "output_dir": self.output_dir.get(),
            "ocr_engine": self.engine_var.get(),
            "orientation": self.orient_var.get(),
            "run_type": self.run_type_var.get(),
            "out_csv": self.out_csv.get(),
            "out_excel": self.out_excel.get(),
            "out_vendor_pdf": self.out_vendor_pdf.get(),
            "out_vendor_tiff": self.out_vendor_tiff.get(),
            "out_sharepoint": self.out_sharepoint.get(),
            "out_combined_pdf": self.out_combined_pdf.get(),
        }
        CONFIG_FILE.write_text(json.dumps(data, indent=2))

    # ------------------------------------------------------------------
    # UI construction
    def build_ui(self) -> None:
        main = ttk.Frame(self)
        main.grid(row=0, column=0, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(0, weight=1)

        # --- scrollable content ------------------------------------------------
        self.content_canvas = tk.Canvas(main, highlightthickness=0)
        self.content_canvas.grid(row=0, column=0, sticky="nsew")
        vsb = ttk.Scrollbar(main, orient="vertical", command=self.content_canvas.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        self.content_canvas.configure(yscrollcommand=vsb.set)

        self.scroll_frame = ttk.Frame(self.content_canvas)
        self.content_canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.scroll_frame.bind(
            "<Configure>",
            lambda e: self.content_canvas.configure(scrollregion=self.content_canvas.bbox("all")),
        )

        # mouse wheel scrolling
        self.content_canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.content_canvas.bind_all("<Button-4>", lambda e: self.content_canvas.yview_scroll(-1, "units"))
        self.content_canvas.bind_all("<Button-5>", lambda e: self.content_canvas.yview_scroll(1, "units"))

        row = 0
        ttk.Label(
            self.scroll_frame,
            text="Lindamood Truck Ticket Pipeline",
            font=("Segoe UI", 12, "bold"),
        ).grid(row=row, column=0, sticky="w", padx=10, pady=(10, 4))
        row += 1
        ttk.Separator(self.scroll_frame, orient="horizontal").grid(
            row=row, column=0, sticky="ew", padx=10, pady=(0, 8)
        )
        row += 1

        # --- Paths --------------------------------------------------------------
        paths = ttk.LabelFrame(self.scroll_frame, text="Paths")
        paths.grid(row=row, column=0, sticky="ew", padx=10, pady=8)
        paths.columnconfigure(0, weight=1)

        self.input_path = tk.StringVar(value=str(self.state.get("input_path", "")))
        self.input_display = tk.StringVar()
        self._update_input_display()
        in_entry = ttk.Entry(paths, textvariable=self.input_display, state="readonly")
        in_entry.grid(row=0, column=0, sticky="ew", padx=(10, 4), pady=(10, 4))
        create_tooltip(in_entry, lambda: self.input_path.get())
        self.file_btn = ttk.Button(paths, text="File", command=self.browse_file)
        self.file_btn.grid(row=0, column=1, padx=(0, 4), pady=(10, 4))
        self.dir_btn = ttk.Button(paths, text="Folder", command=self.browse_folder)
        self.dir_btn.grid(row=0, column=2, padx=(0, 10), pady=(10, 4))

        self.output_dir = tk.StringVar(value=str(self.state.get("output_dir", "")))
        self.out_display = tk.StringVar()
        self._update_output_display()
        out_entry = ttk.Entry(paths, textvariable=self.out_display, state="readonly")
        out_entry.grid(row=1, column=0, sticky="ew", padx=(10, 4), pady=(0, 10))
        create_tooltip(out_entry, lambda: self.output_dir.get())
        self.out_btn = ttk.Button(paths, text="Browse", command=self.browse_output_dir)
        self.out_btn.grid(row=1, column=1, columnspan=2, padx=(0, 10), pady=(0, 10), sticky="w")

        row += 1

        # --- Options ------------------------------------------------------------
        opts = ttk.LabelFrame(self.scroll_frame, text="Options")
        opts.grid(row=row, column=0, sticky="ew", padx=10, pady=8)
        opts.columnconfigure(1, weight=1)

        ttk.Label(opts, text="OCR Engine:").grid(row=0, column=0, sticky="w", padx=10, pady=(10, 4))
        self.engine_var = tk.StringVar(value=self.state.get("ocr_engine", "doctr"))
        ttk.Combobox(
            opts,
            textvariable=self.engine_var,
            values=["doctr", "tesseract"],
            state="readonly",
        ).grid(row=0, column=1, sticky="ew", padx=10, pady=(10, 4))

        ttk.Label(opts, text="Orientation:").grid(row=1, column=0, sticky="w", padx=10, pady=4)
        self.orient_var = tk.StringVar(value=self.state.get("orientation", "auto"))
        ttk.Combobox(
            opts,
            textvariable=self.orient_var,
            values=["auto", "tesseract", "none"],
            state="readonly",
        ).grid(row=1, column=1, sticky="ew", padx=10, pady=4)

        ttk.Label(opts, text="Run Type:").grid(row=2, column=0, sticky="w", padx=10, pady=(4, 10))
        self.run_type_var = tk.StringVar(value=self.state.get("run_type", "initial"))
        ttk.Combobox(
            opts,
            textvariable=self.run_type_var,
            values=["initial", "re-run"],
            state="readonly",
        ).grid(row=2, column=1, sticky="ew", padx=10, pady=(4, 10))

        row += 1

        # --- Outputs ------------------------------------------------------------
        outs = ttk.LabelFrame(self.scroll_frame, text="Outputs")
        outs.grid(row=row, column=0, sticky="ew", padx=10, pady=8)
        for c in range(2):
            outs.columnconfigure(c, weight=1)

        self.out_csv = tk.BooleanVar(value=bool(self.state.get("out_csv", False)))
        self.out_excel = tk.BooleanVar(value=bool(self.state.get("out_excel", False)))
        self.out_vendor_pdf = tk.BooleanVar(value=bool(self.state.get("out_vendor_pdf", False)))
        self.out_vendor_tiff = tk.BooleanVar(value=bool(self.state.get("out_vendor_tiff", False)))
        self.out_sharepoint = tk.BooleanVar(value=bool(self.state.get("out_sharepoint", False)))
        self.out_combined_pdf = tk.BooleanVar(value=bool(self.state.get("out_combined_pdf", False)))

        ttk.Checkbutton(outs, text="CSV", variable=self.out_csv).grid(
            row=0, column=0, sticky="w", padx=10, pady=(10, 4)
        )
        ttk.Checkbutton(outs, text="Excel", variable=self.out_excel).grid(
            row=0, column=1, sticky="w", padx=10, pady=(10, 4)
        )
        ttk.Checkbutton(outs, text="Vendor PDF", variable=self.out_vendor_pdf).grid(
            row=1, column=0, sticky="w", padx=10, pady=4
        )
        ttk.Checkbutton(outs, text="Vendor TIFF", variable=self.out_vendor_tiff).grid(
            row=1, column=1, sticky="w", padx=10, pady=4
        )
        ttk.Checkbutton(outs, text="SharePoint", variable=self.out_sharepoint).grid(
            row=2, column=0, sticky="w", padx=10, pady=(4, 10)
        )
        ttk.Checkbutton(outs, text="Combined PDF", variable=self.out_combined_pdf).grid(
            row=2, column=1, sticky="w", padx=10, pady=(4, 10)
        )

        # --- Status label ------------------------------------------------------
        self.status = tk.StringVar(value="Ready…")
        self.status_label = ttk.Label(main, textvariable=self.status, anchor="w")
        self.status_label.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 4))

        # --- Action bar --------------------------------------------------------
        action = ttk.Frame(main)
        action.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
        action.columnconfigure(0, weight=1)
        ttk.Label(action).grid(row=0, column=0)
        self.run_btn = ttk.Button(action, text="Run", command=self.on_run)
        self.run_btn.grid(row=0, column=1, padx=(0, 5))
        ttk.Button(action, text="Cancel", command=self.on_cancel).grid(row=0, column=2)

    # ------------------------------------------------------------------
    # browsing helpers
    def browse_file(self) -> None:
        path = filedialog.askopenfilename(
            filetypes=[("Documents", "*.pdf *.tif *.tiff *.jpg *.jpeg *.png")]
        )
        if path:
            self.input_path.set(path)
            self._update_input_display()
            self.validate()

    def browse_folder(self) -> None:
        path = filedialog.askdirectory()
        if path:
            self.input_path.set(path)
            self._update_input_display()
            self.validate()

    def browse_output_dir(self) -> None:
        path = filedialog.askdirectory()
        if path:
            self.output_dir.set(path)
            self._update_output_display()
            self.validate()

    def _update_input_display(self) -> None:
        self.input_display.set(_truncate(self.input_path.get()))

    def _update_output_display(self) -> None:
        self.out_display.set(_truncate(self.output_dir.get()))

    # ------------------------------------------------------------------
    # validation & actions
    def validate(self, *_args) -> None:
        valid = Path(self.input_path.get()).exists() and bool(self.output_dir.get())
        self.run_btn.state(["!disabled"] if valid else ["disabled"])
        self.status.set("Ready…" if valid else "Select input and output paths")

    def on_run(self) -> None:
        self.status.set("Running…")
        self.run_btn.state(["disabled"])

        # mock long running task
        self.after(1500, self._finish_run)

    def _finish_run(self) -> None:
        self.status.set("Done")
        self.run_btn.state(["!disabled"])

    def on_cancel(self) -> None:
        self.save_state()
        self.destroy()

    def bind_shortcuts(self) -> None:
        self.bind("<Control-Return>", lambda _e: self.on_run())
        self.bind("<Escape>", lambda _e: self.on_cancel())

    def focus_initial(self) -> None:
        if not self.input_path.get():
            self.file_btn.focus_set()
        elif not self.output_dir.get():
            self.out_btn.focus_set()
        else:
            self.run_btn.focus_set()

    def _on_mousewheel(self, event) -> None:  # pragma: no cover - UI behaviour
        if os.name == "nt":
            self.content_canvas.yview_scroll(int(-event.delta / 120), "units")
        else:
            self.content_canvas.yview_scroll(int(-event.delta), "units")


def launch_gui() -> None:
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_cancel)
    app.mainloop()


if __name__ == "__main__":  # pragma: no cover - manual use
    launch_gui()
