import customtkinter as ctk

class ToastNotification(ctk.CTkToplevel):
    def __init__(self, master, title, message, duration=3000):
        super().__init__(master)
        self.title(title)
        
        # ウィンドウの装飾を消す
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.9)
        
        # メッセージ表示
        self.label = ctk.CTkLabel(self, text=f"{title}\n{message}", font=("游ゴシック", 14), padx=20, pady=10)
        self.label.pack(expand=True, fill="both")
        
        # 画面右下に表示
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        width = 300
        height = 80
        x = screen_width - width - 20
        y = screen_height - height - 60
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        # 指定時間後に閉じる
        self.after(duration, self.destroy)
        
        # クリックで即座に閉じる
        self.label.bind("<Button-1>", lambda e: self.destroy())

def show_toast(master, title, message):
    ToastNotification(master, title, message)
