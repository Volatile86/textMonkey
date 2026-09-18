import os
import re
import sys
import time
import tempfile
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font

# First installed font in each list wins.
UI_FONTS = ["Inter", "Segoe UI", "SF Pro Text", "Noto Sans", "Cantarell", "DejaVu Sans"]
MONO_FONTS = ["JetBrains Mono", "Cascadia Code", "Fira Code", "SF Mono", "Consolas", "Menlo", "DejaVu Sans Mono"]

ACCENT_A = "#7c5cff"   # splash gradient start (violet)
ACCENT_B = "#00d4ff"   # splash gradient end (cyan)


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def _lerp(c1, c2, t):
    """Blend two #rrggbb colors. t=0 -> c1, t=1 -> c2."""
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def pick_font(root, candidates, fallback):
    available = set(font.families(root))
    return next((name for name in candidates if name in available), fallback)


def get_primary_monitor(root):
    """Return (x, y, width, height) of the PRIMARY monitor.

    On Linux/X11, Tk's winfo_screenwidth() returns the width of ALL monitors
    combined, so centering against it lands on the seam between two screens.
    """
    # 1) screeninfo, if installed (pip install screeninfo) - cross-platform
    try:
        from screeninfo import get_monitors
        monitors = get_monitors()
        if monitors:
            m = next((m for m in monitors if m.is_primary), monitors[0])
            return m.x, m.y, m.width, m.height
    except Exception:
        pass

    # 2) Windows: primary monitor metrics (primary always sits at 0,0)
    if sys.platform == "win32":
        try:
            import ctypes
            user32 = ctypes.windll.user32
            return 0, 0, user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        except Exception:
            pass

    # 3) Linux/X11: ask xrandr which output is primary
    if sys.platform.startswith("linux"):
        try:
            out = subprocess.run(["xrandr", "--query"], capture_output=True,
                                 text=True, timeout=2).stdout
            geo = r"(\d+)x(\d+)\+(-?\d+)\+(-?\d+)"
            m = (re.search(rf"^\S+ connected primary {geo}", out, re.M)
                 or re.search(rf"^\S+ connected {geo}", out, re.M))
            if m:
                w, h, x, y = map(int, m.groups())
                return x, y, w, h
        except Exception:
            pass

    # 4) Last resort
    return 0, 0, root.winfo_screenwidth(), root.winfo_screenheight()


def center_on_monitor(window, width, height, monitor):
    mx, my, mw, mh = monitor
    x = mx + (mw - width) // 2
    y = my + (mh - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")


# ----------------------------------------------------------------------------
# Splash screen
# ----------------------------------------------------------------------------
class SplashScreen(tk.Toplevel):
    """Borderless splash, centered on the primary monitor, with a slim progress bar."""
    WIDTH, HEIGHT = 520, 300
    PAD = 40

    def __init__(self, parent, monitor, ui_font):
        super().__init__(parent)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self._set_alpha(0.0)
        center_on_monitor(self, self.WIDTH, self.HEIGHT, monitor)

        W, H, P = self.WIDTH, self.HEIGHT, self.PAD
        self.canvas = tk.Canvas(self, width=W, height=H, highlightthickness=0, bd=0, bg="#0a0a12")
        self.canvas.pack()
        c = self.canvas

        # Vertical background gradient
        for y in range(0, H, 2):
            c.create_rectangle(0, y, W, y + 2, width=0, fill=_lerp("#1a1433", "#0a0a12", y / H))
        # Accent strip along the top edge
        for x in range(0, W, 4):
            c.create_rectangle(x, 0, x + 4, 3, width=0, fill=_lerp(ACCENT_A, ACCENT_B, x / W))
        c.create_rectangle(0, 0, W - 1, H - 1, outline="#2b2748")

        # Branding
        c.create_text(P, 105, text="🐒", font=(ui_font, 34), anchor="w")
        c.create_text(P + 62, 105, text="textMonkey", font=(ui_font, 30, "bold"), fill="#ffffff", anchor="w")
        c.create_text(P + 2, 152, text="Lightweight code & text editor",
                      font=(ui_font, 11), fill="#8b88a8", anchor="w")

        # Status + percentage
        self.status_id = c.create_text(P + 2, 232, text="Starting…", font=(ui_font, 9),
                                       fill="#a9a6c4", anchor="w")
        self.pct_id = c.create_text(W - P, 232, text="0%", font=(ui_font, 9),
                                    fill="#a9a6c4", anchor="e")

        # Progress bar: track + fill
        y = 256
        c.create_line(P, y, W - P, y, width=4, capstyle="round", fill="#241f3d")
        self.fill_id = c.create_line(P, y, P, y, width=4, capstyle="round", fill=ACCENT_B)
        self._bar_y = y
        self._value = 0

        self.update()
        self._fade(0.0, 1.0)

    def _set_alpha(self, value):
        try:
            self.attributes("-alpha", value)
        except tk.TclError:
            pass  # WM/compositor without alpha support - harmless

    def _fade(self, start, end, steps=10, delay=0.015):
        for i in range(steps + 1):
            self._set_alpha(start + (end - start) * i / steps)
            self.update()
            time.sleep(delay)

    def fade_out(self):
        self._fade(1.0, 0.0)

    def _set_bar(self, value):
        P, W = self.PAD, self.WIDTH
        x2 = P + (W - 2 * P) * value / 100
        self.canvas.coords(self.fill_id, P, self._bar_y, x2, self._bar_y)
        self.canvas.itemconfig(self.pct_id, text=f"{int(value)}%")

    def update_progress(self, value, text):
        """Animate the bar smoothly from its current value to `value`."""
        self.canvas.itemconfig(self.status_id, text=text)
        start, steps = self._value, 20
        for i in range(1, steps + 1):
            self._set_bar(start + (value - start) * i / steps)
            self.update()
            time.sleep(0.01)
        self._value = value


# ----------------------------------------------------------------------------
# Editor tab
# ----------------------------------------------------------------------------
class EditorTab(tk.Frame):
    """A single tab holding a Text widget and file metadata."""
    def __init__(self, parent, font_obj, theme):
        super().__init__(parent)
        self.filepath = None

        self.scrollbar = ttk.Scrollbar(self, orient="vertical", style="Editor.Vertical.TScrollbar")
        self.scrollbar.pack(side="right", fill="y")

        self.text_area = tk.Text(
            self, undo=True, wrap="word", font=font_obj,
            relief="flat", borderwidth=0, highlightthickness=0,
            padx=18, pady=14, spacing1=2, spacing3=2, insertwidth=2,
            yscrollcommand=self.scrollbar.set
        )
        self.text_area.pack(fill="both", expand=True)
        self.scrollbar.config(command=self.text_area.yview)

        self.apply_theme(theme)

    def apply_theme(self, theme):
        self.config(bg=theme["bg"])
        self.text_area.config(
            bg=theme["bg"], fg=theme["fg"],
            insertbackground=theme["cursor"],
            selectbackground=theme["select_bg"], selectforeground=theme["select_fg"],
            inactiveselectbackground=theme["select_bg"]
        )


# ----------------------------------------------------------------------------
# Main application
# ----------------------------------------------------------------------------
class TextMonkey:
    def __init__(self, root, splash, monitor, ui_font, mono_font):
        self.root = root
        self.splash = splash
        self.monitor = monitor
        self.ui_font = ui_font
        self.mono_font = mono_font

        splash.update_progress(20, "Loading UI components…")
        self.root.title("textMonkey 🐒")
        center_on_monitor(self.root, 1100, 700, monitor)
        self.root.minsize(640, 400)
        self.current_theme = "dark"
        self.working_directory = None
        self.menus = []

        splash.update_progress(40, "Configuring themes…")
        self._setup_styles()

        splash.update_progress(60, "Building editor interface…")
        self._create_widgets()
        self._create_menu()
        self._bind_events()
        self.set_theme(self.current_theme)

        splash.update_progress(80, "Scanning workspace…")
        self.set_workspace(os.getcwd())
        self.new_file()

        splash.update_progress(100, "Ready")
        time.sleep(0.15)

    # ---- styling ---------------------------------------------------------
    def _setup_styles(self):
        self.themes = {
            "light": {
                "name": "Light",
                "bg": "#ffffff", "fg": "#1f2328", "cursor": "#5b5bd6",
                "select_bg": "#c9d6ff", "select_fg": "#1f2328",
                "chrome_bg": "#f5f6f8", "muted": "#6e7781", "accent": "#5b5bd6",
                "border": "#e3e5ea", "status_bg": "#f5f6f8", "status_fg": "#6e7781",
                "sidebar_bg": "#f5f6f8", "sidebar_fg": "#24292f", "sidebar_select": "#e3e6ef",
                "scroll_thumb": "#d0d4dc",
            },
            "dark": {
                "name": "Dark",
                "bg": "#16161e", "fg": "#d6d9e5", "cursor": "#8b7cf6",
                "select_bg": "#33356b", "select_fg": "#ffffff",
                "chrome_bg": "#101016", "muted": "#7d8199", "accent": "#8b7cf6",
                "border": "#25253a", "status_bg": "#101016", "status_fg": "#7d8199",
                "sidebar_bg": "#101016", "sidebar_fg": "#c3c7d8", "sidebar_select": "#22222f",
                "scroll_thumb": "#2f2f45",
            },
            "cyberpunk": {
                "name": "Cyberpunk 2077",
                "bg": "#0d0221", "fg": "#c9f4ff", "cursor": "#ff2e97",
                "select_bg": "#7a04eb", "select_fg": "#ffffff",
                "chrome_bg": "#0a0118", "muted": "#8a6fb0", "accent": "#ff2e97",
                "border": "#2a0845", "status_bg": "#07000f", "status_fg": "#ff2e97",
                "sidebar_bg": "#12032b", "sidebar_fg": "#00f0ff", "sidebar_select": "#2a0845",
                "scroll_thumb": "#3a1063",
            },
        }
        self.style = ttk.Style()
        self.style.theme_use("clam")  # clam honors far more color options than "default"

        # Slim scrollbars without arrow buttons
        self.style.layout("Vertical.TScrollbar", [
            ("Vertical.Scrollbar.trough", {"sticky": "ns", "children": [
                ("Vertical.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})
            ]})
        ])
        # Treeview without the outer border
        self.style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])

    def _create_widgets(self):
        # Top control bar
        self.control_bar = tk.Frame(self.root, height=38)
        self.control_bar.pack(fill="x", side="top")
        self.control_bar.pack_propagate(False)

        self.brand_label = tk.Label(self.control_bar, text="🐒 textMonkey", font=(self.ui_font, 11, "bold"))
        self.brand_label.pack(side="left", padx=(14, 10))

        self.font_label = tk.Label(self.control_bar, text="Font size", font=(self.ui_font, 9))
        self.font_label.pack(side="left", padx=(10, 6))

        self.font_size_var = tk.IntVar(value=12)
        self.font_spinbox = ttk.Spinbox(
            self.control_bar, from_=8, to=72, textvariable=self.font_size_var,
            width=4, command=self.update_font
        )
        self.font_spinbox.pack(side="left")
        self.font_spinbox.bind("<Return>", lambda e: self.update_font())
        self.font_spinbox.bind("<FocusOut>", lambda e: self.update_font())

        self.separator = tk.Frame(self.root, height=1)
        self.separator.pack(fill="x", side="top")

        # Status bar
        self.status_bar = tk.Label(self.root, text="", anchor="e", padx=14, pady=4, font=(self.ui_font, 9))
        self.status_bar.pack(fill="x", side="bottom")

        # Resizable splitter (sidebar | editor)
        self.paned_window = tk.PanedWindow(self.root, orient="horizontal", sashwidth=3,
                                           sashrelief="flat", borderwidth=0)
        self.paned_window.pack(fill="both", expand=True)

        # Sidebar
        self.sidebar_frame = tk.Frame(self.paned_window, width=240)

        self.sidebar_header = tk.Frame(self.sidebar_frame)
        self.sidebar_header.pack(fill="x", side="top")

        self.sidebar_title = tk.Label(self.sidebar_header, text="EXPLORER",
                                      font=(self.ui_font, 8, "bold"), anchor="w", padx=14, pady=10)
        self.sidebar_title.pack(side="left", fill="x", expand=True)

        self.open_folder_btn = tk.Button(
            self.sidebar_header, text="Open…", command=self.choose_workspace_folder,
            relief="flat", borderwidth=0, padx=10, pady=2, cursor="hand2",
            font=(self.ui_font, 9)
        )
        self.open_folder_btn.pack(side="right", padx=8)

        self.file_tree = ttk.Treeview(self.sidebar_frame, show="tree", selectmode="browse")
        self.file_tree_scroll = ttk.Scrollbar(self.sidebar_frame, orient="vertical",
                                              command=self.file_tree.yview,
                                              style="Side.Vertical.TScrollbar")
        self.file_tree.configure(yscrollcommand=self.file_tree_scroll.set)
        self.file_tree_scroll.pack(side="right", fill="y")
        self.file_tree.pack(fill="both", expand=True)

        self.paned_window.add(self.sidebar_frame, minsize=160)

        # Editor tabs
        self.editor_font = font.Font(family=self.mono_font, size=12)
        self.notebook = ttk.Notebook(self.paned_window)
        self.paned_window.add(self.notebook, minsize=300)

    def _create_menu(self):
        self.menu_bar = tk.Menu(self.root, borderwidth=0)
        self.menus = [self.menu_bar]

        def add_menu(label):
            menu = tk.Menu(self.menu_bar, tearoff=0, borderwidth=0)
            self.menus.append(menu)
            self.menu_bar.add_cascade(label=label, menu=menu)
            return menu

        file_menu = add_menu("File")
        file_menu.add_command(label="New Tab", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Open File…", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Open Folder…", command=self.choose_workspace_folder)
        file_menu.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As…", command=self.save_as_file)
        file_menu.add_separator()
        file_menu.add_command(label="Print…", command=self.print_file, accelerator="Ctrl+P")
        file_menu.add_separator()
        file_menu.add_command(label="Close Tab", command=self.close_tab, accelerator="Ctrl+W")
        file_menu.add_command(label="Exit", command=self.root.quit)

        edit_menu = add_menu("Edit")
        edit_menu.add_command(label="Undo", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self.redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", command=lambda: self._focus_generate("<<Cut>>"), accelerator="Ctrl+X")
        edit_menu.add_command(label="Copy", command=lambda: self._focus_generate("<<Copy>>"), accelerator="Ctrl+C")
        edit_menu.add_command(label="Paste", command=self.paste, accelerator="Ctrl+V")
        edit_menu.add_separator()
        edit_menu.add_command(label="Select All", command=self.select_all, accelerator="Ctrl+A")

        view_menu = add_menu("View")
        view_menu.add_command(label="Toggle Sidebar", command=self.toggle_sidebar)
        view_menu.add_separator()
        theme_menu = tk.Menu(view_menu, tearoff=0, borderwidth=0)
        self.menus.append(theme_menu)
        theme_menu.add_command(label="Light", command=lambda: self.set_theme("light"))
        theme_menu.add_command(label="Dark", command=lambda: self.set_theme("dark"))
        theme_menu.add_command(label="Cyberpunk", command=lambda: self.set_theme("cyberpunk"))
        view_menu.add_cascade(label="Themes", menu=theme_menu)

        self.root.config(menu=self.menu_bar)

    def _bind_events(self):
        # Tk's built-in Text bindings are emacs-style: Ctrl+A = line start,
        # Ctrl+N = down a line, Ctrl+O = insert newline, Ctrl+P = up a line,
        # and on X11 paste doesn't replace the selection. Rebinding at the
        # "Text" class level replaces those defaults, and returning "break"
        # stops them from also running.
        def stop(handler):
            def wrapper(event=None):
                handler()
                return "break"
            return wrapper

        app_shortcuts = {
            "n": self.new_file, "o": self.open_file, "s": self.save_file,
            "w": self.close_tab, "p": self.print_file,
        }
        for key, handler in app_shortcuts.items():
            for k in (key, key.upper()):  # upper-case covers Caps Lock
                self.root.bind(f"<Control-{k}>", stop(handler))
                self.root.bind_class("Text", f"<Control-{k}>", stop(handler))

        # Editing shortcuts only apply inside the text widget
        text_shortcuts = {"a": self.select_all, "v": self.paste, "y": self.redo}
        for key, handler in text_shortcuts.items():
            for k in (key, key.upper()):
                self.root.bind_class("Text", f"<Control-{k}>", handler)
        self.root.bind_class("Text", "<<Paste>>", self.paste)

        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        # Middle-click closes a tab (button 3 is "middle" on macOS)
        self.notebook.bind("<Button-2>", self.on_middle_click_tab)
        if sys.platform == "darwin":
            self.notebook.bind("<Button-3>", self.on_middle_click_tab)

        self.file_tree.bind("<<TreeviewOpen>>", self.on_folder_expand)
        self.file_tree.bind("<Double-1>", self.on_file_double_click)

    # ---- active tab helpers ---------------------------------------------
    def get_active_tab(self):
        selected_id = self.notebook.select()
        return self.notebook.nametowidget(selected_id) if selected_id else None

    def get_active_text_area(self):
        tab = self.get_active_tab()
        return tab.text_area if tab else None

    def _focus_generate(self, sequence):
        widget = self.root.focus_get()
        if widget:
            widget.event_generate(sequence)

    # ---- editing commands (return "break" so Tk defaults don't also fire) ----
    def select_all(self, event=None):
        widget = event.widget if event is not None else self.get_active_text_area()
        if widget is not None:
            widget.tag_add("sel", "1.0", "end-1c")
        return "break"

    def paste(self, event=None):
        widget = event.widget if event is not None else self.get_active_text_area()
        if widget is None:
            return "break"
        try:
            data = widget.clipboard_get()
        except tk.TclError:
            return "break"  # clipboard empty or not text
        widget.edit_separator()
        try:
            widget.delete("sel.first", "sel.last")  # replace selection, like every other editor
        except tk.TclError:
            pass  # nothing selected
        widget.insert("insert", data)
        widget.see("insert")
        widget.edit_separator()
        self.update_status()
        return "break"

    def undo(self, event=None):
        widget = self.get_active_text_area()
        if widget is not None:
            try:
                widget.edit_undo()
            except tk.TclError:
                pass  # nothing to undo
        return "break"

    def redo(self, event=None):
        widget = event.widget if event is not None else self.get_active_text_area()
        if widget is not None:
            try:
                widget.edit_redo()
            except tk.TclError:
                pass  # nothing to redo
        return "break"

    # ---- tab middle-click -----------------------------------------------
    def on_middle_click_tab(self, event):
        try:
            index = self.notebook.tk.call(self.notebook._w, "identify", "tab", event.x, event.y)
            if index != "":
                self.close_specified_tab(self.notebook.tabs()[int(index)])
        except Exception:
            pass

    # ---- workspace / file tree ------------------------------------------
    def choose_workspace_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.set_workspace(folder)

    def set_workspace(self, path):
        self.working_directory = path
        self.file_tree.delete(*self.file_tree.get_children())
        root_node = self.file_tree.insert("", "end", text=f" {os.path.basename(path) or path}",
                                          values=[path], open=True)
        self._populate_tree(root_node, path)

    def _populate_tree(self, parent_node, path):
        try:
            entries = sorted(os.listdir(path),
                             key=lambda s: (not os.path.isdir(os.path.join(path, s)), s.lower()))
            for entry in entries:
                if entry.startswith("."):
                    continue
                full_path = os.path.join(path, entry)
                node = self.file_tree.insert(parent_node, "end", text=f" {entry}", values=[full_path])
                if os.path.isdir(full_path):
                    self.file_tree.insert(node, "end", tags=("placeholder",))
        except PermissionError:
            pass

    def on_folder_expand(self, event):
        item = self.file_tree.focus()
        children = self.file_tree.get_children(item)
        if len(children) == 1 and "placeholder" in self.file_tree.item(children[0], "tags"):
            self.file_tree.delete(children[0])
            self._populate_tree(item, self.file_tree.item(item)["values"][0])

    def on_file_double_click(self, event):
        values = self.file_tree.item(self.file_tree.focus(), "values")
        if values and os.path.isfile(values[0]):
            self.open_specific_file(values[0])

    def toggle_sidebar(self):
        if self.sidebar_frame.winfo_ismapped():
            self.paned_window.remove(self.sidebar_frame)
        else:
            self.paned_window.add(self.sidebar_frame, before=self.notebook, minsize=160)

    # ---- theming --------------------------------------------------------
    def set_theme(self, theme_key):
        if theme_key not in self.themes:
            return
        self.current_theme = theme_key
        t = self.themes[theme_key]
        ui = self.ui_font

        for tab_id in self.notebook.tabs():
            self.notebook.nametowidget(tab_id).apply_theme(t)

        # Plain tk widgets
        self.root.config(bg=t["chrome_bg"])
        self.control_bar.config(bg=t["chrome_bg"])
        self.brand_label.config(bg=t["chrome_bg"], fg=t["accent"])
        self.font_label.config(bg=t["chrome_bg"], fg=t["muted"])
        self.separator.config(bg=t["border"])
        self.status_bar.config(bg=t["status_bg"], fg=t["status_fg"])
        self.paned_window.config(bg=t["border"])
        self.sidebar_frame.config(bg=t["sidebar_bg"])
        self.sidebar_header.config(bg=t["sidebar_bg"])
        self.sidebar_title.config(bg=t["sidebar_bg"], fg=t["muted"])
        self.open_folder_btn.config(bg=t["sidebar_bg"], fg=t["accent"],
                                    activebackground=t["sidebar_select"], activeforeground=t["fg"])
        for menu in self.menus:
            menu.config(bg=t["chrome_bg"], fg=t["sidebar_fg"],
                        activebackground=t["accent"], activeforeground="#ffffff")

        # ttk widgets
        s = self.style
        s.configure("TNotebook", background=t["chrome_bg"], borderwidth=0, tabmargins=[0, 0, 0, 0])
        s.configure("TNotebook.Tab", background=t["chrome_bg"], foreground=t["muted"],
                    padding=[18, 9], borderwidth=0, focuscolor=t["chrome_bg"],
                    lightcolor=t["chrome_bg"], bordercolor=t["chrome_bg"], font=(ui, 10))
        s.map("TNotebook.Tab",
              background=[("selected", t["bg"])],
              foreground=[("selected", t["fg"])],
              lightcolor=[("selected", t["bg"])],
              bordercolor=[("selected", t["bg"])])

        s.configure("Treeview", background=t["sidebar_bg"], foreground=t["sidebar_fg"],
                    fieldbackground=t["sidebar_bg"], borderwidth=0, rowheight=26, font=(ui, 10))
        s.map("Treeview",
              background=[("selected", t["sidebar_select"])],
              foreground=[("selected", t["fg"])])

        for name, trough in (("Editor", t["bg"]), ("Side", t["sidebar_bg"])):
            style = f"{name}.Vertical.TScrollbar"
            s.configure(style, background=t["scroll_thumb"], troughcolor=trough,
                        bordercolor=trough, lightcolor=t["scroll_thumb"],
                        darkcolor=t["scroll_thumb"], gripcount=0, width=10)
            s.map(style, background=[("active", t["muted"])])

        s.configure("TSpinbox", fieldbackground=t["bg"], background=t["chrome_bg"],
                    foreground=t["fg"], arrowcolor=t["muted"], bordercolor=t["border"],
                    lightcolor=t["border"], darkcolor=t["border"], insertcolor=t["fg"], padding=3)

    def update_font(self):
        try:
            self.editor_font.configure(size=self.font_size_var.get())
        except tk.TclError:
            pass  # user is mid-typing a non-number

    # ---- status / title -------------------------------------------------
    def update_status(self, event=None):
        text_area = self.get_active_text_area()
        if not text_area:
            return
        line, col = text_area.index("insert").split(".")
        total_lines = int(text_area.index("end-1c").split(".")[0])
        chars = len(text_area.get("1.0", "end-1c"))
        self.status_bar.config(
            text=f"Ln {line}, Col {int(col) + 1}   •   {total_lines} lines   •   {chars} chars")

    def on_tab_changed(self, event=None):
        tab = self.get_active_tab()
        if tab:
            title = os.path.basename(tab.filepath) if tab.filepath else "Untitled"
            self.root.title(f"textMonkey 🐒 - {title}")
            self.update_status()

    # ---- tab operations -------------------------------------------------
    def _attach_tab(self, tab, title):
        tab.text_area.bind("<KeyRelease>", self.update_status)
        tab.text_area.bind("<ButtonRelease-1>", self.update_status)
        self.notebook.add(tab, text=f" {title} ")
        self.notebook.select(tab)
        tab.text_area.focus_set()

    def new_file(self):
        tab = EditorTab(self.notebook, self.editor_font, self.themes[self.current_theme])
        self._attach_tab(tab, "Untitled")

    def open_specific_file(self, filepath):
        for tab_id in self.notebook.tabs():
            tab = self.notebook.nametowidget(tab_id)
            if tab.filepath == filepath:
                self.notebook.select(tab)
                return

        tab = EditorTab(self.notebook, self.editor_font, self.themes[self.current_theme])
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                tab.text_area.insert("1.0", file.read())
            tab.text_area.edit_reset()  # opening the file shouldn't be undoable
        except Exception as e:
            tab.destroy()
            messagebox.showerror("Error Opening File", f"Could not read file:\n{e}")
            return

        tab.filepath = filepath
        self._attach_tab(tab, os.path.basename(filepath))

    def open_file(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("All Files", "*.*"), ("Text Files", "*.txt")]
        )
        if filepath:
            self.open_specific_file(filepath)

    def _write(self, tab, filepath):
        try:
            with open(filepath, "w", encoding="utf-8") as file:
                file.write(tab.text_area.get("1.0", "end-1c"))
            return True
        except Exception as e:
            messagebox.showerror("Error Saving File", f"Could not save file:\n{e}")
            return False

    def save_file(self):
        tab = self.get_active_tab()
        if not tab:
            return
        if tab.filepath:
            self._write(tab, tab.filepath)
        else:
            self.save_as_file()

    def save_as_file(self):
        tab = self.get_active_tab()
        if not tab:
            return
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if filepath and self._write(tab, filepath):
            tab.filepath = filepath
            filename = os.path.basename(filepath)
            self.notebook.tab(self.notebook.select(), text=f" {filename} ")
            self.root.title(f"textMonkey 🐒 - {filename}")

    def print_file(self):
        text_area = self.get_active_text_area()
        if not text_area:
            return
        content = text_area.get("1.0", "end-1c")
        if not content.strip():
            messagebox.showinfo("Print", "Nothing to print.")
            return

        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        try:
            if sys.platform == "win32":
                os.startfile(tmp_path, "print")  # async; leave the temp file for the spooler
                return
            subprocess.run(["lp", tmp_path], check=True)
        except FileNotFoundError:
            messagebox.showerror("Print", "No 'lp' command found. Install CUPS to print from here.")
        except Exception as e:
            messagebox.showerror("Print", f"Could not print:\n{e}")
        if sys.platform != "win32":
            try:
                os.remove(tmp_path)
            except OSError:
                pass

    def close_specified_tab(self, tab_id):
        if len(self.notebook.tabs()) > 1:
            self.notebook.forget(tab_id)
        else:
            tab = self.get_active_tab()
            tab.text_area.delete("1.0", tk.END)
            tab.filepath = None
            self.notebook.tab(tab_id, text=" Untitled ")
            self.root.title("textMonkey 🐒 - Untitled")

    def close_tab(self):
        current_tab_id = self.notebook.select()
        if current_tab_id:
            self.close_specified_tab(current_tab_id)


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # hide the main window while the splash runs

    monitor = get_primary_monitor(root)
    ui_font = pick_font(root, UI_FONTS, "Helvetica")
    mono_font = pick_font(root, MONO_FONTS, "Courier")

    splash = SplashScreen(root, monitor, ui_font)
    app = TextMonkey(root, splash, monitor, ui_font, mono_font)

    splash.fade_out()
    splash.destroy()
    root.deiconify()
    root.mainloop()
