import threading
from socket import *
from customtkinter import *
import tkinter as tk


class GradientFrame(CTkCanvas):
    def __init__(self, parent, color1, color2, **kwargs):
        super().__init__(parent, **kwargs, highlightthickness=0, bd=0)
        self.color1 = color1
        self.color2 = color2
        self.bind("<Configure>", self._draw_gradient)

    def _draw_gradient(self, event=None):
        self.delete("gradient")
        width = self.winfo_width()
        height = self.winfo_height()

        (r1,g1,b1) = self.winfo_rgb(self.color1)
        (r2,g2,b2) = self.winfo_rgb(self.color2)

        r_ratio = float(r2-r1) / height
        g_ratio = float(g2-g1) / height
        b_ratio = float(b2-b1) / height

        for i in range(height):
            nr = int(r1 + (r_ratio * i))
            ng = int(g1 + (g_ratio * i))
            nb = int(b1 + (b_ratio * i))
            color = f"#{nr//256:02x}{ng//256:02x}{nb//256:02x}"
            self.create_line(0, i, width, i, tags=("gradient",), fill=color)
        self.lower("gradient")


class MainWindow(CTk):
    def __init__(self):
        super().__init__()
        self.title("Чат")
        self.minsize(400, 300)
        self.geometry("600x400")

        self.emojis = {
            ":smile:": "😄",
            ":sad:": "😢",
            ":heart:": "❤️",
            ":ok:": "👌",
            ":fire:": "🔥",
            ":pepe:": "🐸",
            ":skull:": "💀",
            ":angry:": "😡",
            ":cool:": "😎",
        }


        self.bg = GradientFrame(self, "#120033", "#4a0033")
        self.bg.pack(fill="both", expand=True)


        self.frame = CTkFrame(self.bg, width=0, fg_color="#222")  # прозрачность не поддерживается
        self.frame.pack(side="left", fill="y")
        self.frame.pack_propagate(False)
        self.is_show_menu = False
        self.frame_width = 0

        self.label = CTkLabel(self.frame, text='Ваше Ім`я')
        self.label.pack(pady=20)

        self.entry = CTkEntry(self.frame)
        self.entry.pack(pady=5)

        self.save_btn = CTkButton(self.frame, text="Зберегти нік", command=self.save_username)
        self.save_btn.pack(pady=10)

        self.label_theme = CTkOptionMenu(self.frame, values=['Темна', 'Світла'], command=self.change_theme)
        self.label_theme.pack(side='bottom', pady=20)

        self.chat_frame = CTkFrame(self.bg, corner_radius=15)
        self.chat_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self.btn = CTkButton(self.bg, text='▶️', command=self.toggle_show_menu, width=30)
        self.btn.place(x=0, y=0)
        self.menu_show_speed = 20

        self.chat_text = CTkTextbox(self.chat_frame, state='disabled')
        self.chat_text.pack(fill="both", expand=True, padx=5, pady=(5, 0))

        self.bottom_frame = CTkFrame(self.chat_frame)
        self.bottom_frame.pack(fill="x", pady=5)

        self.message_input = CTkEntry(self.bottom_frame, placeholder_text='Введіть повідомлення:')
        self.message_input.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.message_input.bind("<Control-Return>", self.send_message_event)

        self.send_button = CTkButton(self.bottom_frame, text='▶️', width=40, command=self.send_message)
        self.send_button.pack(side="right")

        self.username = "User"

        try:
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.connect(("2.tcp.eu.ngrok.io", 16202))
            hello = f"TEXT@{self.username}@[SYSTEM] {self.username} приєднався(лась) до чату!\n"
            self.sock.send(hello.encode('utf-8'))
            threading.Thread(target=self.recv_message, daemon=True).start()
        except Exception as e:
            self.add_message(f"❌ Не вдалося підключитися: {e}")


    def toggle_show_menu(self):
        if self.is_show_menu:
            self.is_show_menu = False
            self.close_menu()
        else:
            self.is_show_menu = True
            self.show_menu()

    def show_menu(self):
        if self.frame_width <= 200:
            self.frame_width += self.menu_show_speed
            self.frame.configure(width=self.frame_width, height=self.winfo_height())
            if self.frame_width >= 30:
                self.btn.configure(width=self.frame_width, text='◀️')
        if self.is_show_menu:
            self.after(20, self.show_menu)

    def close_menu(self):
        if self.frame_width >= 0:
            self.frame_width -= self.menu_show_speed
            self.frame.configure(width=self.frame_width)
            if self.frame_width >= 30:
                self.btn.configure(width=self.frame_width, text='▶️')
        if not self.is_show_menu:
            self.after(20, self.close_menu)

    def change_theme(self, value):
        if value == 'Темна':
            set_appearance_mode('dark')
        else:
            set_appearance_mode('light')

    def send_message_event(self, event):
        self.send_message()

    def send_message(self):
        message = self.message_input.get()
        if message:
            self.add_message(f"{self.username}: {self.parse_emojis(message)}")
            data = f"TEXT@{self.username}@{message}\n"
            try:
                self.sock.sendall(data.encode())
            except:
                pass
        self.message_input.delete(0, END)

    def add_message(self, text):
        self.chat_text.configure(state='normal')
        self.chat_text.insert(END, text + '\n')
        self.chat_text.configure(state='disabled')
        self.chat_text.see(END)

    def recv_message(self):
        buffer = ""
        while True:
            try:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                buffer += chunk.decode()

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    self.handle_line(line.strip())
            except:
                break
        self.sock.close()

    def handle_line(self, line):
        if not line:
            return
        parts = line.split("@", 2)
        msg_type = parts[0]

        if msg_type == "TEXT":
            if len(parts) >= 3:
                author = parts[1]
                message = parts[2]
                if author != self.username:  # чтоб не дублировать своё
                    self.add_message(f"{author}: {self.parse_emojis(message)}")
        elif msg_type == "IMAGE":
            if len(parts) >= 3:
                author = parts[1]
                filename = parts[2]
                self.add_message(f"{author} надіслав(ла) зображення: {filename}")
        else:
            self.add_message(line)

    def save_username(self):
        new_name = self.entry.get().strip()
        if new_name:
            old_name = self.username
            self.username = new_name
            try:
                msg = f"TEXT@{self.username}@[SYSTEM] {old_name} змінив(ла) імʼя на {self.username}\n"
                self.sock.send(msg.encode('utf-8'))
            except:
                pass
            self.add_message(f"✅ Нік змінено на {self.username}")

    def parse_emojis(self, text):
        for code, emoji in self.emojis.items():
            text = text.replace(code, emoji)
        return text



win = MainWindow()
win.mainloop()
