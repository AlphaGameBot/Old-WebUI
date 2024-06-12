from flask import (
    Flask, 
    request, 
    render_template, 
    send_from_directory, 
    Response, 
    redirect,
)
from werkzeug.exceptions import HTTPException
import mysql.connector
import os
import time
import utility
import json
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file
app = Flask(__name__)

cnx = mysql.connector.connect(
    host=os.getenv('MYSQL_HOST'),
    user=os.getenv('MYSQL_USER'),
    password=os.getenv('MYSQL_PASSWORD'),
    database=os.getenv('MYSQL_DATABASE')
)


def message(title, message, fulltitle=True):
    return render_template('information.html', title=title, content=message, fulltitle=fulltitle)


@app.errorhandler(HTTPException)
def handle_exception(e):
    return message(f"Error #{e.code}", e), e.code

def validateToken(token):
    if token == None:
        return False, -1, None
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
            return message("Authentication Error", "Token is invalid or does not exist. Please try again.")
        elif code == 2:
            return message("Authentication Error", "This token is expired.  Please create a new one in AlphaGameBot with /user settings.")
        elif code == -1:
            return message("Authentication Error", "No token provided. Please provide a token.")
        else:
            return message("Authentication Error", "You cannot be authenticated. Please try again.")
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

@app.route("/healthcheck")
def healthcheck():
    with open("webui.json", "r") as f:
        v = json.load(f)["VERSION"]
    m = {
        "message": "All systems operational.",
        "status": "ok",
        "notes": [],
        "version": v,
        "code": 200
    }
    try:
        c = cnx.cursor()
        c.execute("SELECT 1")
    except:
        m["message"] = "Database connection failed."
        m["status"] = "error"
        m["notes"].append("Database connection failed.")
        m["code"] = 500

    return m, m["code"]

# autorun prevention
if __name__ == "__main__": 
    app.run("0.0.0.0", 5000) 
