import json
import math
import sys
import threading
import time
from pprint import pprint

import mysql.connector
import requests
import websocket

import settings.urls_configs as url_configs
from settings import coins_configs
from settings.database import db_attr, db_coins
from mysql.connector import errorcode
import numpy as np
np.set_printoptions(suppress=True,
   formatter={'float_kind':'{:f}'.format})

def create_cnx():
    try:
        cnx = mysql.connector.connect(**db_attr)
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("DATABASE: Şifre veya kullanıcı adı hatalı")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("DATABASE: Veritabanı bulunamadı")
        else:
            print("DATABASE:", err)
        raise Exception("Program Veritabanından kaynaklanan sorun tarafından durduruldu")
    return cnx
class main:
    def __init__(self):
        self.coin_infos = {}
        self.order_lock = threading.Lock()
        self.request_lock = threading.Lock()
        self.global_lock = threading.Lock()
        self.weight_infos = {}
        self.activated_updates = {}
        self.ram_data = {}
        self.cnx = create_cnx()
        self.update()
        threading.Thread(target=self.reset, daemon=True).start()

    def update(self):
        while True:
            exchange_info_req = requests.get(url_configs.FexchangeInfo)
            if exchange_info_req.status_code == 200:
                break
            else:
                print("ExchangeInfo: veri alınırken hata oluştu.\n", exchange_info_req.status_code,
                      exchange_info_req.reason)
            time.sleep(0.1)

        exchange_info_datas = exchange_info_req.json()

        temp_coin_infos = {}
        symbol_infos = exchange_info_datas["symbols"]
        for symbol_info in symbol_infos:
            if symbol_info["quoteAsset"] == "USDT" and symbol_info["status"] == "TRADING" and symbol_info[
                "contractType"] == "PERPETUAL" and symbol_info["underlyingType"] == "COIN" and symbol_info["symbol"] == \
                    symbol_info["pair"]:
                temp_coin_infos[symbol_info["symbol"]] = symbol_info
                del temp_coin_infos[symbol_info["symbol"]]["pair"]
                del temp_coin_infos[symbol_info["symbol"]]["contractType"]
                del temp_coin_infos[symbol_info["symbol"]]["deliveryDate"]
                del temp_coin_infos[symbol_info["symbol"]]["status"]
                del temp_coin_infos[symbol_info["symbol"]]["baseAsset"]
                del temp_coin_infos[symbol_info["symbol"]]["quoteAsset"]
                del temp_coin_infos[symbol_info["symbol"]]["underlyingType"]
        self.coin_infos = temp_coin_infos
        print("Info:", len(self.coin_infos), "coin var")

        temp_weight_settings = {}
        rateLimits = exchange_info_datas["rateLimits"]
        for rateLimit in rateLimits:
            if rateLimit["rateLimitType"] not in temp_weight_settings:
                temp_weight_settings[rateLimit["rateLimitType"]] = {}

            tt = {"wei_detail": {"limit": rateLimit["limit"], "resetTime": rateLimit["intervalNum"] * coins_configs.klines_text_to_seconds[rateLimit["interval"]]}, "weight": 0}
            tt_calc = "_".join([str(x) for x in tt["wei_detail"].values()])
            if tt_calc not in temp_weight_settings[rateLimit["rateLimitType"]]:
                temp_weight_settings[rateLimit["rateLimitType"]][tt_calc] = tt

        temp_weight_settings["update"] = {"self.update": {"wei_detail": {"resetTime": 60}, "weight": 0}}

        self.weight_infos = temp_weight_settings

        cursor = self.cnx.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS {}".format(db_coins["name"]))
        cursor.execute("USE {}".format(db_coins["name"]))
        cursor.execute("SHOW TABLES")
        database_coins = cursor.fetchall()
        database_coins = [x[0].split("_")[0].upper() for x in database_coins]
        database_coins = list(set(database_coins))
        cache_new_symbols = self.coin_infos.keys()

        will_adds = [x for x in cache_new_symbols if x not in database_coins]
        will_deletes = [x for x in database_coins if x not in cache_new_symbols]

        will_adds_period = [f"{x}_{y}" for x in will_adds for y in coins_configs.usable_period]
        will_deletes_period = [f"{x}_{y}" for x in will_deletes for y in coins_configs.usable_period]

        """        
        for adding_coin in will_adds_period:
            cursor.execute("CREATE TABLE IF NOT EXISTS {} {}".format(adding_coin, db_coins["table_configs"]))

        """

        cache_new_symbols = ["BTCUSDT"] if "BTCUSDT" in cache_new_symbols else []
        #for will_add in will_adds:
        for will_add in cache_new_symbols:
            if will_add not in self.activated_updates:
                self.activated_updates[will_add] = {"status": "db-update"}
                print("Sistemde aktif olmayan coin aktif ediliyor:", will_add)
                SOCKET = f"wss://fstream.binance.com/ws/{will_add.lower()}@kline_1m"
                ws = websocket.WebSocketApp(SOCKET, on_open=lambda wss: self.on_open(wss, will_add),
                                            on_close=lambda wss: self.on_close(wss),
                                            on_message=lambda wss, msg: self.get_websocketted(wss, msg),
                                            on_error=lambda wss, msg: self.on_error(wss, msg))
                wst = threading.Thread(target=lambda: ws.run_forever())
                wst.daemon = True
                wst.start()
                threading.Thread(target=self.update_database, args=(will_add,)).start()

        for will_delete in will_deletes:
            if will_delete in self.activated_updates:
                self.activated_updates.pop(will_delete)
                print("Sistemde aktif olan coin deaktif ediliyor:", will_delete)
            else:
                print("Veritabanında fazlalık olan coin siliniyor:", will_delete)
            threading.Thread(target=self.drop_table, args=(will_delete,)).start()

        cursor.close()

    def drop_table(self, coin_symbol: str, will_delete_period=None, cursor=None):
        new_cursor = False
        if will_delete_period is None:
            will_delete_period = coins_configs.usable_period
        if cursor is None:
            cnx = create_cnx()
            cursor = cnx.cursor()
            cursor.execute("USE {}".format(db_coins["name"]))
            new_cursor = True
        reverse_usable_periods = will_delete_period[::-1]
        for period in reverse_usable_periods:
            cursor.execute("DROP TABLE IF EXISTS {}_{}".format(coin_symbol, period))

        if new_cursor:
            cursor.close()
            cnx.close()

    def create_table(self, coin_symbol: str, will_add_period=None, cursor=None):
        new_cursor = False
        if will_add_period is None:
            will_add_period = coins_configs.usable_period
        if cursor is None:
            cnx = create_cnx()
            cursor = cnx.cursor()
            cursor.execute("USE {}".format(db_coins["name"]))
            new_cursor = True
        reverse_usable_periods = will_add_period[::-1]
        for period in reverse_usable_periods:
            cursor.execute("CREATE TABLE IF NOT EXISTS {}_{} {}".format(coin_symbol, period, db_coins["table_configs"]))

        if new_cursor:
            cursor.close()
            cnx.close()

    def delete_cell(self, coin_symbol: str, where: str, will_add_period=None, cursor=None):
        new_cursor = False
        if will_add_period is None:
            will_add_period = coins_configs.usable_period
        if cursor is None:
            cnx = create_cnx()
            cursor = cnx.cursor()
            cursor.execute("USE {}".format(db_coins["name"]))
            new_cursor = True
        reverse_usable_periods = will_add_period[::-1]
        for period in reverse_usable_periods:
            cursor.execute("DELETE FROM {}_{} where {}".format(coin_symbol, period, where))

        if new_cursor:
            cursor.close()
            cnx.close()

    def update_database(self, coin_symbol: str):
        cnx = create_cnx()
        cursor = cnx.cursor(buffered=True)
        cursor.execute("USE {}".format(db_coins["name"]))
        reverse_usable_periods = coins_configs.usable_period[::-1]
        while True:
            starter = time.time()
            sleep_delay = 60 - (starter % 60)
            time.sleep(sleep_delay + 5)
            starter = time.time()
            for period in reverse_usable_periods:

                cursor.execute("CREATE TABLE IF NOT EXISTS {}_{} {}".format(coin_symbol, period, db_coins["table_configs"]))

                period_to_s = int(period[:-1]) * coins_configs.short_klines_text_to_seconds[period[-1:]]
                curr_time = time.time()
                requ_date = int(((curr_time - (curr_time % period_to_s)) - (db_coins["min_candle"] * period_to_s)) * 1000)


                # check has enough value
                cursor.execute("CREATE TABLE IF NOT EXISTS {}_{} {}".format(coin_symbol, "1m", db_coins["table_configs"]))

                cursor.execute("SELECT COUNT(*) FROM `{}_{}`".format(coin_symbol, "1m"))
                row_count = cursor.fetchall()

                row_count = row_count[0][0]
                if row_count < db_coins["min_candle"]:
                    self.drop_table(coin_symbol,[period],cursor)
                    self.create_table(coin_symbol,[period],cursor)
                else:
                    self.delete_cell(coin_symbol, "`open_time` < {}".format(requ_date),[period],cursor)

                """
                # check has enough value
                cursor.execute("SELECT `open_time` FROM `{}_{}` ORDER BY `open_time` LIMIT 1".format(coin_symbol, period))
                first_open = cursor.fetchall()

                if len(first_open) != 0:
                    first_open = first_open[0][0]
                    if first_open > requ_date:
                        self.drop_table(coin_symbol,[period],cursor)
                        self.create_table(coin_symbol,[period],cursor)
                    else:
                        self.delete_cell(coin_symbol, "`open_time` < {}".format(requ_date),[period],cursor)
                """
                cursor.execute("SELECT `open_time` FROM `{}_{}` ORDER BY `open_time` DESC LIMIT 1".format(coin_symbol, period))
                last_open = cursor.fetchall()

                if len(last_open) == 0:
                    start_date = requ_date
                    remaining_limit = 1000
                    weight = 5
                else:
                    date_from_db = int(last_open[0][0])
                    start_date = date_from_db + (period_to_s * 1000) if date_from_db > requ_date else requ_date
                    remaining_limit = int(((int(time.time()) * 1000) - start_date) / (period_to_s * 1000)) + 1
                    remaining_limit = remaining_limit if remaining_limit < 1000 else 1000
                    if remaining_limit < 100:
                        weight = 1
                    elif remaining_limit < 500:
                        weight = 2
                    else:
                        weight = 5
                add_coindata = (
                    "INSERT INTO {}_{} (open_time, open, high, low, close, volume, close_time, quote_asset_volume, number_of_trades, taker_buy_base_asset_volume, taker_buy_quote_asset_volume) "
                    "VALUES ".format(coin_symbol, period))
                while True:

                    if remaining_limit <= 1:
                        break
                    if self.wei_add_check("REQUEST_WEIGHT", weight):
                        data_link = f'{url_configs.Fklines}?symbol={coin_symbol}&interval={period}&limit={remaining_limit}&startTime={start_date}'
                        data_req = requests.get(data_link)
                        data_list = data_req.json()
                        if data_req.status_code == 200:
                            data_list = list(data_list)

                            len_data_list = len(data_list)

                            if len_data_list < 1000:
                                data_list = data_list[:-1]
                                len_data_list -= 1


                            if len_data_list <= 0:
                                break

                            klines = "(" + "),(".join(",".join(str(x) for x in y[:-1]) for y in data_list) + ")"
                            cursor.execute(add_coindata + klines)

                            if len_data_list < 1000:
                                break

                            start_date = data_list[-1][0] + (period_to_s * 1000)
                            remaining_limit = int(((int(time.time()) * 1000) - start_date) / (period_to_s * 1000)) + 1
                            remaining_limit = remaining_limit if remaining_limit < 1000 else 1000
                            if remaining_limit < 100:
                                weight = 1
                            elif remaining_limit < 500:
                                weight = 2
                            else:
                                weight = 5
                        elif data_req.status_code == 400:
                            code_no = data_list["code"]

                            if code_no == -1102:
                                print(data_link)

                        elif data_req.status_code == 429:
                            code_no = data_list["code"]

                            if code_no == -1003:
                                print("ağırlığa yakalandı, beklemeye alınıyor")
                                self.wei_add_check("REQUEST_WEIGHT", 50000)
                        else:
                            print(data_req.text, data_req.status_code, data_req.headers)
            #print(time.time() - starter, coin_symbol)
            if time.time() - starter < 45:
                self.activated_updates[coin_symbol]["status"] = "websocket"
                print(coin_symbol, "işlemlerini tamamladı. Websockete geçiliyor")
                print("aktifleşmesi beklene coin sayısı:", len([x for x in self.activated_updates.values() if x["status"] == "db-update"]))
                break

        self.ram_data[coin_symbol] = {}
        for period in coins_configs.usable_period:
            cursor.execute(
                "SELECT `open_time`,`open`,`high`,`low`,`close`,`volume` FROM `{}_{}` ORDER BY `open_time` DESC LIMIT {}".format(
                    coin_symbol, period, db_coins["min_candle"]))
            self.ram_data[coin_symbol][period] = np.flip(np.array(cursor.fetchall()), 0)

        """
        self.ram_data[coin_symbol] = {}
        for period in coins_configs.usable_period:
            cursor.execute("SELECT `open_time`,`open`,`high`,`low`,`close`,`volume` FROM `{}_{}` ORDER BY `open_time` DESC LIMIT {}".format(coin_symbol, period, db_coins["min_candle"]))
            detail_ = np.flip(np.array(cursor.fetchall()), 0)
            self.ram_data[coin_symbol][period] = detail_

            SOCKET = f"wss://fstream.binance.com/ws/{coin_symbol.lower()}@kline_{period}"
            print(SOCKET)
            ws = websocket.WebSocketApp(SOCKET, on_open=lambda wss: self.on_open(wss), on_close=lambda wss: self.on_close(wss), on_message=lambda wss, msg: self.get_websocketted(wss, msg))
            wst = threading.Thread(target=lambda: ws.run_forever())
            wst.daemon = True
            wst.start()
        """


        #pprint(self.ram_data)
        cursor.close()
        cnx.close()

    def get_websocketted(self, wss, message):
        json_message = json.loads(message)
        if self.activated_updates[json_message["k"]["s"]]["status"] == "q-update" or json_message["k"]["x"]:
            candle = json_message['k']

            self.activated_updates[candle["s"]]["status"] = "updating"

            cache_cur_val = self.ram_data[candle["s"]][candle["i"]]
            if cache_cur_val[-1][0] == int(candle["t"]):
                cache_cur_val[-1] = [int(candle["t"]), float(candle["o"]), float(candle["h"]), float(candle["l"]), float(candle["c"]), float(candle["v"])]
            else:
                cache_cur_val = np.append(self.ram_data[candle["s"]][candle["i"]], [
                    [int(candle["t"]), float(candle["o"]), float(candle["h"]), float(candle["l"]), float(candle["c"]),
                     float(candle["v"])]], axis=0)

            self.ram_data[candle["s"]][candle["i"]] = cache_cur_val
            #print(f"Web socket {candle['s']} içine {candle['i']} eklendi")
            if self.ram_data[candle["s"]][candle["i"]][-1][0] == self.ram_data[candle["s"]][candle["i"]][-2][0] + coins_configs.short_klines_text_to_seconds["m"]*1000:
                print("doğru")
            else:
                print("yanlış")
            for per_to_per_to, per_to_per_from in coins_configs.period_to_period.items():
                tage_get = self.ram_data[candle["s"]][per_to_per_from]
                curr_time = json_message["E"]

                new_array = tage_get[tage_get[:, 0] >= curr_time - (curr_time % (int(per_to_per_to[:-1]) * coins_configs.short_klines_text_to_seconds[per_to_per_to[-1:]]*1000))]

                if len(new_array) == 0:
                    new_array = tage_get[tage_get[:, 0] >= curr_time - (curr_time % (
                                int(per_to_per_to[:-1]) * coins_configs.short_klines_text_to_seconds[
                            per_to_per_to[-1:]] * 1000)) - (
                                int(per_to_per_to[:-1]) * coins_configs.short_klines_text_to_seconds[
                            per_to_per_to[-1:]] * 1000)]
                    self.activated_updates[json_message["k"]["s"]]["status"] = "q-update"

                filtered_array = np.array([new_array[:, 0][0], new_array[:, 1][0], np.max(new_array[:, 2]), np.min(new_array[:, 3]), new_array[:, 4][-1], np.sum(new_array[:, 5])])

                cache_cur_val = self.ram_data[candle["s"]][per_to_per_to]
                if cache_cur_val[-1][0] == filtered_array[0]:
                    cache_cur_val[-1] = filtered_array
                else:
                    cache_cur_val = np.append(cache_cur_val, [filtered_array], axis=0)
                self.ram_data[candle["s"]][per_to_per_to] = cache_cur_val
                #print(f"Web socket {candle['s']} içine {per_to_per_to} eklendi\n{cache_cur_val[-3:]}")

            if self.activated_updates[json_message["k"]["s"]]["status"] != "q-update":
                self.activated_updates[candle["s"]]["status"] = "updated"

    def on_open(self, wss, will_add):
        while True:
            if will_add in self.ram_data and "1m" in self.ram_data[will_add]:
                break
            time.sleep(1)
        print('opened connection')

    def on_close(self, wss):
        print('closed connection')

    def on_error(self, wss, msg, a=None, b=None):
        print("hata?", msg, a,b)

    def reset(self):
        try:
            reset_times = [y["wei_detail"]["resetTime"] for x in self.weight_infos.values() for y in x.values()]
            reset_times = list(set(reset_times))
            gcd = math.gcd(*reset_times)
            time.sleep(gcd - (time.time() % gcd) + 2)
        except:
            pass
        while True:
            try:
                reset_times = [y["wei_detail"]["resetTime"] for x in self.weight_infos.values() for y in x.values()]
                reset_times = list(set(reset_times))
                gcd, lcm = math.gcd(*reset_times), math.lcm(*reset_times)
                delay_max, delay_min = max(reset_times), min(reset_times)
                if lcm > delay_max:
                    raise Exception("En küçük orak katta bir sorun var")
                if gcd < delay_min:
                    raise Exception("En büyük ortak bölende bir sorun var")
                time_max_mod = time.time() % lcm
                counter = int(time_max_mod / gcd)
                for wei_k, wei_s in self.weight_infos.items():
                    for one_wei_k, one_wei in wei_s.items():
                        if (counter * gcd) % one_wei["wei_detail"]["resetTime"] == 0:
                            if wei_k == "update":
                                if one_wei_k == "self.update":
                                    up = threading.Thread(target=self.update)
                                    up.start()
                                    up.join()
                            else:
                                one_wei["weight"] = 0
                time.sleep(gcd - (time.time() % gcd) + 2)
            except RuntimeError as E:
                print("RESET:", E)
                time.sleep(0.01)
            except KeyError as E:
                print("RESET Key Error", E)
                time.sleep(0.01)
            except Exception as E:
                print("RESET Exception", E)
                time.sleep(0.01)

    def wei_add_check(self, limitType: str, limit: int):
        if limitType == "ORDERS":
            locker = self.order_lock
        elif limitType == "REQUEST_WEIGHT":
            locker = self.request_lock
        else:
            locker = self.global_lock
        with locker:
            while True:
                try:
                    for weigs in self.weight_infos[limitType].values():
                        weigs["weight"] += limit
                        if weigs["weight"] < weigs["wei_detail"]["limit"]*0.9:
                            return True
                        time.sleep(0.1)
                except RuntimeError as E:
                    print("WEI_ADD_CHECK:", E)
                    time.sleep(0.01)


if __name__ == "__main__":
    aa = main()

    try:
        while True:
            time.sleep(1)
    except Exception as E:
        print("HATA!!!", E)
        aa.cnx.close()
