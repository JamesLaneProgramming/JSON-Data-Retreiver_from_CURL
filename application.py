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

application = Flask(__name__, template_folder='templates')

@application.route('/')
def home():
    return render_template('home.html')

@application.route('/create-account', methods=['POST'])
def create_account():
    json_data = json.loads(request.data)
    first_name = json_data['properties']['firstname']['value']
    last_name = json_data['properties']['lastname']['value']
    email_address = json_data['properties']['email']['value']
    print("Welcome: {0} {1}. Your email is: {2}".format(first_name,
                                                       last_name,
                                                       email_address))
    return request.data

@application.route('/some-token-requirement', methods=['GET'])
def get_some_token():
    #Need to research handling heroku tokens without error on local machine.
    #Environ.get() will return None instead of error. Use if statement instead
    #of Try/Catch.
    token = environ.get('token')
    if token:
        return token
    else:
        return "Token not found"
#If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'

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

def google_request():
    #Google credentials
    
    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('sheets', 'v4', http=creds.authorize(Http()))

    result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID,
                                                range=RANGE_NAME).execute()
    sheet_data = result.get('values', [])
    
    #Check if the sheet_data is empty
    if not sheet_data:
        print("No values found in spreadsheet, Exiting")
        sys.exit()
    else:
        return sheet_data

def canvas_request():
    #Canvas data request
    headers = {'Authorization' : 'Bearer {0}'.format(canvas_bearer_token)}
    #Need to check length of request_parameters, Iterate and concatenate for
    #each request_parameter.
    url = 'https://coderacademy.instructure.com/api/v1/courses/{0}/users?{1}'.format(course_ID,
                                                                              request_parameters)
    response = requests.get(url, headers=headers)
    #Load the request data into a JSON object
    canvas_data = json.loads(response.text)

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
    #config = get_config('./config.yaml')
    '''
    #Canvas config variables
    try:
        request_parameters = config['canvas']['request_parameters']
        course_ID = config['canvas']['course_id']
        canvas_bearer_token = config['canvas']['bearer_token']
    except KeyError as error:
        print('Could not find config key specified')
        raise error

    #Google sheets config variables
    try:
        SPREADSHEET_ID = config['google_sheets']['spreadsheet_ID']
        RANGE_NAME = config['google_sheets']['sheet_range']
    except KeyError as error:
        print('could not find config key specified')
        raise error
    
    '''
    #Call update_canvas_email for all elements in students
    '''
    final = list(map(lambda x, y: update_canvas_email(x['id'], y['email'],
                                                      headers), students_found,
                                                         students))
    '''
def update_canvas_email(student_ID, email, _headers):
    parameters = {'user[email]':email}
    url = 'https://coderacademy.instructure.com/api/v1/users/{0}.json'.format(student_ID)
    update_request = requests.put(url, headers = _headers, data = parameters)
    '''
    if(update_request.status == 200):
        print("Successfully updated canvas email")
    else:
        print("There was an error updating a canvas email", '\n')
        print("Student with ID: {0} failed to update with error code: {1}".format(student_ID, update.request.status))
    '''
if __name__ == "__main__":
    application.debug = True
    port = int(os.environ.get('PORT', 5000))
    logging.basicConfig(filename='error.log',level=logging.DEBUG)
    application.run(host='0.0.0.0', port=port)

    #If running locally, call main. ETC.
