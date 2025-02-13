from baseapp import BaseApp

class MyApp(BaseApp):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Теперь можешь добавить собственные виджеты
        self.title("Моё приложение")
        text = tk.Text(self, width=50, height=10)
        text.pack(padx=10, pady=10)
        text.insert("end", "Привет, братик!")

if __name__ == "__main__":
    app = MyApp()
    app.mainloop()