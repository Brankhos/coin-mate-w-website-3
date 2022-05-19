from os import remove
from os.path import exists
import pickle
from cryptography.fernet import Fernet
from mysql.connector import connect
from settings.database import db_attr, db_inside
from settings.general import sessions_loc


def first_open():

    # Şifreleme dosyalarını sil veya oluştur
    for key_name, key_inside in sessions_loc.items():
        if exists(key_inside["location"]):
            while True:
                ppw_delete = input(f"{key_name.upper()} bulundu. Silinmesini ister misiniz? E / H ")
                if ppw_delete.upper() == "E":
                    remove(key_inside["location"])
                    print("Silindi")
                    break
                elif ppw_delete.upper() == "H":
                    print("Silinmiyor")
                    break
                else:
                    print("Yanlış girdi")
        if not exists(key_inside["location"]):
            while True:
                inputed = input(f"{key_name.upper()} dosyası bulunamadı.\nEski keyi kullanmak istiyor musunuz? E / H ")
                if inputed.upper() == "H":
                    key = Fernet.generate_key()
                    print("{} KEYİ YEDEKLE\nKey: {}".format(key_name.upper(), key.decode("UTF-8")))
                    break
                elif inputed.upper() == "E":
                    key = bytes(input("Keyi giriniz: "), "UTF-8")
                    while True:
                        onayla = input(f"Keyin doğruluğunu onaylayınız. D / Y \n --{key}-- ")
                        if onayla.upper() == "D":
                            break
                        elif onayla.upper() == "Y":
                            key = bytes(input("Keyi giriniz: "), "UTF-8")
                            continue
                        else:
                            print("Girdi yanlış")
                    break
                else:
                    print("Yanlış giriş")
            with open(key_inside["location"], "wb") as f:
                if key_inside["fernet"]:
                    key = Fernet(key)
                    fernet = key
                pickle.dump(key, f)
        else:
            if key_name == "ppw":
                with open(key_inside["location"], 'rb') as handle:
                    fernet = pickle.load(handle)
    cnx = connect(**db_attr)
    cursor = cnx.cursor()

    # db_inside içerisindeki veritabanlarını, tabloları ve girdileri ekle
    for type_val, type_inside in db_inside.items():
        if type_val == "databases":
            for database in type_inside:
                cursor.execute("SHOW DATABASES LIKE '{}'".format(database))
                check_for_main = cursor.fetchall()
                if len(check_for_main) == 0:
                    cursor.execute("CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(database))
                else:
                    while True:
                        delete_main = input(f"{database}'in silinmesini istiyor musunuz? E / H ")
                        if delete_main.upper() == "E":
                            cursor.execute("DROP DATABASE `{}`".format(database))
                            print(f"{database} silindi. ", end="")
                            cursor.execute("CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(database))
                            print("Tekrar oluşturuldu")

                            break
                        elif delete_main.upper() == "H":
                            print("Silinmiyor")
                            break
                        else:
                            print("Yanlış girdi")
        elif type_val == "tables":
            for tables in type_inside:
                cursor.execute("USE {}".format(tables["where"]))
                cursor.execute("SHOW TABLES LIKE '{}'".format(tables["name"]))
                check_for_users = cursor.fetchall()
                if len(check_for_users) == 0:
                    cursor.execute("CREATE TABLE `{}` {}".format(tables["name"], "(" + ",".join(
                        [f"{key} {inside}" for key, inside in
                         tables["exec"].items()]) + f") {tables['engine']} {tables['charset']}"))
                else:
                    while True:
                        delete_users = input(f"{tables['name']}'in silinmesini istiyor musunuz? E / H ")
                        if delete_users.upper() == "E":
                            cursor.execute("DROP TABLE `{}`".format(tables["name"]))
                            print("Silindi. ", end="")
                            cursor.execute("CREATE TABLE `{}` {}".format(tables["name"], "(" + ",".join(
                                [f"{key} {inside}" for key, inside in
                                 tables["exec"].items()]) + f") {tables['engine']} {tables['charset']}"))
                            print("Tekrar oluşturuldu")
                            break
                        elif delete_users.upper() == "H":
                            print("Silinmiyor")
                            break
                        else:
                            print("Yanlış girdi")
        elif type_val == "cells":
            for database_name, database_inside in type_inside.items():
                cursor.execute("USE {}".format(database_name))
                for table_name, table_inside in database_inside.items():
                    for table_indexes in table_inside:
                        for mysql_key, mysql_val in table_indexes.items():
                            if mysql_val["key"] == "True":
                                cursor.execute(
                                    "SELECT * FROM {} WHERE `{}`='{}'".format(table_name, mysql_key,
                                                                              mysql_val["value"]))
                                check_cells = cursor.fetchall()
                                break
                        if len(check_cells) == 0:
                            for_keys = []
                            for_values = []
                            for mysql_key, mysql_val in table_indexes.items():
                                for_keys.append("`" + mysql_key + "`")
                                if mysql_val["cryp"] == "True":
                                    passw = fernet.encrypt(bytes(mysql_val["value"], "UTF-8"))
                                    passw = passw.decode("UTF-8")
                                    for_values.append("'" + passw + "'")
                                elif mysql_val["mysql"] == "True":
                                    for_values.append(mysql_val["value"])
                                else:
                                    for_values.append("'" + mysql_val["value"] + "'")
                            text_keys = "(" + ",".join(for_keys) + ")"
                            text_values = "(" + ",".join(for_values) + ")"
                            print("INSERT INTO {} {} VALUES {}".format(table_name, text_keys, text_values))
                            cursor.execute("INSERT INTO {} {} VALUES {}".format(table_name, text_keys, text_values))

    # Farklı colları ekle
    for index_tables in db_inside["tables"]:
        cursor.execute("USE {}".format(index_tables["where"]))
        cursor.execute("SHOW COLUMNS FROM {}".format(index_tables["name"]))
        mysql_tables = cursor.fetchall()
        mysql_tables = [x[0] for x in mysql_tables]
        json_index = [x.strip("`") for x in index_tables["exec"]]
        diff = [x for x in json_index if x not in mysql_tables]
        if len(diff) != 0:
            for adding in diff:
                adding = "`" + adding + "`"
                cursor.execute(
                    "ALTER TABLE {} ADD {} {}".format(index_tables["name"], adding, index_tables["exec"][adding]))
    cursor.close()
    cnx.close()


if __name__ == "__main__":
    first_open()
