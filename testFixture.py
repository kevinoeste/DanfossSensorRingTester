from datetime import datetime
from flask import Flask, render_template, request, session, Response
from flask_sqlalchemy import SQLAlchemy 
from flask_wtf import FlaskForm 
from wtforms import StringField, SubmitField 
from wtforms.validators import DataRequired, Optional

import array, serial, time, threading
import subprocess 
import webview
import sqlite3 as sql
import random
import os

#To do:
#1: Format start test page better
#2: Fix edit database-works now but needs error correcting
#3: Finish adding info to home screen
#4: Add error routing if serial port cant be reached
#5: Add info to Info page(info on clearcore, how test is ran, pass fail parameters, etc)
#6: Check html navigation bar/headers to make sure all are the same


app = Flask(__name__)
data_lock = threading.Lock()

#Uncomment command below to open window when code is ran. Also must change code at bottom of file
#window = webview.create_window('Sensor Ring Test Program',app)

#Configuration used to create and find database file.
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'TestData.db')
app.config['SECRET_KEY'] = '123'
app.secret_key = "1234"

db = SQLAlchemy(app)

#Creates the format for database and is used when storing values in database.
class SenData(db.Model):
    TestN = db.Column(db.Integer, primary_key=True)
    id = db.Column(db.String(10), nullable=False)
    TimeS = db.Column(db.Integer)
    FXP = db.Column(db.Float)
    FXN = db.Column(db.Float)
    FYP = db.Column(db.Float)
    FYN = db.Column(db.Float)
    AXP = db.Column(db.Float)
    AXN = db.Column(db.Float)
    pf = db.Column(db.String(10), nullable=False)

#Used to create form for serial number entry.
class MyForm(FlaskForm):
    SerialNum = StringField('SN:', validators=[DataRequired()])
    submit = SubmitField('Submit')

#used for the x, y and z axis motor tests
class TestForm(FlaskForm):
    Axis = StringField('Enter x, y or z:', validators =[DataRequired()])
    submit = SubmitField('Submit')

#Used to create form to search database.
class MySearch(FlaskForm):
    SerialNum = StringField('Search by serial #:', validators=[DataRequired()])
    submit = SubmitField('Search')

#Used to create form for manual data entry.
class ManualEntry(FlaskForm):
    TestNum = StringField('Test Number:', validators=[DataRequired()])
    SerialNum = StringField('SN:', validators=[DataRequired()])
    FXP = StringField('FXP:', validators=[DataRequired()])
    FXN = StringField('FXN:', validators=[DataRequired()])
    FYP = StringField('FYP:', validators=[DataRequired()])
    FYN = StringField('FYN:', validators=[DataRequired()])
    AXP = StringField('AXP:', validators=[DataRequired()])
    AXN = StringField('AXN:', validators=[DataRequired()])
    submit = SubmitField('Submit Data')

#Used to edit a database value.
class ManualEntryEdit(FlaskForm):
    TestNum = StringField('Test Number:', validators=[DataRequired()])
    SerialNum = StringField('SN:')
    FXP = StringField('FXP:', validators=[Optional()])
    FXN = StringField('FXN:', validators=[Optional()])
    FYP = StringField('FYP:', validators=[Optional()])
    FYN = StringField('FYN:', validators=[Optional()])
    AXP = StringField('AXP:', validators=[Optional()])
    AXN = StringField('AXN:', validators=[Optional()])
    submit = SubmitField('Submit Data')

#Used to allow user to change COM Port
class ComPortEdit(FlaskForm):
    COM = StringField('COM Port:', validators=[DataRequired()])
    submit = SubmitField('Submit')
    
def __repr__(self):
    return f'<SenData  {self.TestN}>'

with app.app_context():
    db.create_all()


#ValueTest checks each sensor value reading and checks if they fall between the spec range
def ValueTest(XA,YA,ZA):
    #Converts float values to integers to allow comparison.
    TFXP = int(XA[1]*1000)
    TFXN = int(XA[2]*1000)
    TFYP = int(YA[3]*1000)
    TFYN = int(YA[4]*1000)
    TAXP = int(ZA[5]*1000)
    TAXN = int(ZA[6]*1000)

    #Checks each sensor value to make sure its within range.
    #If its in the range 1 will be added to TestSum.
    TestSum=0
    if TFXP > 1000 and TFXP < 1150:
        TestSum +=1
    if TFXN > 3000 and TFXN < 3150:
        TestSum +=1
    if TFYP > 1000 and TFYP < 1150:
        TestSum +=1
    if TFYN > 3000 and TFYN < 3150:
        TestSum +=1
    if TAXP > 1000 and TAXP < 1150:
        TestSum +=1
    if TAXN > 3000 and TAXN < 3150:
        TestSum +=1

    return TestSum


#flask page control
@app.route('/')
def index():
    return render_template('index.html')




@app.route('/axisTestSelect', methods=['POST', 'GET'])
def axisTestSelect():
    #try:
    form = TestForm()
    # Reads ComPort value from text file
    #with open('ComPort.txt', 'r') as file:
        #ComPort = file.read()
    ComPort = "COM6"
    if form.validate_on_submit():
        try:
            motorChar = form.Axis.data
            session['MC'] = motorChar
            ser = serial.Serial(ComPort, 9600, timeout=1)
            time.sleep(2)  # Wait for serial connection to initialize
            print("Connected")
            ser.write(bytearray(motorChar, 'ascii'))
            msg = "Sent character to clearCore"
        except serial.SerialException as e:
            print(f"Error opening serial port: {e}")
            ser = None
            error_type = "Comport"
            error_message = "Could not connect to Comport: " + ComPort
            return render_template('Error.html', error_type=error_type, error_message=error_message)
        return render_template("axisTest.html", motorChar=motorChar, msg=msg)

    #except:
        #msg = "Error: Could not communicate with ClearCore"
    return render_template('axisTestSelect.html', form=form)
@app.route('/stopTest')
def stopTest():
    try:
        ser = serial.Serial()
        #using the com port defined by the user
        ser.port = session['COM']
        #unsure of the baud rate of the clearcore serial port, assuming 19200 for now
        ser.baudrate = 19200
        ser.write(bytearray('0', 'ascii'))
        msg = "Stopped test."
    except:
        msg = "Error: Could not stop test"
    finally:
        return render_template("stopTest.html", msg = msg)
@app.route('/Info')
def Info():
    return render_template('Info.html')

#Page that displays database data.
@app.route("/data", methods=['GET', 'POST'])
def View():
    #Gets all data from database and displays it in return.
    AllData = SenData.query.order_by(SenData.TestN.desc()).all()
    
    #Uses form to get serial number from user. Uses value to search all
    # database values containing it and then displays them.
    form = MySearch()
    if form.validate_on_submit():

        SerialNum = form.SerialNum.data
        results = SenData.query.filter(SenData.id == SerialNum).order_by(SenData.TestN.desc()).all()
        return render_template('SearchResults.html',SerialNum=SerialNum,results=results)
    
    return render_template('ViewData.html', AllData=AllData,form=form)

#Routes to page to enter sensor ring serial number to begin test.
@app.route("/Start", methods=['GET', 'POST'])
def Test():

    #Uses form to get serial number from user. Stores it in session to be able to use later.
    form = MyForm()
    if form.validate_on_submit():
        SerialNum = form.SerialNum.data
        session['SN'] = SerialNum
       
        return render_template('Confirm.html',SerialNum=SerialNum)
    
    #Uses form to get Com Port value from user.
    Comform = ComPortEdit()
    if Comform.validate_on_submit():
        Com = Comform.COM.data
        session['COM'] = Com
       
        # Stores Com value in text file.
        with open("ComPort.txt", "w") as file:
            file.write(Com)

        return render_template('ComConfirm.html',Com=Com)
    
    return render_template('StartTest.html',form=form,Comform=Comform)

@app.route("/Edit", methods=['GET', 'POST'])
def Edit():

    return render_template('Edit.html')

#Work in progress-Edits values in database
@app.route("/EditVal", methods=['GET', 'POST'])
def EditVal():
     
    form = ManualEntryEdit()
    if form.validate_on_submit():

        TN = int(form.TestNum.data)
        row_to_update = SenData.query.get(TN)

        #Storing data from form
        SerialNum = form.SerialNum.data
        if form.FXP.data == "":
            FXP = float(row_to_update.FXP)
        else:
            FXP1= form.FXP.data
            FXP = float(FXP1)

        if form.FXN.data == "":
            FXN = float(row_to_update.FXN)
        else:
            FXN1 = form.FXN.data
            FXN = float(FXN1)

        if form.FYP.data == "":
            FYP = float(row_to_update.FYP)
        else:
            FYP1 = form.FYP.data
            FYP = float(FYP1)

        if form.FYN.data == "":
            FYN = float(row_to_update.FYN)
        else:
            FYN1 = form.FYN.data
            FYN = float(FYN1)

        if form.AXP.data == "":
            AXP = float(row_to_update.AXP)
        else:
            AXP1 = form.AXP.data
            AXP = float(AXP1)
        
        if form.FYP.data == "":
            AXN1 = float(row_to_update.AXN)
        else:
            AXN1 = form.AXN.data
            AXN = float(AXN1)             

        #Stores current date and time and formats it.
        FTime = datetime.now()
        Time = FTime.strftime("%m-%d-%Y %H:%M:%S")
        
        if row_to_update:
            row_to_update.FXP = FXP
            row_to_update.FXN = FXN
            row_to_update.FYP = FYP
            row_to_update.FYN = FYN
            row_to_update.AXP = AXP
            row_to_update.AXN = FXN
            db.session.commit()
        else:
            print("Not found.")

        datas = [{'SN': SerialNum, 'Time': Time, 'FXP': FXP, 'FXN': FXN, 'FYP': FYP, 'FYN': FYN, 'AXP': AXP, 'AXN': AXN,'pf':"Pass"}]


        return render_template('Passed.html',data=datas)

    return render_template('EditDatabase.html', form=form)

#Manual entry database values
@app.route("/AddVal", methods=['GET', 'POST'])
def AddEdit():

    form = ManualEntry()
    if form.validate_on_submit():
        #Storing data from form
        SerialNum = form.SerialNum.data
        FXP1= form.FXP.data
        FXN1 = form.FXN.data
        FYP1 = form.FYP.data
        FYN1 = form.FYN.data
        AXP1 = form.AXP.data
        AXN1 = form.AXN.data

        #Converts strings to floats
        FXP = float(FXP1)
        FXN = float(FXN1)
        FYP = float(FYP1)
        FYN = float(FYN1)
        AXP = float(AXP1)
        AXN = float(AXN1)

        #Stores current date and time and formats it.
        FTime = datetime.now()
        Time = FTime.strftime("%m-%d-%Y %H:%M:%S")

        #Counter used to keep track of number of tests done.
        #If theres no database entries TestNum starts at 1.
        TestNum1 = SenData.query.order_by(SenData.TestN.desc()).first()
        if TestNum1 is None:
            TestNum = 1
        else:
            TestNum= int(TestNum1.TestN) +1
    
        #Decides if test passed or failed based on using the ValueTest function. TV represents how many sensors passed.
        TV=ValueTest(FXP,FXN,FYP,FYN,AXP,AXN)
        if TV==6:
            #data sends data to be displayed on the Passed.html page
            data = [{'SN': SerialNum, 'Time': Time, 'FXP': FXP, 'FXN': FXN, 'FYP': FYP, 'FYN': FYN, 'AXP': AXP, 'AXN': AXN,'pf':"Pass"}]

            #datas holds values that are then sent and stored in the database
            datas = SenData(TestN=TestNum, id=SerialNum, TimeS=Time, FXP=FXP, FXN=FXN,FYP=FYP,FYN=FYN,AXP=AXP,AXN=AXN,pf="Pass")
            db.session.add(datas)
            db.session.commit()

            return render_template('Passed.html',data=data)
    
        else:
            #data sends data to be displayed on the Fail.html page.
            data = [{'SN': SerialNum, 'Time': Time, 'FXP': FXP, 'FXN': FXN, 'FYP': FYP, 'FYN': FYN, 'AXP': AXP, 'AXN': AXN,'pf':"Fail"}]

            #datas holds values that are then sent and stored in the database.
            datas = SenData(TestN=TestNum, id=SerialNum, TimeS=Time, FXP=FXP, FXN=FXN,FYP=FYP,FYN=FYN,AXP=AXP,AXN=AXN,pf="Fail")
            db.session.add(datas)
            db.session.commit()

            return render_template('Fail.html',data=data)
        
    return render_template('EditDatabase.html', form=form)


@app.route("/DoTest")
def DoTest():

    return render_template('Testing.html',)


@app.route("/Testing", methods=['GET','POST'])
def Testing():

    #Stored array values
    #0-Voltage read at center
    #1-Voltage at positive x-axis
    #2-Voltage at negative x-axis
    #3-Voltage at positive y-axis
    #4-Voltage at negative y-axis
    #5-Voltage at positve z-axis
    #6-Voltage at negative z-axis
    #                      0    1    2    3    4    5    6
    XA = array.array('d',[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    YA = array.array('d',[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    ZA = array.array('d',[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    # Reads ComPort value from text file
    #with open('ComPort.txt', 'r') as file:
        #ComPort = file.read()
    ComPort = 'COM6'
    #Attempts to connect to serial port
    try:
        ser = serial.Serial(ComPort, 9600, timeout=1)  
        time.sleep(2) # Wait for serial connection to initialize
        print("Connected")

    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")
        ser = None
        error_type = "Comport"
        error_message = "Could not connect to Comport: " + ComPort
        return render_template('Error.html',error_type=error_type,error_message=error_message)


    TestIO = '1'
    #Sends commands to start test to clearcore
    ser.write(TestIO.encode())

    #Initialize variables for test
    
    newdata = None
    latest_data = None
    count=0

    #Loops while test is running to recieve data from serial port.
    while TestIO=='1':
        if ser.in_waiting > 0:
            try:
                line = ser.readline().decode('utf-8').strip()
                with data_lock:
                    latest_data = line
                    
            except Exception as e:
                print(f"Error reading serial data: {e}")
            
            #Updates newdata if data is new
            if latest_data != newdata:
                newdata = latest_data
                #Stores the voltage readings from each axis.
                if newdata !='0':
                    StringData = newdata.split(",")
                    count = int(StringData[0])
                    XA[count] = float(StringData[1])
                    YA[count] = float(StringData[2])
                    ZA[count] = float(StringData[3])

                print(newdata)

            #Clearcore sends 0 at end of test. Once recieved the while loop ends.
            if latest_data =='0':
                TestIO='0'
                
        #Checks if new data available from serial port every 0.5 seconds        
        time.sleep(0.5)

    #Closes serial port  
    ser.close()

    #Storing test data
    FXP = XA[1]
    FXN = XA[2]
    FYP = YA[3]
    FYN = YA[4]
    AXP = ZA[5]
    AXN = ZA[6]

    #Stores current date and time and formats it.
    FTime = datetime.now()
    Time = FTime.strftime("%m-%d-%Y %H:%M:%S")

    #Gets serial number value from earlier form.
    SN = session.get('SN')
    
    #Counter used to keep track of number of tests done.
    #If theres no database entries TestNum starts at 1.
    TestNum1 = SenData.query.order_by(SenData.TestN.desc()).first()
    if TestNum1 is None:
        TestNum = 1
    else:
        TestNum= int(TestNum1.TestN) +1
    
    #Decides if test passed or failed based on using the ValueTest function. TV represents how many sensors passed.
    TV=ValueTest(XA,YA,ZA)
    if TV==6:
        #data sends data to be displayed on the Passed.html page
        data = [{'SN': SN, 'Time': Time, 'FXP': FXP, 'FXN': FXN, 'FYP': FYP, 'FYN': FYN, 'AXP': AXP, 'AXN': AXN,'pf':"Pass"}]

        #datas holds values that are then sent and stored in the database
        datas = SenData(TestN=TestNum, id=SN, TimeS=Time, FXP=FXP, FXN=FXN,FYP=FYP,FYN=FYN,AXP=AXP,AXN=AXN,pf="Pass")
        db.session.add(datas)
        db.session.commit()

        return render_template('Passed.html',data=data)
    else:
        #data sends data to be displayed on the Fail.html page.
        data = [{'SN': SN, 'Time': Time, 'FXP': FXP, 'FXN': FXN, 'FYP': FYP, 'FYN': FYN, 'AXP': AXP, 'AXN': AXN,'pf':"Fail"}]

        #datas holds values that are then sent and stored in the database.
        datas = SenData(TestN=TestNum, id=SN, TimeS=Time, FXP=FXP, FXN=FXN,FYP=FYP,FYN=FYN,AXP=AXP,AXN=AXN,pf="Fail")
        db.session.add(datas)
        db.session.commit()

        return render_template('Fail.html',data=data)


if __name__ == "__main__":
    #Uncomment webview and comment out app.run to launch program in seperate window.
    app.run(debug=True)
    #webview.start()
