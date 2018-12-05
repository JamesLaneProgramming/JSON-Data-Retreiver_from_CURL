#!usr/bin/python
from __future__ import print_function
#Google OATH imports
try:
    pass
    #from googleapiclient.discovery import build
    #from httplib2 import Http
    #from oauth2client import file, client, tools
except Exception as error:
    print('Please run the following command to install Google API modules:',
          '\n')
    print('pip3 install --upgrade google-api-python-client oauth2client')
    raise error
#End Google module imports

import os
from os import environ
import yaml
import sys
from functools import reduce
import requests
import json
from flask import Flask, flash, render_template, request, abort, redirect, url_for
from flask_login import LoginManager, login_user, login_required, current_user
import argparse
import logging
from user_module import User
import pymongo
from pymongo import MongoClient

environment = None
#Set the default folder for templates
application = Flask(__name__, template_folder='templates')
application.secret_key = 'super secret key'
application.config['SESSION_TYPE'] = 'filesystem'
#Set config for MongoDB
application.config['MONGO_DBNAME'] = 'canvas_integration'
application.config['MONGO_URI'] = 'mongodb://localhost:27017/canvas_integration'
#Configure flask-login
login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'login'
login_manager.init_app(application)

'''
Notes:
    https://blog.teamtreehouse.com/how-to-create-bulletproof-sessions
    What parts of the website need access to the cookie?
    Will the cookie need to work across sub domains?
    Will the cookie need to persist if the user leaves an SSL portion of the site?
'''
#user_loader callback used to load a user from a session ID.
@login_manager.user_loader
def load_user(user_id):
    user = User.get(user_id)
    return user

#Handle command line arguments
parser = argparse.ArgumentParser(description='Command line arguments')
parser.add_argument('-env', 
                    '--environment',
                    help='Sets the environment for the program.')
args = parser.parse_args()

def main():
    parse_arguments()
    if environment == 'DEVELOPMENT':
        application.logger.info("Starting development build")
        config = get_config('./config.yaml')
        try:
            try:
                request_parameters = config['canvas']['request_parameters']
            except Exception as error:
                application.logger.info("No additional request parameters were found")
            course_ID = config['canvas']['course_id']
            canvas_bearer_token = config['canvas']['bearer_token']
        except KeyError as error:
            print('Could not find Canvas config keys specified')
            raise error
        try:
            spreadsheet_ID = config['google_sheets']['spreadsheet_ID']
            range_name = config['google_sheets']['sheet_range']
            scope = config['google_sheets']['scope']
        except KeyError as error:
            print('Could not find Google config keys specified')
        
        application.debug = True
        port = int(os.environ.get('PORT', 5000))
        application.run(host='0.0.0.0', port=port)
    elif environment == 'PRODUCTION':
        application.logger.info('Starting production server')
        #Retrieve config variables from Host environment
        #config_variable = environ.get('')
        application.debug = True
        port = int(os.environ.get('PORT', 5000))
        application.run(host='0.0.0.0', port=port)
    else:
        print('Environment parsed but does not match')
        print('Posible environments are: development/production/testing')

    #sheet_data = google_request(spreadsheet_ID, range_name, scope)
    #canvas_data = canvas_request(canvas_bearer_token, course_ID,
    #                             request_parameters)
    #update_canvas_emails(sheet_data, canvas_data, canvas_bearer_token)

@application.route('/')
def home():
    return render_template('home.html')

@application.route('/login', methods=['GET','POST'])
def login():
    if(request.method == 'POST'):
        user = User()
        user.authenticate(request.form['username'], request.form['password'])
        if(user != None and user.is_authenticated):
            login_status = login_user(user, remember=True)
            flash('Logged in successfully.')
            next = request.args.get('next')
            # is_safe_url should check if the url is safe for redirects.
            # See http://flask.pocoo.org/snippets/62/ for an example.
            return redirect(next)
            #return redirect(request.headers['Referer'])
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

@application.route('/student_search')
def student_search():
    canvas_API_request('https://coderacademy.instructure.com/api/v1/accounts/1/users', request_parameters={'search_term': 'james.lane@coderacademy.edu.au'})
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

def parse_arguments():
    '''
    Docstring
    ---------
    Stores command line arguments in global variables for easy access
    '''
    global environment
    if(args.environment != None):
        environment = args.environment.upper()
    else:
        application.logger.info("environment could not be parsed, exiting.")
        application.logger.info("Use python3 application.py -env <Environment>")
        sys.exit(0)

#Opens the YAML file at the specified directory and returns the YAML object.
def get_config(_dir):
    '''
    Arguments
    ---------
    _dir(String):
        Takes a directory string and checks whether a file exists in the current file
        structure
    Returns
    -------
    file_content:
        Reads the file specified by the _dir string and returns the contents
        using yaml.load(). Alternatively you could use yaml.safe_load().
    '''
    if os.path.exists(_dir):
        with open(_dir, 'r') as config_file:
            try:
                print('Token file accessed and read')
                file_content = yaml.load(config_file)
            except IOError as error:
                raise error
                sys.exit(0)
            except EOFError as error:
                raise error
                sys.exit(0)
    else:
        print('Could not find config file')
        sys.exit(0)
    return file_content

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

def canvas_API_request(canvas_URI, request_parameters=None):
    '''
    Docstring
    https://coderacademy.instructure.com/api/v1/courses/{0}/users?{1}
    '''
    #Attempt to load canvas_secret from environment
    try:
        canvas_bearer_token = environ.get('canvas_secret')
    except KeyError as error:
        '''
        If canvas_secret token cannot be loaded from the server, return a 500
        internal server error
        '''
        return abort(500)

    #Setup request headers with auth token.
    _headers = {'Authorization' : 'Bearer {0}'.format(canvas_bearer_token)}
    
    #Append optional parameters to the URI string.
    if(request_parameters != None):
        query_string = None
        for each_key, each_value in request_parameters.items():
            if query_string is None:
                query_string = '?{0}={1}'.format(each_key, each_value)
            else:
                query_string = '{0}&{1}={2}'.format(query_string, each_key, each_value)
        canvas_URI = canvas_URI + query_string
    #Request resource
    response = requests.get(canvas_URI, headers=_headers)
    if response.status_code == 200:
        print("Request successful")
        #Load the request data into a JSON object
        try:
            resource_data = json.loads(response.text)
            print(resource_data)
            return resource_data
        except ValueError as error:
            #Return Unprocessable Entity response if JSON is invalid
            return abort(422)
    elif response.status_code == 401:
        return "Authorisation error, please check canvas_secret environment variable"
    else:
        return response

def canvas_API_post_request(canvas_URI, request_parameters=''):
    pass

def update_canvas_emails(sheet_data, canvas_data, _headers):
    #Lambda to get student name from canvas for matching
    canvas_name_lambda = lambda x: x['name']
    #Lambda to get student ID from canvas to update email with
    canvas_ID_lambda = lambda x: x['id']
    #Lambda to get student name from sheets for matching
    sheet_name_lambda = lambda y: y[0]
    #Lambda to get student email from sheets to update canvas with
    sheet_email_lambda = lambda z: z[2]

    #Update emails based on canvas_data['id'] and sheet_data['email']
    for each_sheet_student in sheet_data:
        for each_canvas_student in canvas_data:
            #Use variables to compare
            student_sheet_name = sheet_name_lambda(each_sheet_student)
            student_canvas_name = canvas_name_lambda(each_canvas_student)
            
            #Use variables to update
            student_sheet_email = sheet_email_lambda(each_sheet_student)
            student_canvas_ID = canvas_ID_lambda(each_canvas_student)
            
            if student_canvas_name == student_sheet_name:
                update_canvas_email(
                                    student_canvas_ID,
                                    student_sheet_email,
                                    _headers
                                   )


def enroll_canvas_student(course_ID, student_ID, section_ID):
    #Retrieve canvas bearer token from environment variables.
    canvas_bearer_token = environ.get('canvas_secret')
    #Setup request headers with auth token.
    _headers = {'Authorization' : 'Bearer {0}'.format(canvas_bearer_token)}
    
    if section_ID:
        parameters = {'enrollment[user_id]': str(student_ID), 'enrollment[course_section_id]': int(section_ID)}
        url = 'https://coderacademy.instructure.com/api/v1/courses/{0}/enrollments'.format(course_ID)
        post_request = requests.post(url, headers = _headers, data = parameters)
        return post_request
    else:
        return "No section_ID provided"

def create_canvas_login(student_name, student_email):
    #Attempt to load canvas_secret from environment
    try:
        canvas_bearer_token = environ.get('canvas_secret')
    except KeyError as error:
        '''
        If canvas_secret token cannot be loaded from the server, return a 500
        internal server error
        '''
        return abort(500)

    #Setup request headers with auth token.
    _headers = {'Authorization' : 'Bearer {0}'.format(canvas_bearer_token)}

    parameters = {'user[name]':student_name, 'pseudonym[unique_id]':student_email}
    url = 'https://coderacademy.instructure.com/api/v1/accounts/1/users'
    post_request = requests.post(url, headers = _headers, data = parameters)
    return post_request

def update_canvas_email(student_ID, email, _headers):
    _headers = {'Authorization' : 'Bearer {0}'.format(_headers)}
    parameters = {'user[email]':email}
    url = 'https://coderacademy.instructure.com/api/v1/users/{0}.json'.format(student_ID)
    update_request = requests.put(url, headers = _headers, data = parameters)

    #Condition if request successful
    if(update_request.status_code == 200):
        print("Successfully updated canvas email")
    elif(update_request.status_code == 422):
        print("Error: ", update_request.status_code)
    else:
        print("There was an error updating a canvas email", '\n')
        print("Student with ID: {0} failed to update with error code: {1}".format(
                                                                                  student_ID, 
                                                                                  update_request.status_code
                                                                                 ))
if __name__ == "__main__":
    main()
