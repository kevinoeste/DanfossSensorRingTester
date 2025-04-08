from datetime import datetime, timedelta

from flask import Flask, render_template, request, session, Response,redirect,url_for,flash
from flask_sqlalchemy import SQLAlchemy 
from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import StringField, SubmitField
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from wtforms.fields.simple import PasswordField
from wtforms.validators import DataRequired, Optional,Length,EqualTo


import array, serial,time, threading
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
app.config['SESSION_COOKIE_LIFETIME'] = None
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

db = SQLAlchemy(app)
login_manager = LoginManager(app)       #Login Manager used to help validate users throughout the app
login_manager.login_view = 'login'

#Creates the format for database and is used when storing values in database.
class SenData(db.Model):
    TestN = db.Column(db.Integer, primary_key=True) #Auto incremented later in program but is unique for each sensor
    id = db.Column(db.String(10), nullable=False)   #This is the serial number
    TimeS = db.Column(db.Integer)
    FXP = db.Column(db.Float)
    FXN = db.Column(db.Float)
    FYP = db.Column(db.Float)
    FYN = db.Column(db.Float)
    AXP = db.Column(db.Float)
    AXN = db.Column(db.Float)
    pf = db.Column(db.String(10), nullable=False)

    def __repr__(self):
        return f'<SenData  {self.TestN}>'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    #Hash the password
    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    #check the entered password hash matches the database hash
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

#table to form a many-to-many relationship between test and user
class TestLog(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)       #Maps to unique user
    test_n = db.Column(db.String(10), db.ForeignKey('sen_data.TestN'), nullable=False)  #Maps to unique test
    timestamp = db.Column(db.String(20), nullable=False)  # Optional: store when the test was performed

    user = db.relationship('User', backref='test_logs')
    test = db.relationship('SenData', backref='test_logs')

    def __repr__(self):
        return f'<TestLog {self.id}>'

#Used to check login user
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

#Used to register new users
class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=50)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    admin_username = StringField('Admin Username', validators=[DataRequired()])
    admin_password = PasswordField('Admin Password', validators=[DataRequired()])
    submit = SubmitField('Register')


#Used to create form for serial number entry.
class MyForm(FlaskForm):
    SerialNum = StringField('SN:', validators=[DataRequired()])
    submit = SubmitField('Submit')

#Used to create form to search database by serial number.
class MySearch(FlaskForm):
    SerialNum = StringField('Search by serial #:', validators=[DataRequired()])
    submit = SubmitField('Search')

# Used to create form to search database by user.
class UserSearch(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    submit = SubmitField('Search by User')

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
    SerialNum = StringField('SN:' , validators=[Optional()])
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

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username="admin").first():      #adding an initial admin.
        user = User(username="admin", is_admin=True)
        user.set_password("admin123")
        db.session.add(user)
        db.session.commit()

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

@login_manager.user_loader              #this starts the login manager and associate the userid with session
def load_user(user_id):
    return User.query.get(int(user_id))
#flask page control
@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login',methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            flash('Login Sucesssful', 'success')
            login_user(user,remember=False)
            session.permanent = False   #creates a session cookie to logout user when browser closes
            return redirect(url_for('index'))
        else:
            flash('Invalid Credentials','error')
    return render_template('login.html',form=form)

@app.route('/logout' , methods=['GET'])
@login_required
def logout():
    flash('You have been logged out.', 'success')
    logout_user()
    session.clear()
    return redirect(url_for('login'))
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # Check if the new username is already taken
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already taken.', 'error')
            return render_template('register.html', form=form)

        # Verify admin credentials
        admin = User.query.filter_by(username=form.admin_username.data).first()
        if not admin or not admin.check_password(form.admin_password.data) or not admin.is_admin:
            flash('Invalid admin credentials. Registration requires valid admin approval.', 'error')
            return render_template('register.html', form=form)

        # If admin credentials are valid, create the new user
        new_user = User(username=form.username.data)
        new_user.set_password(form.password.data)
        # New users are not admins by default
        new_user.is_admin = False
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please log in with your new credentials.', 'success')
        return(render_template('login.html',form=form))

    return render_template('register.html', form=form)
@app.route('/Info')
@login_required
def Info():
    return render_template('Info.html')

#Page that displays database data.
@app.route("/data", methods=['GET', 'POST'])
@login_required
def View():
    # Get all sensor data ordered by TestN
    AllData = SenData.query.order_by(SenData.TestN.desc()).all()

    # Map serial numbers to usernames using TestLog
    test_logs = {}
    for log in TestLog.query.order_by(TestLog.id.desc()).all():
        # Find all SenData records with the matching id
        sen_data_records = SenData.query.filter_by(TestN=log.test_n).all()
        for sen_data in sen_data_records:
            test_logs[sen_data.id] = log.user.username

    serial_form = MySearch()
    user_form = UserSearch()

    # Search by serial number
    if serial_form.validate_on_submit() and serial_form.submit.data:
        SerialNum = serial_form.SerialNum.data
        results = SenData.query.filter(SenData.id == SerialNum).order_by(SenData.TestN.desc()).all()

        search_logs = {}
        test_numbers = [r.TestN for r in results]
        logs = TestLog.query.filter(TestLog.test_n.in_(test_numbers)).order_by(TestLog.id.desc()).all()
        if logs:
            for r in results:
                search_logs[r.id] = logs[0].user.username
        return render_template('SearchResults.html', SerialNum=SerialNum, results=results, search_logs=search_logs)

    # Search by username
    if user_form.validate_on_submit() and user_form.submit.data:
        username = user_form.username.data
        user = User.query.filter_by(username=username).first()
        if user:
            user_logs = TestLog.query.filter_by(user_id=user.id).all()
            test_numbers = [log.test_n for log in user_logs]
            results = SenData.query.filter(SenData.TestN.in_(test_numbers)).order_by(SenData.TestN.desc()).all()

            # Map serial numbers to the username for the matching TestN values
            search_logs = {}
            for log in user_logs:  # Only iterate over TestLog entries for this user
                sen_data_records = SenData.query.filter_by(TestN=log.test_n).all()
                for sen_data in sen_data_records:
                    search_logs[sen_data.id] = log.user.username  # Should be the same user
            return render_template('UserSearchResults.html', username=username, results=results,
                                   search_logs=search_logs)
        else:
            flash('User not found.', 'error')

    return render_template('ViewData.html', AllData=AllData, serial_form=serial_form,
                           user_form=user_form, test_logs=test_logs)
#Routes to page to enter sensor ring serial number to begin test.
@app.route("/Start", methods=['GET', 'POST'])
@login_required
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
@login_required
def Edit():

    return render_template('Edit.html')

#Work in progress-Edits values in database
@app.route("/EditVal", methods=['GET', 'POST'])
@login_required
def EditVal():
     
    form = ManualEntryEdit()
    if form.validate_on_submit():

        TN = int(form.TestNum.data)
        row_to_update = SenData.query.get(TN)

        if row_to_update:
            # Storing data from form, using existing values if fields are empty
            SerialNum = form.SerialNum.data or row_to_update.id
            FXP = float(form.FXP.data) if form.FXP.data else float(row_to_update.FXP)
            FXN = float(form.FXN.data) if form.FXN.data else float(row_to_update.FXN)
            FYP = float(form.FYP.data) if form.FYP.data else float(row_to_update.FYP)
            FYN = float(form.FYN.data) if form.FYN.data else float(row_to_update.FYN)
            AXP = float(form.AXP.data) if form.AXP.data else float(row_to_update.AXP)
            AXN = float(form.AXN.data) if form.AXN.data else float(row_to_update.AXN)
            # Update the row
            row_to_update.id = SerialNum
            row_to_update.FXP = FXP
            row_to_update.FXN = FXN
            row_to_update.FYP = FYP
            row_to_update.FYN = FYN
            row_to_update.AXP = AXP
            row_to_update.AXN = AXN

            # Update timestamp
            FTime = datetime.now()
            Time = FTime.strftime("%m-%d-%Y %H:%M:%S")
            row_to_update.TimeS = Time


            db.session.commit()
            # Prepare data for display
            datas = [{'TestN': row_to_update.TestN,'SN': SerialNum, 'Time': Time, 'FXP': FXP, 'FXN': FXN, 'FYP': FYP, 'FYN': FYN, 'AXP': AXP,
                      'AXN': AXN, 'pf': row_to_update.pf}]
            return render_template('EditedData.html', data=datas)
        else:
            return render_template('EditDatabase.html', form=form,
                                   message="Test Number not found. Use Add Value to create a new entry.")

    return render_template('EditDatabase.html', form=form)
@app.route("/AddVal", methods=['GET', 'POST'])
@login_required
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

        XA = array.array('d', [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        YA = array.array('d', [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        ZA = array.array('d', [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

        XA[1] = FXP  # Positive X-axis
        XA[2] = FXN  # Negative X-axis
        YA[3] = FYP  # Positive Y-axis
        YA[4] = FYN  # Negative Y-axis
        ZA[5] = AXP  # Positive Z-axis
        ZA[6] = AXN  # Negative Z-axis

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
        TV=ValueTest(XA, YA, ZA)
        if TV==6:
            #data sends data to be displayed on the Passed.html page
            data = [{'SN': SerialNum, 'Time': Time, 'FXP': FXP, 'FXN': FXN, 'FYP': FYP, 'FYN': FYN, 'AXP': AXP, 'AXN': AXN,'pf':"Pass"}]

            #datas holds values that are then sent and stored in the database
            datas = SenData(TestN=TestNum, id=SerialNum, TimeS=Time, FXP=FXP, FXN=FXN,FYP=FYP,FYN=FYN,AXP=AXP,AXN=AXN,pf="Pass")
            db.session.add(datas)
            db.session.commit()

            # Create a TestLog entry to link the user to the test
            test_log = TestLog(
                user_id=current_user.id,
                test_n=TestNum,
                timestamp=Time
            )
            db.session.add(test_log)
            db.session.commit()

            return render_template('Passed.html',data=data)
    
        else:
            #data sends data to be displayed on the Fail.html page.
            data = [{'SN': SerialNum, 'Time': Time, 'FXP': FXP, 'FXN': FXN, 'FYP': FYP, 'FYN': FYN, 'AXP': AXP, 'AXN': AXN,'pf':"Fail"}]

            #datas holds values that are then sent and stored in the database.
            datas = SenData(TestN=TestNum, id=SerialNum, TimeS=Time, FXP=FXP, FXN=FXN,FYP=FYP,FYN=FYN,AXP=AXP,AXN=AXN,pf="Fail")
            db.session.add(datas)
            db.session.commit()

            # Create a TestLog entry to link the user to the test
            test_log = TestLog(
                user_id=current_user.id,
                test_n=TestNum,
                timestamp=Time
            )
            db.session.add(test_log)
            db.session.commit()

            return render_template('Fail.html',data=data)
        
    return render_template('EditDatabase.html', form=form)


@app.route("/DoTest")
@login_required
def DoTest():

    return render_template('Testing.html',)


@app.route("/Testing", methods=['GET','POST'])
@login_required
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

        # Create a TestLog entry to link the user to the test
        test_log = TestLog(
            user_id=current_user.id,
            test_n=TestNum,
            timestamp=Time
        )
        db.session.add(test_log)
        db.session.commit()

        return render_template('Passed.html',data=data)
    else:
        #data sends data to be displayed on the Fail.html page.
        data = [{'SN': SN, 'Time': Time, 'FXP': FXP, 'FXN': FXN, 'FYP': FYP, 'FYN': FYN, 'AXP': AXP, 'AXN': AXN,'pf':"Fail"}]

        #datas holds values that are then sent and stored in the database.
        datas = SenData(TestN=TestNum, id=SN, TimeS=Time, FXP=FXP, FXN=FXN,FYP=FYP,FYN=FYN,AXP=AXP,AXN=AXN,pf="Fail")
        db.session.add(datas)
        db.session.commit()

        # Create a TestLog entry to link the user to the test
        test_log = TestLog(
            user_id=current_user.id,
            test_n=TestNum,
            timestamp=Time
        )
        db.session.add(test_log)
        db.session.commit()

        return render_template('Fail.html',data=data)


if __name__ == "__main__":
    #Uncomment webview and comment out app.run to launch program in seperate window.
    app.run(debug=True, port = 8000)
    #webview.start()
