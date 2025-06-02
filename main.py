import requests
from bs4 import BeautifulSoup
from time import sleep
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from threading import Thread
import currency


class PSPriceChecker:
    def __init__(self, root):
        self.root = root
        self.root.title("PS Store Price Checker")
        self.root.geometry("800x600")
        self.setup_ui()

    def setup_ui(self):
        style = ttk.Style()
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabel', background='#f0f0f0', font=('Arial', 10))
        style.configure('TButton', font=('Arial', 10))
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'))

        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        header = ttk.Label(main_frame, text="PlayStation Store Price Checker", style='Header.TLabel')
        header.pack(pady=10)

        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=10)

        ttk.Label(input_frame, text="Название игры:").pack(side=tk.LEFT, padx=5)
        self.game_entry = ttk.Entry(input_frame, width=40)
        self.game_entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        self.game_entry.bind('<Return>', lambda e: self.start_search())

        search_btn = ttk.Button(main_frame, text="Найти цены", command=self.start_search)
        search_btn.pack(pady=5)

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=5)
        update_btn = ttk.Button(
            button_frame,
            text="Обновить курсы валют",
            command=self.start_update_exchange_rates
        )
        update_btn.pack(side=tk.LEFT, padx=5)

        ttk.Label(main_frame, text="Результаты:").pack(anchor=tk.W, pady=(10, 0))
        self.results_area = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            width=80,
            height=20,
            font=('Arial', 10)
        )
        self.results_area.pack(fill=tk.BOTH, expand=True, pady=5)

        self.status_var = tk.StringVar()
        self.status_var.set("Готов к поиску")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, pady=(5, 0))

    def start_update_exchange_rates(self):
        self.status_var.set("Обновление курсов валют...")
        self.root.config(cursor="watch")
        Thread(target=self.cbr_exchange_rates, daemon=True).start()

    def cbr_exchange_rates(self):
        try:
            currency.cbr_exchange_rates()
            self.root.after(0, lambda: messagebox.showinfo(
                "Успешно",
                "Новые ценовые данные сохранены\n"
            ))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror(
                "Ошибка",
                f"Не удалось обновить курсы валют: {str(e)}"
            ))

        finally:
            self.root.after(0, lambda: self.status_var.set("Готов к поиску"))
            self.root.after(0, lambda: self.root.config(cursor=""))

    def start_search(self):
        game_name = self.game_entry.get().strip()
        if not game_name:
            messagebox.showwarning("Ошибка", "Введите название игры")
            return

        self.results_area.delete(1.0, tk.END)
        self.status_var.set("Идет поиск...")
        self.root.config(cursor="watch")

        Thread(target=self.search_prices, args=(game_name,), daemon=True).start()

    def actual_currency(self):
        with open('cbr_exchange_rates.txt', 'r') as file:
            lines = file.readlines()
        date_line = lines[0].strip()
        date = date_line.split(' ')[1] + ' ' + date_line.split(' ')[2]
        uah_rate = None
        tl_rate = None
        for line in lines[1:]:
            if line.startswith('UAH'):
                uah_rate = float(line.split(' ')[1])
            elif line.startswith('TL'):
                tl_rate = float(line.split(' ')[1])
        return date, uah_rate, tl_rate

    def search_prices(self, game_name):
        regions = [
            ('en-tr', 'Турция (TRY)'),
            ('ru-ua', 'Украина (UAH)')
        ]

        date, uah_rate, tl_rate = self.actual_currency()

        results = [f'Последняя проверка актуального курса валют была {date}\n',
                   f'Курс за лиру - {tl_rate} RUB\n',
                   f'Курс за гривну - {uah_rate} RUB\n']

        for region_code, region_name in regions:
            try:
                self.update_status(f"Проверяем {region_name}...")

                url = f"https://store.playstation.com/{region_code}/search/{game_name}"
                headers = {'User-Agent': 'Mozilla/5.0'}

                response = requests.get(url, headers=headers)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')
                game_cards = soup.find_all('li', {
                    'class': 'psw-l-w-1/2@mobile-s psw-l-w-1/2@mobile-l psw-l-w-1/6@tablet-l psw-l-w-1/4@tablet-s psw-l-w-1/6@laptop psw-l-w-1/8@desktop psw-l-w-1/8@max'})

                if not game_cards:
                    results.append(f"\n{region_name} - игры не найдены\n")
                    continue

                results.append(f"\n{region_name} - найдено {len(game_cards)} игр:\n")

                for i, card in enumerate(game_cards[:], 1):
                    try:
                        title = card.find('span', {'class': 'psw-t-body psw-c-t-1 psw-t-truncate-2 psw-m-b-2'}).text.strip()
                        price = card.find('span', {'class': 'psw-m-r-3'})
                        price_info = f"Цена: {price.text}"
                        results.append(f"{i}. {title} | {price_info}\n")
                    except Exception as e:
                        continue

                sleep(1)

            except Exception as e:
                results.append(f"\nОшибка при проверке {region_name}: {str(e)}\n")

        self.root.after(0, self.show_results, results)

    def show_results(self, results):
        self.results_area.insert(tk.END, "".join(results))
        self.status_var.set("Поиск завершен")
        self.root.config(cursor="")

    def update_status(self, message):
        self.root.after(0, lambda: self.status_var.set(message))


if __name__ == "__main__":
    root = tk.Tk()
    app = PSPriceChecker(root)
    root.mainloop()