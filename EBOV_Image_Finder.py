import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageEnhance, ImageOps
import numpy as np

import ttkbootstrap as ttkb
from ttkbootstrap.constants import *

class CustomStyle(ttkb.Style):#this shit doesnt even work
    def __init__(self):
        super().__init__()
        # Override some colors for demonstration
        self.configure('TFrame', background='#222244')
        self.configure('Label', background='#222244', foreground='#FFD700', font=('Arial', 12))
        self.configure('TEntry', fieldbackground='#444466', foreground='#FFD700')
        self.configure('TButton', background='#444466', foreground='#FFD700', font=('Arial', 11, 'bold'))

BASE_PATH = "Images"

class ImageFinderApp(ttkb.Window):
    def __init__(self):
        super().__init__()
        CustomStyle()  # Just instantiate, don't assign to self.style
        self.title("EBOV Image Finder")
        self.geometry("300x300")
        self.resizable(False, False)

        # UI
        self._build_ui()
        self.image_label = None
        self.current_image_path = None
        self.tk_image = None  # Keep reference to prevent garbage collection
        self.current_image = None  # Store the full processed image
        self.current_channels = None  # Store individual channels

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

        # Channel selection
        #

        self.img_canvas = tk.Label(frm, bg='lightgray', text="No image loaded")
        self.img_canvas.grid(row=5, column=0, columnspan=2, pady=10)

        self.download_btn = ttkb.Button(frm, text="Download Image", command=self.download_image, bootstyle="success")
        self.download_btn.grid(row=6, column=0, columnspan=2)
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
            self.img_canvas.config(image='', text="No image found")
            return

        # ADD THIS: Actually load and process the image when found
        try:
            #print(f"Loading image: {full_path}")
            
            # Open the image
            img = Image.open(full_path)
            #print(f"Image opened successfully. Mode: {img.mode}, Size: {img.size}")
            
            # Process the multichannel image
            processed_img = self.process_multichannel_image(img)
            self.current_image = processed_img
            
            # Create thumbnail for main display
            display_img = processed_img.copy()
            display_img.thumbnail((250, 250), Image.Resampling.LANCZOS)
            #print(f"Thumbnail size: {display_img.size}")
            
            # Convert to PhotoImage and display in main canvas
            self.tk_image = ImageTk.PhotoImage(display_img)
            #self.img_canvas.config(image=self.tk_image, text="")
            #print("Image should now be displayed")
            
            self.current_image_path = full_path
            self.download_btn.config(state="normal")
            
            # Also open in new window
            self.open_image_window(processed_img)
            
        except Exception as e:
            print(f"Error details: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Image Error", f"Failed to open image:\n{e}")
            self.download_btn.config(state="disabled")
            self.img_canvas.config(image='', text="Error loading image")

    def process_multichannel_image(self, img):
        """Process 6-channel fluorescence microscopy image."""
        try:
            # If the image is a multi-page TIFF, load all pages as channels
            if hasattr(img, "n_frames") and img.n_frames > 1:
                self.current_channels = []
                for i in range(img.n_frames):
                    img.seek(i)
                    channel = np.array(img)
                    # Normalize each channel
                    if channel.max() > channel.min():
                        normalized = ((channel - channel.min()) / (channel.max() - channel.min()) * 255).astype(np.uint8)
                    else:
                        normalized = np.zeros_like(channel, dtype=np.uint8)
                    self.current_channels.append(Image.fromarray(normalized, mode='L'))
                # Create composite image using first 3 channels as RGB
                if len(self.current_channels) >= 3:
                    composite_img = Image.merge(
                        "RGB",
                        [self.current_channels[0], self.current_channels[1], self.current_channels[2]]
                    )
                    composite_img = ImageOps.autocontrast(composite_img)
                    return composite_img
                else:
                    # If less than 3 channels, just show the first channel
                    return self.current_channels[0].convert('RGB')
            else:
                # If not multi-frame, fall back to array-based channel extraction
                img_array = np.array(img)
                if len(img_array.shape) == 3 and img_array.shape[2] == 6:
                    self.current_channels = []
                    for i in range(6):
                        channel = img_array[:, :, i]
                        if channel.max() > channel.min():
                            normalized = ((channel - channel.min()) / (channel.max() - channel.min()) * 255).astype(np.uint8)
                        else:
                            normalized = np.zeros_like(channel, dtype=np.uint8)
                        self.current_channels.append(Image.fromarray(normalized, mode='L'))
                    composite_array = np.zeros((img_array.shape[0], img_array.shape[1], 3), dtype=np.uint8)
                    for i in range(3):
                        channel = img_array[:, :, i]
                        if channel.max() > channel.min():
                            normalized = ((channel - channel.min()) / (channel.max() - channel.min()) * 255).astype(np.uint8)
                            composite_array[:, :, i] = normalized
                    composite_img = Image.fromarray(composite_array, mode='RGB')
                    composite_img = ImageOps.autocontrast(composite_img)
                    return composite_img
                else:
                    return self.normalize_image(img)
        except Exception as e:
            print(f"Error in process_multichannel_image: {e}")
            return self.normalize_image(img)
            
            # Create thumbnail for main display
            display_img = processed_img.copy()
            display_img.thumbnail((250, 250), Image.Resampling.LANCZOS)
            print(f"Thumbnail size: {display_img.size}")
            
            # Convert to PhotoImage and display in main canvas
            self.tk_image = ImageTk.PhotoImage(display_img)
            self.img_canvas.config(image=self.tk_image, text="")
            print("Image should now be displayed")
            
            self.current_image_path = full_path
            self.download_btn.config(state="normal")
            
            # Also open in new window
            self.open_image_window(processed_img)
            
        #except Exception as e:
        except Exception as e:
            print(f"Error details: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Image Error", f"Failed to open image:\n{e}")
            self.download_btn.config(state="disabled")
            self.img_canvas.config(image='', text="Error loading image")

    def on_channel_change(self, event=None):
        """Handle channel selection change."""
        if not self.current_channels:
            return
            
        selected = self.channel_var.get()
        
        if selected == "composite":
            display_img = self.current_image.copy()
        else:
            # Extract channel number
            channel_num = int(selected.split('_')[1])
            if channel_num < len(self.current_channels):
                # Convert grayscale channel to RGB for display
                display_img = self.current_channels[channel_num].convert('RGB')
                # Apply auto-contrast for better visibility
                display_img = ImageOps.autocontrast(display_img)
            else:
                return
        
        # Update display
        display_img.thumbnail((250, 250), Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(display_img)
        self.img_canvas.config(image=self.tk_image)

        # Open selected channel in new window
        self.open_image_window(display_img)

    def normalize_image(self, img):
        """Fallback normalization for non-multichannel images."""
        try:
            img_array = np.array(img)
            #print(f"Image array shape: {img_array.shape}")
            #print(f"Image array dtype: {img_array.dtype}")
            #print(f"Min value: {img_array.min()}, Max value: {img_array.max()}")
            
            if len(img_array.shape) == 2:
                min_val = img_array.min()
                max_val = img_array.max()
                if min_val != max_val:
                    normalized = ((img_array - min_val) / (max_val - min_val) * 255).astype(np.uint8)
                    return Image.fromarray(normalized, mode='L').convert('RGB')
            
            return img.convert('RGB')
            
        except Exception as e:
            print(f"Error in normalize_image: {e}")
            return img.convert('RGB')

    def open_image_window(self, pil_image):
        """Open the image in a new separate window."""
        try:
            new_win = tk.Toplevel(self)
            new_win.title("Image Viewer")
            new_win.geometry("500x500")
            
            # Use the already processed image
            img = pil_image.copy()
            img.thumbnail((480, 480), Image.Resampling.LANCZOS)
            tk_img = ImageTk.PhotoImage(img)
            lbl = tk.Label(new_win, image=tk_img)
            lbl.image = tk_img  # Keep reference for label
            new_win.tk_img = tk_img  # Keep reference for window
            lbl.pack(expand=True, fill="both")
        except Exception as e:
            print(f"Error opening image window: {e}")
            messagebox.showerror("Window Error", f"Failed to open image window:\n{e}")

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