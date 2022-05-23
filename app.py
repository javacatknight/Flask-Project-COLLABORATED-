"""READ ME:
CODE IS ORDERED AS FOLLOWS:

A) Imports, instantizing, configuration, global variables
B) Classes/Tables
C) Routing
    a) Home/Login/Register/Logout. Session variable 'usernamekey'
    b) Main Pages, Query Functions


COMMENT TYPES:
#! use ctrl+F for "#!" to find stuff that needs to be fixed
## use "##" for summary of some concepts
# comments in lowercase add further detail
# COMMENTS IN UPPERCASE serve as HEADLINES

Suggestion: "Better Comments - Aaron Bond" extension to view color-coded comments
"""

#A. IMPORTS,CONFIGURATION
from datetime import datetime
from flask import Flask, render_template, url_for, flash, redirect, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'  # secret key is used for encryption, design as needed.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

#! Suggested by TA to store values in a set instead of repeatedly fetching them from database; however, I suspect this is causing a bug.
# Globals: https://piazza.com/class/kxj5alixpjg4ft?cid=289
setStudents = set()
setInstructors = set()

# B. TABLES:
class Users(db.Model):
    __tablename__ = "Users"
    # unique username, nullable=False means no leaving it blank
    username = db.Column(db.String(20), primary_key=True)
    type = db.Column(db.Integer, nullable=False)  # 0 = Student, 1 = Instructor
    email = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(20), nullable=False)
    # NEXT PART A LITTLE CONFUSING, ASK CATHERINE TO EXPLAIN IF NEEDED
    # db.relationship forms not a real column but a fake sort of attribute so that I can now access Users.assignments to get the assignments related to this users
    # the backref is the reverse (bidirectional); if i have assignments, i can get assignments.student to get the User

    # if instructor, its empty/null #https://overiq.com/flask-101/database-modelling-in-flask/#defining-relationship
    assignments = db.relationship("Assignments", backref="student")
    #!later in the python, for student view. return render_template("s.html", assignments = Users.query(user).assignments)-> jinja circle through easily
    # ONLY ALLOW THEM TO SEE THEIR OWN FEEDBACK, use return later
    feedback = db.relationship("Feedback", backref="instructor")

    def __repr__(self):  # string representation if debugging aka use python to check correct implementation and stuff
        return f"Users('{self.username}')"


class Assignments(db.Model):
    __tablename__ = "Assignments"
    assignmentID = db.Column(db.Integer, primary_key=True)  # primary key id
    assignmentName = db.Column(db.String(30), nullable=False)
    username = db.Column(db.String(20), db.ForeignKey(
        'Users.username'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    # relationship
    remarkings = db.relationship("Remarks", backref="assignment") 

    def __repr__(self):
        return f"Assignments('{self.assignId}, {self.score}')"

class Feedback(db.Model):
  __tablename__ = "Feedback"
  feedbackID = db.Column(db.Integer, primary_key = True)
  instructorUsername = db.Column(db.String(20), db.ForeignKey('Users.username'), nullable = False)
  comment1 = db.Column(db.String(160), nullable = False)
  comment2 = db.Column(db.String(160), nullable = False)
  comment3 = db.Column(db.String(160), nullable = False)
  comment4 = db.Column(db.String(160), nullable = False)
  def __repr__(self):
      return f"Feedback('{self.feedbackID}')"

class Remarks(db.Model):
    __tablename__ = "Remarks"
    remarksID = db.Column(db.Integer, primary_key=True)
    assignmentID = db.Column(db.Integer, db.ForeignKey(
        'Assignments.assignmentID'), nullable=False)
    comment = db.Column(db.String(160), nullable=False)

    def __repr__(self):
        return f"Feedback('{self.remarksID}')"

# C. ROUTING:
# 1-5 ROUTING PAGES. OPTIONS: not logged in, logging in/out, logged in (all users), logged&type=0, logged&type=1

# 1 NOT LOGGED IN or if logged in, redirect to proper home page.


@app.route('/')
@app.route('/index')
def home():
    # Todo: entire function is different now to match the html
    # If not logged in, return the not logged in home page
    if not 'usernameKey' in session:
        pagename = 'index'
        return render_template('index.html', pagename=pagename)
    else:  # return the right routing
        if session['usernameKey'] in setInstructors:
            return redirect(url_for('instructor'))
        elif session['usernameKey'] in setStudents:
            return redirect(url_for('student'))

# 2 a,b,c: REGISTRATION OF USER, LOGIN OF USER, LOGOUT. Helper functions listed below.
# 2a) REGISTRATION OF USER


# HTTP: GET method just pulls the page, POST method means retrieving data from page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        if 'usernameKey' in session:  # usernameKey is just a variable name #Todo:newly added, check with silly
            flash('Already logged in! Log out to register a new account!')
            return redirect(url_for('home'))  # todo: corrected
        else:
            return render_template('register.html')
    else:
        # Fetch html form data with Flask.request and appropriate values of the matching name attribute,
        # Corresponds to the input tag <input name = "Username">
        username = request.form['Username']
        # Todo:newly added,

        # Check if username is in use.
        for user in Users.query.all():
          if username == user.username:
            flash('Username taken. Try again.')
            return redirect(url_for('register'))
        # else allow the registration to conitnue:
        # Todo:newly added /end
        email = request.form['Email']
        hashed_password = bcrypt.generate_password_hash(request.form['Password']).decode('utf-8')
        type = request.form['radio']
        reg_details = [
            username,
            type,
            email,
            hashed_password
        ]
        # add user to db
        add_user(reg_details)
        flash('Registration Successful! Please login now:')
        # url_for() dynamically built urls so you don't need to manually go around correcting them if you decide to change it once. #anyways it gets the url for the function login (and remember each function has a route/app.route() linked above it)
        return redirect(url_for('login'))


def add_user(reg_details):
    # add username to python instructor/student set, faster than query
    type = reg_details[1]
    if type == 'student':  # todo: changed to match register html
        setStudents.add(reg_details[1])
        reg_details[1]=0
    elif type == 'instructor':
        setInstructors.add(reg_details[1])
        reg_details[1]=1

    # add user to database
    user = Users(username=reg_details[0], type=reg_details[1],
                 email=reg_details[2], password=reg_details[3])
    db.session.add(user)
    db.session.commit()

# 2b) LOGIN

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        # same session, stay in
        if 'usernameKey' in session:  # usernameKey is just a variable name, see below:
            flash('Already logged in!!')
            return redirect(url_for('home'))
        else:
            return render_template('login.html')
    else:  # if post/entering a login:
        username = request.form['Username']
        password = request.form['Password']
        # return first result (as username is unique, it returns only one result anyways)
        user = Users.query.filter_by(username=username).first()
        # if either username is not found or password is not correct, flash
        if not user or not bcrypt.check_password_hash(user.password, password):
            flash('Your username or password is incorrect. Try again.')
            return render_template('login.html')
        else:  # Allow login
            session['usernameKey'] = username
            session.permanent = True
            return redirect(url_for('home'))

# 2c) LOGOUT
@app.route('/logout')
def logout():
    # remove username from session
    session.pop('usernameKey', None)
    return redirect(url_for('home'))

# 3 LOGGED IN, ALL:
# if not logged in, redirect to login
@app.route('/anonfeedback')
def anonfeedback():
    if 'usernameKey' in session:
        pagename = 'anonfeedback'
        return render_template('anonfeedback.html', pagename=pagename)
    else:
        return redirect(url_for('login'))


@app.route('/courseteam')
def courseteam():
    if 'usernameKey' in session:
        pagename = 'courseteam'
        return render_template('courseteam.html', pagename=pagename)
    else:
        return redirect(url_for('login'))


@app.route('/assignments')
def assignments():
    if 'usernameKey' in session:
        pagename = 'assignments'
        return render_template('assignments.html', pagename=pagename)
    else:
        return redirect(url_for('login'))


@app.route('/labs')
def labs():
    if 'usernameKey' in session:
        pagename = 'labs'
        return render_template('labs.html', pagename=pagename)
    else:
        return redirect(url_for('login'))


@app.route('/lecture')
def lecture():
    if 'usernameKey' in session:
        pagename = 'lecture'
        return render_template('lecture.html', pagename=pagename)
    else:
        return redirect(url_for('login'))

# 4: LOGGED IN AS STUDENT. FUNTIONS: a)View grades/add remarkrequest or b) feedback request
@app.route('/student') # !incomplete
def studentHome():
  return render_template('student.html')

@app.route('/gradesStudentView', methods=['GET, POST'])
def viewGradeStudent():
    if request.method == 'GET':
        if 'usernameKey' in session and session['usernameKey'] in setStudents:
            assignments = Assignments.query.filter_by(
                username=session['usernameKey'])
            return render_template('gradesStudentView.html', assignments=assignments)
        else:
            if 'usernameKey' in session:  # then it's instructor
                return redirect(url_for('instructor'))
            else:  # then not in session
                return redirect(url_for('login'))

    elif request.method == 'POST':
        # find the right submit button, the value of the button is the assignmentid
        whichSubmit = request.form['submitted']
        # find the input box by the assignment id
        comment = request.form[whichSubmit]
        assignmentID = whichSubmit
        #if null comment, do not add,
        if len(comment.trim()) == 0:
          return

        # add a remark request.
        newFeedback = Feedback(comment=comment, assignmentID=assignmentID)
        db.session.add(newFeedback)
        db.session.commit()

# FEEDBACK REQUEST, lins 282-314 is work by collaborator 
@app.route('/notes', methods = ['GET', 'POST'])
def notes():
    if request.method == 'GET':
        query_notes_result = query_notes()
        return render_template('notes.html', query_notes_result = query_notes_result)

@app.route('/add', methods = ['GET', 'POST'])
def add():
    if request.method == 'GET':
        return render_template('add.html')
    else:
        note_details =( #GETTING CONENT FROM FORM
            request.form['Note_ID'],
            request.form['Title'],
            request.form['Content1'],
            request.form['Content2'],
            request.form['Content3'],
            request.form['Content4']
        )
        add_notes(note_details)
        return redirect(url_for('notes'))


def add_notes(note_details):
    note = Feedback(feedbackID = note_details[0], instructorUsername = note_details[1], comment1 = note_details[2], comment2 = note_details[3], comment3 = note_details[4], comment4 = note_details[5])
    db.session.add(note)
    db.session.commit()

def query_notes():
    query_notes = Feedback.query.all()
    return query_notes
### END

# 5:LOGGED IN INSTRUCTOR
@app.route('/instructor') # !incomplete
def instructorHome():
  if 'usernameKey' in session and session['usernameKey'] in setInstructors:
    render_template('instructor.html')
# a) EDIT+ADD+VIEW REMARK REQUESTS + GRADES
@app.route('/gradesInstructorEdit', methods=['GET, POST'])
def gradeInstructorEdit():
    if request.method == 'GET':
        if 'usernameKey' in session and session['usernameKey'] in setInstructors:
            assignments = Assignments.query.all()
            return render_template('gradesInstructorEdit.html', assignments=assignments)
        else:
            if 'usernameKey' in session:  # then it's student
                return redirect(url_for('student'))
            else:  # then not in session
                return redirect(url_for('login'))
    elif request.method == 'POST':
      return
      #! incomplete
        # username = request.form['username']
        # assignmentName = request.form['assignmentName']
        # score = request.form['score']
        
        # #check if username valid. else return.
        # if not username in setStudents:
        #   return

        # #check if it exists already aka edit grade.
        # # listAssignments = Assignments.query.all()
        # # if ()
        # # if assignmentName in 
        # #   if username == user.username:

        # # newAssignment = Assignment(comment=comment, assignmentID=assignmentID)

        # db.session.add(newAssignment)
        # db.session.commit()


if __name__ == '__main__':
    app.run(debug=True)
