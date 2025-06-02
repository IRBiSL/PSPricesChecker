import requests
from datetime import datetime


def fetch_cbr_rates():
    """Получает курсы UAH и TRY к RUB с API ЦБ РФ."""
    url = "https://www.cbr-xml-daily.ru/daily_json.js"
    try:
        response = requests.get(url)
        data = response.json()

        # Получаем курсы валют (ЦБ дает курс за 1 единицу валюты в рублях)
        uah_rate = data["Valute"]["UAH"]["Value"] / data["Valute"]["UAH"]["Nominal"]
        try_rate = data["Valute"]["TRY"]["Value"] / data["Valute"]["TRY"]["Nominal"]

        return {
            "UAH": uah_rate,
            "TL": try_rate,  # TRY - это код турецкой лиры (TL - неофициальное обозначение)
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        print(f"Ошибка при получении данных: {e}")
        return None


def save_rates_to_file(rates, clear_file=False):
    """Сохраняет курсы в файл. Если clear_file=True, файл очищается перед записью."""
    if not rates:
        return

    mode = "w" if clear_file else "a"  # 'w' - перезапись, 'a' - добавление

    with open("cbr_exchange_rates.txt", mode, encoding="utf-8") as file:
        file.write(f"Data {rates['timestamp']}\n")
        file.write(f"UAH {rates['UAH']:.4f} RUB\n")
        file.write(f"TL {rates['TL']:.4f} RUB\n")

def cbr_exchange_rates():
    rates = fetch_cbr_rates()
    if rates:
        save_rates_to_file(rates, clear_file=True)
    else:
        print("Не удалось получить данные.")