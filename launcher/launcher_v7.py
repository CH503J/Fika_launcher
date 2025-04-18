import tkinter as tk
from tkinter import filedialog
import subprocess
import os
import datetime
import threading
import psutil
import time
import signal
import json

CONFIG_PATH = "config.json"


def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"读取配置失败: {e}")
    return {}


def save_config(data):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"保存配置失败: {e}")


class AppLauncherGUI:

    def __init__(self, root):
        self.root = root
        self.root.title("AB 启动器")
        self.root.geometry("700x460")

        self.a_path = tk.StringVar()
        self.b_path = tk.StringVar()

        self.a_proc = None
        self.b_proc = None

        # A 文件选择器
        tk.Label(root, text="A 文件路径（SPT.Server.exe）:").pack(anchor="w", padx=10, pady=5)
        a_frame = tk.Frame(root)
        a_frame.pack(fill="x", padx=10)
        tk.Entry(a_frame, textvariable=self.a_path, width=60).pack(side="left", fill="x", expand=True)
        tk.Button(a_frame, text="选择", command=self.select_a_file).pack(side="left", padx=5)

        # B 文件选择器
        tk.Label(root, text="B 文件路径（Start_headless.ps1）:").pack(anchor="w", padx=10, pady=5)
        b_frame = tk.Frame(root)
        b_frame.pack(fill="x", padx=10)
        tk.Entry(b_frame, textvariable=self.b_path, width=60).pack(side="left", fill="x", expand=True)
        tk.Button(b_frame, text="选择", command=self.select_b_file).pack(side="left", padx=5)

        # 按钮栏
        button_frame = tk.Frame(root)
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="启动 A", command=self.start_a_file, width=15).pack(side="left", padx=10)
        tk.Button(button_frame, text="一键关闭 A/B", command=self.terminate_processes, width=15).pack(side="left",
                                                                                                      padx=10)

        # 日志框
        tk.Label(root, text="日志输出:").pack(anchor="w", padx=10, pady=5)
        self.log_text = tk.Text(root, height=12, wrap="word", state="disabled")
        self.log_text.pack(fill="both", padx=10, pady=(0, 10), expand=True)

        # 控制端口监控线程
        self.monitoring = False
        self.port_checked = False

        config = load_config()
        self.a_path.set(config.get("a_path", ""))
        self.b_path.set(config.get("b_path", ""))

    def log(self, message):
        timestamp = datetime.datetime.now().strftime("[%H:%M:%S]")
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"{timestamp} {message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def select_a_file(self):
        file_path = filedialog.askopenfilename(title="选择 A 文件", filetypes=[("EXE 文件", "*.exe")])
        if file_path:
            self.a_path.set(file_path)
            save_config({"a_path": file_path, "b_path": self.b_path.get()})

    def select_b_file(self):
        file_path = filedialog.askopenfilename(title="选择 B 文件", filetypes=[("PowerShell 脚本", "*.ps1")])
        if file_path:
            self.b_path.set(file_path)
            save_config({"a_path": self.a_path.get(), "b_path": file_path})

    def start_a_file(self):
        a_file = self.a_path.get()
        if os.path.exists(a_file):
            a_dir = os.path.dirname(a_file)
            try:
                self.a_proc = subprocess.Popen(a_file, cwd=a_dir, creationflags=subprocess.CREATE_NEW_CONSOLE)
                self.log(f"A 文件已启动，PID={self.a_proc.pid}")
                self.port_checked = False
                self.monitoring = True
                threading.Thread(target=self.monitor_port_6969, daemon=True).start()
            except Exception as e:
                self.log(f"A 文件启动失败: {e}")
        else:
            self.log("A 文件路径无效或不存在")

    def start_b_file(self):
        b_file = self.b_path.get()
        if os.path.exists(b_file):
            b_dir = os.path.dirname(b_file)
            try:
                self.b_proc = subprocess.Popen(
                    ["powershell", "-NoExit", "-File", b_file],
                    cwd=b_dir,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
                self.log(f"B 文件已自动启动，PID={self.b_proc.pid}")
            except Exception as e:
                self.log(f"B 文件启动失败: {e}")
        else:
            self.log("B 文件路径无效或不存在，无法启动")

    def monitor_port_6969(self):
        retry = 0
        while self.monitoring and not self.port_checked:
            time.sleep(1)
            ports_in_use = [conn.laddr.port for conn in psutil.net_connections() if conn.status == 'LISTEN']
            if 6969 in ports_in_use:
                self.log("检测到端口 6969 被占用，自动启动 B 文件 ...")
                self.port_checked = True
                self.start_b_file()
                break
            retry += 1
            if retry >= 30:
                self.log("超时未检测到端口 6969 被占用")
                break

    def terminate_processes(self):
        def kill_process_tree(pid):
            try:
                parent = psutil.Process(pid)
                for child in parent.children(recursive=True):
                    child.kill()
                parent.kill()
                self.log(f"成功关闭 PID={pid} 及其子进程")
            except Exception as e:
                self.log(f"关闭 PID={pid} 时出错: {e}")

        if self.a_proc and self.a_proc.poll() is None:
            kill_process_tree(self.a_proc.pid)
            self.a_proc = None
        else:
            self.log("A 进程未启动或已退出")

        if self.b_proc and self.b_proc.poll() is None:
            kill_process_tree(self.b_proc.pid)
            self.b_proc = None
        else:
            self.log("B 进程未启动或已退出")


if __name__ == "__main__":
    root = tk.Tk()
    app = AppLauncherGUI(root)
    root.mainloop()
