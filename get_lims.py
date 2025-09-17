from pybit.unified_trading import HTTP

API_KEY = "UBX1dpzpCux8bgJv6V"
API_SECRET = "8tCnPYBiqkAxqojMfM6xRt2MwEK8UDcZgzVN"

session = HTTP(
    testnet=False,
    api_key=API_KEY,
    api_secret=API_SECRET,
)

def get_limit_orders(category="linear", symbol=None, side=None):
    result = session.get_open_orders(category=category, symbol=symbol, limit=50)
    orders = result.get("result", {}).get("list", [])
    limit_orders = [o for o in orders if o.get("orderType") == "Limit"]
    if side:
        limit_orders = [o for o in limit_orders if o.get("side") == side]
    return limit_orders

def change_order_price(order, new_price):
    response = session.amend_order(
        category="linear",
        symbol=order["symbol"],
        orderId=order["orderId"],
        price=str(new_price)
    )
    return response

if __name__ == "__main__":
    orders = get_limit_orders(category="linear", symbol="FUSDT", side="Sell")
    if not orders:
        print("Нет активных лимитных ордеров")
    else:
        order_to_change = orders[0]
        print("Выбрали ордер для изменения:")
        print(order_to_change)

        new_price = float(order_to_change["price"]) * 1.05  # +1%
        result = change_order_price(order_to_change, new_price)
        print("Результат изменения цены ордера:")
        print(result)
