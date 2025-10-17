from pprint import pprint

prev_hedge_price = None


def calculate_hedge_params(
    balance, 
    buy_volume, 
    sell_volume, 
    buy_price, 
    sell_price, 
    hedge_loss_ratio
):
    # Находим направление ордера
    net_volume = buy_volume - sell_volume
    if net_volume == 0:
        return None, None
    if net_volume > 0:
        entry_price = buy_price
        order_side = "Sell"
    else:
        entry_price = sell_price
        order_side = "Buy"

    # Находим цену ордера
    target_loss = balance * hedge_loss_ratio
    order_price = entry_price - (target_loss / net_volume)

    # Возвращаем параметры 
    return order_price, order_side


def check_active_orders(symbol, side, exclude_ids, bybit_driver):
    # Фильтруем активные ордера по символу, стороне, исключаем ордера из exclude_ids
    # и оставляем только лимитные ордера
    active_orders = bybit_driver.get_active_orders(symbol)
    #pprint(active_orders)
    filtered_orders = [
        order for order in active_orders
        if order["side"] == side
        and order["order_id"] not in exclude_ids
        and order["orderType"] == "Limit"
        #and not order.get("stopOrderType")  # пустое поле
    ]

    #pprint(filtered_orders)

    if filtered_orders:
        return
    else:
        raise Exception(f"Нет активных лимитных {side} ордеров")


def check_hedging_conditions(symbol, hedge_order_price, hedge_order_side, bybit_driver):
    cur_price = bybit_driver.get_last_price(symbol)
    if hedge_order_side == "Buy":
        if cur_price > hedge_order_price:
            return True
        else:
            return False
    elif hedge_order_side == "Sell":
        if cur_price < hedge_order_price:
            return True
        else:
            return False
    else:
        raise ValueError("Неверное направление ордера")


def check_hedge(
        symbol, 
        hedge_loss_ratio=0.01, 
        hedge_order_size=0.001,
        hedge_sl_ratio=None, 
        exclude_ids=[], 
        bybit_driver=None,
        logger=None
    ):

    global prev_hedge_price

    # Получаем данные по балансу и позициям
    balance = bybit_driver.get_balance()
    buy_size, sell_size, a1, a2, buy_price, sell_price = bybit_driver.get_position_data(symbol)

    # Рассчитываем параметры хедж ордера
    hedge_order_price, hedge_order_side = calculate_hedge_params(
        balance, 
        buy_size, 
        sell_size, 
        buy_price, 
        sell_price, 
        hedge_loss_ratio=hedge_loss_ratio
    )

    # Проверяем, изменилась ли цена хеджа
    if hedge_order_price != prev_hedge_price:
        logger.info(f"hedge_order_price={hedge_order_price}, hedge_order_side={hedge_order_side}, hedge_order_size={hedge_order_size}")
        prev_hedge_price = hedge_order_price


    # Если хедж ордер не нужен, выходим
    if hedge_order_side is None:
        #print("Нет необходимости в хеджировании")
        return

    # Проверяем есть ли активные ордера в нужную сторону
    check_active_orders(symbol, hedge_order_side, exclude_ids, bybit_driver)
    
    # Размещаем хедж ордер, если нужно
    if check_hedging_conditions(symbol, hedge_order_price, hedge_order_side, bybit_driver):
        bybit_driver.wait_chase_order(
            symbol=symbol, 
            side=hedge_order_side,
            qty=hedge_order_size,
            sl_ratio=hedge_sl_ratio,
            exclude_ids=exclude_ids
        )
    

# # Logging Setup
# logger = logging.getLogger()
# logger.setLevel(logging.INFO)
# formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
# ch = logging.StreamHandler()
# ch.setFormatter(formatter)
# logger.addHandler(ch)

# # Telegram Setup
# telegram = Telegram(logger=logger)

# api_key="UBX1dpzpCux8bgJv6V"
# api_secret="8tCnPYBiqkAxqojMfM6xRt2MwEK8UDcZgzVN"
# bybit_driver = BybitDriver(api_key=api_key, api_secret=api_secret, logger=logger, telegram=telegram)

# # Пример использования
# check_hedge(
#     "MERLUSDT", 
#     target_loss_ratio=0.01, 
#     order_size_ratio=0.001, 
#     exclude_ids=[], 
#     bybit_driver=bybit_driver
#)
