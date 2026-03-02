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
from PIL import Image, ImageOps, ImageDraw, ImageFont
import math

# CustomTkinter Configuration
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

APPDATA_DIR = os.path.join(os.getenv('APPDATA'), "DirHue")
OVERLAYS_DIR = os.path.join(APPDATA_DIR, "overlays")

for directory in [APPDATA_DIR, OVERLAYS_DIR]:
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
        except:
            pass

PRESETS_FILE = os.path.join(APPDATA_DIR, "presets.json")

DEFAULT_PRESETS = [
    {"name": "Ruby Red", "hex": "#E74C3C", "overlay": None},
    {"name": "Sunset Orange", "hex": "#E67E22", "overlay": None},
    {"name": "Sunflower Yellow", "hex": "#F1C40F", "overlay": None},
    {"name": "Emerald Green", "hex": "#2ECC71", "overlay": None},
    {"name": "Ocean Blue", "hex": "#3498DB", "overlay": None},
    {"name": "Deep Indigo", "hex": "#3F51B5", "overlay": None},
    {"name": "Amethyst Purple", "hex": "#9B59B6", "overlay": None}
]

BUILTIN_ICONS = [
    "None", "⭐ Star", "❤️ Heart", "🔒 Lock", "🎮 Gamepad", "🎵 Music",
    "📁 Folder", "🔥 Fire", "🚀 Rocket", "⚡ Lightning", "💡 Idea",
    "📌 Pin", "💼 Work", "📷 Camera", "🎓 Education", "✈️ Travel",
    "💰 Money", "🛠️ Tools", "🐛 Bug", "✅ Success", "❌ Error",
    "⚠ Warning", "💬 Chat", "🔔 Bell", "🌍 Web", "☁️ Cloud", "🎨 Art"
]

MODERN_PALETTE = [
    "#1ABC9C", "#2ECC71", "#3498DB", "#9B59B6", "#34495E",
    "#16A085", "#27AE60", "#2980B9", "#8E44AD", "#2C3E50",
    "#F1C40F", "#E67E22", "#E74C3C", "#ECF0F1", "#95A5A6",
    "#F39C12", "#D35400", "#C0392B", "#BDC3C7", "#7F8C8D",
    "#FF9FF3", "#FF6B6B", "#48DBFB", "#1DD1A1", "#5F27CD"
]


class ColorizerApp(ctk.CTk):
    def __init__(self, folder_path, test_mode=False):
        super().__init__()
        self.folder_path = os.path.abspath(folder_path)
        self.test_mode = test_mode

        title_suffix = " (TEST MODE)" if self.test_mode else f" - {os.path.basename(self.folder_path)}"
        self.title(f"DirHue{title_suffix}")

        # ZWIĘKSZONY ROZMIAR OKNA
        self.geometry("700x800")
        self.resizable(False, False)

        icon_path = os.path.join(os.path.dirname(__file__), "app.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)

        self.presets = self.load_presets()
        self.current_overlay = None
        self.overlay_type = "none"

        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(__file__)
        self.mask_path = os.path.join(base_path, "mask.png")

        self.setup_ui()

    def change_theme(self, new_theme: str):
        ctk.set_appearance_mode(new_theme)

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
        except Exception:
            pass

    def setup_ui(self):
        # ZWIĘKSZONY TABVIEW
        self.tabview = ctk.CTkTabview(self, width=680, height=620)
        self.tabview.pack(padx=20, pady=(10, 0), fill="both", expand=True)

        self.tabview.add("Library")
        self.tabview.add("Create Style")
        self.tabview.add("Support ❤️")

        # --- ZAKŁADKA: LIBRARY ---
        lib_tab = self.tabview.tab("Library")

        controls_frame = ctk.CTkFrame(lib_tab, fg_color="transparent")
        controls_frame.pack(fill="x", padx=5, pady=5)

        search_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        search_frame.pack(fill="x", pady=(0, 5))

        self.search_var = ctk.StringVar(value="")
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="🔍 Search styles...",
                                         textvariable=self.search_var)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_library())

        self.view_mode_var = ctk.StringVar(value="List")
        self.view_mode_switch = ctk.CTkSegmentedButton(search_frame, values=["List", "Grid"],
                                                       variable=self.view_mode_var, command=self.refresh_library)
        self.view_mode_switch.pack(side="right")

        filter_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        filter_frame.pack(fill="x")

        ctk.CTkLabel(filter_frame, text="Type:", font=("Segoe UI", 12), text_color=("#000000", "#FFFFFF")).pack(
            side="left", padx=(0, 5))
        self.filter_var = ctk.StringVar(value="All")
        self.filter_menu = ctk.CTkOptionMenu(filter_frame, values=["All", "No Overlay", "Built-in", "Custom Image"],
                                             variable=self.filter_var, command=self.refresh_library, width=120)
        self.filter_menu.pack(side="left", padx=(0, 15))

        ctk.CTkLabel(filter_frame, text="Sort:", font=("Segoe UI", 12), text_color=("#000000", "#FFFFFF")).pack(
            side="left", padx=(0, 5))
        self.sort_var = ctk.StringVar(value="Newest")
        self.sort_menu = ctk.CTkOptionMenu(filter_frame, values=["Newest", "Oldest", "A-Z", "Z-A"],
                                           variable=self.sort_var, command=self.refresh_library, width=100)
        self.sort_menu.pack(side="left")

        self.library_scroll = ctk.CTkScrollableFrame(lib_tab, fg_color=("#EBEBEB", "#242424"))
        self.library_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        self.refresh_library()

        # --- ZAKŁADKA: CREATE STYLE ---
        create_tab = ctk.CTkScrollableFrame(self.tabview.tab("Create Style"), fg_color=("#EBEBEB", "#242424"))
        create_tab.pack(fill="both", expand=True)

        ctk.CTkLabel(create_tab, text="1. Folder Base Color", bg_color="transparent", font=("Segoe UI", 14, "bold"),
                     text_color=("#000000", "#FFFFFF")).pack(anchor="w", pady=(0, 5))

        # --- PODGLĄD FOLDERU NA SAMEJ GÓRZE ---
        preview_frame = ctk.CTkFrame(create_tab, fg_color="transparent")
        preview_frame.pack(pady=(5, 10), fill="x")

        self.preview_label = ctk.CTkLabel(preview_frame, text="")
        self.preview_label.pack()  # Domyślnie wyśrodkuje podgląd

        # --- KONTENER NA KOŁO BARW I SUWAKI (Obok siebie) ---
        wheel_sliders_frame = ctk.CTkFrame(create_tab, fg_color="transparent")
        wheel_sliders_frame.pack(pady=5, fill="x")

        # LEWA STRONA: KOŁO BARW
        wheel_size = 140
        self.wheel_img_base = self.generate_color_wheel(wheel_size)
        self.wheel_ctk_img = ctk.CTkImage(light_image=self.wheel_img_base, dark_image=self.wheel_img_base,
                                          size=(wheel_size, wheel_size))

        self.wheel_label = ctk.CTkLabel(wheel_sliders_frame, text="", image=self.wheel_ctk_img, cursor="crosshair")
        self.wheel_label.pack(side="left", padx=(40, 30), pady=5)

        self.wheel_label.bind("<Button-1>", self.on_wheel_click)
        self.wheel_label.bind("<B1-Motion>", self.on_wheel_click)

        # PRAWA STRONA: SUWAKI
        sliders_frame = ctk.CTkFrame(wheel_sliders_frame, fg_color="transparent")
        sliders_frame.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(sliders_frame, text="Hue (Color):", font=("Segoe UI", 12), text_color=("#000000", "#FFFFFF")).pack(
            anchor="w", padx=5, pady=(0, 0))
        self.hue_slider = ctk.CTkSlider(sliders_frame, from_=0, to=1, command=self.update_from_sliders, width=250)
        self.hue_slider.pack(pady=(0, 5), padx=5, anchor="w")
        self.hue_slider.set(0.5)

        ctk.CTkLabel(sliders_frame, text="Saturation:", font=("Segoe UI", 12), text_color=("#000000", "#FFFFFF")).pack(
            anchor="w", padx=5)
        self.sat_slider = ctk.CTkSlider(sliders_frame, from_=0, to=1, command=self.update_from_sliders, width=250)
        self.sat_slider.pack(pady=(0, 5), padx=5, anchor="w")
        self.sat_slider.set(0.8)

        ctk.CTkLabel(sliders_frame, text="Brightness:", font=("Segoe UI", 12), text_color=("#000000", "#FFFFFF")).pack(
            anchor="w", padx=5)
        self.val_slider = ctk.CTkSlider(sliders_frame, from_=0, to=1, command=self.update_from_sliders, width=250)
        self.val_slider.pack(pady=(0, 5), padx=5, anchor="w")
        self.val_slider.set(0.9)
        # -----------------------------------------------------

        fh_frame = ctk.CTkFrame(create_tab, fg_color="transparent")
        fh_frame.pack(pady=5)
        self.wheel_btn = ctk.CTkButton(fh_frame, text="🎨 Color Palette", width=110,
                                       command=lambda: self.open_custom_color_picker("base"))
        self.wheel_btn.grid(row=0, column=0, padx=5)
        self.hex_entry = ctk.CTkEntry(fh_frame, width=90)
        self.hex_entry.grid(row=0, column=1, padx=5)
        self.hex_entry.bind("<Return>", self.update_from_hex)

        ctk.CTkLabel(create_tab, text="2. Overlay (Optional)", font=("Segoe UI", 14, "bold"),
                     text_color=("#000000", "#FFFFFF")).pack(anchor="w", pady=(15, 5))

        overlay_frame = ctk.CTkFrame(create_tab)
        overlay_frame.pack(fill="x")

        self.builtin_btn = ctk.CTkButton(overlay_frame, text="⭐ Choose Icon", fg_color="#2980B9", hover_color="#3498DB",
                                         width=110, command=self.open_icon_picker)
        self.builtin_btn.grid(row=0, column=0, padx=10, pady=10)

        self.overlay_btn = ctk.CTkButton(overlay_frame, text="📂 Upload Image", fg_color="#8E44AD",
                                         hover_color="#9B59B6", width=100, command=self.choose_overlay)
        self.overlay_btn.grid(row=0, column=1, padx=5, pady=10)

        self.clear_overlay_btn = ctk.CTkButton(overlay_frame, text="❌", width=30, fg_color="transparent",
                                               border_width=1, border_color=("#999", "#555"),
                                               text_color=("#000", "#FFF"), command=self.clear_overlay)
        self.clear_overlay_btn.grid(row=0, column=2, padx=5, pady=10)

        color_ov_frame = ctk.CTkFrame(create_tab)
        color_ov_frame.pack(fill="x", pady=5)
        self.colorize_overlay_var = ctk.BooleanVar(value=False)
        self.colorize_cb = ctk.CTkCheckBox(color_ov_frame, text="Colorize Overlay:", text_color=("#000000", "#FFFFFF"),
                                           variable=self.colorize_overlay_var, command=self.force_preview_update)
        self.colorize_cb.pack(side="left", padx=10, pady=10)

        self.ov_color_btn = ctk.CTkButton(color_ov_frame, text="🎨", width=30,
                                          command=lambda: self.open_custom_color_picker("overlay"))
        self.ov_color_btn.pack(side="left", padx=(0, 5), pady=10)

        self.overlay_color_entry = ctk.CTkEntry(color_ov_frame, width=80)
        self.overlay_color_entry.insert(0, "#FFFFFF")
        self.overlay_color_entry.pack(side="left", padx=5, pady=10)
        self.overlay_color_entry.bind("<Return>", lambda e: self.force_preview_update())

        pos_frame = ctk.CTkFrame(create_tab)
        pos_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(pos_frame, text="Size:", text_color=("#000000", "#FFFFFF")).grid(row=0, column=0, padx=10, pady=10,
                                                                                      sticky="e")
        self.ov_size_slider = ctk.CTkSlider(pos_frame, from_=0.1, to=1.0, width=120, command=self.force_preview_update)
        self.ov_size_slider.set(0.5)
        self.ov_size_slider.grid(row=0, column=1, padx=5, pady=10)

        ctk.CTkLabel(pos_frame, text="Position:", text_color=("#000000", "#FFFFFF")).grid(row=0, column=2, padx=10,
                                                                                          pady=10, sticky="e")
        self.pos_var = ctk.StringVar(value="Center")
        self.pos_menu = ctk.CTkOptionMenu(pos_frame,
                                          values=["Center", "Top-Left", "Top-Right", "Bottom-Left", "Bottom-Right",
                                                  "Custom"], variable=self.pos_var, width=110,
                                          command=self.toggle_custom_pos)
        self.pos_menu.grid(row=0, column=3, padx=5, pady=10)

        self.custom_pos_frame = ctk.CTkFrame(create_tab)

        ctk.CTkLabel(self.custom_pos_frame, text="X Offset:", text_color=("#000000", "#FFFFFF")).grid(row=0, column=0,
                                                                                                      padx=10, pady=10)
        self.ov_x_slider = ctk.CTkSlider(self.custom_pos_frame, from_=-100, to=100, width=120,
                                         command=self.force_preview_update)
        self.ov_x_slider.set(0)
        self.ov_x_slider.grid(row=0, column=1, padx=5, pady=10)

        ctk.CTkLabel(self.custom_pos_frame, text="Y Offset:", text_color=("#000000", "#FFFFFF")).grid(row=0, column=2,
                                                                                                      padx=10, pady=10)
        self.ov_y_slider = ctk.CTkSlider(self.custom_pos_frame, from_=-100, to=100, width=120,
                                         command=self.force_preview_update)
        self.ov_y_slider.set(10)
        self.ov_y_slider.grid(row=0, column=3, padx=5, pady=10)

        save_frame = ctk.CTkFrame(create_tab, fg_color="transparent")
        save_frame.pack(pady=(15, 5))
        ctk.CTkLabel(save_frame, text="Style Name:", font=("Segoe UI", 12), text_color=("#000000", "#FFFFFF")).pack(
            side="left", padx=5)
        self.name_entry = ctk.CTkEntry(save_frame, width=120)
        self.name_entry.insert(0, "My Custom Folder")
        self.name_entry.pack(side="left", padx=5)
        self.add_btn = ctk.CTkButton(save_frame, text="➕ Add to Library", command=self.add_to_library,
                                     fg_color="#27AE60", hover_color="#2ECC71")
        self.add_btn.pack(side="left", padx=10)

        self.update_from_sliders(None)

        # --- ZAKŁADKA: SUPPORT ---
        support_tab = self.tabview.tab("Support ❤️")
        ctk.CTkLabel(support_tab, text="☕ Support the Developer", font=("Segoe UI", 22, "bold"),
                     text_color=("#000000", "#FFFFFF")).pack(pady=(40, 10))
        support_text = "This software is 100% free to use, forever.\nIf this tool saved you some time, consider supporting its development!"
        ctk.CTkLabel(support_tab, text=support_text, font=("Segoe UI", 13), text_color=("#000000", "#FFFFFF"),
                     justify="center").pack(pady=20)
        self.donate_btn = ctk.CTkButton(support_tab, text="Buy me a coffee ☕", height=40, font=("Segoe UI", 14, "bold"),
                                        fg_color="#F39C12", hover_color="#D68910", text_color="black",
                                        command=lambda: webbrowser.open("https://buymeacoffee.com/sobalarafaa"))
        self.donate_btn.pack(pady=10)

        # --- GLOBALNY PASEK DOLNY ---
        bottom_bar = ctk.CTkFrame(self, fg_color="transparent")
        bottom_bar.pack(fill="x", padx=20, pady=10, side="bottom")

        self.theme_menu = ctk.CTkOptionMenu(bottom_bar, values=["Dark", "Light", "System"], command=self.change_theme,
                                            width=90, height=35)
        self.theme_menu.pack(side="left")
        self.theme_menu.set("Dark")

        self.reset_btn = ctk.CTkButton(bottom_bar, text="↺ Restore Default Folder Style", fg_color="transparent",
                                       border_width=1, border_color=("#999999", "#555555"),
                                       hover_color=("#D9D9D9", "#333333"), text_color=("#000000", "#FFFFFF"),
                                       command=self.reset_folder, height=35)
        self.reset_btn.pack(side="right", fill="x", expand=True, padx=(10, 0))

    def toggle_custom_pos(self, value):
        if value == "Custom":
            self.custom_pos_frame.pack(fill="x", pady=5, after=self.pos_menu.master)
        else:
            self.custom_pos_frame.pack_forget()
        self.force_preview_update()

    def set_builtin_overlay(self, choice):
        if choice == "None":
            self.overlay_type = "none"
            self.current_overlay = None
        else:
            self.overlay_type = "builtin"
            self.current_overlay = choice.split(" ")[0]
        self.force_preview_update()

    def open_icon_picker(self):
        picker = ctk.CTkToplevel(self)
        picker.title("Select Icon")
        picker.geometry("340x400")
        picker.attributes("-topmost", True)
        picker.grab_set()

        scroll = ctk.CTkScrollableFrame(picker, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        columns = 3
        for col in range(columns):
            scroll.grid_columnconfigure(col, weight=1)

        btn_fg = ("#D9D9D9", "#3A3A4A")
        btn_hover = ("#C0C0C0", "#4A4A5A")
        btn_text = ("#000000", "#FFFFFF")

        for i, icon in enumerate(BUILTIN_ICONS):
            row = i // columns
            col = i % columns
            btn = ctk.CTkButton(scroll, text=icon, height=35, fg_color=btn_fg, hover_color=btn_hover,
                                text_color=btn_text, command=lambda c=icon, p=picker: self.select_builtin_icon(c, p))
            btn.grid(row=row, column=col, padx=4, pady=4, sticky="ew")

    def select_builtin_icon(self, choice, picker_window):
        if choice == "None":
            self.builtin_btn.configure(text="⭐ Choose Icon")
            self.set_builtin_overlay("None")
        else:
            self.builtin_btn.configure(text=choice)
            self.set_builtin_overlay(choice)

        picker_window.destroy()

    def choose_overlay(self):
        filetypes = [("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.webp"), ("All Files", "*.*")]
        file_path = filedialog.askopenfilename(title="Select Overlay Image", filetypes=filetypes)
        if file_path:
            filename = f"overlay_{int(time.time())}{os.path.splitext(file_path)[1]}"
            dest_path = os.path.join(OVERLAYS_DIR, filename)
            try:
                shutil.copy2(file_path, dest_path)
                self.current_overlay = dest_path
                self.overlay_type = "file"
                self.builtin_var.set("None")
                self.force_preview_update()
            except Exception:
                pass

    def clear_overlay(self):
        self.current_overlay = None
        self.overlay_type = "none"
        self.builtin_btn.configure(text="⭐ Choose Icon")
        self.force_preview_update()

    # ZMIENIONY COLOR PICKER - ZAWIERA TERAZ KOŁO BARW I PALETĘ
    def open_custom_color_picker(self, target="base"):
        picker = ctk.CTkToplevel(self)
        title_text = "Folder Color" if target == "base" else "Overlay Color"
        picker.title(f"Select {title_text}")
        picker.geometry("380x560")
        picker.attributes("-topmost", True)
        picker.grab_set()

        scroll = ctk.CTkScrollableFrame(picker, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        # Sekcja: Interaktywne koło
        ctk.CTkLabel(scroll, text="Interactive Color Wheel", font=("Segoe UI", 14, "bold"),
                     text_color=("#000000", "#FFFFFF")).pack(pady=(0, 5))

        wheel_size = 160
        wheel_img = self.generate_color_wheel(wheel_size)
        wheel_ctk_img = ctk.CTkImage(light_image=wheel_img, dark_image=wheel_img, size=(wheel_size, wheel_size))

        wheel_lbl = ctk.CTkLabel(scroll, text="", image=wheel_ctk_img, cursor="crosshair")
        wheel_lbl.pack(pady=5)

        # Logika podpięta pod nowe koło
        def on_popup_wheel(event, release=False):
            c = wheel_size / 2
            x, y = event.x, event.y
            dist = math.sqrt((x - c) ** 2 + (y - c) ** 2)
            if dist <= c:
                hue = (math.atan2(y - c, x - c) + math.pi) / (2 * math.pi)
                sat = dist / c
                r, g, b = [int(v * 255) for v in colorsys.hsv_to_rgb(hue, sat, 1.0)]
                hex_color = f"#{r:02x}{g:02x}{b:02x}".upper()

                if target == "base":
                    self.hex_entry.delete(0, "end")
                    self.hex_entry.insert(0, hex_color)
                    self.update_from_hex(None)
                elif target == "overlay":
                    self.overlay_color_entry.delete(0, "end")
                    self.overlay_color_entry.insert(0, hex_color)
                    self.force_preview_update()

            if release:
                picker.destroy()

        # Reaguje na przeciąganie (podgląd na żywo) i puszczenie myszy (zatwierdzenie)
        wheel_lbl.bind("<Button-1>", lambda e: on_popup_wheel(e, release=False))
        wheel_lbl.bind("<B1-Motion>", lambda e: on_popup_wheel(e, release=False))
        wheel_lbl.bind("<ButtonRelease-1>", lambda e: on_popup_wheel(e, release=True))

        # Sekcja: Paleta
        ctk.CTkLabel(scroll, text="Modern Palette", font=("Segoe UI", 14, "bold"),
                     text_color=("#000000", "#FFFFFF")).pack(pady=(20, 5))

        palette_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        palette_frame.pack()

        columns = 5
        for col in range(columns):
            palette_frame.grid_columnconfigure(col, weight=1)

        for i, hex_color in enumerate(MODERN_PALETTE):
            row = i // columns
            col = i % columns
            btn = ctk.CTkButton(palette_frame, text="", width=45, height=45, corner_radius=8,
                                fg_color=hex_color, hover_color=hex_color,
                                border_width=2, border_color=("#CCCCCC", "#333333"),
                                command=lambda c=hex_color, p=picker: self.select_custom_color(c, p, target))
            btn.grid(row=row, column=col, padx=5, pady=5)

    def select_custom_color(self, hex_color, picker_window, target):
        if target == "base":
            self.hex_entry.delete(0, "end")
            self.hex_entry.insert(0, hex_color)
            self.update_from_hex(None)
        elif target == "overlay":
            self.overlay_color_entry.delete(0, "end")
            self.overlay_color_entry.insert(0, hex_color)
            self.force_preview_update()

        picker_window.destroy()

    def generate_color_wheel(self, size):
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        pixels = img.load()
        c = size / 2
        for x in range(size):
            for y in range(size):
                dx = x - c
                dy = y - c
                dist = math.sqrt(dx ** 2 + dy ** 2)
                if dist <= c:
                    hue = (math.atan2(dy, dx) + math.pi) / (2 * math.pi)
                    sat = dist / c
                    r, g, b = [int(v * 255) for v in colorsys.hsv_to_rgb(hue, sat, 1.0)]
                    pixels[x, y] = (r, g, b, 255)
        return img

    def on_wheel_click(self, event):
        size = 140
        c = size / 2
        x, y = event.x, event.y
        dx = x - c
        dy = y - c
        dist = math.sqrt(dx ** 2 + dy ** 2)

        if dist <= c:
            hue = (math.atan2(dy, dx) + math.pi) / (2 * math.pi)
            sat = dist / c
            self.hue_slider.set(hue)
            self.sat_slider.set(sat)
            self.update_from_sliders(None)

    def generate_builtin_image(self, char):
        img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("seguiemj.ttf", 200)
        except IOError:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), char, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        draw.text(((256 - w) / 2, (256 - h) / 2 - bbox[1]), char, font=font, fill="white")
        return img

    def compose_folder_image(self, hex_color, overlay_data):
        rgb = tuple(int(hex_color.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))

        if os.path.exists(self.mask_path):
            mask_img = Image.open(self.mask_path).convert("L")
            colored_folder = ImageOps.colorize(mask_img, black="black", white=rgb, mid="#808080").convert("RGBA")
            colored_folder.putalpha(mask_img)
        else:
            colored_folder = Image.new("RGBA", (256, 256), color=rgb)

        if not overlay_data or overlay_data.get("type", "none") == "none":
            return colored_folder

        o_type = overlay_data["type"]
        o_val = overlay_data["val"]

        try:
            if o_type == "builtin":
                overlay_img = self.generate_builtin_image(o_val)
            else:
                if os.path.exists(o_val):
                    overlay_img = Image.open(o_val).convert("RGBA")
                else:
                    return colored_folder

            if overlay_data.get("colorize", False):
                o_hex = overlay_data.get("color", "#FFFFFF")
                try:
                    o_rgb = tuple(int(o_hex.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))
                    alpha = overlay_img.split()[3]
                    solid = Image.new("RGBA", overlay_img.size, o_rgb)
                    solid.putalpha(alpha)
                    overlay_img = solid
                except Exception:
                    pass

            folder_w, folder_h = colored_folder.size
            size_factor = overlay_data.get("size", 0.5)
            overlay_size = int(folder_w * size_factor)
            overlay_img = overlay_img.resize((overlay_size, overlay_size), Image.Resampling.LANCZOS)

            pos_mode = overlay_data.get("pos", "Center")

            if pos_mode == "Center":
                x = (folder_w - overlay_size) // 2
                y = (folder_h - overlay_size) // 2 + int(folder_h * 0.1)
            elif pos_mode == "Top-Left":
                x, y = int(folder_w * 0.1), int(folder_h * 0.1)
            elif pos_mode == "Top-Right":
                x, y = folder_w - overlay_size - int(folder_w * 0.1), int(folder_h * 0.1)
            elif pos_mode == "Bottom-Left":
                x, y = int(folder_w * 0.1), folder_h - overlay_size - int(folder_h * 0.1)
            elif pos_mode == "Bottom-Right":
                x, y = folder_w - overlay_size - int(folder_w * 0.1), folder_h - overlay_size - int(folder_h * 0.1)
            else:
                x = (folder_w - overlay_size) // 2 + int(overlay_data.get("x_off", 0))
                y = (folder_h - overlay_size) // 2 + int(overlay_data.get("y_off", 10))

            colored_folder.paste(overlay_img, (x, y), overlay_img)
        except Exception:
            pass

        return colored_folder

    def get_current_overlay_data(self):
        return {
            "type": self.overlay_type,
            "val": self.current_overlay,
            "colorize": self.colorize_overlay_var.get(),
            "color": self.overlay_color_entry.get().strip(),
            "size": self.ov_size_slider.get(),
            "pos": self.pos_var.get(),
            "x_off": self.ov_x_slider.get(),
            "y_off": self.ov_y_slider.get()
        }

    def force_preview_update(self, *args):
        hex_color = self.hex_entry.get().strip()
        if len(hex_color) == 7 and hex_color.startswith("#"):
            try:
                ov_data = self.get_current_overlay_data()
                colored_folder = self.compose_folder_image(hex_color, ov_data)
                colored_folder = colored_folder.resize((100, 100), Image.Resampling.LANCZOS)
                img = ctk.CTkImage(light_image=colored_folder, dark_image=colored_folder, size=(100, 100))
                self.preview_label.configure(image=img)
                self.preview_label.image = img
            except Exception:
                pass

    def update_from_sliders(self, _):
        h, s, v = self.hue_slider.get(), self.sat_slider.get(), self.val_slider.get()
        r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(h, s, v)]
        hex_color = f"#{r:02x}{g:02x}{b:02x}".upper()
        self.hex_entry.delete(0, "end")
        self.hex_entry.insert(0, hex_color)
        self.force_preview_update()

    def update_from_hex(self, event):
        hex_color = self.hex_entry.get().strip()
        if len(hex_color) == 7 and hex_color.startswith("#"):
            try:
                rgb = tuple(int(hex_color.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))
                h, s, v = colorsys.rgb_to_hsv(rgb[0] / 255, rgb[1] / 255, rgb[2] / 255)
                self.hue_slider.set(h)
                self.sat_slider.set(s)
                self.val_slider.set(v)
                self.force_preview_update()
            except ValueError:
                pass

    def add_to_library(self):
        hex_color = self.hex_entry.get().strip()
        name = self.name_entry.get().strip()
        if len(hex_color) == 7 and hex_color.startswith("#") and name:
            preset = {
                "name": name,
                "hex": hex_color,
                "overlay_data": self.get_current_overlay_data()
            }
            self.presets.append(preset)
            self.save_presets()
            self.refresh_library()
            self.tabview.set("Library")

    def remove_preset(self, index):
        del self.presets[index]
        self.save_presets()
        self.refresh_library()

    def refresh_library(self, *args):
        for widget in self.library_scroll.winfo_children():
            widget.destroy()

        mode = self.view_mode_var.get()
        columns = 4

        if mode == "Grid":
            for col_idx in range(columns):
                self.library_scroll.grid_columnconfigure(col_idx, weight=1)
        else:
            for col_idx in range(columns):
                self.library_scroll.grid_columnconfigure(col_idx, weight=0)

        search_query = self.search_var.get().lower()
        filter_type = self.filter_var.get()
        sort_type = self.sort_var.get()

        display_presets = []
        for original_idx, preset in enumerate(self.presets):
            if search_query and search_query not in preset["name"].lower():
                continue

            ov_data = preset.get("overlay_data", None)
            if not ov_data:
                old_ov = preset.get("overlay", None)
                if old_ov:
                    ov_data = {"type": "file", "val": old_ov}
                else:
                    ov_data = {"type": "none"}

            o_type = ov_data.get("type", "none")

            if filter_type == "No Overlay" and o_type != "none": continue
            if filter_type == "Built-in" and o_type != "builtin": continue
            if filter_type == "Custom Image" and o_type != "file": continue

            display_presets.append((original_idx, preset, ov_data))

        if sort_type == "Newest":
            display_presets.reverse()
        elif sort_type == "A-Z":
            display_presets.sort(key=lambda x: x[1]["name"].lower())
        elif sort_type == "Z-A":
            display_presets.sort(key=lambda x: x[1]["name"].lower(), reverse=True)

        card_bg = ("#dedede", "#2B2B36")

        for render_idx, (original_idx, preset, ov_data) in enumerate(display_presets):
            if mode == "List":
                card = ctk.CTkFrame(self.library_scroll, fg_color=card_bg, corner_radius=8)
                card.pack(fill="x", pady=4, padx=5)

                colored_folder = self.compose_folder_image(preset["hex"], ov_data)
                colored_folder = colored_folder.resize((45, 45), Image.Resampling.LANCZOS)
                img = ctk.CTkImage(light_image=colored_folder, dark_image=colored_folder, size=(45, 45))

                img_lbl = ctk.CTkLabel(card, text="", image=img)
                img_lbl.image = img
                img_lbl.pack(side="left", padx=10, pady=8)

                ctk.CTkLabel(card, text=preset["name"], font=("Segoe UI", 14, "bold")).pack(side="left", padx=10)

                ctk.CTkButton(card, text="✕", width=30, height=30, fg_color="#E74C3C", hover_color="#C0392B",
                              command=lambda idx=original_idx: self.remove_preset(idx)).pack(side="right", padx=(5, 10))
                ctk.CTkButton(card, text="Apply", width=70, height=30, fg_color="#3498DB", hover_color="#2980B9",
                              command=lambda h=preset["hex"], o=ov_data: self.apply_style(h, o)).pack(side="right",
                                                                                                      padx=5)
            else:
                row, col = render_idx // columns, render_idx % columns
                card = ctk.CTkFrame(self.library_scroll, fg_color=card_bg, corner_radius=8)
                card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

                colored_folder = self.compose_folder_image(preset["hex"], ov_data)
                colored_folder = colored_folder.resize((70, 70), Image.Resampling.LANCZOS)
                img = ctk.CTkImage(light_image=colored_folder, dark_image=colored_folder, size=(70, 70))

                img_lbl = ctk.CTkLabel(card, text="", image=img)
                img_lbl.image = img
                img_lbl.pack(pady=(10, 0))

                short_name = preset["name"][:10] + "..." if len(preset["name"]) > 10 else preset["name"]
                ctk.CTkLabel(card, text=short_name, font=("Segoe UI", 11, "bold")).pack(pady=5)

                btn_frame = ctk.CTkFrame(card, fg_color="transparent")
                btn_frame.pack(pady=(0, 10))
                ctk.CTkButton(btn_frame, text="Apply", width=45, height=25, font=("Segoe UI", 11), fg_color="#3498DB",
                              hover_color="#2980B9",
                              command=lambda h=preset["hex"], o=ov_data: self.apply_style(h, o)).pack(side="left",
                                                                                                      padx=2)
                ctk.CTkButton(btn_frame, text="✕", width=25, height=25, font=("Segoe UI", 11), fg_color="#E74C3C",
                              hover_color="#C0392B", command=lambda idx=original_idx: self.remove_preset(idx)).pack(
                    side="left", padx=2)

    def apply_style(self, hex_code, overlay_data):
        self.process(hex_code, overlay_data)

    def create_dynamic_icon(self, hex_color, overlay_data):
        icon_path = os.path.join(self.folder_path, "folder_custom.ico")
        try:
            if os.path.exists(icon_path):
                ctypes.windll.kernel32.SetFileAttributesW(icon_path, 128)
                try:
                    os.remove(icon_path)
                except OSError:
                    pass

            final_folder = self.compose_folder_image(hex_color, overlay_data)
            final_folder.save(icon_path, format="ICO", sizes=[(256, 256), (64, 64), (48, 48), (32, 32), (16, 16)])
            return icon_path
        except Exception:
            return None

    def process(self, hex_color, overlay_data):
        if self.test_mode:
            messagebox.showinfo("Test Mode",
                                f"Sukces! Aplikacja spróbowałaby teraz zmienić kolor i ikonę na {hex_color}.\n\nJesteś w trybie testowym, więc żaden plik na Twoim dysku nie został zmodyfikowany.")
            return

        icon_path = self.create_dynamic_icon(hex_color, overlay_data)
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
        if self.test_mode:
            messagebox.showinfo("Test Mode",
                                "Aplikacja spróbowałaby teraz przywrócić domyślną ikonę Windows.\n\nŻadne pliki nie zostały zmienione.")
            return
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
        self.geometry("500x380")
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

        test_btn = ctk.CTkButton(self, text="🛠️ Test GUI Mode (No Install)", fg_color="#3498DB", hover_color="#2980B9",
                                 command=self.run_test_mode)
        test_btn.pack(pady=(15, 5))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=15)

        ctk.CTkButton(btn_frame, text="Install to Context Menu", fg_color="#27AE60", hover_color="#2ECC71",
                      command=self.install).pack(side="left", expand=True, padx=5, fill="x")
        ctk.CTkButton(btn_frame, text="Uninstall", fg_color="#C0392B", hover_color="#E74C3C",
                      command=self.uninstall).pack(side="right", expand=True, padx=5, fill="x")

    def run_test_mode(self):
        self.destroy()
        app = ColorizerApp(os.path.abspath("."), test_mode=True)
        app.mainloop()

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

        key_path = r"Directory\shell\ColorizeFolder"
        try:
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, key_path) as key:
                winreg.SetValue(key, "", winreg.REG_SZ, "DirHue - Colorize")
                winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, f"{dest_path},0")
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, key_path + r"\command") as key:
                winreg.SetValue(key, "", winreg.REG_SZ, f'"{dest_path}" "%1"')
            messagebox.showinfo("Success", f"Installed successfully!\n\nLocation: {dest_path}")
        except PermissionError:
            messagebox.showerror("Error", "Run the installer as Administrator to modify the registry.")

    def uninstall(self):
        key_path = r"Directory\shell\ColorizeFolder"
        try:
            winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, key_path + r"\command")
            winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, key_path)
            messagebox.showinfo("Success", "Removed from context menu successfully.")
        except FileNotFoundError:
            pass
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