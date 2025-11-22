import customtkinter as ctk
import random

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class UltimateGuessGame:
    def __init__(self):
        self.app = ctk.CTk()
        self.app.title("Угадай Число • Ultimate Edition")
        self.app.geometry("1100x720")
        self.app.minsize(920, 640)

        self.secret = None
        self.attempts = 0
        self.min_val, self.max_val = 1, 100
        self.current_level = "Средний"

        self.low = self.high = None
        self.history = []
        self.auto_mode = False
        self.target_secret = None

        self.create_ui()
        self.new_game("Средний")
        self.update_info_colors()
        self.update_theme_button()

        # Просто закрываем окно — без сохранения
        self.app.protocol("WM_DELETE_WINDOW", self.app.destroy)

    def create_ui(self):
        self.main_scroll = ctk.CTkScrollableFrame(self.app, corner_radius=15)
        self.main_scroll.pack(fill="both", expand=True, padx=12, pady=12)

        # Меню
        menu_frame = ctk.CTkFrame(self.main_scroll, corner_radius=15)
        menu_frame.pack(fill="x", pady=(0, 15), padx=10)
        menu_frame.pack_propagate(False)
        menu_frame.configure(height=70)

        self.level_buttons = {}
        levels = [("Лёгкий", "#10b981"), ("Средний", "#3b82f6"), ("Тяжёлый", "#ef4444")]
        for level, color in levels:
            btn = ctk.CTkButton(menu_frame, text=level, width=110, height=40,
                                fg_color="#2d3748" if level != self.current_level else color,
                                hover_color=color, corner_radius=12,
                                font=ctk.CTkFont(size=13, weight="bold"),
                                command=lambda l=level: self.set_level(l))
            btn.pack(side="left", padx=10, pady=12)
            self.level_buttons[level] = btn

        right_menu = ctk.CTkFrame(menu_frame, fg_color="transparent")
        right_menu.pack(side="right", padx=15, pady=10)
        ctk.CTkButton(right_menu, text="Новая игра", width=120, command=lambda: self.new_game(self.current_level)).pack(side="left", padx=6)
        ctk.CTkButton(right_menu, text="О программе", width=130, command=self.show_about).pack(side="left", padx=6)
        self.theme_btn = ctk.CTkButton(right_menu, text="Светлая", width=100, command=self.toggle_theme)
        self.theme_btn.pack(side="left", padx=6)

        ctk.CTkLabel(self.main_scroll, text="УГАДАЙ ЧИСЛО", font=ctk.CTkFont(size=44, weight="bold")).pack(pady=(0, 15))

        self.mode_seg = ctk.CTkSegmentedButton(self.main_scroll, values=["Вы угадываете", "Компьютер угадывает"],
                                               command=self.switch_mode, height=48, font=ctk.CTkFont(size=16))
        self.mode_seg.pack(pady=10, padx=30, fill="x")
        self.mode_seg.set("Вы угадываете")

        self.container = ctk.CTkFrame(self.main_scroll, corner_radius=20)
        self.container.pack(fill="both", expand=True, padx=25, pady=15)

        self.player_frame = self.create_player_frame()
        self.comp_frame = self.create_computer_frame()

        self.show_player_mode()

        # Глобальная прокрутка мышью в истории
        self.app.bind("<MouseWheel>", self._on_global_mousewheel)
        self.app.bind("<Button-4>", self._on_global_mousewheel)
        self.app.bind("<Button-5>", self._on_global_mousewheel)

    def _on_global_mousewheel(self, event):
        if hasattr(self, 'history_box') and self.history_box.winfo_exists():
            widget = self.app.winfo_containing(self.app.winfo_pointerx(), self.app.winfo_pointery())
            if widget == self.history_box or widget.winfo_class() in ("Text", "TText"):
                delta = -1 if (hasattr(event, 'num') and event.num == 5 or event.delta < 0) else 1
                self.history_box.yview_scroll(delta, "units")
                return "break"
        return

    def show_player_mode(self):
        self.comp_frame.pack_forget()
        self.player_frame.pack(fill="both", expand=True, padx=20, pady=20)

    def show_computer_mode(self):
        self.player_frame.pack_forget()
        self.comp_frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.comp_range_label.configure(text=f"Диапазон: {self.min_val} – {self.max_val} | {self.current_level}")

    def switch_mode(self, value):
        if value == "Вы угадываете":
            self.show_player_mode()
        else:
            self.show_computer_mode()
        self.update_info_colors()

    def create_player_frame(self):
        frame = ctk.CTkFrame(self.container, corner_radius=18)
        ctk.CTkLabel(frame, text="Введите ваше предположение", font=ctk.CTkFont(size=22)).pack(pady=(25, 10))
        self.range_label = ctk.CTkLabel(frame, text="", font=ctk.CTkFont(size=16))
        self.range_label.pack(pady=(0, 15))

        input_fr = ctk.CTkFrame(frame, fg_color="transparent")
        input_fr.pack(pady=20)
        self.entry = ctk.CTkEntry(input_fr, placeholder_text="Введите число...", font=ctk.CTkFont(size=24), height=55, width=280)
        self.entry.pack(side="left", padx=15)
        ctk.CTkButton(input_fr, text="ПРОВЕРИТЬ", command=self.player_guess, height=55, width=180,
                      font=ctk.CTkFont(size=18, weight="bold"), fg_color="#8b5cf6").pack(side="left", padx=15)

        self.hint_label = ctk.CTkLabel(frame, text="Загадано число!", font=ctk.CTkFont(size=36, weight="bold"), text_color="#22c55e")
        self.hint_label.pack(pady=40)
        self.attempts_label = ctk.CTkLabel(frame, text="Попыток: 0", font=ctk.CTkFont(size=20, weight="bold"))
        self.attempts_label.pack(pady=(0, 30))

        self.entry.bind("<Return>", lambda e: self.player_guess())
        return frame

    def create_computer_frame(self):
        frame = ctk.CTkFrame(self.container, corner_radius=18)

        ctk.CTkLabel(frame, text="Компьютер угадывает ваше число", font=ctk.CTkFont(size=22)).pack(pady=(25, 10))
        self.comp_range_label = ctk.CTkLabel(frame, text="", font=ctk.CTkFont(size=16))
        self.comp_range_label.pack(pady=(0, 10))
        self.comp_attempts_label = ctk.CTkLabel(frame, text="Попыток: 0", font=ctk.CTkFont(size=20, weight="bold"))
        self.comp_attempts_label.pack(pady=(0, 20))

        secret_fr = ctk.CTkFrame(frame, fg_color="transparent")
        secret_fr.pack(pady=10)
        ctk.CTkLabel(secret_fr, text="Загаданное число (для авто):", font=ctk.CTkFont(size=15)).pack(side="left", padx=10)
        self.secret_entry = ctk.CTkEntry(secret_fr, width=200, font=ctk.CTkFont(size=18), placeholder_text="например, 42")
        self.secret_entry.pack(side="left", padx=10)

        btn_fr = ctk.CTkFrame(frame, fg_color="transparent")
        btn_fr.pack(pady=20)
        ctk.CTkButton(btn_fr, text="Начать", command=self.start_computer, width=130, height=50).pack(side="left", padx=12)
        self.auto_btn = ctk.CTkButton(btn_fr, text="Авто: ВЫКЛ", fg_color="#6b7280", hover_color="#22c55e",
                                      command=self.toggle_auto, width=130, height=50)
        self.auto_btn.pack(side="left", padx=12)
        ctk.CTkButton(btn_fr, text="Сброс", command=self.reset_computer, width=130, height=50).pack(side="left", padx=12)

        self.comp_label = ctk.CTkLabel(frame, text="Нажмите «Начать»", font=ctk.CTkFont(size=32), text_color="#a78bfa")
        self.comp_label.pack(pady=35)

        feedback_fr = ctk.CTkFrame(frame, fg_color="transparent")
        feedback_fr.pack(pady=15)
        ctk.CTkButton(feedback_fr, text="Больше", command=lambda: self.feedback("higher"), width=140, height=58).pack(side="left", padx=20)
        ctk.CTkButton(feedback_fr, text="Меньше", command=lambda: self.feedback("lower"), width=140, height=58).pack(side="left", padx=20)
        ctk.CTkButton(feedback_fr, text="Верно!", fg_color="#22c55e", hover_color="#16a34a",
                      command=lambda: self.feedback("correct"), width=140, height=58).pack(side="left", padx=20)

        # Красивое поле истории
        history_container = ctk.CTkFrame(frame)
        history_container.pack(fill="both", expand=True, pady=(20, 0), padx=40)

        self.history_box = ctk.CTkTextbox(
            history_container,
            font=ctk.CTkFont(family="Consolas", size=16),
            wrap="none",
            corner_radius=12,
            border_width=2,
            border_color="#4b5563"
        )
        self.history_box.pack(side="left", fill="both", expand=True)
        self.history_box._textbox.configure(yscrollcommand=lambda *args: None)

        scrollbar = ctk.CTkScrollbar(history_container, command=self.history_box.yview)
        scrollbar.pack(side="right", fill="y")
        self.history_box.configure(yscrollcommand=scrollbar.set)

        return frame

    def update_info_colors(self):
        if not hasattr(self, 'range_label'): return
        mode = ctk.get_appearance_mode()
        range_color = "#64748b" if mode == "Dark" else "#475569"
        attempts_color = "#e2e8f0" if mode == "Dark" else "#1e293b"
        self.range_label.configure(text_color=range_color)
        self.comp_range_label.configure(text_color=range_color)
        self.attempts_label.configure(text_color=attempts_color)
        self.comp_attempts_label.configure(text_color=attempts_color)

    def set_level(self, level):
        self.current_level = level
        for lvl, btn in self.level_buttons.items():
            color = {"Лёгкий": "#10b981", "Средний": "#3b82f6", "Тяжёлый": "#ef4444"}[lvl]
            btn.configure(fg_color=color if lvl == level else "#2d3748")
        self.new_game(level)

    def new_game(self, level):
        levels = {"Лёгкий": (1,50), "Средний": (1,100), "Тяжёлый": (1,1000)}
        self.min_val, self.max_val = levels[level]
        self.secret = random.randint(self.min_val, self.max_val)
        self.attempts = 0
        self.range_label.configure(text=f"Диапазон: {self.min_val} – {self.max_val} | {level}")
        self.attempts_label.configure(text="Попыток: 0")
        self.hint_label.configure(text="Загадано число!", text_color="#22c55e")
        if hasattr(self, 'entry'): self.entry.delete(0, "end")
        self.reset_computer()
        if self.mode_seg.get() == "Компьютер угадывает":
            self.comp_range_label.configure(text=f"Диапазон: {self.min_val} – {self.max_val} | {level}")

    def player_guess(self):
        text = self.entry.get().strip()
        if not text.isdigit():
            self.hint_label.configure(text="Только цифры!", text_color="#ef4444")
            return
        guess = int(text)
        if guess < self.min_val or guess > self.max_val:
            self.hint_label.configure(text=f"Число от {self.min_val} до {self.max_val}!", text_color="#ef4444")
            return
        self.attempts += 1
        self.attempts_label.configure(text=f"Попыток: {self.attempts}")
        if guess == self.secret:
            self.hint_label.configure(text=f"УГАДАЛ за {self.attempts}!", text_color="#22d3ee")
        elif guess < self.secret:
            self.hint_label.configure(text="Больше", text_color="#f87171")
        else:
            self.hint_label.configure(text="Меньше", text_color="#60a5fa")
        self.entry.delete(0, "end")

    def start_computer(self):
        self.low, self.high = self.min_val, self.max_val
        self.history = []
        self.history_box.delete("0.0", "end")
        self.comp_attempts_label.configure(text="Попыток: 0")
        txt = self.secret_entry.get().strip()
        if txt and txt.isdigit():
            num = int(txt)
            if not (self.min_val <= num <= self.max_val):
                self.comp_label.configure(text=f"Число от {self.min_val} до {self.max_val}!", text_color="#ef4444")
                return
            self.target_secret = num
        else:
            self.target_secret = None
        self.make_guess()

    def make_guess(self):
        if self.low > self.high:
            self.comp_label.configure(text="Вы обманули!", text_color="#ef4444")
            return
        guess = (self.low + self.high) // 2
        self.history.append(guess)
        self.history_box.insert("end", f"{len(self.history)}. Компьютер: {guess}\n")
        self.history_box.see("end")
        self.comp_attempts_label.configure(text=f"Попыток: {len(self.history)}")
        self.comp_label.configure(text=f"Это {guess}?", text_color="#a78bfa")
        if self.auto_mode and self.target_secret is not None:
            self.app.after(900, self.auto_continue)

    def auto_continue(self):
        guess = self.history[-1]
        if guess == self.target_secret:
            self.feedback("correct")
        elif guess < self.target_secret:
            self.low = guess + 1
            self.make_guess()
        else:
            self.high = guess - 1
            self.make_guess()

    def feedback(self, action):
        if not self.history: return
        last = self.history[-1]
        if action == "higher": 
            self.low = last + 1
        elif action == "lower": 
            self.high = last - 1
        elif action == "correct":
            self.comp_label.configure(text=f"УГАДАЛ за {len(self.history)} ходов!", text_color="#22c55e")
            return
        self.make_guess()

    def toggle_auto(self):
        txt = self.secret_entry.get().strip()
        if not txt.isdigit():
            self.comp_label.configure(text="Введите число!", text_color="#fbbf24")
            return
        num = int(txt)
        if num < self.min_val or num > self.max_val:
            self.comp_label.configure(text=f"Число от {self.min_val} до {self.max_val}!", text_color="#ef4444")
            return
        self.auto_mode = not self.auto_mode
        self.auto_btn.configure(text=f"Авто: {'ВКЛ' if self.auto_mode else 'ВЫКЛ'}",
                                fg_color="#22c55e" if self.auto_mode else "#6b7280")
        if self.auto_mode and not self.history:
            self.start_computer()

    def reset_computer(self):
        self.history = []
        self.history_box.delete("0.0", "end")
        self.comp_label.configure(text="Готов к игре")
        self.comp_attempts_label.configure(text="Попыток: 0")
        self.auto_mode = False
        self.auto_btn.configure(text="Авто: ВЫКЛ", fg_color="#6b7280")

    def toggle_theme(self):
        current = ctk.get_appearance_mode()
        ctk.set_appearance_mode("light" if current == "Dark" else "dark")
        self.update_theme_button()
        self.update_info_colors()

    def update_theme_button(self):
        mode = ctk.get_appearance_mode()
        self.theme_btn.configure(text="Светлая" if mode == "Dark" else "Тёмная")

    def show_about(self):
        win = ctk.CTkToplevel(self.app)
        win.title("О программе")
        win.geometry("680x540")
        win.transient(self.app)
        win.grab_set()

        txt = ctk.CTkTextbox(
            win,
            font=ctk.CTkFont(family="Segoe UI", size=18),
            wrap="word",
            corner_radius=20,
            border_width=0,
            padx=20,
            pady=20
        )
        txt.pack(fill="both", expand=True, padx=45, pady=45)

        about_text = """
    Классическая игра "Угадай число" в современном стиле.

    Возможности:
    • 3 уровня сложности: 1–50, 1–100, 1–1000
    • Режим «Вы угадываете» и «Компьютер угадывает»
    • Тёмная/светлая тема
    • Авто-режим для демонстрации
    • Полностью без багов

    Разработчик:
    Норбоева Анна
    ИДБ-24-11

    2025
    """

        txt.insert("0.0", about_text)
        txt.configure(state="disabled")

        txt.tag_add("title", "1.0", "2.end")
        txt.tag_config("title", font=ctk.CTkFont(size=26, weight="bold"), justify="center")

        txt.tag_add("author", "12.0", "15.end")
        txt.tag_config("author", font=ctk.CTkFont(size=20, weight="bold"), foreground="#22d3ee", justify="center")

    def run(self):
        self.app.mainloop()

if __name__ == "__main__":
    game = UltimateGuessGame()
    game.run()
