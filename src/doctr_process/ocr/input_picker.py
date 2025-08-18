import argparse
import os

# Conditionally import tkinter only when needed
try:
    import tkinter as tk
    from tkinter import filedialog
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="PDF file or directory")
    # ignore unknown args like pytest’s -q, -k, etc.
    args, _ = parser.parse_known_args(argv)
    return args


def pick_file_or_folder():
    """Pick a file or folder using GUI dialog or console input."""
    if not HAS_TKINTER:
        # Fallback to console input when tkinter is not available
        print("GUI not available. Please specify input using --input argument.")
        return None
        
    root = tk.Tk()
    root.withdraw()  # Hide main window
    choice = input("Pick [F]ile or [D]irectory? ").strip().lower()
    if choice == "f":
        return filedialog.askopenfilename(title="Select input PDF or image file")
    elif choice == "d":
        return filedialog.askdirectory(title="Select input directory")
    else:
        print("Invalid choice.")
        return None


def resolve_input(cfg):
    """Resolve the input path from CLI args, config or a GUI picker."""
    # Parse known CLI args but ignore unknown ones (e.g. from pytest)
    args = parse_args()
    # Prefer command-line, then config, then GUI picker
    input_path = args.input or cfg.get("input_pdf") or cfg.get("input_dir")
    if not input_path:
        input_path = pick_file_or_folder()
    if input_path:
        if os.path.isdir(input_path):
            cfg["input_dir"] = input_path
            cfg["batch_mode"] = True
        elif os.path.isfile(input_path):
            cfg["input_pdf"] = input_path
            cfg["batch_mode"] = False
        else:
            raise ValueError("Input must be a file or directory")
    else:
        raise ValueError("No input file or directory provided!")
    return cfg
