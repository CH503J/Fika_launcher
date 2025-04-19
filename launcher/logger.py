# logger.py
import queue
import tkinter as tk

class Logger:
    def __init__(self, root):
        self.root = root
        self.a_log_queue = queue.Queue()
        self._setup_log_updates()

    def setup_a_log(self, parent_frame):
        self.a_log_text = self._create_log_widget(parent_frame)
        return self.a_log_text

    def setup_gui_log(self, parent_frame):
        self.gui_log_text = self._create_log_widget(parent_frame)
        return self.gui_log_text

    def _create_log_widget(self, parent):
        scrollbar = tk.Scrollbar(parent)
        scrollbar.grid(row=0, column=1, sticky="ns")

        log_text = tk.Text(
            parent,
            wrap=tk.WORD,
            state=tk.DISABLED,
            yscrollcommand=scrollbar.set
        )
        log_text.grid(row=0, column=0, sticky="nsew")

        scrollbar.config(command=log_text.yview)
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        return log_text

    def log_a(self, message):
        self._update_log(self.a_log_text, message)

    def log_gui(self, message):
        self._update_log(self.gui_log_text, message)

    def _update_log(self, text_widget, message):
        text_widget.config(state=tk.NORMAL)
        text_widget.insert(tk.END, message + "\n")
        text_widget.config(state=tk.DISABLED)
        text_widget.yview(tk.END)

    def _setup_log_updates(self):
        def update_a_log():
            try:
                while True:
                    line = self.a_log_queue.get_nowait()
                    self.log_a(line)
            except queue.Empty:
                pass
            self.root.after(100, update_a_log)
        self.root.after(100, update_a_log)