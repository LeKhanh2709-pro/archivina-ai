# -*- coding: utf-8 -*-
"""Cửa sổ dịch Việt ↔ Anh để chat với khách nước ngoài qua Zalo.

Cách dùng:
  - Gõ tiếng Việt rồi Enter → ra tiếng Anh, bản dịch tự chép sẵn, sang Zalo bấm Ctrl+V.
  - Dán tin tiếng Anh của khách rồi Enter → ra tiếng Việt để đọc.
  - Shift+Enter = xuống dòng. Esc = xoá ô nhập.

Dịch qua dịch vụ Google Translate miễn phí (cần Internet, không cần khoá API).
Chữ bạn gõ được gửi lên Google để dịch – không gõ mật khẩu / thông tin mật vào đây.

Chạy thử không mở cửa sổ:  python translator.py --test
"""
import json
import sys
import threading
import tkinter as tk
import urllib.parse
import urllib.request
from tkinter import scrolledtext

URL = "https://translate.googleapis.com/translate_a/single"
TIMEOUT_S = 15


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


class TranslatorApp:
    def __init__(self, root):
        self.root = root
        self.busy = False
        root.title("Dịch Việt ↔ Anh")
        root.geometry("520x560")
        root.minsize(380, 420)
        root.configure(bg="#f4f5f7")

        font = ("Segoe UI", 11)
        top = tk.Frame(root, bg="#f4f5f7")
        top.pack(fill="x", padx=12, pady=(10, 4))
        tk.Label(top, text="Gõ tiếng Việt (hoặc dán tin tiếng Anh của khách), Enter để dịch",
                 bg="#f4f5f7", fg="#333", font=("Segoe UI", 9)).pack(side="left")
        self.topmost = tk.BooleanVar(value=True)
        tk.Checkbutton(top, text="Luôn nổi", variable=self.topmost, bg="#f4f5f7",
                       font=("Segoe UI", 9), command=self.apply_topmost).pack(side="right")

        self.inp = tk.Text(root, height=5, wrap="word", font=font, relief="solid", bd=1)
        self.inp.pack(fill="x", padx=12)
        self.inp.bind("<Return>", self.on_enter)
        self.inp.bind("<Escape>", lambda e: self.inp.delete("1.0", "end"))

        bar = tk.Frame(root, bg="#f4f5f7")
        bar.pack(fill="x", padx=12, pady=6)
        tk.Button(bar, text="Dịch (Enter)", font=("Segoe UI", 10, "bold"), bg="#0068ff",
                  fg="white", relief="flat", padx=12, command=self.translate).pack(side="left")
        tk.Button(bar, text="Chép bản dịch", font=("Segoe UI", 10), relief="flat",
                  padx=10, command=self.copy_result).pack(side="left", padx=6)
        self.status = tk.Label(bar, text="", bg="#f4f5f7", fg="#666", font=("Segoe UI", 9))
        self.status.pack(side="right")

        self.out = tk.Text(root, height=5, wrap="word", font=font, relief="solid", bd=1,
                           bg="#eef5ff")
        self.out.pack(fill="x", padx=12)

        tk.Label(root, text="Lịch sử (chỉ trong phiên này)", bg="#f4f5f7", fg="#333",
                 font=("Segoe UI", 9)).pack(anchor="w", padx=12, pady=(10, 2))
        self.hist = scrolledtext.ScrolledText(root, wrap="word", font=("Segoe UI", 10),
                                              relief="solid", bd=1, state="disabled")
        self.hist.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.hist.tag_configure("dir", foreground="#888", font=("Segoe UI", 8))
        self.hist.tag_configure("res", foreground="#0050c8")

        self.apply_topmost()
        self.inp.focus_set()

    def apply_topmost(self):
        self.root.attributes("-topmost", self.topmost.get())

    def on_enter(self, event):
        if event.state & 0x0001:  # Shift+Enter: xuống dòng
            return None
        self.translate()
        return "break"

    def translate(self):
        text = self.inp.get("1.0", "end").strip()
        if not text or self.busy:
            return
        self.busy = True
        self.status.config(text="Đang dịch…", fg="#666")
        threading.Thread(target=self._worker, args=(text,), daemon=True).start()

    def _worker(self, text):
        try:
            result, direction = translate_auto(text)
            self.root.after(0, self._done, text, result, direction, None)
        except Exception as exc:  # mất mạng, Google chặn…
            self.root.after(0, self._done, text, None, None, exc)

    def _done(self, text, result, direction, error):
        self.busy = False
        if error is not None:
            self.status.config(text="Lỗi: %s" % error, fg="#c00")
            return
        self.out.delete("1.0", "end")
        self.out.insert("1.0", result)
        self.copy_result()
        self.status.config(text="%s · đã chép, sang Zalo bấm Ctrl+V" % direction, fg="#080")
        self.inp.delete("1.0", "end")
        self.hist.config(state="normal")
        self.hist.insert("1.0", "\n")
        self.hist.insert("1.0", result + "\n", "res")
        self.hist.insert("1.0", text + "\n")
        self.hist.insert("1.0", direction + "\n", "dir")
        self.hist.config(state="disabled")

    def copy_result(self):
        text = self.out.get("1.0", "end").strip()
        if text:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)


def self_test():
    for sample in ("Chào anh, em sẽ gửi bản vẽ mặt bằng tầng 3 vào thứ Sáu.",
                   "Could you send me the revised drawings by next Monday?"):
        result, direction = translate_auto(sample)
        print("%s | %s\n    -> %s" % (direction, sample, result))
    root = tk.Tk()
    root.withdraw()
    TranslatorApp(root)
    root.update()
    root.destroy()
    print("Cửa sổ dựng được: OK")


if __name__ == "__main__":
    if "--test" in sys.argv:
        sys.stdout.reconfigure(encoding="utf-8")
        self_test()
    else:
        root = tk.Tk()
        TranslatorApp(root)
        root.mainloop()
