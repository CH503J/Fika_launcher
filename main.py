import tkinter as tk
from launcher.launcher import AppLauncherGUI  # 从 launcher 中导入 GUI 类

def main():
    root = tk.Tk()
    AppLauncherGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
