import tkinter as tk


class BaseTkApp(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bind_hotkeys()

    def bind_hotkeys(self):
        # Основные комбинации клавиш
        self.bind("<Control-KeyPress-z>", self._ctrl_z)
        self.bind("<Control-KeyPress-y>", self._ctrl_y)
        self.bind("<Control-KeyPress-s>", self._ctrl_s)
        self.bind("<Control-KeyPress-o>", self._ctrl_o)
        self.bind("<Control-KeyPress-p>", self._ctrl_p)
        self.bind("<Control-KeyPress-f>", self._ctrl_f)
        self.bind("<Control-KeyPress-h>", self._ctrl_h)
        self.bind("<Control-KeyPress-n>", self._ctrl_n)
        self.bind("<Control-KeyPress-w>", self._ctrl_w)
        self.bind("<Control-KeyPress-q>", self._ctrl_q)

        # Опциональные (если используешь в своих проектах)
        self.bind("<Control-KeyPress-t>", self._ctrl_t)
        self.bind("<Control-Shift-KeyPress-z>", self._ctrl_shift_z)
        self.bind("<Control-KeyPress-Return>", self._ctrl_enter)
        self.bind("<Control-KeyPress-d>", self._ctrl_d)
        self.bind("<Control-Shift-KeyPress-v>", self._ctrl_shift_v)

    def _ctrl_z(self, event):
        print("Отмена действия (Ctrl+Z)")

    def _ctrl_y(self, event):
        print("Повтор действия (Ctrl+Y)")

    def _ctrl_s(self, event):
        print("Сохранение файла (Ctrl+S)")

    def _ctrl_o(self, event):
        print("Открытие файла (Ctrl+O)")

    def _ctrl_p(self, event):
        print("Печать (Ctrl+P)")

    def _ctrl_f(self, event):
        print("Поиск (Ctrl+F)")

    def _ctrl_h(self, event):
        print("Замена (Ctrl+H)")

    def _ctrl_n(self, event):
        print("Создание нового документа (Ctrl+N)")

    def _ctrl_w(self, event):
        print("Закрытие окна (Ctrl+W)")

    def _ctrl_q(self, event):
        print("Выход из приложения (Ctrl+Q)")

    def _ctrl_t(self, event):
        print("Создание новой вкладки (Ctrl+T)")

    def _ctrl_shift_z(self, event):
        print("Повтор отменённого действия (Ctrl+Shift+Z)")

    def _ctrl_enter(self, event):
        print("Вставка разрыва строки (Ctrl+Enter)")

    def _ctrl_d(self, event):
        print("Дублирование строки (Ctrl+D)")

    def _ctrl_shift_v(self, event):
        print("Вставка без форматирования (Ctrl+Shift+V)")


if __name__ == "__main__":
    app = BaseTkApp()
    app.mainloop()
