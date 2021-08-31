from flask import Flask, render_template, request
import csv
import sqlite3

app = Flask(__name__)

@app.route("/", methods = ["GET", "POST"])
def index():
    if request.method == "POST":

        # get data and codes, return error message if they aren't present
        data = request.files["upload_data"]
        if not data:
            return render_template("index.html", message = "Missing data to upload")
        # codes = request.files["upload_codes"]
        #if not codes:
        #    return render_template("index.html", message = "Missing qualitative codes")

        # temporarily save files
        data.save(data.filename)
        #codes.save("codes_" + codes.filename)

        # open sqlite conection
        conn = sqlite3.connect("qual_data.db")

        # read in data and create table
        with open(data.filename) as file:
            reader = csv.reader(file)
            header = next(reader)
            tablename = data.filename.lower().replace('.csv', '').replace(' ', '_')
            colnames = [colname + " TEXT" for colname in header]

            conn.execute("CREATE TABLE IF NOT EXISTS {tablename} ({columns})".format(
                tablename = tablename,
                columns = ', '.join(colnames)
                )
            )
        return render_template("index.html")

    else:
        return render_template("index.html")

        # save data file, 
        data.save(data.filename)