import os
import sys
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font

class SplashScreen(tk.Toplevel):
    """A borderless, centered splash screen during app initialization."""
    def __init__(self, parent):
        super().__init__(parent)
        self.overrideredirect(True)  # Hide title bar and window borders

        # Dimensions
        width, height = 450, 260

        # Force Tkinter to calculate geometry relative to the primary monitor
        self.update_idletasks()

        # Get primary monitor geometry safely
        try:
            # Win32 / macOS system geometry retrieval fallback
            screen_w = self.winfo_vrootwidth() if self.winfo_vrootwidth() > 0 else self.winfo_screenwidth()
            screen_h = self.winfo_vrootheight() if self.winfo_vrootheight() > 0 else self.winfo_screenheight()

            # If total width suggests multi-monitor spanning, fall back to standard primary resolution width
            if screen_w > 2500 and self.winfo_screenwidth() != screen_w:
                screen_w = self.winfo_screenwidth()
        except Exception:
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()

        # Calculate coordinates on primary monitor
        # If running multi-monitor on Windows, x boundary offset keeps it on Primary screen (0,0)
        x = max(0, (self.winfo_screenwidth() // 2) - (width // 2))

        # If winfo_screenwidth returned combined width, cap X to primary monitor center
        if x >= self.winfo_screenwidth() // 2 and self.winfo_screenwidth() > 2500:
            x = (1920 // 2) - (width // 2) # Default primary width calculation

        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

        self.configure(bg="#1a0826")  # Cyberpunk Dark Purple

        # Branding Header
        tk.Label(
            self, text="🐒 textMonkey",
            font=("Arial", 26, "bold"), fg="#ffe600", bg="#1a0826"
        ).pack(pady=(40, 5))

        tk.Label(
            self, text="Lightweight Graphical Code & Text Editor",
            font=("Arial", 10, "italic"), fg="#00f0ff", bg="#1a0826"
        ).pack(pady=(0, 20))

        # Progress Indicator
        self.status_label = tk.Label(
            self, text="Initializing workspace...",
            font=("Arial", 9), fg="#ff007f", bg="#1a0826"
        )
        self.status_label.pack(pady=5)

        self.progress = ttk.Progressbar(self, orient="horizontal", length=350, mode="determinate")
        self.progress.pack(pady=10)

    def update_progress(self, value, text):
        self.progress["value"] = value
        self.status_label.config(text=text)
        self.update()

    """A borderless, centered splash screen during app initialization."""
    def __init__(self, parent):
        super().__init__(parent)
        self.overrideredirect(True)  # Hide title bar and window borders

        # Dimensions and Centering
        width, height = 450, 260
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w // 2) - (width // 2)
        y = (screen_h // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

        self.configure(bg="#1a0826")  # Cyberpunk Dark Purple

        # Branding Header
        tk.Label(
            self, text="🐒 textMonkey",
            font=("Arial", 26, "bold"), fg="#ffe600", bg="#1a0826"
        ).pack(pady=(40, 5))

        tk.Label(
            self, text="Lightweight Graphical Code & Text Editor",
            font=("Arial", 10, "italic"), fg="#00f0ff", bg="#1a0826"
        ).pack(pady=(0, 20))

        # Progress Indicator
        self.status_label = tk.Label(
            self, text="Initializing workspace...",
            font=("Arial", 9), fg="#ff007f", bg="#1a0826"
        )
        self.status_label.pack(pady=5)

        self.progress = ttk.Progressbar(self, orient="horizontal", length=350, mode="determinate")
        self.progress.pack(pady=10)

    def update_progress(self, value, text):
        self.progress["value"] = value
        self.status_label.config(text=text)
        self.update()


class EditorTab(tk.Frame):
    """Represents a single tab holding a Text widget and file metadata."""
    def __init__(self, parent, font_obj, theme_dict):
        super().__init__(parent)
        self.filepath = None

        self.scrollbar = tk.Scrollbar(self)
        self.scrollbar.pack(side="right", fill="y")

        self.text_area = tk.Text(
            self, undo=True, wrap="word",
            font=font_obj, relief="flat", padx=10, pady=10,
            yscrollcommand=self.scrollbar.set
        )
        self.text_area.pack(fill="both", expand=True)
        self.scrollbar.config(command=self.text_area.yview)

        self.apply_theme(theme_dict)

    def apply_theme(self, theme):
        self.text_area.config(
            bg=theme["bg"],
            fg=theme["fg"],
            insertbackground=theme["cursor"],
            selectbackground=theme["select_bg"]
        )


class TextMonkey:
    def __init__(self, root, splash):
        self.root = root
        self.splash = splash

        # Simulate Initialization Steps with Splash Screen Progress
        splash.update_progress(20, "Loading UI components...")
        time.sleep(0.2)

        self.root.title("textMonkey 🐒")
        self.root.geometry("1000x650")
        self.current_theme = "light"
        self.working_directory = None

        splash.update_progress(40, "Configuring themes...")
        time.sleep(0.2)
        self._setup_styles()

        splash.update_progress(60, "Building editor interface...")
        time.sleep(0.2)
        self._create_widgets()
        self._create_menu()
        self._bind_events()

        splash.update_progress(80, "Scanning workspace directory...")
        time.sleep(0.2)
        self.set_workspace(os.getcwd())
        self.new_file()

        splash.update_progress(100, "Ready!")
        time.sleep(0.3)

    def _setup_styles(self):
        self.themes = {
            "light": {
                "name": "Light",
                "bg": "#ffffff", "fg": "#000000", "select_bg": "#0078d7",
                "cursor": "#000000", "toolbar_bg": "#ececec", "toolbar_fg": "#000000",
                "status_bg": "#f0f0f0", "status_fg": "#333333",
                "sidebar_bg": "#f5f5f5", "sidebar_fg": "#000000", "sidebar_select": "#d9d9d9"
            },
            "dark": {
                "name": "Dark",
                "bg": "#1e1e1e", "fg": "#d4d4d4", "select_bg": "#264f78",
                "cursor": "#ffffff", "toolbar_bg": "#2d2d2d", "toolbar_fg": "#ffffff",
                "status_bg": "#252526", "status_fg": "#a0a0a0",
                "sidebar_bg": "#252526", "sidebar_fg": "#cccccc", "sidebar_select": "#37373d"
            },
            "cyberpunk": {
                "name": "Cyberpunk 2077",
                "bg": "#0d0221", "fg": "#00f0ff", "select_bg": "#7a04eb",
                "cursor": "#ff007f", "toolbar_bg": "#1a0826", "toolbar_fg": "#ffe600",
                "status_bg": "#05010d", "status_fg": "#ff007f",
                "sidebar_bg": "#12032b", "sidebar_fg": "#00f0ff", "sidebar_select": "#2a0845"
            }
        }
        self.style = ttk.Style()

    def _create_widgets(self):
        # Top Control Bar
        self.control_bar = tk.Frame(self.root, height=35)
        self.control_bar.pack(fill="x", side="top")

        self.brand_label = tk.Label(self.control_bar, text=" 🐒 textMonkey ", font=("Arial", 10, "bold"))
        self.brand_label.pack(side="left", padx=5)

        self.font_label = tk.Label(self.control_bar, text="|  Font Size:")
        self.font_label.pack(side="left", padx=5)

        self.font_size_var = tk.IntVar(value=12)
        self.font_spinbox = tk.Spinbox(
            self.control_bar, from_=8, to=72, textvariable=self.font_size_var,
            width=5, command=self.update_font
        )
        self.font_spinbox.pack(side="left", padx=5)

        # Status Bar
        self.status_bar = tk.Label(self.root, text="Lines: 1 | Chars: 0", anchor="e", padx=10)
        self.status_bar.pack(fill="x", side="bottom")

        # Main Resizable Splitter Pane (Sidebar | Editor)
        self.paned_window = tk.PanedWindow(self.root, orient="horizontal", sashwidth=4, bg="#888888")
        self.paned_window.pack(fill="both", expand=True)

        # Sidebar
        self.sidebar_frame = tk.Frame(self.paned_window, width=220)

        self.sidebar_header = tk.Frame(self.sidebar_frame)
        self.sidebar_header.pack(fill="x", side="top")

        self.sidebar_title = tk.Label(self.sidebar_header, text="EXPLORER", font=("Arial", 9, "bold"), anchor="w", padx=5, pady=4)
        self.sidebar_title.pack(side="left", fill="x", expand=True)

        self.open_folder_btn = tk.Button(self.sidebar_header, text="📁", command=self.choose_workspace_folder, relief="flat", padx=5)
        self.open_folder_btn.pack(side="right")

        # Treeview Directory Widget
        self.file_tree = ttk.Treeview(self.sidebar_frame, show="tree", selectmode="browse")
        self.file_tree_scroll = tk.Scrollbar(self.sidebar_frame, orient="vertical", command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=self.file_tree_scroll.set)

        self.file_tree_scroll.pack(side="right", fill="y")
        self.file_tree.pack(fill="both", expand=True)

        self.paned_window.add(self.sidebar_frame, minsize=150)

        # Notebook Container for Editor Tabs
        self.editor_font = font.Font(family="Consolas", size=12)
        self.notebook = ttk.Notebook(self.paned_window)
        self.paned_window.add(self.notebook, minsize=300)

        self.set_theme("light")

    def _create_menu(self):
        self.menu_bar = tk.Menu(self.root)

        # File Menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="New Tab", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Open File...", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Open Folder...", command=self.choose_workspace_folder)
        file_menu.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As...", command=self.save_as_file)
        file_menu.add_separator()
        file_menu.add_command(label="Close Tab", command=self.close_tab, accelerator="Ctrl+W")
        file_menu.add_command(label="Exit", command=self.root.quit)
        self.menu_bar.add_cascade(label="File", menu=file_menu)

        # Edit Menu
        edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        edit_menu.add_command(label="Undo", command=lambda: self.get_active_text_area().edit_undo(), accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=lambda: self.get_active_text_area().edit_redo(), accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", command=lambda: self.root.focus_get().event_generate("<<Cut>>"))
        edit_menu.add_command(label="Copy", command=lambda: self.root.focus_get().event_generate("<<Copy>>"))
        edit_menu.add_command(label="Paste", command=lambda: self.root.focus_get().event_generate("<<Paste>>"))
        self.menu_bar.add_cascade(label="Edit", menu=edit_menu)

        # View Menu
        view_menu = tk.Menu(self.menu_bar, tearoff=0)
        view_menu.add_command(label="Toggle Sidebar", command=self.toggle_sidebar)
        view_menu.add_separator()

        # Theme Sub-Menu
        theme_menu = tk.Menu(view_menu, tearoff=0)
        theme_menu.add_command(label="Light Mode", command=lambda: self.set_theme("light"))
        theme_menu.add_command(label="Dark Mode", command=lambda: self.set_theme("dark"))
        theme_menu.add_command(label="Cyberpunk ⚡", command=lambda: self.set_theme("cyberpunk"))
        view_menu.add_cascade(label="Themes", menu=theme_menu)

        self.menu_bar.add_cascade(label="View", menu=view_menu)
        self.root.config(menu=self.menu_bar)

    def _bind_events(self):
        self.root.bind("<Control-n>", lambda e: self.new_file())
        self.root.bind("<Control-o>", lambda e: self.open_file())
        self.root.bind("<Control-s>", lambda e: self.save_file())
        self.root.bind("<Control-w>", lambda e: self.close_tab())
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        # Middle Click Tab Closure
        self.notebook.bind("<Button-2>", self.on_middle_click_tab)
        if sys.platform != "darwin":
            self.notebook.bind("<Button-2>", self.on_middle_click_tab)

        # Sidebar Interactions
        self.file_tree.bind("<<TreeviewOpen>>", self.on_folder_expand)
        self.file_tree.bind("<Double-1>", self.on_file_double_click)

    # Active Tab Helpers
    def get_active_tab(self) -> EditorTab:
        selected_id = self.notebook.select()
        if selected_id:
            return self.notebook.nametowidget(selected_id)
        return None

    def get_active_text_area(self) -> tk.Text:
        tab = self.get_active_tab()
        return tab.text_area if tab else None

    # Middle Click Tab Closure
    def on_middle_click_tab(self, event):
        try:
            clicked_tab_index = self.notebook.tk.call(self.notebook._w, "identify", "tab", event.x, event.y)
            if clicked_tab_index != "":
                tab_id = self.notebook.tabs()[int(clicked_tab_index)]
                self.close_specified_tab(tab_id)
        except Exception:
            pass

    # Workspace & File Tree Functions
    def choose_workspace_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.set_workspace(folder)

    def set_workspace(self, path):
        self.working_directory = path
        self.file_tree.delete(*self.file_tree.get_children())

        root_node = self.file_tree.insert("", "end", text=f" 📂 {os.path.basename(path) or path}", values=[path], open=True)
        self._populate_tree(root_node, path)

    def _populate_tree(self, parent_node, path):
        try:
            entries = sorted(os.listdir(path), key=lambda s: (not os.path.isdir(os.path.join(path, s)), s.lower()))
            for entry in entries:
                if entry.startswith("."):
                    continue
                full_path = os.path.join(path, entry)
                is_dir = os.path.isdir(full_path)
                icon = "📂" if is_dir else "📄"

                node = self.file_tree.insert(parent_node, "end", text=f" {icon} {entry}", values=[full_path])
                if is_dir:
                    self.file_tree.insert(node, "end", text="dummy")
        except PermissionError:
            pass

    def on_folder_expand(self, event):
        selected_item = self.file_tree.focus()
        children = self.file_tree.get_children(selected_item)
        if len(children) == 1 and self.file_tree.item(children[0])["text"] == "dummy":
            self.file_tree.delete(children[0])
            folder_path = self.file_tree.item(selected_item)["values"][0]
            self._populate_tree(selected_item, folder_path)

    def on_file_double_click(self, event):
        selected_item = self.file_tree.focus()
        values = self.file_tree.item(selected_item, "values")
        if values:
            filepath = values[0]
            if os.path.isfile(filepath):
                self.open_specific_file(filepath)

    def toggle_sidebar(self):
        if self.sidebar_frame.winfo_ismapped():
            self.paned_window.remove(self.sidebar_frame)
        else:
            self.paned_window.add(self.sidebar_frame, before=self.notebook, minsize=150)

    # Theme Management
    def set_theme(self, theme_key):
        if theme_key not in self.themes:
            return

        self.current_theme = theme_key
        theme = self.themes[theme_key]

        # Apply to Tabs
        for tab_id in self.notebook.tabs():
            tab = self.notebook.nametowidget(tab_id)
            tab.apply_theme(theme)

        # Apply to Controls
        self.control_bar.config(bg=theme["toolbar_bg"])
        self.brand_label.config(bg=theme["toolbar_bg"], fg=theme["toolbar_fg"])
        self.font_label.config(bg=theme["toolbar_bg"], fg=theme["toolbar_fg"])
        self.status_bar.config(bg=theme["status_bg"], fg=theme["status_fg"])

        # Apply to Sidebar Containers
        self.sidebar_frame.config(bg=theme["sidebar_bg"])
        self.sidebar_header.config(bg=theme["sidebar_bg"])
        self.sidebar_title.config(bg=theme["sidebar_bg"], fg=theme["sidebar_fg"])
        self.open_folder_btn.config(bg=theme["sidebar_bg"], fg=theme["sidebar_fg"])

        # Configure TTK Treeview Theme Engine
        self.style.theme_use("default")
        self.style.configure(
            "Treeview",
            background=theme["sidebar_bg"],
            foreground=theme["sidebar_fg"],
            fieldbackground=theme["sidebar_bg"],
            borderwidth=0
        )
        self.style.map(
            "Treeview",
            background=[("selected", theme["sidebar_select"])],
            foreground=[("selected", theme["sidebar_fg"])]
        )

    def update_font(self):
        size = self.font_size_var.get()
        self.editor_font.configure(size=size)

    def update_status(self, event=None):
        text_area = self.get_active_text_area()
        if text_area:
            text = text_area.get("1.0", tk.END)
            lines = str(int(text_area.index("end-1c").split(".")[0]))
            chars = str(len(text) - 1)
            self.status_bar.config(text=f"Lines: {lines} | Chars: {chars}")

    def on_tab_changed(self, event=None):
        tab = self.get_active_tab()
        if tab:
            title = os.path.basename(tab.filepath) if tab.filepath else "Untitled"
            self.root.title(f"textMonkey 🐒 - {title}")
            self.update_status()

    # Tab Operations
    def new_file(self):
        theme = self.themes[self.current_theme]
        tab = EditorTab(self.notebook, self.editor_font, theme)
        tab.text_area.bind("<KeyRelease>", self.update_status)

        self.notebook.add(tab, text="Untitled")
        self.notebook.select(tab)

    def open_specific_file(self, filepath):
        for tab_id in self.notebook.tabs():
            tab = self.notebook.nametowidget(tab_id)
            if tab.filepath == filepath:
                self.notebook.select(tab)
                return

        theme = self.themes[self.current_theme]
        tab = EditorTab(self.notebook, self.editor_font, theme)

        try:
            with open(filepath, "r", encoding="utf-8") as file:
                tab.text_area.insert("1.0", file.read())
        except Exception as e:
            messagebox.showerror("Error Opening File", f"Could not read file:\n{e}")
            return

        tab.filepath = filepath
        tab.text_area.bind("<KeyRelease>", self.update_status)

        filename = os.path.basename(filepath)
        self.notebook.add(tab, text=filename)
        self.notebook.select(tab)

    def open_file(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if filepath:
            self.open_specific_file(filepath)

    def save_file(self):
        tab = self.get_active_tab()
        if not tab:
            return

        if tab.filepath:
            with open(tab.filepath, "w", encoding="utf-8") as file:
                file.write(tab.text_area.get("1.0", "end-1c"))
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
        if filepath:
            with open(filepath, "w", encoding="utf-8") as file:
                file.write(tab.text_area.get("1.0", "end-1c"))
            tab.filepath = filepath
            filename = os.path.basename(filepath)

            current_tab_id = self.notebook.select()
            self.notebook.tab(current_tab_id, text=filename)
            self.root.title(f"textMonkey 🐒 - {filename}")

    def close_specified_tab(self, tab_id):
        if len(self.notebook.tabs()) > 1:
            self.notebook.forget(tab_id)
        else:
            tab = self.get_active_tab()
            tab.text_area.delete("1.0", tk.END)
            tab.filepath = None
            self.notebook.tab(tab_id, text="Untitled")
            self.root.title("textMonkey 🐒 - Untitled")

    def close_tab(self):
        current_tab_id = self.notebook.select()
        if current_tab_id:
            self.close_specified_tab(current_tab_id)


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Hide main window during splash loading

    splash = SplashScreen(root)
    app = TextMonkey(root, splash)

    splash.destroy()  # Close splash screen
    root.deiconify() # Reveal main app window
    root.mainloop()
