from flask import Flask, render_template, request, redirect, url_for, session, send_file
import re
import sqlite3
import datetime
import csv
from io import StringIO, BytesIO
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Needed for session management


# SQLite Database Setup
def init_db():
    if not os.path.exists('registrations.db'):
        conn = sqlite3.connect('registrations.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE registrations 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      name TEXT NOT NULL, 
                      vorname TEXT NOT NULL, 
                      timestamp TEXT NOT NULL)''')
        conn.commit()
        conn.close()


# Save data to SQLite
def save_to_db(name, vorname):
    try:
        conn = sqlite3.connect('registrations.db')
        c = conn.cursor()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO registrations (name, vorname, timestamp) VALUES (?, ?, ?)",
                  (name, vorname, timestamp))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Fehler beim Speichern in der Datenbank: {str(e)}")
        return False


# Get all registrations
def get_registrations():
    try:
        conn = sqlite3.connect('registrations.db')
        c = conn.cursor()
        c.execute("SELECT name, vorname, timestamp FROM registrations")
        data = c.fetchall()
        conn.close()
        return data
    except Exception as e:
        print(f"Fehler beim Abrufen der Daten: {str(e)}")
        return []


@app.route("/", methods=["GET", "POST"])
def anmeldung():
    init_db()  # Ensure database exists
    error_handling = ""
    name = request.form.get('name', '').strip()
    vorname = request.form.get('vorname', '').strip()

    if request.method == "POST":
        name_pattern = re.compile(r'^[A-Za-z\s-]+$')

        if not name or not vorname:
            error_handling = "Bitte füllen Sie sowohl Name als auch Vorname aus 😊"
        elif not name_pattern.match(name) or not name_pattern.match(vorname):
            error_handling = "Name und Vorname dürfen nur Buchstaben, Leerzeichen oder Bindestriche enthalten"
        elif len(name) < 2 or len(vorname) < 2:
            error_handling = "Name und Vorname müssen mindestens 2 Zeichen lang sein"
        else:
            success = save_to_db(name, vorname)
            if success:
                greeting = f"Hallo {vorname} {name}, willkommen zur Anmeldung! Ihre Daten wurden gespeichert."
                return render_template("anmeldung.html", error_handling=greeting, success=True)
            else:
                error_handling = "Daten konnten nicht gespeichert werden."

    return render_template("anmeldung.html", error_handling=error_handling, success=False)


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = ""
    if request.method == "POST":
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        # Hardcoded for simplicity (use proper auth in production)
        if username == "admin" and password == "password123":
            session['logged_in'] = True
            return redirect(url_for('admin_panel'))
        else:
            error = "Ungültiger Benutzername oder Passwort."
    return render_template("admin_login.html", error=error)


@app.route("/admin", methods=["GET"])
def admin_panel():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))

    registrations = get_registrations()
    return render_template("admin_panel.html", registrations=registrations)


@app.route("/admin/export", methods=["GET"])
def export_csv():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))

    registrations = get_registrations()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "Vorname", "Timestamp"])
    writer.writerows(registrations)

    # Convert StringIO to BytesIO for send_file
    output.seek(0)
    csv_data = BytesIO(output.getvalue().encode('utf-8'))

    return send_file(
        csv_data,
        mimetype='text/csv',
        as_attachment=True,
        download_name='registrations.csv'
    )


@app.route("/admin/logout")
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('anmeldung'))


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)