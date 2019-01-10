from __future__ import print_function
'''
#Google OATH imports
try:
    from googleapiclient.discovery import build
    from httplib2 import Http
    from oauth2client import file, client, tools
except Exception as error:
    print('Please run the following command to install Google API modules:',
          '\n')
    print('pip3 install --upgrade google-api-python-client oauth2client')
    raise error
#End Google module imports
'''
#TODO: Setup workflow for OAuth2 refresh tokens

import os, sys
from os import environ
import sys
import requests
import json
from flask import Flask, flash, render_template, request, abort, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mongoengine import MongoEngine
#Should not import canvas_API_request function. Instead create an endpoint for specific action.
from canvas_module import update_canvas_email, create_canvas_login
from canvas_module import enroll_canvas_student, extract_rubric_data, search_students
from users.user_model import User
from assessments.assessment_model import Assessment
from learning_outcomes.learning_outcome_model import Learning_Outcome

#Set the default folder for templates
application = Flask(__name__, template_folder='templates')

#Set application secret key to secure against CSRF
application.secret_key = 'super secret key'
application.config['SESSION_TYPE'] = 'filesystem'

#Configure mongodb server connection
application.config['MONGODB_SETTINGS'] = {
    'db': 'canvas_integration',
    'host': 'ds125684.mlab.com:25684',
    'username': 'James',
    'password': environ.get('mongoDB_Password'),
    'authentication_source': 'canvas_integration'
}

#Initialise the mongo engine.
#TODO: Add testing when MongoEngine cannot be initialised. For example when MongoDB_Password cannot be retreived from environment
db = MongoEngine(application)
#AssertTrue(db.connection, pymongo.MongoClient)
#AssertRaises(InvalidSettingsError, MongoEngine, db)

#Configure flask-login
login_manager = LoginManager()
login_manager.session_protection = 'strong'

#Redirect to login view when a user has yet to authenticate.
login_manager.login_view = 'login'
login_manager.init_app(application)

'''
Notes:
    https://blog.teamtreehouse.com/how-to-create-bulletproof-sessions
    What parts of the website need access to the cookie?
    Will the cookie need to work across sub domains?
    Will the cookie need to persist if the user leaves an SSL portion of the site?
    TODO: See development task: https://trello.com/c/qZfDhqaE/9-create-a-session-collection-in-the-database-track-views-actions-etc-when-a-user-authenticates-add-those-values-to-the-user-docum
'''
#user_loader callback used to load a user from a session ID.
@login_manager.user_loader
def load_user(user_id):
    return User.objects(pk=user_id).first()

def main():
    print('Starting production server')
    #Set application.debug to False if running a production server.
    application.debug = True
    port = int(os.environ.get('PORT', 5000))
    application.run(host='0.0.0.0', port=port)

@application.route('/')
def home():
    return render_template('home.html')

@application.route('/signup', methods=['GET', 'POST'])
def signup():
    if(request.method == 'POST'):
        username = request.form['username']
        password = request.form['password']
        assert username is not None
        assert password is not None
        User.create(username, password)
        return redirect('/')
    else:
        return render_template('signup.html')

@application.route('/login', methods=['GET','POST'])
def login():
    if(request.method == 'POST'):
        username = request.form['username']
        password = request.form['password']
        assert username is not None
        assert password is not None
        user = User.authenticate(username, password)
        if(user != None and user.is_authenticated):
            login_status = login_user(user)
            flash('Logged in successfully.')
            #TODO: Issue redirecting to /None after successful login
            next = request.args.get('next')
            # is_safe_url should check if the url is safe for redirects.
            # See http://flask.pocoo.org/snippets/62/ for an example.
            return redirect(next)
        else:
            return redirect('login', code=302)
    else:
        return render_template('login.html')

@application.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

@application.route('/rubric_data')
@login_required
def rubric_data():
    course_ID = 144
    assessment_ID = 667
    request = extract_rubric_data(course_ID, assessment_ID)
    #Perform analysis and remapping here:
    map_rubric_data(request.json())
    return request.text

def map_rubric_data(submission_data):
    for each_submission_item in submission_data:
        try:
            submission_ID = each_submission_item['id']
            submission_assignment_ID = each_submission_item['assignment_id']
        except Exception as error:
            raise error
        try:
            submission_rubric_assessment = each_submission_item['rubric_assessment'] 
        except Exception as error:
            pass
        #Return each criterion ID, points and comments.
        #Need to create a view for criterion ID to learning outcome objective.
        #TODO: What are the falsy values for python, print them out.
        #TODO: Store learning outcomes in database.
        assessment_mapping_hash = {

                                  }
        if(submission_rubric_assessment):
            submission = submission_object(submission_ID, submission_assignment_ID,
                                          submission_rubric_assessment)
            submission_grades = []
            for each in submission.criteria:
                learning_outcome = Learning_Outcome(each)
                learning_outcome.set_grade(each['points'])
                learning_outcome.save()
                submission_grades.append(learning_outcome)
            Assessment.create(each_submission_item['user_id'], grades)

class submission_object():
    def __init__(self, submission_ID, submission_assessment_ID,
                 submission_rubric_assessment):
        self.criteria = []
        self.id = submission_ID
        self.assessment_ID = submission_assessment_ID
        for key, value in submission_rubric_assessment.items():
            points = None
            comments = None
            try:
                points = value['points']
                comments = value['comments']
            except KeyError as error:
                pass
            except Exception as error:
                raise error
            if(points != None):
                criterion_object = criterion(key, points, comments)
                self.criteria.append(criterion_object)

class criterion():
    def __init__(self, id, points, comments):
        self.id = id
        self.points = points
        self.comments = comments

@application.route('/students', methods=['GET', 'POST'])
@login_required
def student_search():
    if(request.method == 'POST'):
        try:
            search_term = request.form['search_term']
            search_results = search_students(search_term)
            #TODO: Replace this with request.json() for encoding purposes
            return search_results.text
        except Exception as error:
            raise error
    else:
        #TODO: Create the student search template
        return render_template('student_search.html')

@application.route('/create-account', methods=['POST'])
def create_canvas_account():
    '''
    Docstring
    ---------
    create_account() should only be run in a production environment
    Arguments
    ---------
    student_data(JSON Object):
        Takes a JSON Object that contains firstname, lastname and email
    Returns
    -------
    Account_Creation_Successful(template):
        Returns a template to be rendered by Flask on successful request.
    Note: A course ID will be sent from the webhook as a query paramter. Is this safe?
    '''  
    #Extract the required data from the URL string.
    try:
        course_ID = int(request.args.get('course_id'))
        section_ID = int(request.args.get('section_id'))
    except Exception as error:
        raise error
    
    #Validate POST payload
    if not request.json:
        #If the request has invalid json return 415 status code.
        return abort(415)
    else:
        json_data = request.get_json()
        try:
            first_name = json_data['properties']['firstname']['value']
            last_name = json_data['properties']['lastname']['value'] 
            student_email = json_data['properties']['email']['value']
        except KeyError as error:
            print("Could not extract json fields")
            return abort(415)
        except Exception as error:
            print(error)
    #Concatenate student_name from json data.
    student_name = first_name + " " + last_name
    #TODO YOU NEED TO CHECK IF THE USER ALREADY EXISTS
    creation_response = create_canvas_login(student_name, student_email)
    if(creation_response.status_code == 400):
        print("The user already exists")
        return "User already exists, user not enrolled"
        #Use Student_Search endpoint to retrieve existing student.

    elif(creation_response.status_code == 200):
        try:
            student_details = json.loads(creation_response.text)
            try:
                student_ID = int(student_details['id'])
            except TypeError as error:
                print("Webhook is most likely sending array of student data.")
            except Exception as error:
                raise error
            enrollment_response = enroll_canvas_student(student_ID, course_ID, section_ID)
            print(enrollment_response.text)
        except Exception as error:
            raise error
        #TODO You will need to query the canvas Users endpoint with the search_term query parameter to find the user and return ID.
        #This ID will be used to enroll the student in selected course.
        return str(enrollment_response.status_code)
    '''
    user_data = post_request.get_json()
    #enroll_post_request = enroll_canvas_student(create_post_request)
    if (post_request.status_code == 201):
        application.logger.info(post_request)
        return render_template('Canvas_Account_Creation_Successful.html'), 201
    else:
        application.logger.info(post_request)
        return "Canvas account could not be created at this time...\
                Please try again later or contact us for more information"
    '''

#Opens the YAML file at the specified directory and returns the scriptable YAML object.
def get_config(_dir):
    '''
    Arguments
    ---------
    _dir(String):
        Takes a directory method argument used to load configuration.
    Returns
    -------
    file_content:
        Reads the file specified by the _dir string and returns the contents
        using yaml.load(). Alternatively you could use yaml.safe_load().
    '''
    
    file_content = None

    #Checks whether the _dir method argument is a string. isinstance() supports DataTypes that inherit the String base class.
    assert isinstance(_dir, str)
    
    #Check if the directory method argument exists in the current filesystem.
    if os.path.exists(_dir):
        with open(_dir, 'r') as config_file:
            try:
                print('config accessed and read')
                #Load the configuration into a scriptable object.
                file_content = yaml.load(config_file)
            except IOError as error:
                raise error
                sys.exit(0)
            except EOFError as error:
                raise error
                sys.exit(0)
            except ImportError as error:
                print("YAML module could not be imported, please ensure that YAML module has been installed and is in the requirements.txt file")
            except Exception as error:
                raise error
            if(file_content != None):
                return file_content
            else:
                print("Could not load configuration from file but no errors were thrown")
    else:
        print('_dir method argument is not a valid directory in the current filesystem')

def google_request(spreadsheet_ID, range_name, scope):
    '''
    Arguments
    ---------
    spreadsheet_ID(String):
        Takes a string agrument that represents the google spreadsheet
        identifier.
    range_name(String):
        Take a string argument that represents the google sheet ranges to
        retreive data from. Format for the string is as follows:
            '<sheet_name>!<start_range>:<end_range>'
    scope(Google)
    '''
    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', scope)
        creds = tools.run_flow(flow, store)
    service = build('sheets', 'v4', http=creds.authorize(Http()))

    result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_ID,
                                                range=range_name).execute()
    sheet_data = result.get('values', [])
    
    if not sheet_data:
        sys.exit()
    else:
        return sheet_data

if __name__ == "__main__":
    main()
