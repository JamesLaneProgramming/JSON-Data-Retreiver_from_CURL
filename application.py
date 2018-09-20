import os
from os import environ
import yaml
import sys
from functools import reduce
import requests
import json
import flask
from flask import render_template
import argparse
import logging
import flask_login
from User import User
import database as db
try:
    import google_sheets_module as gsm
except Exception as e:
    raise e

environment = None

#Initialises the Flask application
application = flask.Flask(__name__, template_folder='templates')
login_manager = flask_login.LoginManager()
login_manager.init_app(application)

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@application.route('/')
def home():
    return render_template('home.html')

@application.route('/login', methods=['GET','POST'])
def login():
    if(flask.request.method == 'GET'):
        return render_template('login.html')
    else:
        print(flask.request.values)
        current_user = User.get_user(flask.request.form.get('user'),
                                     flask.request.form.get('pass'))
        #If current_user us None, "could not find user"; register?
        flask_login.login_user(current_user)
@application.route('/logout')
def logout():
    flask_login.logout_user()
    return redirect('/')
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
    '''

    #NOT SAFE AT ALL, WHY DID WE DO THIS. REQUIRE LOGIN TO USE THIS ENDPOINT.
    #Attempts to lead canvas_secret from environment
    try:
        _headers = environ.get('canvas_secret')
    except KeyError as error:
        '''
        If canvas_secret token cannot be loaded from the server, return a 500
        internal server error
        '''
        abort(500)
    #Attempts to load json data from student_data
    
    if not request.json:
        abort(415)
    else:
        json_data = request.get_json()
        try:
            first_name = json_data['properties']['firstname']['value']
            last_name = json_data['properties']['lastname']['value'] 
            student_email = json_data['properties']['email']['value']
        except KeyError as error:
            abort(415)
    student_name = first_name + " " + last_name
    post_request = create_canvas_login(student_name, student_email,
                                           _headers)
    user_data = post_request.get_json()
    #enroll_post_request = enroll_canvas_student(create_post_request)
    if (post_request.status_code == 201):
        application.logger.info(post_request)
        return render_template('Canvas_Account_Creation_Successful.html'), 201
    else:
        application.logger.info(post_request)
        return "Canvas account could not be created at this time...\
                Please try again later or contact us for more information"

def parse_arguments():
    '''
    Docstring
    ---------
    Stores command line arguments in global variables for easy access
    
    For development purposes run:
        <python3 application --environment development>
    For production purposes run:
        <python3 application --environment production>
    '''
    global environment
    #Initialises argparse to handle command line arguments
    parser = argparse.ArgumentParser(description='Handle command line arguments')
    parser.add_argument('-env', 
                        '--environment',
                        help='Sets the environment for the application.')
    args = parser.parse_args()

    if(args.environment != None):
        environment = args.environment.upper()
    else:
        application.logger.info("environment could not be parsed, exiting.")
        application.logger.info("Use python3 application.py -env <Environment>")
        sys.exit(0)
def main():
    #Handle the command line arguments
    parse_arguments()
    if environment == 'DEVELOPMENT':
        application.logger.info("Starting development build")
        #Retrieve the local config file.
        config = get_config('./config.yaml')
        try:
            request_parameters = config['canvas']['request_parameters']
            course_ID = config['canvas']['course_ID']
            canvas_bearer_token = config['canvas']['bearer_token']
        except KeyError as error:
            print('Could not find config key specified')
            raise error
        try:
            spreadsheet_ID = config['google_sheets']['spreadsheet_ID']
            range_name = config['google_sheets']['sheet_range']
            scope = config['google_sheets']['scope']
        except KeyError as error:
            print('could not find config key specified')
            raise error
        submission = retrieve_submission(109, 620, canvas_bearer_token).text
        extract_rubric_data(submission)
        
        '''
        #Ruby test
        print (retrieve_submission(109, 172, canvas_bearer_token).text)
        #Terminal App
        print (retrieve_submission(109, 579, canvas_bearer_token).text)
        #Portfolio
        print (retrieve_submission(109, 587, canvas_bearer_token).text)
        
        #Term 2
        #2SMP
        print (retrieve_submission(109, 620, canvas_bearer_token).text)
        #Discrete Maths
        print (retrieve_submission(109, 188, canvas_bearer_token).text)
        
        #Term 3
        print (retrieve_submission(109, 633, canvas_bearer_token).text)
        '''
        application.logger.info('Starting development server')
        #Retrieve config variables from Heroku
        #config_variable = environ.get('')
        application.debug = True
        port = int(os.environ.get('PORT', 5000))
        application.run(host='0.0.0.0', port=port)
    elif environment == 'PRODUCTION':
        application.logger.info('Starting production server')
        #Retrieve config variables from Heroku
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

def canvas_request(canvas_bearer_token, course_ID, request_parameters=''):
    '''
    Docstring
    '''
    headers = {'Authorization' : 'Bearer {0}'.format(canvas_bearer_token)}
    url = 'https://coderacademy.instructure.com/api/v1/courses/{0}/users?{1}'.format(course_ID,
                                                                              request_parameters)
    response = requests.get(url, headers=headers)
    if not response:
        print(response)
        print("No data found at endpoint: {0}".format(url))
        sys.exit()
    else:
        #Load the request data into a JSON object
        canvas_data = json.loads(response.text)
        return canvas_data

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


def enroll_canvas_student(student_ID, course_ID, _headers):
    _headers = {'Authorization' : 'Bearer {0}'.format(_headers)}
    parameters = {'enrollment[user_id]': student_id}
    url = 'https://coderacademy.instructure.com/api/v1/courses/{0}/enrollments'.format(course_ID)
    post_request = requests.post(url, headers = _headers, data = parameters)
    return post_request

def create_canvas_login(student_name, student_email, _headers):
    _headers = {'Authorization' : 'Bearer {0}'.format(_headers)}
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
def retrieve_submission(course_ID, assessment_ID, _headers, student_IDs = 'all'):
    '''
    Docstring
    ---------
    Retrieves specified assessment submissions.
    
    Arguments
    ---------
    course_ID(String):
        course_ID specifies which course submissions will be retrieved from.
    assessment_ID(String):
        assessment_ID specifies which assessment submissions will be retrieved
        from.
    student_IDs(String):
        student_IDs specify from which students submissions will be retrieved.
        Default will return all students that match course_ID and assessment_ID
    _headers(JSON):
        _headers specifies request parameters.
    
    Returns
    -------
    request:
        Returns the request object.
    '''
    _headers = {'Authorization' : 'Bearer {0}'.format(_headers)}
    parameters = {'student_ids[]': '{0}'.format(student_IDs), 
                  'assignment_ids[]': '{0}'.format(assessment_ID),
                  'include[]': 'rubric_assessment'}
    #404: while(1);{"errors":[{"message":"The specified resource does not exist."}],"error_report_id":3556}
    #401: {"status":"unauthorised","errors":[{"message":"user not authorised to perform that action"}]}
    url = 'https://coderacademy.beta.instructure.com/api/v1/courses/{0}/students/submissions'.format(course_ID)
    request = requests.get(url, headers = _headers, data = parameters)
    return request

def extract_rubric_data(submission_object):
    json_data = json.loads(submission_object)
    for each in json_data:
        try:
            print(each['rubric_assessment'])
        except KeyError:
            print("Submission does not have a rubric_assessment")
if __name__ == "__main__":
    main()
