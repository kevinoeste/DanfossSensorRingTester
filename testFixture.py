from datetime import datetime
from flask import Flask, render_template, request, session
from flask_sqlalchemy import SQLAlchemy # type: ignore
from flask_wtf import FlaskForm # type: ignore
from wtforms import StringField, SubmitField # type: ignore
from wtforms.validators import DataRequired # type: ignore

import sqlite3 as sql
import random
import os


app = Flask(__name__)

#set FLASK_APP = server

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.db')

app.config['SECRET_KEY'] = '123'
app.secret_key = "1234"

db = SQLAlchemy(app)



conn = sql.connect('testData.db')
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

isBroken = False
isTT = False
isVTT = False

test_no = 0

class SenData(db.Model):
    TestN = db.Column(db.Integer, primary_key=True)
    id = db.Column(db.String(10), nullable=False)
    TimeS = db.Column(db.Integer)
    xp_dis = db.Column(db.Float)
    xn_dis = db.Column(db.Float)
    yp_dis = db.Column(db.Float)
    yn_dis = db.Column(db.Float)
    zp_dis = db.Column(db.Float)
    zn_dis = db.Column(db.Float)
    pf = db.Column(db.String(10), nullable=False)

class MyForm(FlaskForm):
    SerialNum = StringField('SN', validators=[DataRequired()])
    submit = SubmitField('Start Test')
    
def __repr__(self):
    return f'<User  {self.id}>'

with app.app_context():
    db.create_all()
#define upper and lower limits of sensitivity to determine pass/fail


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



#flask page control
@app.route('/')
def index():
    return render_template('index.html')


@app.route("/data")
def View():
    allu = SenData.query.all()
    return render_template('ViewData.html', users=allu)

@app.route("/Start", methods=['GET', 'POST'])
def Test():

    form = MyForm()
    if form.validate_on_submit():
        SerialNum = form.SerialNum.data
        session['SN'] = SerialNum
       
        return render_template('Testing.html',SerialNum=SerialNum)
    
    return render_template('StartTest.html',form=form)

@app.route("/Edit")
def Edit():
    return render_template('EditDatabase.html')

@app.route("/DoTest")
def DoTest():

    return render_template('Testing.html',)


@app.route("/Testing", methods=['GET','POST'])
def Testing():
    low=1.4
    high=2

    xp_dis = round(random.uniform(low, high), 2)
    xn_dis = round(random.uniform(low, high), 2)
    yp_dis = round(random.uniform(low, high), 2)
    yn_dis = round(random.uniform(low, high), 2)
    zp_dis = round(random.uniform(low, high), 2)
    zn_dis = round(random.uniform(low, high), 2)
    FTime = datetime.now()
    Time = FTime.strftime("%m-%d-%Y %H:%M:%S")
    SN = session.get('SN')

    TestNum1 = SenData.query.order_by(SenData.TestN).value(0)
    
    TestNum= 12
    

    x1=int(xp_dis*100)
    if x1 < 150 | x1 > 180:
        data = [
        {'SN': SN, 'Time': TestNum1, 'xp_dis': xp_dis, 'xn_dis': xn_dis, 'yp_dis': yp_dis, 'yn_dis': yn_dis, 'zp_dis': zp_dis, 'zn_dis': zn_dis,'pf':"Pass"}   
        ]

        datas = SenData(TestN=TestNum, id=SN, TimeS=Time, xp_dis=xp_dis, xn_dis=xn_dis, yp_dis=yp_dis, yn_dis=yn_dis, zp_dis=zp_dis, zn_dis=zn_dis,pf="Pass")
        db.session.add(datas)
        db.session.commit()
        return render_template('Passed.html',data=data)
    else:
        data = [
        {'SN': SN, 'Time': TestNum1, 'xp_dis': xp_dis, 'xn_dis': xn_dis, 'yp_dis': yp_dis, 'yn_dis': yn_dis, 'zp_dis': zp_dis, 'zn_dis': zn_dis,'pf':"Fail"}   
        ]
        datas = SenData(TestN=TestNum, id=SN, TimeS=Time, xp_dis=xp_dis, xn_dis=xn_dis, yp_dis=yp_dis, yn_dis=yn_dis, zp_dis=zp_dis, zn_dis=zn_dis,pf="Fail")
        db.session.add(datas)
        db.session.commit()
        return render_template('Fail.html',data=data)


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


def startTest():
    test_no += 1
    #Get movement and displacement values from microcomputer and black box
    conn.execute("INSERT INTO SensorData (timestamp, fx_pos, fx_neg, fy_pos, fy_neg, ax_pos, ax_neg)  VALUES (CURRENT_TIME(), fx_plus, fx_minus, fy_plus, fy_minus, ax_plus, ax_minus);")
    #calculate sensitivity and insert into database
    #determine if the sensors in the sensor ring pass or fail the test
    return render_template('test_results.html')

if __name__ == "__main__":
    app.run(debug=True)

