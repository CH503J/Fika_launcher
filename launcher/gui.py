# gui.py
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from config.config import load_config, save_config


class AppLauncherGUI:
    def __init__(self, root, process_manager, logger):
        self.root = root
        self.process_manager = process_manager
        self.logger = logger
        self.config = load_config()

        self.root.title("Fika开服器")
        self._setup_window()
        self._create_widgets()
        self._bind_events()

    def _setup_window(self):
        # 窗口初始尺寸
        width = self.config.get("window_width", 500)
        height = self.config.get("window_height", 350)
        self.root.geometry(f"{width}x{height}")

        # 配置网格布局权重（关键修改）
        self.root.grid_columnconfigure(0, weight=0)  # 标签列固定宽度
        self.root.grid_columnconfigure(1, weight=1)  # 输入框列可拉伸
        self.root.grid_columnconfigure(2, weight=0)  # 按钮列固定宽度
        self.root.grid_rowconfigure(4, weight=1)  # 第4行可拉伸

    def _create_widgets(self):
        # 路径选择组件
        self._create_path_selector()
        # 操作按钮
        self._create_action_buttons()
        # 日志标签页（关键修改位置）
        self._create_log_tabs()

    def _create_path_selector(self):
        self.a_path = tk.StringVar(value=self.config.get("a_path", ""))
        self.b_path = tk.StringVar(value=self.config.get("b_path", ""))

        # 第一行组件
        tk.Label(self.root, text="服务端路径：").grid(row=0, column=0, padx=(10,5), pady=10, sticky="e")
        tk.Entry(self.root, textvariable=self.a_path, width=40).grid(row=0, column=1, padx=5, pady=10, sticky="ew")
        tk.Button(self.root, text="浏览...", command=self.select_a_file).grid(row=0, column=2, padx=(5,10), pady=10)

        # 第二行组件
        tk.Label(self.root, text="Headless路径：").grid(row=1, column=0, padx=(10,5), pady=10, sticky="e")
        tk.Entry(self.root, textvariable=self.b_path, width=40).grid(row=1, column=1, padx=5, pady=10, sticky="ew")
        tk.Button(self.root, text="浏览...", command=self.select_b_file).grid(row=1, column=2, padx=(5,10), pady=10)

    def _create_action_buttons(self):
        # 操作按钮居中显示
        tk.Button(self.root, text="启动专用主机", command=self.start_a_file).grid(
            row=2, column=0, columnspan=3, pady=10, sticky="ew")
        tk.Button(self.root, text="一键关闭", command=self.terminate_processes).grid(
            row=3, column=0, columnspan=3, pady=10, sticky="ew")

    def _create_log_tabs(self):
        # 创建Notebook容器（关键修改）
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(
            row=4,
            column=0,
            columnspan=3,  # 跨所有三列
            padx=10,       # 左右对称边距
            pady=10,
            sticky="nsew"
        )

        # GUI日志标签页
        gui_log_frame = ttk.Frame(self.notebook)
        self._configure_tab_layout(gui_log_frame)
        self.notebook.add(gui_log_frame, text="日志")
        self.logger.setup_gui_log(gui_log_frame)

        # 服务端日志标签页
        a_log_frame = ttk.Frame(self.notebook)
        self._configure_tab_layout(a_log_frame)
        self.notebook.add(a_log_frame, text="服务端")
        self.logger.setup_a_log(a_log_frame)

        # Headless日志标签页
        a_log_frame = ttk.Frame(self.notebook)
        self._configure_tab_layout(a_log_frame)
        self.notebook.add(a_log_frame, text="Headless")
        self.logger.setup_a_log(a_log_frame)

        # 专用主机日志标签页
        a_log_frame = ttk.Frame(self.notebook)
        self._configure_tab_layout(a_log_frame)
        self.notebook.add(a_log_frame, text="专用主机")
        self.logger.setup_a_log(a_log_frame)

    def _configure_tab_layout(self, tab):
        """统一配置标签页布局"""
        tab.grid_rowconfigure(0, weight=1)
        tab.grid_columnconfigure(0, weight=1)

    def _bind_events(self):
        self.root.bind("<Configure>", self.on_window_resize)

    def on_window_resize(self, event):
        if event.widget == self.root:
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            self.config["window_width"] = width
            self.config["window_height"] = height
            save_config(self.config)

    def select_a_file(self):
        file_path = filedialog.askopenfilename(title="选择服务端", filetypes=[("EXE 文件", "*.exe")])
        if file_path:
            self.a_path.set(file_path)
            self._save_path_config()

    def select_b_file(self):
        file_path = filedialog.askopenfilename(title="选择Headless", filetypes=[("PowerShell 脚本", "*.ps1")])
        if file_path:
            self.b_path.set(file_path)
            self._save_path_config()

    def start_a_file(self):
        self.process_manager.start_a_file(self.a_path.get())

    def terminate_processes(self):
        self.process_manager.terminate_processes()

    def _save_path_config(self):
        save_config({
            "a_path": self.a_path.get(),
            "b_path": self.b_path.get()
        })