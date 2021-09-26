from flask import Flask, render_template, request, redirect, flash, session
import csv
import sqlite3
import re
import os

app = Flask(__name__)
app.secret_key = 'keyfornow'

#### Input new data
@app.route("/", methods = ["GET", "POST"])
def index():
    if request.method == "POST":

        if "dismiss_submit" in request.form:
            return redirect('/')
        
        if "submit_data" in request.form:
            # get data and codes, return error message if they aren't present
            data = request.files["upload_data"]
            if not data:
                flash("Missing data to upload.")
                return redirect('/')
            codes = request.files["upload_codes"]
            if not codes:
                flash("Missing qualitative codes.")
                return redirect('/')

            # temporarily save data and code files
            data.save("temp_data.csv")
            codes.save("temp_codes.csv")

            # create tables for the data and codes
            create_table(data, codes)

            # remove data and code files
            os.system("rm temp_data.csv temp_codes.csv")

            return redirect("/")

        if "code_data" in request.form:
            tablename = request.form.get("select_table")
            if not tablename:
                flash("Missing data to code.")
                return redirect("/")
            session["tablename"] = tablename
            session["index"] = 0

            return redirect("/code")

            

    else:
        conn = sqlite3.connect("qual_data.db")
        cursor = conn.cursor()
        tables_init = cursor.execute("SELECT table_name FROM table_list").fetchall()
        tables = ()
        if len(tables_init) > 0:
            tables = tables_init[0]
        return render_template("index.html", tables = tables)


def create_table(input_data, input_codes):

    #### Open SQLite connection
    conn = sqlite3.connect("qual_data.db")
    cursor = conn.cursor()

    #### Write data and codes to a table
    with open("temp_data.csv") as data, open("temp_codes.csv") as codes:

        #### Data - prepare data to add to table

        # read in data
        reader = csv.reader(data)
        header = next(reader) # save column names
        if len(header) != 2: # make sure there are two columns
            flash("Data must have two columns.")
            return redirect('/')
        if len(list(reader)) < 1: # make sure there's at least one row of data
            flash("CSV must have one row of column names and at least one row of data.")
        
        # prepare table name and column names
        tablename = clean_string(input_data.filename)
        colnames = prep_colnames(header)


        #### Codes - prepare qualitative codes to add to table
        codes_reader = csv.reader(codes)
        # need to put codes in a list since they're coming in the first column instead of first row
        codenames_init = []
        for row in codes_reader:
            if len(row) > 1: # make sure there's no more than one value per row
                flash("Codes must have only one column.")
                return redirect('/')
            if row[0] not in codenames_init:
                codenames_init.append(row[0])
        if len(codenames_init) == 0: # make sure there's at least one row
            flash("Codes must have at least one row.")
            return redirect('/')
        
        codenames = prep_colnames(codenames_init)



        #### Create table and insert data
        # create an empty table if it doesn't exist
        create_query = "CREATE TABLE IF NOT EXISTS {tablename} ({colnames_typed}, UNIQUE({colnames_untyped}))".format(
            tablename = tablename, 
            colnames_typed = colnames["typed"] + ', ' + codenames["typed"], 
            colnames_untyped = colnames["untyped"]
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

    # Open SQL connection, read in data from SQL table, and set data index to 0
    conn = sqlite3.connect("qual_data.db")
    cursor = conn.cursor()
    tablename = session["tablename"]
    data = cursor.execute("SELECT * FROM {}".format(tablename))
    data_full = data.fetchall()

    index = session["index"]

    # Get column names and qualitative codes
    colnames = []
    for i in range(len(data.description)):
        colnames.append(data.description[i][0])
    codes = colnames[2:]
    code_values = []

    if request.method == "POST":

        for code in codes:
            if request.form.get(code) == 'on':
                code_values.append("1")
            else:
                code_values.append("0")
        values = list(data_full[index][0:2])
        for value in code_values:
            values.append(value)

        insert_query = "INSERT OR REPLACE INTO {tablename} ({colnames}) VALUES ({values})".format(
            tablename = tablename,
            colnames = ', '.join(colnames),
            values = ', '.join(['?'] * len(values))
        )
        cursor.execute(insert_query, values)
            
        #### Commit changes and close SQL connection
        conn.commit()
        conn.close()

        if "back" in request.form:
            if session["index"] > 0:
                session["index"] -= 1
            return redirect("/code")

        else:
            session["index"] += 1
            return redirect("/code")

    else:
        if index >= len(data_full):
            flash("No more data to code")
            return render_template("code.html", display_data = '', codes = '')

        # construct the display data
        display_data = {"id": data_full[index][0], "text": data_full[index][1]}
        display_data["text"] = display_data["text"].replace("\n", "<br />")
        for i in range(len(codes)):
            display_data[codes[i]] = data_full[index][i + 2]
        
        #### Commit changes and close SQL connection
        conn.commit()
        conn.close()
    
        #for code in data[data_index]
        return render_template("code.html", display_data = display_data, codes = codes)