import os
import subprocess
import socket
import threading
import time
import tkinter as tk
from tkinter import filedialog
from config.config_manager import load_config, save_config

class AppLauncherGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("App Launcher")
        self.root.geometry("500x350")

        self.config = load_config()
        self.a_path = tk.StringVar(value=self.config.get("a_path", ""))
        self.b_path = tk.StringVar(value=self.config.get("b_path", ""))

        self.a_pid = None
        self.b_pid = None
        self.b_started = False

        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.root, text="选择 A 文件:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        tk.Entry(self.root, textvariable=self.a_path, width=40).grid(row=0, column=1, padx=10, pady=10)
        tk.Button(self.root, text="浏览...", command=self.select_a_file).grid(row=0, column=2, padx=10, pady=10)

        tk.Label(self.root, text="选择 B 文件:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        tk.Entry(self.root, textvariable=self.b_path, width=40).grid(row=1, column=1, padx=10, pady=10)
        tk.Button(self.root, text="浏览...", command=self.select_b_file).grid(row=1, column=2, padx=10, pady=10)

        tk.Button(self.root, text="启动 A 文件", command=self.start_a_file).grid(row=2, column=0, columnspan=3, pady=10)
        tk.Button(self.root, text="一键关闭", command=self.terminate_processes).grid(row=3, column=0, columnspan=3, pady=10)

        tk.Label(self.root, text="日志输出:").grid(row=4, column=0, padx=10, pady=10, sticky="ne")
        self.log_text = tk.Text(self.root, width=60, height=10, state=tk.DISABLED)
        self.log_text.grid(row=4, column=1, columnspan=2, padx=10, pady=10)

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
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            self.a_pid = process.pid
            self.log(f"A 文件已启动，PID: {self.a_pid}")

            # 启动后台线程监听端口是否被占用
            threading.Thread(target=self.monitor_port_and_start_b, daemon=True).start()
        except Exception as e:
            self.log(f"启动 A 文件失败: {e}")

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
        for name, pid in [("A", self.a_pid), ("B", self.b_pid)]:
            if pid:
                try:
                    subprocess.run(["taskkill", "/PID", str(pid), "/F"], check=True)
                    killed.append(f"{name} 进程（PID {pid}）已关闭")
                except Exception as e:
                    killed.append(f"关闭 {name} 进程失败: {e}")
        self.log("\n".join(killed) if killed else "无可关闭的进程")

    def log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.config(state=tk.DISABLED)
        self.log_text.yview(tk.END)

    def save_config(self):
        save_config({
            "a_path": self.a_path.get(),
            "b_path": self.b_path.get()
        })
