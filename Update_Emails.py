#!usr/bin/python
#Google OATH imports
from __future__ import print_function
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
#End Google OATH imports

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
# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'

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
    

    #Need to remove students that do not match the filter requirements
    students = []
    new_emails =[]
    for each in values:
        students.append(each[0])
        new_emails.append(each[1])
    print("{0} students extracted from spreadsheet".format(len(students)))
        
    students_found = list(filter(lambda x: x['name'] in students, json_data))
    print("{0} students after filter".format(len(students_found)))
    
    list(map(lambda x: print(x['id']), students_found))

def update_canvas_email(student_ID, email):
    parameters = {'user[email]':email}
    url = 'https://coderacademy.instructure.com/api/v1/users/{0}.json'.format(student_ID)
    requests.put(url, headers = headers, data = parameters)
if __name__ == "__main__":
    main()
