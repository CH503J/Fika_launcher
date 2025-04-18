import tkinter as tk
from tkinter import filedialog
import subprocess
import os
import datetime
import threading
import psutil
import time

class AppLauncherGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AB 启动器")
        self.root.geometry("700x420")

        self.a_path = tk.StringVar()
        self.b_path = tk.StringVar()

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

        # 启动按钮（只剩 A）
        button_frame = tk.Frame(root)
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="启动 A", command=self.start_a_file, width=15).pack(side="left", padx=10)

        # 日志框
        tk.Label(root, text="日志输出:").pack(anchor="w", padx=10, pady=5)
        self.log_text = tk.Text(root, height=10, wrap="word", state="disabled")
        self.log_text.pack(fill="both", padx=10, pady=(0, 10), expand=True)

        # 控制端口监控线程
        self.monitoring = False
        self.port_checked = False

    def log(self, message):
        timestamp = datetime.datetime.now().strftime("[%H:%M:%S]")
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"{timestamp} {message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def select_a_file(self):
        file_path = filedialog.askopenfilename(title="选择 A 文件（SPT.Server.exe）", filetypes=[("EXE 文件", "*.exe")])
        if file_path:
            self.a_path.set(file_path)

    def select_b_file(self):
        file_path = filedialog.askopenfilename(title="选择 B 文件（PowerShell 脚本）", filetypes=[("PowerShell 脚本", "*.ps1")])
        if file_path:
            self.b_path.set(file_path)

    def start_a_file(self):
        a_file = self.a_path.get()
        if os.path.exists(a_file):
            a_dir = os.path.dirname(a_file)
            try:
                subprocess.Popen(a_file, cwd=a_dir, creationflags=subprocess.CREATE_NEW_CONSOLE)
                self.log("A 文件已启动，开始监控端口 6969 ...")
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
                subprocess.Popen(["powershell", "-NoExit", "-File", b_file], cwd=b_dir, creationflags=subprocess.CREATE_NEW_CONSOLE)
                self.log("B 文件已自动启动")
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
            if retry >= 30:  # 最多检查 30 秒
                self.log("超时未检测到端口 6969 被占用")
                break

if __name__ == "__main__":
    root = tk.Tk()
    app = AppLauncherGUI(root)
    root.mainloop()
