import subprocess
import os
from server.config import SERVER_PATH

def run_server(log_callback=print):
    if not os.path.exists(SERVER_PATH):
        raise FileNotFoundError(f"服务器路径不存在: {SERVER_PATH}")

    log_callback("正在启动服务器，请稍等...")
    process = subprocess.Popen([SERVER_PATH], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    for line in process.stdout:
        log_callback(line.strip())
