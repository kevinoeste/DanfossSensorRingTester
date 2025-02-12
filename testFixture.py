from datetime import datetime
from flask import Flask, render_template, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

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

class User(db.Model):
    id = db.Column(db.String(10), nullable=False, primary_key=True)
    TimeS = db.Column(db.Integer)
    x_dis = db.Column(db.Integer)

class MyForm(FlaskForm):
    SerialNum = StringField('SN', validators=[DataRequired()])
    submit = SubmitField('Start Test')
    
def __repr__(self):
    return f'<User  {self.id}>'

with app.app_context():
    db.create_all()
#define upper and lower limits of sensitivity to determine pass/fail

def insertTestData(fxpos, fxneg, fypos, fyneg, axpos, axneg):
    insertCommand = """INSERT INTO SensorData(timestamp, fx_pos, fx_neg, fy_pos, fy_neg, ax_pos, ax_neg) VALUES
    (""" + str(datetime.now()) + ", " + str(fxpos) + ", " + str(fxneg) + ", " + str(fypos) + """, 
    """ + str(fyneg) + ", " + str(axpos) + ", " + str(axneg) + ")"
    conn.execute(insertCommand)



#flask page control
@app.route('/')
def index():
    return render_template('index.html')


@app.route("/data")
def View():
    allu = User.query.all()
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
    x_dis = random.randint(0, 300)
    y_dis = random.randint(0, 300)
    FTime = datetime.now()
    Time = FTime.strftime("%m-%d-%Y %H:%M:%S")
    SN = session.get('SN')

    data = [
    {'SN': SN, 'Time': Time, 'x_dis': x_dis, 'y_dis': y_dis}   
    ]

    user = User(id=SN, TimeS=Time, x_dis=x_dis)
    db.session.add(user)
    db.session.commit()
    
    
    if x_dis < 100:
        return render_template('Passed.html',data=data)
    else:
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
