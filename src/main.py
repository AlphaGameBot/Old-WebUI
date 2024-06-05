from flask import Flask, request, render_template, send_from_directory, Response
import mysql.connector
import os
import time
import utility
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file
app = Flask(__name__)

cnx = mysql.connector.connect(
    host=os.getenv('MYSQL_HOST'),
    user=os.getenv('MYSQL_USER'),
    password=os.getenv('MYSQL_PASSWORD'),
    database=os.getenv('MYSQL_DATABASE')
)


def message(message, type="INFO"):
    return render_template('messagebox.html', type=type, message=message)

@app.route('/')
def index():
    return 'Sorry, no root here.'

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route("/user/settings")
def user_settings():
    cnx.commit() # get latest and gratest data
    if request.args.get("token") == None:
        return "No token provided", 400
    c = cnx.cursor()
    ct = time.time() 
    # check if token is valid
    c.execute("SELECT * FROM webui_tokens WHERE token = %s", (request.args.get("token"),))
    r = c.fetchone()
    if r == None:
        return Response(message("Invalid Token!  Please create a new one using /user settings in AlphaGameBot.", type="ERROR"), 403)
    # check if the token is expired
    if r[2] > ct:
        return Response(message("This token has expired.  Please create a new one using /user settings in AlphaGameBot.", type="ERROR"), 403)

    c.execute("SELECT message_tracking_consent FROM user_settings WHERE userid = %s", [r[0]])
    usersettings = c.fetchone()
    return render_template("settings.html", message_tracking_consent=usersettings[0])
# autorun prevention
if __name__ == "__main__": 
    app.run("0.0.0.0", 5000, debug=True) 