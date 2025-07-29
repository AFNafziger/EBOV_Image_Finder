import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

import ttkbootstrap as ttkb
from ttkbootstrap.constants import *

BASE_PATH = "Images"

class ImageFinderApp(ttkb.Window):
    def __init__(self):
        super().__init__(themename="vapor")
        self.title("")
        self.geometry("300x300")
        self.resizable(False, False)

        # UI
        self._build_ui()
        self.image_label = None
        self.current_image_path = None

        # Print folders at startup
        #self.print_image_folders()

    def _build_ui(self):
        frm = ttkb.Frame(self, padding=20)
        frm.pack(fill=BOTH, expand=True)

        # Input fields
        self.plate_var = tk.StringVar()
        self.well_var = tk.StringVar()
        self.tile_var = tk.StringVar()

        ttkb.Label(frm, text="Plate:").grid(row=0, column=0, sticky=W, pady=5)
        ttkb.Entry(frm, textvariable=self.plate_var, width=20).grid(row=0, column=1, sticky=W)

        ttkb.Label(frm, text="Well:").grid(row=1, column=0, sticky=W, pady=5)
        ttkb.Entry(frm, textvariable=self.well_var, width=20).grid(row=1, column=1, sticky=W)

        ttkb.Label(frm, text="Tile:").grid(row=2, column=0, sticky=W, pady=5)
        ttkb.Entry(frm, textvariable=self.tile_var, width=20).grid(row=2, column=1, sticky=W)

        # Buttons
        ttkb.Button(frm, text="Find Image", command=self.find_image, bootstyle="primary").grid(row=3, column=0, columnspan=2, pady=15)

        self.img_canvas = tk.Label(frm)
        self.img_canvas.grid(row=4, column=0, columnspan=2, pady=10)

        self.download_btn = ttkb.Button(frm, text="Download Image", command=self.download_image, bootstyle="success")
        self.download_btn.grid(row=5, column=0, columnspan=2)
        self.download_btn.config(state="disabled")

    def find_image(self):
        plate = self.plate_var.get().strip()
        well = self.well_var.get().strip()
        tile = self.tile_var.get().strip()

        if not (plate and well and tile):
            messagebox.showerror("Error", "Please fill all fields.")
            return

        folder = f"GW{plate}"
        filename = f"Well{well}_Tile-{tile}.phenotype_corr.tif"
        full_path = os.path.join(BASE_PATH, folder, filename)

        if not os.path.isfile(full_path):
            messagebox.showerror("Not Found", f"Image not found:\n{full_path}")
            self.download_btn.config(state="disabled")
            self.img_canvas.config(image='')
            return

        try:
            img = Image.open(full_path)
            img.thumbnail((400, 400))
            #self.tk_image = ImageTk.PhotoImage(img)
            #self.img_canvas.config(image=self.tk_image)
            self.current_image_path = full_path
            self.download_btn.config(state="normal")
            self.open_image_window(img)  # Open in new window
        except Exception as e:
            messagebox.showerror("Image Error", f"Failed to open image:\n{e}")
            self.download_btn.config(state="disabled")

    def open_image_window(self, pil_image):
        """Open the image in a new separate window."""
        new_win = tk.Toplevel(self)
        new_win.title("Image Viewer")
        new_win.geometry("500x500")
        img = pil_image.copy()
        img.thumbnail((480, 480))
        tk_img = ImageTk.PhotoImage(img)
        lbl = tk.Label(new_win, image=tk_img)
        lbl.image = tk_img  # Keep reference for label
        new_win.tk_img = tk_img  # Keep reference for window
        lbl.pack(expand=True, fill="both")

    def download_image(self):
        if not self.current_image_path:
            return

        target_path = filedialog.asksaveasfilename(
            defaultextension=".tif",
            filetypes=[("TIFF files", "*.tif")],
            initialfile=os.path.basename(self.current_image_path)
        )
        if target_path:
            shutil.copy(self.current_image_path, target_path)
            messagebox.showinfo("Downloaded", f"Image saved to:\n{target_path}")

    def print_image_folders(self):
        """Print all folders in the BASE_PATH directory to the console."""
        try:
            folders = [f for f in os.listdir(BASE_PATH) if os.path.isdir(os.path.join(BASE_PATH, f))]
            print("Folders in", BASE_PATH)
            for folder in folders:
                print(folder)
        except Exception as e:
            print(f"Error accessing {BASE_PATH}: {e}")

if __name__ == "__main__":
    app = ImageFinderApp()
    app.mainloop()
