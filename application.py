#!usr/bin/python
from __future__ import print_function
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

import os
from os import environ
import yaml
import sys
import requests
import json
from flask import Flask, render_template, request
import logging

environment = 'Development'

application = Flask(__name__, template_folder='templates')

@application.route('/')
def home():
    return render_template('home.html')

@application.route('/create-account', methods=['POST'])
def create_account():
    json_data = json.loads(request.data)
    first_name = json_data['properties']['firstname']['value']
    last_name = json_data['properties']['lastname']['value']
    student_name = first_name + " " + last_name
    student_email = json_data['properties']['email']['value']
    
    _headers = environ.get('canvas_secret')
    if _headers:
        post_request = create_canvas_login(student_name, student_email,
                                           _headers)
        
        user_data = json.loads(post_request.text)
        print(user_data, "Canvas Account Created")
        #enroll_post_request = enroll_canvas_student(create_post_request)
        return "Canvas Account Created"
    else:
        return "Could not find token"
#Opens the YAML file at the specified directory and returns the YAML object.

def get_config(_dir):
    if os.path.exists(_dir):
        with open(_dir, 'r') as config_file:
            try:
                print('Token file accessed and read')
                file_content = yaml.load(config_file)
            except IOError as error:
                raise error
                sys.exit()
            except EOFError as error:
                raise error
                sys.exit()
    else:
        print('Could not find config file')
        sys.exit()
    return file_content

def google_request(spreadsheet_ID, range_name, scope):
    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', scope)
        creds = tools.run_flow(flow, store)
    service = build('sheets', 'v4', http=creds.authorize(Http()))

    result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_ID,
                                                range=range_name).execute()
    sheet_data = result.get('values', [])
    
    #Check if the sheet_data is empty
    if not sheet_data:
        print("No values found in spreadsheet, Exiting")
        sys.exit()
    else:
        return sheet_data

def canvas_request(canvas_bearer_token, course_ID, request_parameters=''):
    '''
    Docstring
    '''
    headers = {'Authorization' : 'Bearer {0}'.format(canvas_bearer_token)}
    url = 'https://coderacademy.instructure.com/api/v1/courses/{0}/users?{1}'.format(course_ID,
                                                                              request_parameters)
    response = requests.get(url, headers=headers)
    if not response:
        print("No data found at endpoint: {0}".format(url))
        sys.exit()
    else:
        #Load the request data into a JSON object
        canvas_data = json.loads(response.text)
        return canvas_data
def filter_students_from_sheets():
    #Create an array of dictionaries from google sheet values
    students = []
    for each in sheet_data:
        students.append({"name": each[0], "email": each[1]})
    
    names = []
    for each in students:
        names.append(each['name'].lower())
    
    students_missing = list(filter(lambda x: x['name'].lower() not in names,
                                 canvas_data)) 
    students_found = list(filter(lambda x: x['name'].lower() in names,
                                 canvas_data))

    #Statistics
    number_of_canvas_users = len(canvas_data)
    number_of_students_in_spreadsheet = len(sheet_data)
    number_of_students_matched = len(students_found)
    number_of_remaining_students = len(sheet_data) - len(students_found)
    number_of_canvas_staff = number_of_canvas_users - (
                                    number_of_students_matched + 
                                    number_of_remaining_students)

    print('{0} users extracted from Canvas'.format(number_of_canvas_users))
    print('{0} students extracted from the spreadsheet'.format(
                                number_of_students_in_spreadsheet))
    
    print("{0} students matched in spreadsheet".format(number_of_students_matched))
    print("{0} students are not matched".format(number_of_remaining_students))
    print("{0} staff or imposters in canvas".format(number_of_canvas_staff))
    #Returns all students in section 145(STAFF)
    print(get_students_in_section(canvas_bearer_token, course_ID, 149))

def main():
    #Loads the config file
    if environment == 'Development':
        config = get_config('./config.yaml')

        #Canvas config variables
        try:
            request_parameters = config['canvas']['request_parameters']
            course_ID = config['canvas']['course_ID']
            canvas_bearer_token = config['canvas']['bearer_token']
        except KeyError as error:
            print('Could not find config key specified')
            raise error

        #Google sheets config variables
        try:
            spreadsheet_ID = config['google_sheets']['spreadsheet_ID']
            range_name = config['google_sheets']['sheet_range']
            scope = config['google_sheets']['scope']
        except KeyError as error:
            print('could not find config key specified')
            raise error
    elif environment == 'Production':
        #Retrieve config variables from Heroku
        application.debug = True
        port = int(os.environ.get('PORT', 5000))
        logging.basicConfig(filename='error.log',level=logging.DEBUG)
        application.run(host='0.0.0.0', port=port)
        pass

    sheet_data = google_request(spreadsheet_ID, range_name, scope)
    canvas_data = canvas_request(canvas_bearer_token, course_ID,
                                 request_parameters)
    print(sheet_data, "End of sheet data")
    print(canvas_data, "End of canvas data")
    #Call update_canvas_email for all elements in students
    '''
    final = list(map(lambda x, y: update_canvas_email(x['id'], y['email'],
                                                      headers), students_found,
                                                         students))
    '''
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
    parameters = {'user[email]':email}
    url = 'https://coderacademy.instructure.com/api/v1/users/{0}.json'.format(student_ID)
    update_request = requests.post(url, headers = _headers, data = parameters)
    '''
    if(update_request.status == 200):
        print("Successfully updated canvas email")
    else:
        print("There was an error updating a canvas email", '\n')
        print("Student with ID: {0} failed to update with error code: {1}".format(student_ID, update.request.status))
    '''
if __name__ == "__main__":
    main()
    
    #If running locally, call main. ETC.
