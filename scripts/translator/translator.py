# -*- coding: utf-8 -*-
"""Bot dịch Việt ↔ Anh để chat với khách nước ngoài qua Zalo.

Mở app: hiện hình bot nổi ở góc màn hình (kéo để dời chỗ).
  - Bấm vào bot → mở / ẩn khung chat.
  - Chuột phải vào bot → menu (Mở khung chat, Thoát).
Trong khung chat:
  - Gõ tiếng Việt rồi Enter → bot trả tiếng Anh, tự chép sẵn, sang Zalo bấm Ctrl+V.
  - Dán tin tiếng Anh của khách rồi Enter → bot trả tiếng Việt.
  - Bấm vào câu dịch cũ để chép lại. Shift+Enter = xuống dòng.

Dịch qua dịch vụ Google Translate miễn phí (cần Internet, không cần khoá API).
Chữ bạn gõ được gửi lên Google để dịch – không gõ mật khẩu / thông tin mật vào đây.
Hình bot ở thư mục assets (vẽ bằng make_bot_icon.py).

Chạy thử không mở cửa sổ:  python translator.py --test
"""
import json
import os
import random
import sys
import threading
import tkinter as tk
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
SETTINGS = os.path.join(HERE, "settings.json")

URL = "https://translate.googleapis.com/translate_a/single"
TIMEOUT_S = 15

KEY_COLOR = "#8c96a0"   # nền hình bot, đặt trong suốt (trùng make_bot_icon.py)
HEADER_BG = "#0068ff"
CHAT_BG = "#f2f4f7"
ME_BG = "#d6e8ff"
BOT_BG = "#ffffff"
FONT = ("Segoe UI", 11)
GREETING = ("Chào bạn! Gõ tiếng Việt, mình dịch sang tiếng Anh và chép sẵn để dán vào Zalo.\n"
            "Dán tin tiếng Anh của khách, mình dịch sang tiếng Việt.")


# ---------------------------------------------------------------- Dịch
def google_translate(text, source, target):
    """Gọi Google Translate; trả về (bản dịch, ngôn ngữ nguồn đã nhận)."""
    params = urllib.parse.urlencode(
        {"client": "gtx", "sl": source, "tl": target, "dt": "t", "q": text}
    )
    req = urllib.request.Request(URL + "?" + params, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    translated = "".join(part[0] for part in data[0] if part and part[0])
    return translated, data[2]


def translate_auto(text):
    """Tiếng Việt → Anh, còn lại (tiếng Anh…) → Việt. Trả về (bản dịch, chiều dịch)."""
    out, src = google_translate(text, "auto", "en")
    if src == "vi":
        return out, "VI → EN"
    out, src = google_translate(text, "auto", "vi")
    return out, "%s → VI" % src.upper()


def virtual_screen(widget):
    """(x, y, rộng, cao) vùng gộp mọi màn hình; Tk trên Windows chỉ biết màn hình chính."""
    try:
        import ctypes
        m = ctypes.windll.user32.GetSystemMetrics
        return m(76), m(77), m(78), m(79)
    except Exception:
        return 0, 0, widget.winfo_screenwidth(), widget.winfo_screenheight()


# ---------------------------------------------------------------- Lưu vị trí bot
def load_settings():
    try:
        with open(SETTINGS, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_settings(data):
    try:
        with open(SETTINGS, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass


# ---------------------------------------------------------------- Khung chat
class ChatWindow:
    def __init__(self, master, head_img):
        self.busy = False
        self.msg_no = 0
        win = self.win = tk.Toplevel(master)
        win.title("Bot dịch Việt ↔ Anh")
        win.geometry("380x540")
        win.minsize(320, 380)
        win.configure(bg=CHAT_BG)
        win.protocol("WM_DELETE_WINDOW", self.hide)
        win.attributes("-topmost", True)

        head = tk.Frame(win, bg=HEADER_BG)
        head.pack(fill="x")
        if head_img is not None:
            tk.Label(head, image=head_img, bg=HEADER_BG).pack(side="left", padx=(10, 6), pady=6)
        tk.Label(head, text="Bot dịch Việt ↔ Anh", bg=HEADER_BG, fg="white",
                 font=("Segoe UI", 12, "bold")).pack(side="left")
        self.topmost = tk.BooleanVar(value=True)
        tk.Checkbutton(head, text="Luôn nổi", variable=self.topmost, bg=HEADER_BG, fg="white",
                       selectcolor=HEADER_BG, activebackground=HEADER_BG,
                       activeforeground="white", font=("Segoe UI", 9),
                       command=lambda: win.attributes("-topmost", self.topmost.get())
                       ).pack(side="right", padx=8)

        bottom = tk.Frame(win, bg="white")
        bottom.pack(side="bottom", fill="x")
        self.status = tk.Label(bottom, text="Enter = dịch · Shift+Enter = xuống dòng",
                               bg="white", fg="#888", font=("Segoe UI", 8), anchor="w")
        self.status.pack(fill="x", padx=10, pady=(4, 0))
        row = tk.Frame(bottom, bg="white")
        row.pack(fill="x", padx=8, pady=(2, 8))
        self.inp = tk.Text(row, height=3, wrap="word", font=FONT, relief="solid", bd=1,
                           highlightthickness=0)
        self.inp.pack(side="left", fill="x", expand=True)
        self.inp.bind("<Return>", self.on_enter)
        tk.Button(row, text="Dịch", font=("Segoe UI", 10, "bold"), bg=HEADER_BG, fg="white",
                  activebackground="#0050c8", activeforeground="white", relief="flat",
                  padx=14, command=self.send).pack(side="right", fill="y", padx=(6, 0))

        body = tk.Frame(win, bg=CHAT_BG)
        body.pack(fill="both", expand=True)
        sb = tk.Scrollbar(body)
        sb.pack(side="right", fill="y")
        self.log = tk.Text(body, wrap="word", font=FONT, bg=CHAT_BG, relief="flat", bd=0,
                           padx=8, pady=8, cursor="arrow", yscrollcommand=sb.set,
                           spacing1=2, spacing3=2)
        self.log.pack(side="left", fill="both", expand=True)
        sb.config(command=self.log.yview)
        self.log.tag_configure("me", justify="right", lmargin1=70, lmargin2=70, rmargin=4,
                               background=ME_BG)
        self.log.tag_configure("bot", justify="left", lmargin1=4, lmargin2=4, rmargin=70,
                               background=BOT_BG)
        self.log.tag_configure("note_me", justify="right", foreground="#8a94a3",
                               font=("Segoe UI", 8), rmargin=4)
        self.log.tag_configure("note_bot", justify="left", foreground="#8a94a3",
                               font=("Segoe UI", 8), lmargin1=4)
        self.log.tag_configure("err", foreground="#c00000")
        self.log.config(state="disabled")
        self.add_bot(GREETING, "")

    # -- hiển thị
    def show_near(self, bx, by, bw, bh):
        self.win.update_idletasks()
        w, h = self.win.winfo_width(), self.win.winfo_height()
        if w < 50:
            w, h = 380, 540
        vx, vy, vw, vh = virtual_screen(self.win)
        x = bx - w - 10 if bx - w - 10 >= vx else bx + bw + 10
        x = max(vx, min(x, vx + vw - w))
        y = max(vy, min(by + bh - h, vy + vh - h - 40))
        self.win.geometry("+%d+%d" % (x, y))
        self.win.deiconify()
        self.win.lift()
        self.inp.focus_set()

    def hide(self):
        self.win.withdraw()

    def visible(self):
        return self.win.state() != "withdrawn"

    # -- tin nhắn
    def _append(self, text, tag, note, note_tag, extra_tag=None):
        self.log.config(state="normal")
        tags = (tag, extra_tag) if extra_tag else (tag,)
        self.log.insert("end", " " + text + " \n", tags)
        if note:
            self.log.insert("end", note + "\n", note_tag)
        self.log.insert("end", "\n")
        self.log.config(state="disabled")
        self.log.see("end")

    def add_me(self, text):
        self._append(text, "me", "", "note_me")

    def add_bot(self, text, note, copyable=False, error=False):
        copy_tag = "err" if error else None
        if copyable:
            self.msg_no += 1
            copy_tag = "copy%d" % self.msg_no
            self.log.tag_bind(copy_tag, "<Button-1>", lambda e, t=text: self.copy(t, True))
            self.log.tag_bind(copy_tag, "<Enter>", lambda e: self.log.config(cursor="hand2"))
            self.log.tag_bind(copy_tag, "<Leave>", lambda e: self.log.config(cursor="arrow"))
        self._append(text, "bot", note, "note_bot", copy_tag)

    def copy(self, text, tell=False):
        self.win.clipboard_clear()
        self.win.clipboard_append(text)
        if tell:
            self.status.config(text="Đã chép lại câu dịch", fg="#080")

    # -- dịch
    def on_enter(self, event):
        if event.state & 0x0001:  # Shift+Enter: xuống dòng
            return None
        self.send()
        return "break"

    def send(self):
        text = self.inp.get("1.0", "end").strip()
        if not text or self.busy:
            return
        self.busy = True
        self.inp.delete("1.0", "end")
        self.add_me(text)
        self.status.config(text="Đang dịch…", fg="#666")
        threading.Thread(target=self._worker, args=(text,), daemon=True).start()

    def _worker(self, text):
        try:
            result, direction = translate_auto(text)
            self.win.after(0, self._done, result, direction, None)
        except Exception as exc:  # mất mạng, Google chặn…
            self.win.after(0, self._done, None, None, exc)

    def _done(self, result, direction, error):
        self.busy = False
        if error is not None:
            self.add_bot("Không dịch được: %s" % error, "Kiểm tra Internet rồi gửi lại.",
                         error=True)
            self.status.config(text="Lỗi khi dịch", fg="#c00")
            return
        self.add_bot(result, direction + " · bấm vào để chép lại", copyable=True)
        self.copy(result)
        self.status.config(text="%s · đã chép, sang Zalo bấm Ctrl+V" % direction, fg="#080")


# ---------------------------------------------------------------- Bot nổi
class FloatingBot:
    def __init__(self, root, start_pos=None):
        self.root = root
        self.settings = load_settings()
        self.img = tk.PhotoImage(file=os.path.join(ASSETS, "bot.png"))
        self.img_blink = tk.PhotoImage(file=os.path.join(ASSETS, "bot_blink.png"))
        try:
            self.img_head = tk.PhotoImage(file=os.path.join(ASSETS, "bot_head.png"))
        except tk.TclError:
            self.img_head = None
        if self.img_head is not None:
            root.iconphoto(True, self.img_head)  # thay icon lông chim của Tk

        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.configure(bg=KEY_COLOR)
        root.attributes("-transparentcolor", KEY_COLOR)
        self.label = tk.Label(root, image=self.img, bg=KEY_COLOR, bd=0, cursor="hand2")
        self.label.pack()

        bw, bh = self.img.width(), self.img.height()
        if start_pos is None:
            pos = self.settings.get("bot_pos")
            if pos and self._on_screen(pos[0], pos[1]):
                start_pos = pos
            else:
                start_pos = (root.winfo_screenwidth() - bw - 24,
                             root.winfo_screenheight() - bh - 60)
        root.geometry("%dx%d+%d+%d" % (bw, bh, start_pos[0], start_pos[1]))

        self.chat = ChatWindow(root, self.img_head)
        self.chat.hide()

        self.menu = tk.Menu(root, tearoff=0)
        self.menu.add_command(label="Mở / ẩn khung chat", command=self.toggle_chat)
        self.menu.add_separator()
        self.menu.add_command(label="Thoát", command=self.quit)

        self.label.bind("<ButtonPress-1>", self.on_press)
        self.label.bind("<B1-Motion>", self.on_drag)
        self.label.bind("<ButtonRelease-1>", self.on_release)
        self.label.bind("<Button-3>", lambda e: self.menu.tk_popup(e.x_root, e.y_root))
        self.root.after(2500, self.blink)

    def _on_screen(self, x, y):
        vx, vy, vw, vh = virtual_screen(self.root)
        return vx <= x <= vx + vw - 40 and vy <= y <= vy + vh - 40

    def on_press(self, e):
        self.drag_from = (e.x_root, e.y_root, self.root.winfo_x(), self.root.winfo_y())
        self.moved = False

    def on_drag(self, e):
        sx, sy, wx, wy = self.drag_from
        dx, dy = e.x_root - sx, e.y_root - sy
        if abs(dx) + abs(dy) > 4:
            self.moved = True
        if self.moved:
            self.root.geometry("+%d+%d" % (wx + dx, wy + dy))

    def on_release(self, e):
        if self.moved:
            self.settings["bot_pos"] = [self.root.winfo_x(), self.root.winfo_y()]
            save_settings(self.settings)
        else:
            self.toggle_chat()

    def toggle_chat(self):
        if self.chat.visible():
            self.chat.hide()
        else:
            self.open_chat()

    def open_chat(self):
        self.chat.show_near(self.root.winfo_x(), self.root.winfo_y(),
                            self.img.width(), self.img.height())

    def blink(self):
        self.label.config(image=self.img_blink)
        self.root.after(160, lambda: self.label.config(image=self.img))
        self.root.after(random.randint(2500, 6000), self.blink)

    def quit(self):
        self.root.destroy()


# ---------------------------------------------------------------- Chạy thử
def self_test():
    for sample in ("Chào anh, em sẽ gửi bản vẽ mặt bằng tầng 3 vào thứ Sáu.",
                   "Could you send me the revised drawings by next Monday?"):
        result, direction = translate_auto(sample)
        print("%s | %s\n    -> %s" % (direction, sample, result))
    root = tk.Tk()
    root.withdraw()
    FloatingBot(root, start_pos=(100, 100))
    root.update()
    root.destroy()
    print("Bot + khung chat dựng được: OK")


if __name__ == "__main__":
    if "--test" in sys.argv:
        sys.stdout.reconfigure(encoding="utf-8")
        self_test()
    else:
        root = tk.Tk()
        FloatingBot(root)
        root.mainloop()
