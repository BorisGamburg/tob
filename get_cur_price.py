import sys
import requests

def get_bybit_perp_price(symbol):
    try:
        # Формируем URL для API Bybit (v5, публичный endpoint для получения рыночных данных)
        url = f"https://api.bybit.com/v5/market/tickers?category=linear&symbol={symbol}"
        
        # Отправляем GET запрос
        response = requests.get(url)
        response.raise_for_status()  # Проверка на ошибки HTTP
        
        # Парсим JSON ответ
        data = response.json()
        
        # Проверяем, успешен ли запрос
        if data['retCode'] != 0:
            return None
        
        # Извлекаем последнюю цену из ответа
        for ticker in data['result']['list']:
            if ticker['symbol'] == f"{symbol}":
                return float(ticker['lastPrice'])
        
        return None
    
    except requests.RequestException as e:
        return f"Ошибка запроса: {e}"
    except (KeyError, ValueError) as e:
        return f"Ошибка обработки данных: {e}"

def main():
    # Проверяем, передан ли аргумент командной строки
    if len(sys.argv) != 2:
        print("Использование: python script.py <symbol> (например, BTC, ETH)")
        sys.exit(1)
    
    symbol = sys.argv[1].upper()  # Получаем символ из аргумента и приводим к верхнему регистру
    print(get_bybit_perp_price(symbol))
    

if __name__ == "__main__":
    main()