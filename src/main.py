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
import disc
load_dotenv() # Load environment variables from .env file
app = Flask(__name__)

cnx = mysql.connector.connect(
    host=os.getenv('MYSQL_HOST'),
    user=os.getenv('MYSQL_USER'),
    password=os.getenv('MYSQL_PASSWORD'),
    database=os.getenv('MYSQL_DATABASE')
)


def message(title, message, fulltitle=True):
    return render_template('information.html',
    title=title,
    content=[line.strip("\n") for line in message.split("\n")], 
    fulltitle=fulltitle)

# SERVE STATIC FILES
@app.route("/webui/static/<path:path>")
def _static(path: str):
    return send_from_directory("static", path)

@app.route("/favicon.ico")
def _favicon():
    return redirect("https://static.alphagame.dev/alphagamebot/img/icon.png")
@app.errorhandler(HTTPException)
def handle_exception(e):
    return message(f"Error #{e.code}", e), e.code

def validateToken(token, tokenType):
    if token == None:
        return False, -1, None
    cnx.reconnect() # fix a stupid bug where it disconnects.  Bandaid fix, but oh-well...
    cnx.commit() # get latest and gratest data
    
    c = cnx.cursor()
    # check if token is valid
    c.execute("SELECT * FROM webui_tokens WHERE token = %s;", (request.args.get("token"),))
    r = c.fetchone()
    token_for = (r[4] if r != None else None)
    if r == None:
        return False, 1, r
    elif r[3] > time.time():
        return False, 2, r
    else:
        if token_for != tokenType:
            return False, 3, r
        return True, 0, r

@app.route("/webui/")
def index():
    return message("AlphaGameBot WebUI", "Welcome to the AlphaGameBot WebUI.\nUnfortunately, there is no real 'index'...  Please use a command like /user settings in AlphaGameBot to get a link to interact with it.")

@app.route("/webui/user/settings")
def user_settings():
    cnx.reconnect() # fix a stupid bug where it disconnects.  Bandaid fix, but oh-well...
    token = request.args.get("token")
    token_valid, code, tokenResponse = validateToken(token, "USER_SETTINGS")
    if not token_valid:
        if code == 1:
            return message("Authentication Error", "Token is invalid or does not exist. Please try again.")
        elif code == 2:
            return message("Authentication Error", "This token is expired.  Please create a new one in AlphaGameBot with /user settings.")
        elif code == 3:
            return message("Authentication Error", "This token is of an invalid type.  Please create another token in AlphaGameBot.")
        elif code == -1:
            return message("Authentication Error", "No token provided. Please provide a token.")
        else:
            return message("Authentication Error", "You cannot be authenticated. Please try again.")
    c = cnx.cursor()
    c.execute("SELECT message_tracking_consent FROM user_settings WHERE userid = %s", [tokenResponse[0]])
    usersettings = c.fetchone()
    return render_template("settings.html", token=token, message_tracking_consent=usersettings[0])

@app.route("/webui/guild/settings")
def guild_settings():
    cnx.reconnect()
    token = request.args.get("token")
    token_valid, code, tokenResponse = validateToken(token, "GUILD_SETTINGS")
    if not token_valid:
        if code == 1:
            return message("Authentication Error", "Token is invalid or does not exist. Please try again.")
        elif code == 2:
            return message("Authentication Error", "This token is expired.  Please create a new one in AlphaGameBot with /guild settings.")
        elif code == 3:
            return message("Authentication Error", "This token is of an invalid type.  Please create another token in AlphaGameBot.")
        elif code == -1:
            return message("Authentication Error", "No token provided. Please provide a token.")
        else:
            return message("Authentication Error", "You cannot be authenticated. Please try again.")
    c = cnx.cursor()
    c.execute("SELECT leveling_enabled FROM guild_settings WHERE guildid = %s", [tokenResponse[1]])
    usersettings = c.fetchone()
    return render_template("guild_settings.html", token=token, leveling=usersettings[0])
    
def checkboxValueToBoolean(value):
    if value == "on" or value == 1:
        return 1
    elif value == "off" or value == 0:
        return 0
    else:
        raise ValueError("Invalid value for checkbox, expected 'on' or 'off' but got " + value)
    
@app.route("/webui/guild/settings/apply", methods=["POST"])
def guild_settings_apply():
    cnx.reconnect() # fix a stupid bug where it disconnects.  Bandaid fix, but oh-well...
    token = request.args.get("token")
    token_valid, code, tokenResponse = validateToken(token, "GUILD_SETTINGS")
    if not token_valid:
        return {"error": "Invalid token", "code": code}, 403
    c = cnx.cursor()
    c.execute("UPDATE guild_settings SET leveling_enabled = %s WHERE guildid = %s", [checkboxValueToBoolean(request.form["leveling"]), tokenResponse[1]])
    cnx.commit()
    if not c.rowcount > 0:
        return "<h2>Success</h2><p>No changes were made.</p>"
    return redirect("/webui/guild/settings/applied", code=302)

@app.route("/webui/user/settings/apply", methods=["POST"])
def user_settings_apply():
    cnx.reconnect() # fix a stupid bug where it disconnects.  Bandaid fix, but oh-well...
    token = request.args.get("token")
    token_valid, code, tokenResponse = validateToken(token, "USER_SETTINGS")
    if not token_valid:
        return {"error": "Invalid token", "code": code}, 403
    c = cnx.cursor()
    c.execute("UPDATE user_settings SET message_tracking_consent = %s WHERE userid = %s", [checkboxValueToBoolean(request.form["message_tracking"]), tokenResponse[0]])
    cnx.commit()
    return redirect("/webui/user/settings/applied", code=302)

@app.route("/webui/user/settings/applied")
def user_settings_applied():
    return "<h2>Settings Applied.</h2><p>Your settings have been saved.  You can now go back to AlphaGameBot.</p>"

@app.route("/webui/guild/settings/applied")
def guild_settings_applied():
    return "<h2>Settings Applied.</h2>"
    
@app.route("/webui/user/stats/<int:userid>")
def user_page_global(userid: int):
    cnx.reconnect()
    c = cnx.cursor()
    
    c.execute("SELECT messages_sent, commands_ran FROM user_stats WHERE userid = %s", [userid])

    try:
        messages, commands = c.fetchone()
    except TypeError:
        return message("Error", 
        "This user is not recognized.\n"
        "Remember that AlphaGameBot needs to be able to see this user (i.e, being in at least one server with them),"
        " and that they need to have sent at least one message.\n\n"
        "If you believe that this is an error, please make a GitHub issue."), 404


    i = disc.ShittyDiscordHandler(os.getenv("TOKEN"))

    pfp, d = i.getAvatarFromUser(userid, size=64, rc=True)    
    print(pfp)

    return render_template("user_stats.html", messages_sent=messages, username=d['username'], commands_ran=commands, pfp=pfp, guild=True, userid=userid)
         


        
@app.route("/webui/user/stats/<int:userid>/<int:guildid>")
def user_page_guild(userid: int, guildid: int):
    cnx.reconnect()
    c = cnx.cursor()
        
    c.execute("SELECT messages_sent, commands_ran, user_level FROM guild_user_stats WHERE userid = %s AND guildid = %s", (userid, guildid))
    
    try:
        messages, commands, level = c.fetchone()
    except TypeError:
        return message("Error", "This user and/or guild is not recognized."), 404

    i = disc.ShittyDiscordHandler(os.getenv("TOKEN"))

    pfp, d = i.getAvatarFromUser(userid, size=64, rc=True)    
    print(pfp)
    return render_template("user_stats.html", messages_sent=messages, username=d['username'], commands_ran=commands, level=level, pfp=pfp, guild=True, userid=userid)
         
@app.route("/healthcheck")
@app.route("/webui/healthcheck")
def healthcheck():
    cnx.reconnect() # fix a stupid bug where it disconnects.  Bandaid fix, but oh-well...
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
