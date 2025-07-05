import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading
import sys
import os

# Giả sử client.py nằm trong cùng thư mục
from client import SecureMessagingClient, SERVER_HOST, SERVER_PORT

class SecureMessagingGUI:
    def __init__(self, master):
        self.master = master
        master.title("Ứng dụng nhắn tin bảo mật")
        master.geometry("600x700")

        self.client = None
        self.user_id = None

        # --- Bước 1: ID người dùng và Đăng ký ---
        self.frame_login = tk.LabelFrame(master, text="Thiết lập người dùng", padx=10, pady=10)
        self.frame_login.pack(pady=10, fill="x", padx=10)

        tk.Label(self.frame_login, text="Nhập ID người dùng:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.user_id_entry = tk.Entry(self.frame_login, width=30)
        self.user_id_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.user_id_entry.focus_set()

        self.register_button = tk.Button(self.frame_login, text="Đăng ký & Kết nối", command=self.register_user)
        self.register_button.grid(row=1, columnspan=2, pady=10)

        # --- Khu vực thông báo trạng thái ---
        self.status_label = tk.Label(master, text="Trạng thái: Chưa kết nối", fg="blue")
        self.status_label.pack(pady=5)

        # --- Bước 2: Gửi tin nhắn ---
        self.frame_send = tk.LabelFrame(master, text="Gửi tin nhắn", padx=10, pady=10)
        # Ban đầu ẩn
        self.frame_send.pack_forget()

        tk.Label(self.frame_send, text="ID người nhận:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.recipient_entry = tk.Entry(self.frame_send, width=30)
        self.recipient_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(self.frame_send, text="Tin nhắn:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.message_text = scrolledtext.ScrolledText(self.frame_send, width=40, height=5, wrap=tk.WORD)
        self.message_text.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        self.send_button = tk.Button(self.frame_send, text="Gửi tin nhắn bảo mật", command=self.send_message_gui)
        self.send_button.grid(row=2, columnspan=2, pady=10)

        # --- Bước 3: Nhận tin nhắn ---
        self.frame_receive = tk.LabelFrame(master, text="Tin nhắn đã nhận", padx=10, pady=10)
        # Ban đầu ẩn
        self.frame_receive.pack_forget()

        self.message_display = scrolledtext.ScrolledText(self.frame_receive, width=70, height=15, state='disabled', wrap=tk.WORD, bg="#f0f0f0")
        self.message_display.pack(padx=5, pady=5, fill="both", expand=True)

        self.check_messages_button = tk.Button(self.frame_receive, text="Kiểm tra tin nhắn mới", command=self.check_messages_gui)
        self.check_messages_button.pack(pady=10)

        # --- Tính năng bổ sung ---
        self.frame_additional = tk.LabelFrame(master, text="Tính năng bổ sung", padx=10, pady=10)
        self.frame_additional.pack(pady=10, fill="x", padx=10)

        tk.Label(self.frame_additional, text=f"Máy chủ Host: {SERVER_HOST}").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        tk.Label(self.frame_additional, text=f"Cổng máy chủ: {SERVER_PORT}").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        
        self.exit_button = tk.Button(self.frame_additional, text="Thoát", command=self.exit_app)
        self.exit_button.grid(row=0, column=1, rowspan=2, padx=10, pady=5, sticky="e")

        # Cấu hình trọng số cột để thay đổi kích thước
        self.frame_login.grid_columnconfigure(1, weight=1)
        self.frame_send.grid_columnconfigure(1, weight=1)
        self.frame_additional.grid_columnconfigure(1, weight=1)


    def update_status(self, message, color="blue"):
        self.status_label.config(text=f"Trạng thái: {message}", fg=color)

    def register_user(self):
        self.user_id = self.user_id_entry.get().strip()
        if not self.user_id:
            messagebox.showerror("Lỗi nhập liệu", "Vui lòng nhập ID người dùng.")
            return

        self.update_status(f"Đang cố gắng đăng ký {self.user_id}...", "blue")
        try:
            self.client = SecureMessagingClient(self.user_id)
            self.client.register_public_key()
            self.update_status(f"Người dùng {self.user_id} đã đăng ký và kết nối!", "green")
            
            # Ẩn khung đăng nhập, hiển thị các khung khác
            self.frame_login.pack_forget()
            self.frame_send.pack(pady=10, fill="x", padx=10)
            self.frame_receive.pack(pady=10, fill="both", expand=True, padx=10)

        except Exception as e:
            self.update_status(f"Đăng ký thất bại: {e}", "red")
            messagebox.showerror("Lỗi kết nối", f"Không thể kết nối hoặc đăng ký: {e}\nVui lòng đảm bảo máy chủ đang chạy.")

    def send_message_gui(self):
        if not self.client:
            messagebox.showwarning("Chưa kết nối", "Vui lòng đăng ký ID người dùng của bạn trước.")
            return

        recipient_id = self.recipient_entry.get().strip()
        message_content = self.message_text.get("1.0", tk.END).strip()

        if not recipient_id or not message_content:
            messagebox.showwarning("Lỗi nhập liệu", "Vui lòng nhập ID người nhận và nội dung tin nhắn.")
            return

        self.update_status(f"Đang gửi tin nhắn đến {recipient_id}...", "blue")
        # Chạy gửi trong một luồng riêng để giữ cho GUI phản hồi
        threading.Thread(target=self._send_message_task, args=(recipient_id, message_content)).start()

    def _send_message_task(self, recipient_id, message_content):
        try:
            self.client.send_message(recipient_id, message_content)
            self.update_status(f"Tin nhắn đã gửi thành công đến {recipient_id}!", "green")
            # Xóa hộp tin nhắn sau khi gửi
            self.message_text.delete("1.0", tk.END)
        except Exception as e:
            self.update_status(f"Không thể gửi tin nhắn: {e}", "red")
            messagebox.showerror("Lỗi gửi", f"Không thể gửi tin nhắn: {e}")

    def check_messages_gui(self):
        if not self.client:
            messagebox.showwarning("Chưa kết nối", "Vui lòng đăng ký ID người dùng của bạn trước.")
            return

        self.update_status("Đang kiểm tra tin nhắn mới...", "blue")
        # Chạy kiểm tra trong một luồng riêng để giữ cho GUI phản hồi
        threading.Thread(target=self._check_messages_task).start()

    def _check_messages_task(self):
        try:
            # Tạm thời chuyển hướng stdout để nắm bắt các câu lệnh in của client
            # Đây là một mẹo nhỏ nhưng cho phép hiển thị đầu ra chi tiết của client
            old_stdout = sys.stdout
            sys.stdout = TextRedirector(self.message_display, "stdout")

            self.client.get_messages()

            sys.stdout = old_stdout # Khôi phục stdout
            self.update_status("Kiểm tra tin nhắn hoàn tất.", "green")

        except Exception as e:
            sys.stdout = old_stdout # Đảm bảo stdout được khôi phục ngay cả khi có lỗi
            self.update_status(f"Lỗi khi kiểm tra tin nhắn: {e}", "red")
            messagebox.showerror("Lỗi nhận", f"Lỗi khi kiểm tra tin nhắn: {e}")

    def exit_app(self):
        if messagebox.askyesno("Thoát", "Bạn có chắc chắn muốn thoát?"):
            self.master.destroy()

# Lớp trợ giúp để chuyển hướng các câu lệnh in đến tiện ích Text
class TextRedirector:
    def __init__(self, widget, tag="stdout"):
        self.widget = widget
        self.tag = tag

    def write(self, str_to_write):
        self.widget.config(state='normal')
        self.widget.insert(tk.END, str_to_write)
        self.widget.see(tk.END)
        self.widget.config(state='disabled')

    def flush(self):
        pass # Yêu cầu cho các đối tượng giống tệp

if __name__ == "__main__":
    root = tk.Tk()
    gui = SecureMessagingGUI(root)
    root.mainloop()