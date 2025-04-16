import tkinter as tk
from tkinter import messagebox
from server import start_server

def launch_server():
    try:
        log_text.insert(tk.END, "尝试启动 Fika 本地服务器...\n")
        start_server.run_server(log_callback=lambda msg: log_text.insert(tk.END, msg + "\n"))
    except Exception as e:
        messagebox.showerror("启动失败", str(e))

app = tk.Tk()
app.title("Fika 一键开服器")
app.geometry("500x300")

start_button = tk.Button(app, text="启动服务器", command=launch_server, height=2, width=20)
start_button.pack(pady=20)

log_text = tk.Text(app, height=10, width=60)
log_text.pack(pady=10)

app.mainloop()
