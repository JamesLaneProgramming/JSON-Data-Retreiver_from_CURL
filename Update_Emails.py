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
import yaml
import sys
import requests
import json

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

def main():
    #Loads the config file
    config = get_config('./config.yaml')

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

    #Canvas data request
    headers = {'Authorization' : 'Bearer {0}'.format(canvas_bearer_token)}
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
    print("{0} students extracted from spreadsheet".format(len(sheet_data)))
    students_found = list(filter(lambda x: x['name'].lower() not in names,
                                 canvas_data))
    #final = list(map(lambda x, y: update_canvas_email(x['id'], y['email'],
    #                                                  headers), students_found, students)
    print("{0} students after filter".format(len(students_found)))
    print(students_found)

def update_canvas_email(student_ID, email, _headers):
    parameters = {'user[email]':email}
    url = 'https://coderacademy.instructure.com/api/v1/users/{0}.json'.format(student_ID)
    update_request = requests.put(url, headers = _headers, data = parameters)
    if(update_request.status == 200):
        print("Successfully updated canvas email")
    else:
        print("There was an error updating a canvas email", '\n')
        print("Student with ID: {0} failed to update with error code: {1}".format(student_ID, update.request.status))

if __name__ == "__main__":
    main()
