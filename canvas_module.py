from os import environ
import requests
from functools import reduce

#TODO: Setup routes and function for retrieving rubric data

def extract_rubric_data(course_ID, assessment_ID, per_page=100):
    '''
    Docstring
    ---------
    extract_rubric_data is used to extract the rubric grading data from the specified assessment.

    Arguments
    ---------
    course_ID(Int):
        Takes an int function argument that is used to specify the course.
    assessment_ID(Int):
        Takes an int function argument that is used to specify the assessment to extract rubric data from.
    
    Returns
    -------
    rubric_data(JSON):
        returns the rubric data extracted from the specified assessment in JSON format.
    '''
    #TODO: Assert that the course_ID and assessment_ID are strings or can be
    #converted to strings without error.
    parameters = { 
            'include[]': 'rubric_assessment', 
            'per_page': per_page 
            }
    request_url = 'https://coderacademy.instructure.com/api/v1/courses/{0}/assignments/{1}/submissions'.format(course_ID, assessment_ID)
    response = canvas_API_request(request_url, request_parameters=parameters, request_method='GET')
    return response

            
def update_canvas_emails(sheet_data, canvas_data, _headers):
    #TODO: Setup front end for this feature
    #TODO: Setup routes for this, identify database needs
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
def search_students(search_term):
    '''
    Docstring
    ---------
    search_students is used to search for canvas users that meet the
    search_term

    Arguments
    ---------
    search_term(String):
        Takes a String argument that is used to query canvas user.

    Returns
    -------
    response(response):
        returns a response object.
    '''
    request_url = 'https://coderacademy.instructure.com/api/v1/accounts/1/users'
    response = canvas_API_request(request_url, request_parameters={'search_term': search_term})
    return response

def enroll_canvas_student(student_ID, course_ID, section_ID=None):
    '''
    Docstring
    ---------
    enroll_canvas_student is used to enroll a canvas user to a specific course and section.
    
    Arguments
    ---------
    student_ID(Integer):
        Takes an integer argument that is used to specify the canvas user to enroll into a course.
    course_ID(Integer):
        Takes an integer argument that is used to specify the course to enroll the canvas user into.
    section_ID(Integer)(default = None):
        Takes an integer argument that is used to specify the course section to enroll the canvas user into.

    Returns
    -------
    response(Response):
        returns a response object.
    Notes
    -----
    Need to assert that the arguments are positive integers and that they are valid canvas users, courses and sections.
    '''
    try:
        request_url = 'https://coderacademy.instructure.com/api/v1/courses/{0}/enrollments'.format(str(course_ID))
        print(request_url)
        parameters = {'enrollment[user_id]': str(student_ID)}
        if(section_ID != None):
            parameters['enrollment[course_section_id]'] = str(section_ID)
        print(parameters)
    except Exception as error:
        raise error
    else:
        response = canvas_API_request(request_url, request_parameters=parameters, request_method='POST')
    return response

def create_canvas_login(student_name, student_email):
    '''
    Docstring
    ---------
    create_canvas_login is used to create a new canvas account using a specified name and email with the option to specify a password. A default is used if the password argument is not parsed.

    Arguments
    ---------
    student_name(String):
        Takes a string argument that is used to represent the name of the new canvas account.
    student_email(String):
        Takes a string argument that is used to represent the email of the new canvas account.
    Returns
    -------
    response(Response):
        returns a response object.

    Notes
    -----
    Argument names will need to change to user_name, user_email when this function is used to create accounts that are not students(E.g. teachers)
    '''
    assert isinstance(student_name, str)
    assert isinstance(student_email, str)
    
    parameters = {'user[name]':student_name, 'pseudonym[unique_id]':student_email, 'pseudonym[force_self_registration]': 'True'}
    response = canvas_API_request('https://coderacademy.instructure.com/api/v1/accounts/1/users', parameters, request_method='POST')
    return response

def update_canvas_email(student_ID, student_email):
    '''
    Docstring
    ---------
    update_canvas_email is used to update the primary email for a specified canvas user.

    Arguments
    ---------
    student_ID(Integer):
        Takes an integer argument that specifies the canvas user to update.
    student_email(String):
        Takes a string argument that represents the email used to update the canvas user account.

    Returns
    -------
    response(Response):
        returns a response object.
    '''
    assert isinstance(student_ID, int)
    assert isinstance(student_email, str)

    parameters = {'user[email]':email}
    request_url = 'https://coderacademy.instructure.com/api/v1/users/{0}.json'.format(student_ID)
    response = canvas_API_request(request_url, request_parameters=parameters, request_method='PUT')
    return response

def get_current_canvas_instance():
    return environ.get('canvas_instance')

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
        Returns a response Object.
    '''
    #Attempt to load canvas_secret from environment
    try:
        canvas_bearer_token = str(environ.get('canvas_secret'))
        canvas_URI = str(canvas_URI)
    except KeyError as error:
        '''
        If canvas_secret token cannot be loaded from the server, return a 500
        internal server error
        '''
        return abort(500)
    except ImportError as error:
        print("OS module could not be imported, please ensure that OS module has been installed and is in the requirements.txt file")
        return abort(500)
    #Handle conversion error
    except Exception as error:
        raise error
    else:
        #Setup request headers with auth token.
        _headers = {'Authorization' : 'Bearer {0}'.format(canvas_bearer_token)}
        #Append optional parameters to the URI string.
        if(request_parameters != None and isinstance(request_parameters, dict)):
            query_string = None
            for each_key, each_value in request_parameters.items():
                try:
                    string_formatted_key = str(each_key)
                    string_formatted_value = str(each_value)
                except Exception as error:
                    print("Could not convert key/value to string")
                else:
                    #can dict value be None?
                    '''
                    If each_key/each_value is the first element in requests_parameters, generate formatting accordingly. Else append to existing query_string.
                    '''
                    if query_string is None:
                        query_string = '?{0}={1}'.format(string_formatted_key, string_formatted_value)
                    else:
                        query_string = '{0}&{1}={2}'.format(query_string, string_formatted_key, string_formatted_value)
            #Concatenate URI and query string
            canvas_URI = canvas_URI + query_string
        else:
            print("Incorrect argument type parsed, request_parameters must be a dictionary")
        #TODO: Convert to switch statement.
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

