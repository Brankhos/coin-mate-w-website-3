db_attr = {
    'user': 'root',
    'password': '',
    'host': 'localhost',
    'raise_on_warnings': False,
    "sql_mode": 'ALLOW_INVALID_DATES',
    'autocommit': True
}

db_inside = {
    "databases": ["coin_mate_main"],
    "tables": [{
        "name": "users",
        "exec": {"`id`": "INT AUTO_INCREMENT PRIMARY KEY",
                 "`user_name`": "TINYTEXT NOT NULL",
                 "`user_pass`": "MEDIUMTEXT NOT NULL",
                 "`api_key`": "MEDIUMTEXT",
                 "`secret_key`": "MEDIUMTEXT",
                 "`max_order`": "TINYINT unsigned DEFAULT '5'",
                 "`current_order`": "TINYINT unsigned DEFAULT '0'",
                 "`use_balance`": "TINYINT unsigned DEFAULT '50'",
                 "`black_list`": "TEXT DEFAULT '[]'",
                 "`reg_date`": "TIMESTAMP DEFAULT 0",
                 "`exp_date`": "TIMESTAMP DEFAULT 0",
                 "`type`": "TINYTEXT DEFAULT 'normal'",
                 },
        "engine": "ENGINE=InnoDB",
        "charset": "DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci",
        "where": "coin_mate_main"
    }],
    "cells": {
        "coin_mate_main": {
            "users": [
                {
                    "user_name": {"value": "Brankhos", "cryp": "False", "mysql": "False", "key": "True"},
                    "user_pass": {"value": "RandomŞifre", "cryp": "True", "mysql": "False", "key": "False"},
                    "reg_date": {"value": "NOW()", "cryp": "False", "mysql": "True", "key": "False"},
                    "type": {"value": "admin", "cryp": "False", "mysql": "False", "key": "False"}
                }
            ]
        }
    }
}

db_coins = {
    "name": "coin_mate_coins",
    "min_candle": 2000,
    "table_configs": " ( `open_time` bigint NOT NULL primary key,"
                     "  `open` FLOAT NOT NULL,"
                     "  `high` FLOAT NOT NULL,"
                     "  `low` FLOAT NOT NULL,"
                     "  `close` FLOAT NOT NULL,"
                     "  `volume` FLOAT NOT NULL,"
                     "  `close_time` bigint NOT NULL,"
                     "  `quote_asset_volume` FLOAT NOT NULL,"
                     "  `number_of_trades` bigint NOT NULL,"
                     "  `taker_buy_base_asset_volume` FLOAT NOT NULL,"
                     "  `taker_buy_quote_asset_volume` FLOAT NOT NULL"
                     ") ENGINE=InnoDB"
}
