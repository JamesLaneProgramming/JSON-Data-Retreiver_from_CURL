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
import yaml
import sys
import requests
import json
from flask import Flask, flash, render_template, request, abort, redirect, url_for
from flask_login import LoginManager, login_user, login_required, current_user
import canvas_module
from . import users.user_model
import pymongo
from pymongo import MongoClient

#Set the default folder for templates
application = Flask(__name__, template_folder='templates')
application.secret_key = 'super secret key'
application.config['SESSION_TYPE'] = 'filesystem'

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
    user = User.get(user_id)
    return user

def main():
    #Retrieve config variables from Host environment
    #config_variable = environ.get('')
    
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
        new_user = User.create(username, password)
        return redirect('/')
    else:
        return render_template('signup.html')

@application.route('/login', methods=['GET','POST'])
def login():
    if(request.method == 'POST'):
        user = User()
        username = request.form['username']
        password = request.form['password']
        assert username is not None
        assert password is not None
        user.authenticate(username, password)
        if(user != None and user.is_authenticated):
            login_status = login_user(user, remember=True)
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

@application.route('/backup')
@login_required
def backup():
    '''
    Implement a text field and a sumbit button. Text field should contain a course ID.
    '''
    course_ID = 144
    backup_URI = 'https://coderacademy.instructure.com/api/v1/courses/{0}/users'.format(course_ID)
    request = canvas_API_request(backup_URI)
    return "Hello"

@application.route('/student_search', methods=['GET', 'POST'])
@login_required
def student_search():
    if(request.method == 'POST'):
        try:
            search_term = request.form['search_term']
            canvas_request = canvas_API_request('https://coderacademy.instructure.com/api/v1/accounts/1/users', 
                    request_parameters={'search_term': search_term})
            return canvas_request.text
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
    #Extract the course_ID from the URL string.
    try:
        course_ID = request.args.get('course_id')
        section_ID = request.args.get('section_id')
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

    elif(creation_response.status_code == 200):
        try:
            student_details = json.loads(creation_response.text)
            enrollment_response = enroll_canvas_student(course_ID, student_details['id'], section_ID)
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
