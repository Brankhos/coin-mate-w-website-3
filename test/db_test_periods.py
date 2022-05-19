import time

import mysql.connector
import numpy as np

from settings import coins_configs
from settings.database import db_attr, db_coins

cnx = mysql.connector.connect(**db_attr)

cursor = cnx.cursor()

cursor.execute("USE {}".format(db_coins["name"]))
period_to_second_for_short = {"s": 1000, "m": 60000, "h": 3600000, "d": 86400000}
period_to_period = {"5m": "1m", "3m": "1m"}


cursor.execute(
    "SELECT `open_time`,`open`,`high`,`low`,`close`,`volume` FROM `{}_{}` ORDER BY `open_time` DESC".format("BTCUSDT", "1m"))
detail_ = np.flip(np.array(cursor.fetchall()), 0)
dict_for_per = {"1m": detail_}
for per_to_per_pre, per_to_per_get in period_to_period.items():
    tage_get = dict_for_per[per_to_per_get]
    curr_time = int(time.time() * 1000) - 3600000
    print(curr_time - (curr_time % (int(per_to_per_pre[:-1]) * period_to_second_for_short[per_to_per_pre[-1:]])))
    new_array = tage_get[tage_get[:, 0] >= curr_time - (curr_time % (int(per_to_per_pre[:-1]) * period_to_second_for_short[per_to_per_pre[-1:]]))]
    print(len(new_array))
    filtered_array = np.array([new_array[:, 0][0], new_array[:, 1][0], np.max(new_array[:, 2]), np.min(new_array[:, 3]), new_array[:, 4][-1], np.sum(new_array[:, 5])])

cursor.close()
cnx.close()