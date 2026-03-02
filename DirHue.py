import os
import sys
import ctypes
import winreg
import time
import random
import json
import colorsys
import shutil
import webbrowser
import customtkinter as ctk
from tkinter import messagebox, colorchooser, filedialog
from PIL import Image, ImageOps

# CustomTkinter Configuration
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# Bezpieczne miejsce na zapisywanie presetów (AppData)
APPDATA_DIR = os.path.join(os.getenv('APPDATA'), "DirHueApp")
if not os.path.exists(APPDATA_DIR):
    try:
        os.makedirs(APPDATA_DIR)
    except:
        pass
PRESETS_FILE = os.path.join(APPDATA_DIR, "presets.json")

# Zmienione, unikalne presety startowe
DEFAULT_PRESETS = [
    {"name": "Neon Cyan", "hex": "#00FFFF"},
    {"name": "Deep Royal", "hex": "#4169E1"},
    {"name": "Toxic Green", "hex": "#39FF14"},
    {"name": "Sunset Orange", "hex": "#FF4500"},
    {"name": "Bubblegum", "hex": "#FFC0CB"},
    {"name": "Dark Knight", "hex": "#2C3E50"}
]


class ColorizerApp(ctk.CTk):
    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = os.path.abspath(folder_path)
        self.title(f"DirHueApp - {os.path.basename(self.folder_path)}")
        self.geometry("600x580")
        self.resizable(False, False)

        icon_path = os.path.join(os.path.dirname(__file__), "app.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)

        self.presets = self.load_presets()

        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(__file__)
        self.mask_path = os.path.join(base_path, "mask.png")

        self.setup_ui()

    def load_presets(self):
        if os.path.exists(PRESETS_FILE):
            try:
                with open(PRESETS_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return DEFAULT_PRESETS.copy()

    def save_presets(self):
        try:
            with open(PRESETS_FILE, "w") as f:
                json.dump(self.presets, f, indent=4)
        except Exception as e:
            print(f"Nie można zapisać presetów: {e}")

    def setup_ui(self):
        # --- ZAKŁADKI (TABVIEW) ---
        self.tabview = ctk.CTkTabview(self, width=560, height=450)
        self.tabview.pack(padx=20, pady=(10, 0), fill="both", expand=True)

        self.tabview.add("Library")
        self.tabview.add("Create Style")
        self.tabview.add("Support ❤️")

        # --- ZAKŁADKA: LIBRARY ---
        self.library_scroll = ctk.CTkScrollableFrame(self.tabview.tab("Library"), fg_color="transparent")
        self.library_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        self.refresh_library()

        # --- ZAKŁADKA: CREATE STYLE ---
        create_tab = self.tabview.tab("Create Style")

        self.preview_label = ctk.CTkLabel(create_tab, text="")
        self.preview_label.pack(pady=10)

        sliders_frame = ctk.CTkFrame(create_tab, fg_color="transparent")
        sliders_frame.pack(pady=5, fill="x")

        # Suwak Hue (Odcień)
        ctk.CTkLabel(sliders_frame, text="Hue (Color):", font=("Segoe UI", 12)).pack(anchor="w", padx=65)
        self.hue_slider = ctk.CTkSlider(sliders_frame, from_=0, to=1, command=self.update_from_sliders, width=250)
        self.hue_slider.pack(pady=(0, 10))
        self.hue_slider.set(0.5)

        # Suwak Saturation (Nasycenie)
        ctk.CTkLabel(sliders_frame, text="Saturation (Intensity):", font=("Segoe UI", 12)).pack(anchor="w", padx=65)
        self.sat_slider = ctk.CTkSlider(sliders_frame, from_=0, to=1, command=self.update_from_sliders, width=250)
        self.sat_slider.pack(pady=(0, 10))
        self.sat_slider.set(0.8)

        # Suwak Brightness (Jasność)
        ctk.CTkLabel(sliders_frame, text="Brightness:", font=("Segoe UI", 12)).pack(anchor="w", padx=65)
        self.val_slider = ctk.CTkSlider(sliders_frame, from_=0, to=1, command=self.update_from_sliders, width=250)
        self.val_slider.pack(pady=(0, 10))
        self.val_slider.set(0.9)

        self.wheel_btn = ctk.CTkButton(create_tab, text="🎨 Pick from Color Wheel",
                                       fg_color="#4A4A5A", hover_color="#5A5A6A", command=self.open_color_wheel)
        self.wheel_btn.pack(pady=10)

        input_frame = ctk.CTkFrame(create_tab, fg_color="transparent")
        input_frame.pack(pady=5)

        ctk.CTkLabel(input_frame, text="HEX:", font=("Segoe UI", 12)).grid(row=0, column=0, padx=5, sticky="e")
        self.hex_entry = ctk.CTkEntry(input_frame, width=120)
        self.hex_entry.grid(row=0, column=1, padx=5, pady=5)
        self.hex_entry.bind("<Return>", self.update_from_hex)

        ctk.CTkLabel(input_frame, text="Name:", font=("Segoe UI", 12)).grid(row=1, column=0, padx=5, sticky="e")
        self.name_entry = ctk.CTkEntry(input_frame, width=120)
        self.name_entry.grid(row=1, column=1, padx=5, pady=5)
        self.name_entry.insert(0, "My Custom Glow")

        self.add_btn = ctk.CTkButton(create_tab, text="➕ Add to Library",
                                     command=self.add_to_library, fg_color="#27AE60", hover_color="#2ECC71")
        self.add_btn.pack(pady=15)
        self.update_from_sliders(None)

        # --- ZAKŁADKA: SUPPORT (WinRAR style nag) ---
        support_tab = self.tabview.tab("Support ❤️")

        ctk.CTkLabel(support_tab, text="☕ Support the Developer", font=("Segoe UI", 22, "bold")).pack(pady=(40, 10))

        support_text = (
            "This software is 100% free to use, forever.\n"
            "There are no hidden fees, no watermarks, and no annoying ads.\n\n"
            "However, if this tool saved you some time or brightened up your desktop,\n"
            "consider supporting its development. It helps keep the updates coming!"
        )
        ctk.CTkLabel(support_tab, text=support_text, font=("Segoe UI", 13), justify="center").pack(pady=20)

        self.donate_btn = ctk.CTkButton(support_tab, text="Buy me a coffee ☕", height=40, font=("Segoe UI", 14, "bold"),
                                        fg_color="#F39C12", hover_color="#D68910", text_color="black",
                                        command=self.open_donation_link)
        self.donate_btn.pack(pady=10)

        # --- GLOBALNY PASEK DOLNY ---
        bottom_bar = ctk.CTkFrame(self, fg_color="transparent")
        bottom_bar.pack(fill="x", padx=20, pady=15, side="bottom")

        self.reset_btn = ctk.CTkButton(bottom_bar, text="↺ Restore Default Folder Style", fg_color="transparent",
                                       border_width=1, border_color="#555", hover_color="#333",
                                       command=self.reset_folder, height=35)
        self.reset_btn.pack(fill="x")

    def open_donation_link(self):
        # Zmień ten link na swój prawdziwy (np. buymeacoffee.com, zrzutka.pl, patreon)
        webbrowser.open("https://buymeacoffee.com/sobalarafaa")

    def open_color_wheel(self):
        color = colorchooser.askcolor(title="Choose a Color")[1]
        if color:
            self.hex_entry.delete(0, "end")
            self.hex_entry.insert(0, color.upper())
            self.update_from_hex(None)

    def get_preview_image(self, hex_color, size=(64, 64)):
        if os.path.exists(self.mask_path):
            try:
                rgb = tuple(int(hex_color.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))
                mask_img = Image.open(self.mask_path).convert("L")
                colored_folder = ImageOps.colorize(mask_img, black="black", white=rgb, mid="#808080")
                colored_folder.putalpha(mask_img)
                colored_folder = colored_folder.resize(size, Image.Resampling.LANCZOS)
                return ctk.CTkImage(light_image=colored_folder, dark_image=colored_folder, size=size)
            except Exception:
                pass
        img = Image.new("RGBA", size, color=hex_color)
        return ctk.CTkImage(light_image=img, dark_image=img, size=size)

    def update_from_sliders(self, _):
        h, s, v = self.hue_slider.get(), self.sat_slider.get(), self.val_slider.get()
        r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(h, s, v)]
        hex_color = f"#{r:02x}{g:02x}{b:02x}".upper()
        self.hex_entry.delete(0, "end")
        self.hex_entry.insert(0, hex_color)
        img = self.get_preview_image(hex_color, size=(80, 80))
        self.preview_label.configure(image=img)
        self.preview_label.image = img

    def update_from_hex(self, event):
        hex_color = self.hex_entry.get().strip()
        if len(hex_color) == 7 and hex_color.startswith("#"):
            try:
                rgb = tuple(int(hex_color.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))
                h, s, v = colorsys.rgb_to_hsv(rgb[0] / 255, rgb[1] / 255, rgb[2] / 255)
                self.hue_slider.set(h)
                self.sat_slider.set(s)
                self.val_slider.set(v)
                img = self.get_preview_image(hex_color, size=(80, 80))
                self.preview_label.configure(image=img)
                self.preview_label.image = img
            except ValueError:
                pass

    def add_to_library(self):
        hex_color = self.hex_entry.get().strip()
        name = self.name_entry.get().strip()
        if len(hex_color) == 7 and hex_color.startswith("#") and name:
            self.presets.append({"name": name, "hex": hex_color})
            self.save_presets()
            self.refresh_library()
            self.tabview.set("Library")  # Automatyczny powrót do biblioteki po dodaniu

    def remove_preset(self, index):
        del self.presets[index]
        self.save_presets()
        self.refresh_library()

    def refresh_library(self):
        for widget in self.library_scroll.winfo_children():
            widget.destroy()

        for i, preset in enumerate(self.presets):
            card = ctk.CTkFrame(self.library_scroll, fg_color="#2B2B36", corner_radius=10)
            card.pack(fill="x", pady=5, padx=5)

            img = self.get_preview_image(preset["hex"], size=(40, 40))
            img_lbl = ctk.CTkLabel(card, text="", image=img)
            img_lbl.image = img
            img_lbl.pack(side="left", padx=15, pady=10)

            ctk.CTkLabel(card, text=preset["name"], font=("Segoe UI", 14, "bold")).pack(side="left", padx=10)

            ctk.CTkButton(card, text="✕", width=30, height=30, fg_color="#E74C3C", hover_color="#C0392B",
                          command=lambda idx=i: self.remove_preset(idx)).pack(side="right", padx=(5, 15))

            ctk.CTkButton(card, text="Apply", width=80, height=30, fg_color="#3498DB", hover_color="#2980B9",
                          command=lambda h=preset["hex"]: self.apply_hex(h)).pack(side="right", padx=5)

    def apply_hex(self, hex_code):
        rgb = tuple(int(hex_code.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))
        self.process(rgb)

    def create_dynamic_icon(self, color_rgb):
        icon_path = os.path.join(self.folder_path, "folder_custom.ico")
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(__file__)
        mask_path = os.path.join(base_path, "mask.png")

        try:
            if os.path.exists(icon_path):
                ctypes.windll.kernel32.SetFileAttributesW(icon_path, 128)
                try:
                    os.remove(icon_path)
                except OSError:
                    pass

            if os.path.exists(mask_path):
                mask_img = Image.open(mask_path).convert("L")
                colored_folder = ImageOps.colorize(mask_img, black="black", white=color_rgb, mid="#808080")
                colored_folder.putalpha(mask_img)
                colored_folder.save(icon_path, format="ICO", sizes=[(256, 256), (64, 64), (48, 48), (32, 32), (16, 16)])
            else:
                img = Image.new("RGBA", (256, 256), color=color_rgb)
                img.save(icon_path, format="ICO")
            return icon_path
        except PermissionError:
            messagebox.showerror("Permission Error",
                                 "Windows is locking the icon file. Close the folder window and try again.")
            return None
        except Exception as e:
            messagebox.showerror("Mask Error", f"Details: {e}")
            return None

    def process(self, rgb):
        icon_path = self.create_dynamic_icon(rgb)
        if not icon_path: return
        ini_path = os.path.join(self.folder_path, "desktop.ini")

        try:
            for p in [icon_path, ini_path]:
                if os.path.exists(p): ctypes.windll.kernel32.SetFileAttributesW(p, 128)

            content = ["[.ShellClassInfo]\n", "IconResource=folder_custom.ico,0\n", "IconIndex=0\n", "[ViewState]\n",
                       "Mode=\n", "Vid=\n", "FolderType=Generic\n"]
            with open(ini_path, "w", encoding="utf-16") as f:
                f.writelines(content)

            ctypes.windll.kernel32.SetFileAttributesW(icon_path, 2)
            ctypes.windll.kernel32.SetFileAttributesW(ini_path, 2 | 4)
            ctypes.windll.kernel32.SetFileAttributesW(self.folder_path, 1)

            self.atomic_refresh()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply: {e}")

    def reset_folder(self):
        try:
            for f in ["folder_custom.ico", "desktop.ini"]:
                p = os.path.join(self.folder_path, f)
                if os.path.exists(p):
                    ctypes.windll.kernel32.SetFileAttributesW(p, 128)
                    os.remove(p)
            ctypes.windll.kernel32.SetFileAttributesW(self.folder_path, 128)
            self.atomic_refresh()
            self.destroy()
        except Exception:
            pass

    def atomic_refresh(self):
        try:
            parent = os.path.dirname(self.folder_path)
            basename = os.path.basename(self.folder_path)
            temp_name = os.path.join(parent, f"{basename}_re_{random.randint(100, 999)}")
            os.rename(self.folder_path, temp_name)
            time.sleep(0.1)
            os.rename(temp_name, self.folder_path)
            ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x0000, None, None)
        except Exception:
            ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x0000, None, None)


# --- INSTALLER LOGIC ---
class InstallerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("DirHue - Setup")
        self.geometry("500x320")
        self.resizable(False, False)

        icon_path = os.path.join(os.path.dirname(__file__), "app.ico")
        if os.path.exists(icon_path): self.iconbitmap(icon_path)

        default_dir = os.path.join(os.environ.get('PROGRAMFILES', 'C:\\Program Files'), "DirHue")
        self.path_var = ctk.StringVar(value=default_dir)
        self.setup_ui()

    def setup_ui(self):
        ctk.CTkLabel(self, text="Installation", font=("Segoe UI", 20, "bold")).pack(pady=(20, 5))
        ctk.CTkLabel(self, text="Choose where to install the application", text_color="gray").pack(pady=(0, 20))

        path_frame = ctk.CTkFrame(self, fg_color="transparent")
        path_frame.pack(fill="x", padx=30, pady=10)

        ctk.CTkLabel(path_frame, text="Install Location:").pack(anchor="w")

        entry_frame = ctk.CTkFrame(path_frame, fg_color="transparent")
        entry_frame.pack(fill="x", pady=5)

        ctk.CTkEntry(entry_frame, textvariable=self.path_var, width=330).pack(side="left", padx=(0, 10))
        ctk.CTkButton(entry_frame, text="Browse...", width=80, command=self.browse_folder).pack(side="left")

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=30)

        ctk.CTkButton(btn_frame, text="Install to Context Menu", fg_color="#27AE60", hover_color="#2ECC71",
                      command=self.install).pack(side="left", expand=True, padx=5, fill="x")
        ctk.CTkButton(btn_frame, text="Uninstall", fg_color="#C0392B", hover_color="#E74C3C",
                      command=self.uninstall).pack(side="right", expand=True, padx=5, fill="x")

    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.path_var.get())
        if folder: self.path_var.set(os.path.join(folder, "DirHue"))

    def install(self):
        target_dir = self.path_var.get()
        is_exe = getattr(sys, 'frozen', False)

        if not is_exe:
            messagebox.showwarning("Notice",
                                   "Compile the script into an .exe first using PyInstaller.\nRegistry keys will point to this .py script for now.")
            exe_path = os.path.abspath(sys.argv[0])
            dest_path = exe_path
        else:
            exe_path = sys.executable
            exe_name = os.path.basename(exe_path)
            dest_path = os.path.join(target_dir, exe_name)

            try:
                if not os.path.exists(target_dir): os.makedirs(target_dir)
                if os.path.abspath(exe_path) != os.path.abspath(dest_path):
                    shutil.copy2(exe_path, dest_path)
            except PermissionError:
                messagebox.showerror("Error", "Run the installer as Administrator to install in Program Files.")
                return
            except Exception as e:
                messagebox.showerror("Error", f"Failed to copy files:\n{e}")
                return

        key_path = r"Directory\shell\DirHueFolder"
        try:
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, key_path) as key:
                winreg.SetValue(key, "", winreg.REG_SZ, "Colorize Folder")
                winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, f"{dest_path},0")
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, key_path + r"\command") as key:
                winreg.SetValue(key, "", winreg.REG_SZ, f'"{dest_path}" "%1"')
            messagebox.showinfo("Success", f"Installed successfully!\n\nLocation: {dest_path}")
        except PermissionError:
            messagebox.showerror("Error", "Run the installer as Administrator to modify the registry.")

    def uninstall(self):
        key_path = r"Directory\shell\DirHueFolder"
        try:
            winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, key_path + r"\command")
            winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, key_path)
            messagebox.showinfo("Success", "Removed from context menu successfully.")
        except FileNotFoundError:
            messagebox.showinfo("Info", "Application is not installed in the registry.")
        except PermissionError:
            messagebox.showerror("Error", "Run the installer as Administrator.")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and os.path.isdir(" ".join(args)):
        app = ColorizerApp(" ".join(args))
        app.mainloop()
    else:
        installer = InstallerApp()
        installer.mainloop()