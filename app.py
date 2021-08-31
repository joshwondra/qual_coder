from flask import Flask, render_template, request
import csv
import sqlite3
import re

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

        # open sqlite conection and create cursor
        conn = sqlite3.connect("qual_data.db")
        cursor = conn.cursor()

        # read in data and create table
        with open(data.filename) as file:

            # read in data
            reader = csv.reader(file)
            header = next(reader)

            # get table name
            tablename_init = data.filename.lower().replace('.csv', '') # set to lower case and get rid of the .csv ending
            tablename = re.sub(r'[^\w]', '_', tablename_init) # change punctuation to _ to reduce risk of SQL injection attacks

            # get column names
            colnames_init = [re.sub(r'[^\w]', '_', colname) for colname in header] # change punctuation to _ to reduce risk of SQL injection attacks 
            colname_type = ', '.join([colname + " TEXT" for colname in colnames_init]) # prep column names with data type
            colnames = colname_type.replace(" TEXT", "") # remove data type

            # create an empty table if it doesn't exist
            create_query = "CREATE TABLE IF NOT EXISTS {tablename} ({colname_type}, UNIQUE({colnames}))".format(
                tablename = tablename, 
                colname_type = colname_type, 
                colnames = colnames
                )
            cursor.execute(create_query)

            # insert data into the table
            insert_query = "INSERT INTO {tablename} ({colnames}) VALUES ({values})".format(
                tablename = tablename, 
                colnames = colnames,
                values = ','.join('?' * len(header))
                )
            for row in reader:
                cursor.execute(insert_query, row)

            # finalize changes to the table
            conn.commit()

        return render_template("index.html")

    else:
        return render_template("index.html")

        # save data file, 
        data.save(data.filename)