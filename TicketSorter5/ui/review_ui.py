import tkinter as tk
from tkinter import ttk, messagebox

from PIL import ImageTk


class ReviewUI:
    def __init__(self, root, page_data):
        self.root = root
        self.page_data = page_data

        # Predeclare all attributes to prevent runtime warnings
        self.canvas = None
        self.info_frame = None
        self.vendor_var = None
        self.vendor_entry = None
        self.ticket_var = None
        self.ticket_entry = None
        self.status = None
        self.tk_img = None
        self.current_index = 0
        self.updated_entries = []

        self.root.geometry("800x700")

        self.canvas = tk.Label(self.root)
        self.canvas.pack(pady=10)

        self.info_frame = tk.Frame(self.root)
        self.info_frame.pack()

        tk.Label(self.info_frame, text="Detected Vendor:").grid(row=0, column=0, sticky="e")
        self.vendor_var = tk.StringVar()
        self.vendor_entry = ttk.Combobox(self.info_frame, textvariable=self.vendor_var, width=30)
        self.vendor_entry.grid(row=0, column=1)

        tk.Label(self.info_frame, text="Ticket #:").grid(row=1, column=0, sticky="e")
        self.ticket_var = tk.StringVar()
        self.ticket_entry = tk.Entry(self.info_frame, textvariable=self.ticket_var, width=30)
        self.ticket_entry.grid(row=1, column=1)

        nav_frame = tk.Frame(self.root)
        nav_frame.pack(pady=15)

        tk.Button(nav_frame, text="⬅️ Previous", command=self.prev_page).grid(row=0, column=0, padx=10)
        tk.Button(nav_frame, text="💾 Save & Next", command=self.save_and_next).grid(row=0, column=1, padx=10)

        self.status = tk.Label(self.root, text="", font=("Segoe UI", 9))
        self.status.pack()

        self.load_page()

    def load_page(self):
        try:
            page_info = self.page_data[self.current_index]
            self.vendor_var.set(page_info.get("Vendor", ""))
            self.ticket_var.set(page_info.get("Ticket Number", ""))

            img = page_info.get("Image")
            resized = img.resize((600, 800))
            self.tk_img = ImageTk.PhotoImage(resized)
            self.canvas.config(image=self.tk_img)

            self.status.config(text=f"Page {self.current_index + 1} of {len(self.page_data)}")
        except Exception as e:
            self.status.config(text=f"⚠️ Failed to load page {self.current_index + 1}: {e}")

    def save_and_next(self):
        entry = self.page_data[self.current_index]
        entry["Vendor"] = self.vendor_var.get()
        entry["Ticket Number"] = self.ticket_var.get()
        self.updated_entries.append(entry)

        if self.current_index + 1 < len(self.page_data):
            self.current_index += 1
            self.load_page()
        else:
            self.status.config(text="✅ Review Complete")
            messagebox.showinfo("Done", "All pages reviewed.")
            self.root.quit()

    def prev_page(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.load_page()


def launch_review(page_data):
    root = tk.Tk()
    app = ReviewUI(root, page_data)
    root.mainloop()
    return app.updated_entries
