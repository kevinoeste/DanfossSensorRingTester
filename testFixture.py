from datetime import datetime
from flask import Flask, render_template, request, session
from flask_sqlalchemy import SQLAlchemy 
from flask_wtf import FlaskForm 
from wtforms import StringField, SubmitField 
from wtforms.validators import DataRequired 

import webview
import sqlite3 as sql
import random
import os


app = Flask(__name__)

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
    submit = SubmitField('Start Test')

#Used to create form to search database.
class MySearch(FlaskForm):
    SerialNum = StringField('Search by serial #:', validators=[DataRequired()])
    submit = SubmitField('Search')

#Used to create form for manual data entry.
class ManualEntry(FlaskForm):
    SerialNum = FXP = StringField('SN:    ', validators=[DataRequired()])
    FXP = StringField('FXP:', validators=[DataRequired()])
    FXN = StringField('FXN:', validators=[DataRequired()])
    FYP = StringField('FYP:', validators=[DataRequired()])
    FYN = StringField('FYN:', validators=[DataRequired()])
    AXP = StringField('AXP:', validators=[DataRequired()])
    AXN = StringField('AXN:', validators=[DataRequired()])
    submit = SubmitField('Submit Data')
    
def __repr__(self):
    return f'<SenData  {self.TestN}>'

with app.app_context():
    db.create_all()


#ValueTest checks each sensor value reading and checks if they fall between the spec range
def ValueTest(FXP,FXN,FYP,FYN,AXP,AXN):
    #Converts float values to integers to allow comparison.
    TFXP = int(FXP*100)
    TFXN = int(FXN*100)
    TFYP = int(FYP*100)
    TFYN = int(FYN*100)
    TAXP = int(AXP*100)
    TAXN = int(AXN*100)

    #Checks each sensor value to make sure its within range.
    #If its in the range 1 will be added to TestSum.
    TestSum=0
    if TFXP > 150 and TFXP < 180:
        TestSum +=1
    if TFXN > 150 and TFXN < 180:
        TestSum +=1
    if TFYP > 150 and TFYP < 180:
        TestSum +=1
    if TFYN > 150 and TFYN < 180:
        TestSum +=1
    if TAXP > 150 and TAXP < 180:
        TestSum +=1
    if TAXN > 150 and TAXN < 180:
        TestSum +=1

    return TestSum


#flask page control
@app.route('/')
def index():
    return render_template('index.html')


@app.route("/data", methods=['GET', 'POST'])
def View():
    #Gets all data from database and displays it in return.
    AllData = SenData.query.order_by(SenData.TestN.desc()).all()
    
    #Uses form to get serial number from user. Uses value to search all
    # database values containing it and then displays them.
    form = MySearch()
    if form.validate_on_submit():

        SerialNum = form.SerialNum.data
        results = SenData.query.filter(SenData.id == SerialNum).all()
        return render_template('SearchResults.html',SerialNum=SerialNum,results=results)
    
    return render_template('ViewData.html', AllData=AllData,form=form)

@app.route("/Start", methods=['GET', 'POST'])
def Test():

    #Uses form to get serial number from user. Stores it in session to be able to use later.
    form = MyForm()
    if form.validate_on_submit():
        SerialNum = form.SerialNum.data
        session['SN'] = SerialNum
       
        return render_template('Testing.html',SerialNum=SerialNum)
    
    return render_template('StartTest.html',form=form)

@app.route("/Edit", methods=['GET', 'POST'])
def Edit():

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

    #Creates random values ranging between the low and high values.
    low=1.4
    high=2

    FXP = round(random.uniform(low, high), 2)
    FXN = round(random.uniform(low, high), 2)
    FYP = round(random.uniform(low, high), 2)
    FYN = round(random.uniform(low, high), 2)
    AXP = round(random.uniform(low, high), 2)
    AXN = round(random.uniform(low, high), 2)

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
    TV=ValueTest(FXP,FXN,FYP,FYN,AXP,AXN)
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
