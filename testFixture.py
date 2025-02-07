from flask import Flask, render_template, request
import sqlite3 as sql

app = Flask(__name__)

#set FLASK_APP = server

conn = sqlite3.connect('testData.db')
print("Connected to testData.")

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

isBroken = False;
isTT = False;
isVTT = False;

test_no = 0

#define upper and lower limits of sensitivity to determine pass/fail

#flask page control
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/viewDatabase')
def viewData():
    conn.execute("SELECT * FROM SensorData;")
    return render_template('view_data.html')

def startTest():
    test_no += 1
    #Get movement and displacement values from microcomputer and black box
    conn.execute("INSERT INTO SensorData (timestamp, fx_pos, fx_neg, fy_pos, fy_neg, ax_pos, ax_neg)  VALUES (CURRENT_TIME(), fx_plus, fx_minus, fy_plus, fy_minus, ax_plus, ax_minus);")
    #calculate sensitivity and insert into database
    #determine if the sensors in the sensor ring pass or fail the test
    return render_template('test_results.html')


