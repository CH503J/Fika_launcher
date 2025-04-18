import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os

class AppLauncherGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AB 启动器")
        self.root.geometry("600x200")

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

        # 启动按钮
        button_frame = tk.Frame(root)
        button_frame.pack(pady=15)
        tk.Button(button_frame, text="启动 A", command=self.start_a_file, width=15).pack(side="left", padx=10)
        tk.Button(button_frame, text="启动 B", command=self.start_b_file, width=15).pack(side="left", padx=10)

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
            subprocess.Popen(a_file, cwd=a_dir, creationflags=subprocess.CREATE_NEW_CONSOLE)
            messagebox.showinfo("启动成功", "已启动 A 文件（SPT.Server.exe）")
        else:
            messagebox.showerror("错误", "A 文件路径无效或不存在")

    def start_b_file(self):
        b_file = self.b_path.get()
        if os.path.exists(b_file):
            b_dir = os.path.dirname(b_file)
            subprocess.Popen(["powershell", "-NoExit", "-File", b_file], cwd=b_dir, creationflags=subprocess.CREATE_NEW_CONSOLE)
            messagebox.showinfo("启动成功", "已启动 B 文件（Start_headless.ps1）")
        else:
            messagebox.showerror("错误", "B 文件路径无效或不存在")

if __name__ == "__main__":
    root = tk.Tk()
    app = AppLauncherGUI(root)
    root.mainloop()
