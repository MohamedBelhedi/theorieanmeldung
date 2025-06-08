from flask import Flask, render_template, request
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime

app = Flask(__name__)


# Google Sheets Setup
def connect_to_gsheets():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    try:
        credentials = ServiceAccountCredentials.from_json_keyfile_name('./credentials.json', scope)
        client = gspread.authorize(credentials)
        spreadsheet_id = "12uNf1PXvRJeRIdJWEGiVYhROMyjC6tsfyFGRkzQ2v_4"
        sheet = client.open_by_key(spreadsheet_id).sheet1
        return sheet
    except gspread.exceptions.SpreadsheetNotFound:
        return None
    except Exception as e:
        print(f"Verbindung zu Google Sheets fehlgeschlagen: {str(e)}")
        return None


# Funktion zum Speichern der Daten
def save_to_gsheets(sheet, name, vorname):
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = [name, vorname, timestamp]
        sheet.append_row(data)
        return True
    except gspread.exceptions.APIError as api_err:
        print(f"API-Fehler beim Speichern: {str(api_err)}")
        return False
    except Exception as e:
        print(f"Sonstiger Fehler beim Speichern: {str(e)}")
        return False


@app.route("/", methods=["GET", "POST"])
def anmeldung():
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
            sheet = connect_to_gsheets()
            if sheet:
                success = save_to_gsheets(sheet, name, vorname)
                if success:
                    greeting = f"Hallo {vorname} {name}, willkommen zur Anmeldung! Ihre Daten wurden gespeichert."
                    return render_template("anmeldung.html", error_handling=greeting, success=True)
                else:
                    error_handling = "Daten konnten nicht in Google Sheets gespeichert werden."
            else:
                error_handling = "Verbindung zu Google Sheets fehlgeschlagen."

    return render_template("anmeldung.html", error_handling=error_handling, success=False)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)