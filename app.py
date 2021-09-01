from flask import Flask, render_template, request, redirect
import csv
import sqlite3
import re
import os

app = Flask(__name__)

@app.route("/", methods = ["GET", "POST"])
def index():
    if request.method == "POST":

        # get data and codes, return error message if they aren't present
        data = request.files["upload_data"]
        if not data:
            return render_template("index.html", message = "Missing data to upload")
        codes = request.files["upload_codes"]
        if not codes:
            return render_template("index.html", message = "Missing qualitative codes")

        # create tables for the data and codes, function returns the table names
        table_data = create_table(data)
        table_codes = create_table(codes)

        # create a table that links the data to the codes
        link_tables(table_data, table_codes)

        return redirect("/")

    else:
        conn = sqlite3.connect("qual_data.db")
        cursor = conn.cursor()
        tables = cursor.execute("SELECT table_data FROM data_code_linkage").fetchall()[0]
        return render_template("index.html", tables = tables)


def create_table(input):

    # temporarily save file
    input.save("temp.csv")

    with open("temp.csv") as file:

        # read in data
        reader = csv.reader(file)
        header = next(reader)

        # get table name
        tablename_init = input.filename.lower().replace('.csv', '') # set to lower case and get rid of the .csv ending
        tablename = re.sub(r'[^\w]', '_', tablename_init) # change punctuation to _ to reduce risk of SQL injection attacks

        # get column names
        colnames_init = [re.sub(r'[^\w]', '_', colname) for colname in header] # change punctuation to _ to reduce risk of SQL injection attacks 
        colname_type = ', '.join([colname + " TEXT" for colname in colnames_init]) # prep column names with data type
        colnames = colname_type.replace(" TEXT", "") # remove data type

        # open sqlite conection and create cursor
        conn = sqlite3.connect("qual_data.db")
        cursor = conn.cursor()    

        # create an empty table if it doesn't exist
        create_query = "CREATE TABLE IF NOT EXISTS {tablename} ({colname_type}, UNIQUE({colnames}))".format(
            tablename = tablename, 
            colname_type = colname_type, 
            colnames = colnames
            )
        cursor.execute(create_query)

        # insert data into the table
        insert_query = "INSERT OR IGNORE INTO {tablename} ({colnames}) VALUES ({values})".format(
            tablename = tablename, 
            colnames = colnames,
            values = ','.join('?' * len(header))
            )
        for row in reader:
            cursor.execute(insert_query, row)

        # finalize changes to the table
        conn.commit()
        conn.close()
        
    # remove original data file when we're done
    os.system("rm temp.csv")
    return tablename

def link_tables(table_name_data, table_name_codes):
    # open sqlite conection and create cursor
    conn = sqlite3.connect("qual_data.db")
    cursor = conn.cursor() 

    # create table and insert data
    cursor.execute("CREATE TABLE IF NOT EXISTS data_code_linkage (table_data TEXT, table_code TEXT, UNIQUE(table_data, table_code))")
    cursor.execute("INSERT OR IGNORE INTO data_code_linkage (table_data, table_code) VALUES('{data}', '{codes}')".format(
        data = table_name_data, 
        codes = table_name_codes
        ))

    # finalize changes to the table
    conn.commit()
    conn.close()

@app.route("/code", methods = ["GET", "POST"])
def code():
    if request.method == "POST":
        data = request.form.get("select_table")
        if not data:
            return render_template("index.html", message = "Missing data to code")
        return render_template("code.html")
    else:
        return redirect("/")