import mysql.connector

from settings import coins_configs
from settings.database import db_attr, db_coins

cnx = mysql.connector.connect(**db_attr)

cursor = cnx.cursor()

cursor.execute("USE {}".format(db_coins["name"]))
period_to_second_for_short = {"s": 1000, "m": 60000, "h": 3600000, "d": 86400000}
reverse_usable_periods = ["1m"]
print("prog-baş")
for period in reverse_usable_periods:
    cursor.execute("SELECT `open_time` FROM `{}_{}`".format("BTCUSDT", period))
    open_times = cursor.fetchall()
    open_times = [x[0] for x in open_times]
    for index, open_time in enumerate(open_times):
        if index != 0:
            if open_time == open_times[index - 1] + int(period[:-1]) * period_to_second_for_short[period[-1:]]:
                print("doğru")
            else:
                print("yanlış")


cursor.execute("SELECT `open_time` FROM `{}_{}` ORDER BY `open_time` LIMIT 1".format("fttusdt", "1m"))
first_open = cursor.fetchall()
print(first_open)

cursor.execute("SELECT `open_time` FROM `{}_{}` LIMIT 1".format("BTCUSDT", "1m"))
first_open = cursor.fetchall()
print(first_open)


print("prog-son")
cursor.close()
cnx.close()