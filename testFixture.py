from flask import Flask, render_template, request, redirect
import sqlite3 as sql
import datetime
import random

app = Flask(__name__)

#set FLASK_APP = testFixture.py

#initialize inductor voltage values
fx_plus = 0
fx_minus = 0
fy_plus = 0
fy_minus = 0
ax_plus = 0
ax_minus = 0

#initialize movement values
x_displacement = 0
y_displacement = 0
z_displacement = 0

isBroken = False
isTT = False
isVTT = False

test_no = 0

def insertTestData(fxpos, fxneg, fypos, fyneg, axpos, axneg):
    try:
        conn = sql.connect('testData.db')
        print("Connected to testData.")
        testData = (fxpos, fxneg, fypos, fyneg, axpos, axneg)
        conn.execute("INSERT INTO SensorData(timestamp, fx_pos, fx_neg, fy_pos, fy_neg, ax_pos, ax_neg) VALUES (CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?)", testData)
        conn.commit()
        conn.close()
    except:
        print("Error inserting values into the table.")
def randomTestData(numEntries):
    for x in range (0, numEntries):
        insertTestData(random.random(), random.random(), random.random(), random.random(), random.random(), random.random())
#define upper and lower limits of sensitivity to determine pass/fail

#flask page control
#pretty much the home page
@app.route('/')
def index():
    return render_template('index.html')

#View the database
@app.route('/viewDatabase')
def viewData():
    try:    
        conn = sql.connect('testData.db')
        print("Connected to testData.")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM SensorData;")
        results = cursor.fetchall()
        msg = ""
        conn.close()
    except:
        results = ["#"]
        msg = "Error: Could not connect to database."
    finally:
        return render_template('view_data.html', msg = msg, results = results)

#display the HTML form for adding the data
@app.route('/manualAddDataForm', methods = ['POST', 'GET'])
def manualAddDataForm():
    return render_template('manualDataForm.html')
#function for actually adding the data from the HTML form to the database
@app.route('/manualAddData', methods = ['POST', 'GET'])
def manualAddData():
    if request.method == 'POST':
        try:
            #get the information from the HTML form
            fxpos = request.form['fx_pos']
            fxneg = request.form['fx_neg']
            fypos = request.form['fy_pos']
            fyneg = request.form['fy_neg']
            axpos = request.form['ax_pos']
            axneg = request.form['ax_neg']

            #add the values to the database
            insertTestData(fxpos, fxneg, fypos, fyneg, axpos, axneg)
            msg = "Test data was successfully stored."
        except:
            msg = "Error: Test data could not be added to the database."
        finally:
            return render_template("result.html", msg = msg)

@app.route('/addRandomData')
def addRandomData():
    try:
        randomTestData(5)
        msg = "Data added"
    except:
        msg = "Error: Cannot add the random test data"
    return render_template('result.html', msg = msg)
@app.route('/resetDB')
def resetDB():
    try:
        conn = sql.connect('testData.db')
        print("Connected to testData.")
        conn.execute("DELETE * FROM SensorData;")
        msg = "Table SensorData has been cleared."
    except:
        msg = "Error: Table SensorData could not be cleared."
    finally:
        conn.close()
        return render_template("result.html", msg = msg)

@app.route('/editParameters')
def editParameters():
    #don't know if we're gonna use this, but I'll have it here just in case
    #would allow the user to edit how the test is run
    #not yet implemented, low priority
    return render_template("index.html")
            

@app.route('/startTest')
def startTest():
    conn = sql.connect('testData.db')
    print("Connected to testData.")
    test_no += 1
    #Get movement and displacement values from microcomputer and black box
    conn.execute("INSERT INTO SensorData (timestamp, fx_pos, fx_neg, fy_pos, fy_neg, ax_pos, ax_neg)  VALUES (CURRENT_TIME(), fx_plus, fx_minus, fy_plus, fy_minus, ax_plus, ax_minus);")
    #calculate sensitivity and insert into database
    #determine if the sensors in the sensor ring pass or fail the test
    conn.close()
    return render_template('test_results.html')

if __name__ == "__main__":
    app.run(debug = True)
