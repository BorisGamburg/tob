from pybit.unified_trading import WebSocket
import json
import time

def handle_exec(msg):
    data = msg.get("data", [])
    for d in data:
        if d["execType"] == "Trade" and d["orderType"] in ["Limit", "Market"]:
            if d.get("stopOrderType") == "TakeProfit":
                print(f"✅ TP сработал! Ордер {d['orderId']} исполнился.")
                print(json.dumps(d, indent=2))

ws = WebSocket(
    testnet=False,
    channel_type="private",
    api_key="UBX1dpzpCux8bgJv6V",
    api_secret="8tCnPYBiqkAxqojMfM6xRt2MwEK8UDcZgzVN"
)

ws.execution_stream(callback=handle_exec)

# Чтобы скрипт не завершался
while True:
    time.sleep(1)