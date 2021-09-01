from flask import Flask, render_template, request, redirect
import csv
import sqlite3
import re
import os

app = Flask(__name__)

#### Input new data
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

        # create tables for the data and codes
        create_table(data, codes)

        return redirect("/")

    else:
        conn = sqlite3.connect("qual_data.db")
        cursor = conn.cursor()
        tables_init = cursor.execute("SELECT table_name FROM table_list").fetchall()
        tables = ()
        if len(tables_init) > 0:
            tables = tables_init[0]
        return render_template("index.html", tables = tables)


def create_table(input_data, input_codes):

    #### Temporarily save data and code files
    input_data.save("temp_data.csv")
    input_codes.save("temp_codes.csv")

    #### Open SQLite connection
    conn = sqlite3.connect("qual_data.db")
    cursor = conn.cursor()

    #### Write data and codes to a table
    with open("temp_data.csv") as data, open("temp_codes.csv") as codes:

        #### Data - prepare data to add to table

        # read in data
        reader = csv.reader(data)
        header = next(reader) # save column names
        
        # prepare table name and column names
        test = input_data.filename
        tablename = clean_string(input_data.filename)
        colnames = prep_colnames(header)


        #### Codes - prepare qualitative codes to add to table
        codes_reader = csv.reader(codes)
        # need to put codes in a list since they're coming in the first column instead of first row
        codenames_init = [] 
        for row in codes_reader:
            codenames_init.append(row[0])
        codenames = prep_colnames(codenames_init)



        #### Create table and insert data
        # create an empty table if it doesn't exist
        create_query = "CREATE TABLE IF NOT EXISTS {tablename} ({colnames_typed}, UNIQUE({colnames_untyped}))".format(
            tablename = tablename, 
            colnames_typed = colnames["typed"] + ', ' + codenames["typed"], 
            colnames_untyped = colnames["untyped"] + ', ' + codenames["untyped"]
            )
        cursor.execute(create_query)

        # insert data into the table
        insert_query = "INSERT OR IGNORE INTO {tablename} ({colnames_untyped}) VALUES ({values})".format(
            tablename = tablename,
            colnames_untyped = colnames["untyped"],
            values = ','.join('?' * len(header))
            )
        for row in reader:
            cursor.execute(insert_query, row)


        

        #### Finalize changes
        
        # add record of the new table
        cursor.execute("INSERT OR IGNORE INTO table_list (table_name) VALUES ('{}')".format(tablename))


    #### Commit changes and close SQL connection
    conn.commit()
    conn.close()

    #### Remove data and code files
    os.system("rm temp_data.csv temp_codes.csv")

def clean_string(string): # formats string and cleans it to reduce risk of SQL injection attacks
    string_temp = string.lower().replace('.csv', '') # lower case, remove .csv
    string_cleaned = re.sub(r'[^\w]', '_', string_temp) # change punctuation to _
    return string_cleaned

def prep_colnames(colnames): # takes list of column names as input, cleans them, and stores names with type and without
    cleaned = [clean_string(colname) for colname in colnames] # format and clean column names
    typed = ', '.join([colname + " TEXT" for colname in cleaned]) # get column names with TEXT data type
    untyped = typed.replace(" TEXT", "") # remove TEXT data type
    return {"typed": typed, "untyped": untyped}

#### Select data to code
@app.route("/code", methods = ["GET", "POST"])
def code():
    if request.method == "POST":
        data = request.form.get("select_table")
        if not data:
            return render_template("index.html", message = "Missing data to code")
        return render_template("code.html")
    else:
        return redirect("/")