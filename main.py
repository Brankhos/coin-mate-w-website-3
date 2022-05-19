import pickle

import mysql.connector
from flask import Flask, session, redirect, url_for, escape, request, render_template, render_template_string
from funcs.database_setup import first_open
from settings.database import db_attr, db_inside
from settings.general import sessions_loc
from flask_classful import FlaskView, route

app = Flask(__name__,
            static_folder='assets',
            template_folder='templates')
first_open()
with open(sessions_loc['app_key']['location'], 'rb') as handle:
    app_key = pickle.load(handle)
app.secret_key = app_key.decode("UTF-8")

cnx = mysql.connector.connect(**db_attr)


def check_logged():
    if 'id' in session:
        return True
    return False


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template("index.html")

@app.route('/summary', methods=['GET', 'POST'])
def summary():
    return render_template("summary.html")

@app.route('/coins', methods=['GET', 'POST'])
def coins():
    return render_template("coins.html")

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    # remove the username from the session if it is there
    if check_logged():
        keys = list(session.keys())
        for key in keys:
            session.pop(key, None)

    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(host='192.168.1.4', port=80, debug=True)
