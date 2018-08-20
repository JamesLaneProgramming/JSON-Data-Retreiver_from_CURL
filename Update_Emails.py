#!usr/bin/python

import os
import sys
import requests
import json

def get_bearer_token(_dir):
    if os.path.exists(_dir):
        with open(_dir, 'r') as token_file:
            try:
                print('Token file accessed and read')
                file_content = token_file.read().splitlines()[0]
            except IOError as e:
                raise e
                sys.exit()
            except EOFError as e:
                raise e
                sys.exit()
    return file_content

def get_generated_emails(_dir):
    if os.path.exists(_dir):
        with open(_dir, 'r') as email_file:
            try:
                file_content = email_file.read().splitlines()[0]
            except IOError as e:
                raise e
            except EOFError as e:
                throw e
    return file_content

def main():
    bearer_token = get_bearer_token('./token')
    headers = {'Authorization' : 'Bearer {0}'.format(bearer_token)}
    response = requests.get('https://coderacademy.instructure.com/api/v1/courses/92/users?per_page=100',
                headers=headers)

    json_data = json.loads(response.text)
    for each_element in json_data:
        #Load the JSON data into a dictionary so that we can read key/value pairs
        for key, value in each_element:
            if(key == 'login_id'):
                #print(value)
                currentUserEmail = key
            if(key == 'id'):
                currentUserID = key
            #Generate the new email address based on a lambda filter function

def update_canvas_email(_student_ID, _email):
    parameters = {'user[email]':_email}
    url = 'https://coderacademy.instructure.com/api/v1/users/{0}.json'.format(student_ID)
    requests.put(url, headers = headers, data = parameters)
if __name__ == "__main__":
    main()
