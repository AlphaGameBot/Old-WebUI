from flask import render_template

def message(message, type="INFO"):
    return render_template('messagebox.html', type=type, message=message)