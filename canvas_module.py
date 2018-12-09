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

def create_canvas_login(student_name, student_email, password=None):
    assert isinstance(student_name, str)
    assert isinstance(student_email, str)
    
    #password function argument defaults to 'None' to ensure assert works.
    if password is None:
        parameters = {'user[name]':student_name, 'pseudonym[unique_id]':student_email, 'pseudonym[password]': '12345678'}
    else:
        assert isinstance(password, str)
        parameters = {'user[name]':student_name, 'pseudonym[unique_id]':student_email, 'pseudonym[password]': password}
    response = canvas_API_request('https://coderacademy.instructure.com/api/v1/accounts/1/users', parameters)
    return response
    '''
    #Setup request headers with auth token.
    _headers = {'Authorization' : 'Bearer {0}'.format(canvas_bearer_token)}

        url = 'https://coderacademy.instructure.com/api/v1/accounts/1/users'
    post_request = requests.post(url, headers = _headers, data = parameters)
    return post_request
    '''

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

def canvas_API_request(canvas_URI, request_parameters=None, request_method='GET'):
    '''
    Docstring
    ---------
        canvas_API_request('https://coderacademy.instructure.com/api/v1/courses/1/users', request_parameters={'search_term': 'test'})
    Arguments
    ---------
    canvas_URI(String):
        Takes a String method argument that dictates the canvas endpoint to request.
    request_parameters(Dict):
        Takes a dictionary of additional request parameters. These are parsed as query parameters to the endpoint specified by the canvas_URI.
    request_method(String)(Default = 'GET')
        Takes a String method argument that dictates the request method to be used.
    Returns
    -------
    response(Response): http://docs.python-requests.org/en/master/api/
        Returns a Response Object.
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
    except ImportError as error:
        print("OS module could not be imported, please ensure that OS module has been installed and is in the requirements.txt file")
        return abort(500)
    except Exception as error:
        raise error

    assert isinstance(canvas_URI, str)
    assert isinstance(request_parameters, dict)
    assert isinstance(request_method, str)

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
        #Concatenate URI and query string
        canvas_URI = canvas_URI + query_string
    
    #Request resource
    if(request_method.upper() == 'POST'):
        response = requests.post(canvas_URI, headers=_headers)
    elif(request_method.upper() == 'GET'):
        response = requests.get(canvas_URI, headers=_headers)
    elif(request_method.upper() == 'PUT'):
        response = requests.put(canvas_URI, headers=_headers)
    else:
        print("Could not understand request_method, Please specify 'GET', 'POST' or 'PUT'")

    #Handle responses
    if response.status_code == 200:
        print("Request successful")
    elif response.status_code == 401:
        print("Authorisation error, please check canvas_secret environment variable")
    else:
        print(response.status_code)
    return response

