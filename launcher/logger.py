# logger.py
import queue
import tkinter as tk
from threading import Lock


class Logger:
    def __init__(self, root, batch_size=50, max_lines=1000):
        self.root = root
        self.batch_size = batch_size  # 批量处理数量
        self.max_lines = max_lines    # 最大保留行数
        self.log_queues = {
            'main': queue.Queue(),
            'server': queue.Queue(),
            'headless': queue.Queue(),
            'dedicated': queue.Queue()
        }

        self.text_widgets = {}
        self.lock = Lock()  # 线程锁

    def setup_server_log(self, parent_frame):
        self.text_widgets['server'] = self._create_log_widget(parent_frame)

    def log_server(self, message):
        self._enqueue_message('server', message)

    def setup_a_log(self, parent_frame):
        self.a_log_text = self._create_log_widget(parent_frame)
        return self.a_log_text

    def setup_gui_log(self, parent_frame):
        self.gui_log_text = self._create_log_widget(parent_frame)
        return self.gui_log_text

    def _create_log_widget(self, parent):
        """创建带优化的日志组件"""
        text = tk.Text(
            parent,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=('Consolas', 10),  # 等宽字体提升渲染性能
            tabs=('0.5c', 'right')  # 优化制表符处理
        )
        scroll = tk.Scrollbar(parent, command=text.yview)
        text.configure(yscrollcommand=scroll.set)

        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        return text

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

    def setup_headless_log(self, parent_frame):
        self.text_widgets['headless'] = self._create_log_widget(parent_frame)

    def setup_dedicated_log(self, parent_frame):
        self.text_widgets['dedicated'] = self._create_log_widget(parent_frame)

    def _enqueue_message(self, log_type, message):
        """线程安全的日志入队"""
        with self.lock:
            q = self.log_queues[log_type]
            q.put(message)
            # 控制队列最大长度
            if q.qsize() > 10000:
                q.get()  # 丢弃最旧日志

    def start_update_loop(self):
        """启动批量更新循环"""
        self._process_queue()

    def _process_queue(self):
        """批量处理队列"""
        with self.lock:
            for log_type, q in self.log_queues.items():
                widget = self.text_widgets.get(log_type)
                if not widget:
                    continue

                # 批量获取日志
                messages = []
                for _ in range(self.batch_size):
                    try:
                        messages.append(q.get_nowait())
                    except queue.Empty:
                        break

                if messages:
                    self._batch_update(widget, messages)

        # 每50ms处理一次（可调节）
        self.root.after(50, self._process_queue)

    def _batch_update(self, widget, messages):
        """批量更新组件"""
        widget.configure(state=tk.NORMAL)

        # 删除超出行数
        current_lines = int(widget.index('end-1c').split('.')[0])
        if current_lines + len(messages) > self.max_lines:
            delete_count = current_lines + len(messages) - self.max_lines
            widget.delete(1.0, f"{delete_count}.0")

        # 批量插入
        widget.insert(tk.END, '\n'.join(messages) + '\n')

        # 自动滚动判断
        scrollbar_pos = widget.yview()
        if scrollbar_pos[1] >= 0.99:  # 当滚动条到底部时自动跟进
            widget.see(tk.END)

        widget.configure(state=tk.DISABLED)

    # 添加对应的日志方法
    def log_headless(self, message):
        self._enqueue_message('headless', message)

    def log_dedicated(self, message):
        self._enqueue_message('dedicated', message)

    def print_queue_status(self):
        print("当前日志队列状态：")
        for log_type, q in self.log_queues.items():
            print(f"{log_type}: {q.qsize()}条待处理")