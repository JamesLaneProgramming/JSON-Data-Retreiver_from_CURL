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
import sys
import requests
import json
try:
    import emailgenerator as EG
except ImportError as error:
    print("Error importing module")
    raise error
except Exception as error:
    raise error
#If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'

#Opens the file at the specified directory and returns the first line.
#Useful for integrating a .config file.
def get_bearer_token(_dir):
    if os.path.exists(_dir):
        with open(_dir, 'r') as token_file:
            try:
                print('Token file accessed and read')
                file_content = token_file.read().splitlines()[0]
            except IOError as error:
                raise error
                sys.exit()
            except EOFError as error:
                raise error
                sys.exit()
    return file_content

def main():
    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('sheets', 'v4', http=creds.authorize(Http()))

    # Call the Sheets API
    SPREADSHEET_ID = '1FVjXzSXizzJNIFTuDRuuhVfNMq-qiKnbZq8aUuNUnaI'
    RANGE_NAME = 'emails!A2:B82'
    result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID,
                                                range=RANGE_NAME).execute()
    values = result.get('values', [])

    if not values:
        print("No values found in spreadsheet, Exiting")
        sys.exit()
    else:
        for row in values:
            # Print columns A and E, which correspond to indices 0 and 4.
            pass

    bearer_token = get_bearer_token('./token')
    headers = {'Authorization' : 'Bearer {0}'.format(bearer_token)}
    response = requests.get('https://coderacademy.instructure.com/api/v1/courses/144/users?per_page=100',
                headers=headers)

    json_data = json.loads(response.text)
    
    #Create an array of dictionaries from google sheet values
    students = []
    for each in values:
        students.append({"name": each[0], "email": each[1]})
    names = []
    for each in students:
        names.append(each['name'].lower())
    print("{0} students extracted from spreadsheet".format(len(values)))
    students_found = list(filter(lambda x: x['name'].lower() not in names, json_data))
    #final = list(map(lambda x, y: update_canvas_email(x['id'], y['email'],
    #                                                  headers), students_found, students)
    print("{0} students after filter".format(len(students_found)))
    print(students_found)

def update_canvas_email(student_ID, email, _headers):
    parameters = {'user[email]':email}
    url = 'https://coderacademy.instructure.com/api/v1/users/{0}.json'.format(student_ID)
    update_request = requests.put(url, headers = _headers, data = parameters)
    print(update_request)

if __name__ == "__main__":
    main()
