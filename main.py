import tkinter as tk
from launcher.gui import AppLauncherGUI
from launcher.process import ProcessManager
from launcher.logger import Logger


def main():
    root = tk.Tk()
    logger = Logger(root)
    process_manager = ProcessManager(logger)
    app = AppLauncherGUI(root, process_manager, logger)

    logger.start_update_loop()  # ✅ 确保调用
    root.mainloop()


if __name__ == "__main__":
    main()
