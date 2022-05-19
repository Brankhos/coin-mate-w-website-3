import threading
import time

import websocket, json, pprint

from settings import coins_configs


def on_open(ws):
    print('opened connection')
    time.sleep(10)
    print("ttttt")


def on_close(ws, mess=None, tt=None):
    print(mess)
    print(tt)
    print('closed connection')

def on_error(ws, message):
    print(message)

def on_message(ws, message):
    global closes, highs, lows

    json_message = json.loads(message)
    pprint.pprint(json_message)

    candle = json_message['k']

    is_candle_closed = candle['x']

    if is_candle_closed:
        close = candle['c']
        high = candle['h']
        low = candle['l']
        print('close', close, 'high', high, 'low', low )

        # listelerimize ekliyoruz
        closes.append(close)
        highs.append(high)
        lows.append(low)



#for period in coins_configs.usable_period:
SOCKET = "wss://fstream.binance.com/ws/bnbusdt@kline_{}".format("1m")
ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message, on_error=on_error)
wst = threading.Thread(target=lambda: ws.run_forever())
wst.daemon = True
wst.start()

while True:
    time.sleep(5000)
