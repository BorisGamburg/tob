from pybit.unified_trading import HTTP

class BybitClient:
    def __init__(self, api_key, api_secret, timeout=10):
        self.http_client = HTTP(
            testnet=False,
            api_key=api_key,
            api_secret=api_secret,
            timeout=timeout
        )

    def get_bid_ask_prices(self, symbol="BTCUSDT"):
        try:
            response = self.http_client.get_tickers(
                category="linear",
                symbol=symbol
            )
            result = response['result']['list'][0]
            return {
                'bid': float(result['bid1Price']),
                'ask': float(result['ask1Price'])
            }
        except Exception as e:
            print(f"Ошибка: {e}")
            return None

# Пример использования
if __name__ == "__main__":
    client = BybitClient("your_api_key", "your_api_secret")
    prices = client.get_bid_ask_prices("SPECUSDT")
    if prices:
        print(f"Bid: {prices['bid']}")
        print(f"Ask: {prices['ask']}")