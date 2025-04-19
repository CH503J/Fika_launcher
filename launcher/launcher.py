import os
import subprocess
import socket
import threading
import time
import tkinter as tk
from tkinter import filedialog
from config.config_manager import load_config, save_config
import psutil
from tkinter import ttk
import queue
import re


class AppLauncherGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("App Launcher")
        self.config = load_config()
        width = self.config.get("window_width", 500)
        height = self.config.get("window_height", 350)
        self.root.geometry(f"{width}x{height}")
        self.a_log_queue = queue.Queue()
        self.root.after(100, self.update_a_log_text)

        self.config = load_config()
        self.a_path = tk.StringVar(value=self.config.get("a_path", ""))
        self.b_path = tk.StringVar(value=self.config.get("b_path", ""))

        self.a_pid = None
        self.b_pid = None
        self.b_started = False
        self.b_child_pid = None  # 添加子进程PID属性

        self.create_widgets()

        self.root.bind("<Configure>", self.on_window_resize)

    def on_window_resize(self, event):
        if event.widget == self.root:
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            self.config["window_width"] = width
            self.config["window_height"] = height
            save_config(self.config)

    def create_widgets(self):
        tk.Label(self.root, text="选择 A 文件:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        tk.Entry(self.root, textvariable=self.a_path, width=40).grid(row=0, column=1, padx=10, pady=10)
        tk.Button(self.root, text="浏览...", command=self.select_a_file).grid(row=0, column=2, padx=10, pady=10)

        tk.Label(self.root, text="选择 B 文件:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        tk.Entry(self.root, textvariable=self.b_path, width=40).grid(row=1, column=1, padx=10, pady=10)
        tk.Button(self.root, text="浏览...", command=self.select_b_file).grid(row=1, column=2, padx=10, pady=10)

        tk.Button(self.root, text="启动 A 文件", command=self.start_a_file).grid(row=2, column=0, columnspan=3, pady=10)
        tk.Button(self.root, text="一键关闭", command=self.terminate_processes).grid(row=3, column=0, columnspan=3,
                                                                                     pady=10)

        # 创建标签页
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=4, column=1, columnspan=2, padx=10, pady=10, sticky="nsew")

        # 创建一个标签页用于 GUI 日志
        self.gui_log_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.gui_log_tab, text="GUI日志")

        # 创建一个标签页用于 A 日志
        self.a_log_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.a_log_tab, text="A")

        # 滚动条
        a_scrollbar = tk.Scrollbar(self.a_log_tab)
        a_scrollbar.grid(row=0, column=1, sticky="ns")

        # 日志框（Text 控件）
        self.a_log_text = tk.Text(
            self.a_log_tab,
            wrap=tk.WORD,
            state=tk.DISABLED,
            yscrollcommand=a_scrollbar.set
        )
        self.a_log_text.grid(row=0, column=0, sticky="nsew")

        # 滚动条与 Text 关联
        a_scrollbar.config(command=self.a_log_text.yview)

        # 让日志框可以随着窗口变化拉伸
        self.a_log_tab.grid_rowconfigure(0, weight=1)
        self.a_log_tab.grid_columnconfigure(0, weight=1)

        self.a_log_tab.grid_rowconfigure(0, weight=1)
        self.a_log_tab.grid_columnconfigure(0, weight=1)

        # 创建日志框（Text控件），并放入GUI日志标签页中
        self.gui_log_text = tk.Text(self.gui_log_tab, wrap=tk.WORD, state=tk.DISABLED)
        self.gui_log_text.grid(row=0, column=0, sticky="nsew")

        # 让日志框随窗口变化
        self.gui_log_tab.grid_rowconfigure(0, weight=1)
        self.gui_log_tab.grid_columnconfigure(0, weight=1)

        # 设置GUI日志框随窗口大小变化
        self.root.grid_rowconfigure(4, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_columnconfigure(2, weight=1)

    def append_a_log(self, message):
        self.a_log_text.config(state=tk.NORMAL)
        self.a_log_text.insert(tk.END, message + "\n")
        self.a_log_text.config(state=tk.DISABLED)
        self.a_log_text.yview(tk.END)

    def select_a_file(self):
        file_path = filedialog.askopenfilename(title="选择 A 文件", filetypes=[("EXE 文件", "*.exe")])
        if file_path:
            self.a_path.set(file_path)
            self.save_config()

    def select_b_file(self):
        file_path = filedialog.askopenfilename(title="选择 B 文件", filetypes=[("PowerShell 脚本", "*.ps1")])
        if file_path:
            self.b_path.set(file_path)
            self.save_config()

    def start_a_file(self):
        a_file_path = self.a_path.get()
        if not os.path.exists(a_file_path):
            self.log(f"A 文件路径无效：{a_file_path}")
            return

        self.log(f"正在启动 A 文件：{a_file_path}")
        try:
            process = subprocess.Popen(
                a_file_path,
                cwd=os.path.dirname(a_file_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW,
                text=True,
                bufsize=1,
                encoding="utf-8",
                errors="replace"
            )
            self.a_pid = process.pid
            self.log(f"A 文件已启动，PID: {self.a_pid}")

            # 启动后台线程读取输出
            threading.Thread(target=self.read_a_output, args=(process,), daemon=True).start()
            threading.Thread(target=self.monitor_port_and_start_b, daemon=True).start()
        except Exception as e:
            self.log(f"启动 A 文件失败: {e}")

    def read_a_output(self, process):
        # 正则表达式判断日志是否包含错误或警告
        error_pattern = re.compile(r"(error|fail)", re.IGNORECASE)  # 匹配错误日志
        warn_pattern = re.compile(r"(warn|warning)", re.IGNORECASE)  # 匹配警告日志

        for line in process.stdout:
            decoded = line.strip()

            # 如果日志中包含 "error" 或 "fail"，或者 "warn" 或 "warning"（不区分大小写），就显示
            if error_pattern.search(decoded) or warn_pattern.search(decoded):
                self.append_a_log(decoded)
            # 如果是其他日志，不输出
            else:
                continue

        process.stdout.close()

    def update_progress_line(self, text):
        self.a_log_text.config(state=tk.NORMAL)
        # 删除最后一行进度条
        self.a_log_text.delete("end-2l", "end-1l")  # 删除倒数第二行
        self.a_log_text.insert("end-1l", text + "\n")  # 插入新的进度条
        self.a_log_text.config(state=tk.DISABLED)
        self.a_log_text.yview(tk.END)

    def append_log_line(self, text):
        self.a_log_text.config(state=tk.NORMAL)
        self.a_log_text.insert(tk.END, text + "\n")
        self.a_log_text.config(state=tk.DISABLED)
        self.a_log_text.yview(tk.END)

    def update_a_log_text(self):
        try:
            while True:
                line = self.a_log_queue.get_nowait()
                self.a_log_text.config(state=tk.NORMAL)
                self.a_log_text.insert(tk.END, line + "\n")
                self.a_log_text.config(state=tk.DISABLED)
                self.a_log_text.yview(tk.END)
        except queue.Empty:
            pass
        self.root.after(100, self.update_a_log_text)

    def monitor_port_and_start_b(self):
        while not self.b_started:
            if self.is_port_in_use(6969):
                self.log("检测到 6969 端口被占用，准备启动 B 文件")
                self.start_b_file()
                break
            time.sleep(1)

    def is_port_in_use(self, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            result = s.connect_ex(("192.168.101.102", port))  # 检查本机所有 IP
            return result == 0

    def start_b_file(self):
        b_file_path = self.b_path.get()
        if not os.path.exists(b_file_path):
            self.log(f"B 文件路径无效：{b_file_path}")
            return

        try:
            self.log(f"尝试启动 B 文件：{b_file_path}")
            process = subprocess.Popen(
                ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", b_file_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_CONSOLE  # 开独立窗口
            )
            self.b_pid = process.pid
            self.b_started = True
            self.log(f"B 文件已启动，PID: {self.b_pid}")

        except Exception as e:
            self.log(f"启动 B 文件失败: {e}")

    def terminate_processes(self):
        killed = []

        # 先关闭 A 和 B 的主进程
        for name, pid in [("A", self.a_pid), ("B", self.b_pid)]:
            if pid:
                try:
                    subprocess.run(["taskkill", "/PID", str(pid), "/F"], check=True)
                    killed.append(f"{name} 进程（PID {pid}）已关闭")
                except Exception as e:
                    killed.append(f"关闭 {name} 进程失败: {e}")

        # 再检测并关闭 B 的子进程 C（EscapeFromTarkov.exe）
        c_killed = False
        if self.b_pid:
            try:
                parent = psutil.Process(self.b_pid)

                # 尝试等待子进程出现（最多3秒）
                for _ in range(3):
                    children = parent.children(recursive=True)
                    c_proc = next((child for child in children if child.name() == "EscapeFromTarkov.exe"), None)
                    if c_proc:
                        c_proc.kill()
                        killed.append(f"C 进程（EscapeFromTarkov.exe，PID {c_proc.pid}）已关闭")
                        c_killed = True
                        break
                    time.sleep(1)

                if not c_killed:
                    killed.append("未检测到 C 进程（EscapeFromTarkov.exe）或其已提前退出")

            except psutil.NoSuchProcess:
                killed.append("B 进程已退出，无法检测子进程")
            except Exception as e:
                killed.append(f"检测/关闭 C 进程失败: {e}")

        self.log("\n".join(killed) if killed else "无可关闭的进程")

    def log(self, message):
        # 始终输出到GUI日志框
        self.gui_log_text.config(state=tk.NORMAL)
        self.gui_log_text.insert(tk.END, message + "\n")
        self.gui_log_text.config(state=tk.DISABLED)
        self.gui_log_text.yview(tk.END)

    def save_config(self):
        save_config({
            "a_path": self.a_path.get(),
            "b_path": self.b_path.get()
        })
