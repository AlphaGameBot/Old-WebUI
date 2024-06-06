from flask import Flask, request, render_template, send_from_directory, Response, redirect
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

@app.errorhandler(500)
def internal_error(error):
    return message("Internal Server Error", "ERROR"), 500

@app.errorhandler(404)
def not_found(error):
    return message("Page not found", "ERROR"), 404

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

def validateToken(token):
    if token == None:
        return False, -1
    cnx.commit() # get latest and gratest data
    
    c = cnx.cursor()
    # check if token is valid
    c.execute("SELECT * FROM webui_tokens WHERE token = %s", (request.args.get("token"),))
    r = c.fetchone()
    if r == None:
        return False, 1, r
    elif r[2] > time.time():
        return False, 2, r
    else:
        return True, 0, r
    
@app.route("/user/settings")
def user_settings():
    token = request.args.get("token")
    token_valid, code, tokenResponse = validateToken(token)
    if not token_valid:
        if code == 1:
            return message("Token Invalid", "ERROR")
        elif code == 2:
            return message("Token Expired", "ERROR")
        elif code == -1:
            return message("No token provided", "ERROR")
        else:
            return message("Token Authentication Error", "ERROR")
    c = cnx.cursor()
    c.execute("SELECT message_tracking_consent FROM user_settings WHERE userid = %s", [tokenResponse[0]])
    usersettings = c.fetchone()
    return render_template("settings.html", token=token, message_tracking_consent=usersettings[0])

def checkboxValueToBoolean(value):
    if value == "on" or value == 1:
        return 1
    elif value == "off" or value == 0:
        return 0
    else:
        raise ValueError("Invalid value for checkbox, expected 'on' or 'off' but got " + value)
    
@app.route("/user/settings/apply", methods=["POST"])
def user_settings_apply():
    token = request.args.get("token")
    token_valid, code, tokenResponse = validateToken(token)
    if not token_valid:
        return {"error": "Invalid token", "code": code}, 400
    c = cnx.cursor()
    c.execute("UPDATE user_settings SET message_tracking_consent = %s WHERE userid = %s", [checkboxValueToBoolean(request.form["message_tracking"]), tokenResponse[0]])
    cnx.commit()
    return redirect("/user/settings/applied", code=302)

@app.route("/user/settings/applied")
def user_settings_applied():
    return "<h2>Settings Applied.</h2><p>Your settings have been saved.  You can now go back to AlphaGameBot.</p>"
# autorun prevention
if __name__ == "__main__": 
    app.run("0.0.0.0", 5000) 
