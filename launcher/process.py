# process.py
import os
import socket
import subprocess
import threading
import time
import psutil
import re
from config.config import load_config

class ProcessManager:
    def __init__(self, logger):
        self.logger = logger
        self.a_pid = None
        self.b_pid = None
        self.b_started = False
        self.error_pattern = re.compile(r"(error|fail)", re.IGNORECASE)
        self.warn_pattern = re.compile(r"(warn|warning)", re.IGNORECASE)

    def start_a_file(self, a_path):
        if not os.path.exists(a_path):
            self.logger.log_gui(f"A 文件路径无效：{a_path}")
            return

        self.logger.log_gui(f"正在启动 A 文件：{a_path}")
        try:
            process = subprocess.Popen(
                a_path,
                cwd=os.path.dirname(a_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW,
                text=True,
                bufsize=1,
                encoding="utf-8",
                errors="replace"
            )
            self.a_pid = process.pid
            self.logger.log_gui(f"A 文件已启动，PID: {self.a_pid}")

            threading.Thread(target=self._read_a_output, args=(process,), daemon=True).start()
            threading.Thread(target=self._monitor_port_and_start_b, daemon=True).start()
        except Exception as e:
            self.logger.log_gui(f"启动 A 文件失败: {e}")

    def _read_a_output(self, process):
        for line in process.stdout:
            decoded = line.strip()
            if self.error_pattern.search(decoded) or self.warn_pattern.search(decoded):
                self.logger.log_a(decoded)
        process.stdout.close()

    def _monitor_port_and_start_b(self):
        while not self.b_started:
            if self._is_port_in_use(6969):
                self.logger.log_gui("检测到 6969 端口被占用，准备启动 B 文件")
                self._start_b_file()
                break
            time.sleep(1)

    def _start_b_file(self):
        b_path = load_config().get("b_path", "")
        if not os.path.exists(b_path):
            self.logger.log_gui(f"B 文件路径无效：{b_path}")
            return

        try:
            self.logger.log_gui(f"尝试启动 B 文件：{b_path}")
            process = subprocess.Popen(
                ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", b_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            self.b_pid = process.pid
            self.b_started = True
            self.logger.log_gui(f"B 文件已启动，PID: {self.b_pid}")
        except Exception as e:
            self.logger.log_gui(f"启动 B 文件失败: {e}")

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
        self.logger.log_gui("\n".join(killed) if killed else "无可关闭的进程")

    @staticmethod
    def _is_port_in_use(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(("192.168.101.102", port)) == 0