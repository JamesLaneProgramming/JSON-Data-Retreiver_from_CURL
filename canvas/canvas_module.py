from os import environ
import requests
from functools import reduce
from flask import Blueprint, flash, abort
from hubspot_requests.hubspot_request_model import Hubspot_Request
from hubspot.hubspot_authentication import require_hubspot_signature_validation

canvas_blueprint = Blueprint('canvas', __name__)

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
        if(request_parameters != None):
            if(isinstance(request_parameters, dict)):
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

@require_hubspot_signature_validation
@canvas_blueprint.route('/create-account', methods=['POST'])
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
    try:
        course_ID = str(request.args.get('course_id'))
        section_ID = str(request.args.get('section_id'))
    except Exception as error:
        print("Invalid course_id or section_id")
        return abort(500)
    else:
        #Validate POST payload
        try:
            json_data = request.get_json()
        except Exception as error:
            return abort(415)
        else:
            #http://flask.pocoo.org/docs/1.0/api/#response-objects
            #Returns None if JSON could not be parsed.
            if(json_data is not None):
                try:
                    first_name = json_data['properties']['firstname']['value']
                    last_name = json_data['properties']['lastname']['value']
                    student_email = json_data['properties']['email']['value']
                    student_name = first_name + " " + last_name
                except KeyError as error:
                    print("Specified JSON fields are not present")
                    return abort(422)
                except Exception as error:
                    return abort(500)
                #Check if JSON data was parsed correctly.
                #Validate JSON Object is dict not array.
                if json_data and isinstance(json_data, dict):
                    try:
                        first_name = json_data['properties']['firstname']['value']
                        last_name = json_data['properties']['lastname']['value']
                        user_email = json_data['properties']['email']['value']
                        user_name = first_name + " " + last_name
                    except KeyError as error:
                        print("Specified JSON fields are not present")
                        return abort(422)
                    except Exception as error:
                        print(error)
                        return abort(500)
                    else:
                        try:
                            hubspot_request = Hubspot_Request(course_ID, section_ID, first_name, last_name, user_email).save()
                        except Exception as error:
                            print(error)
                        creation_response = create_canvas_login(user_name, user_email)
                        if(creation_response.status_code == 400):
                            print("The user already exists", creation_response)
                            users_found = search_students(user_email).json()
                            best_fit_user = users_found[0] or {}
                            if isinstance(best_fit_user, dict):
                                try:
                                    user_ID = best_fit_user['id']
                                except KeyError as error:
                                    print("Specified JSON fields are not present")
                                    return abort(422)
                            else:
                                print('users_found is not a json object')
                                return abort(422)
                        elif(creation_response.status_code == 200):
                            try:
                                user_details = creation_response.json()
                                user_ID = user_details['id']
                            except TypeError as error:
                                print("Specified JSON fields are not present")
                                return abort(422)
                            except Exception as error:
                                print(error)
                                return abort(500)
                        else:
                            return abort(creation_response.status_code)
                        #Endpoint will return 422 if student_id doesn't exist
                        enroll_user_in_course(course_ID, section_ID, user_ID)
                else:
                    flash("JSON data not a dictionary")
                    return abort(400)
            else:
                flash("Could not parse JSON, Bad Request")
                return abort(400)

#TODO: Remove endpoint and convert to internal method.
def enroll_user_in_course(course_id, section_id, user_id):
    try:
        student_enrollment_request = enroll_canvas_student(user_ID, course_ID, section_ID)
    except Exception as error:
        print(error)
        print(student_enrollment_request.text)
    else:
        return student_enrollment_request.text

@canvas_blueprint.route('/sis_id_update', methods=['GET', 'POST'])
@login_required
def update_sis_id():
    if(request.method == 'GET'):
        return render_template('sis_id_uploader.html')
    if(request.method == 'POST'):
        # https://openpyxl.readthedocs.io/en/stable/
        if 'File' not in request.files:
            flask("No file uploaded")
            return redirect(url_for(update_sis_id))
        uploaded_file = request.files['File']
        if(uploaded_file.filename == ""):
            flask("No selected file")
            return redirect(url_for(update_sis_id))
        if uploaded_file:
            data_stream = pandas.read_csv(uploaded_file.stream)
            for i in range(0, len(data_stream.index) - 1):
                try:
                    first_name = data_stream['First Name [Required]'][i]
                    last_name = data_stream['Last Name [Required]'][i]
                    student_name = first_name + " " + last_name
                    student_email = data_stream['Email Address [Required]'][i]
                    student_number = (student_email).split('@')[0]
                except Exception as error:
                    raise error
                else:
                    best_fit_student = json.loads(search_students(student_name).text)
                if(best_fit_student):
                    try:
                        user_id = best_fit_student[0]['id']
                        user_name = best_fit_student[0]['name']
                    except Exception as error:
                        raise error
                    else:
                        if(student_name.upper() == user_name.upper()):
                            domain = 'https://coderacademy.instructure.com'
                            endpoint = '/api/v1/users/{0}/logins'.format(user_id)
                            user_login = canvas_API_request(
                                                            domain + endpoint,
                                                            request_method = 'GET'
                                                           )
                            user_login_id = json.loads(user_login.text)[0]['id']
                            endpoint = '/api/v1/accounts/0/logins/{0}'.format(user_login_id)
                            user_login_details = canvas_API_request(
                                                                    domain + endpoint,
                                                                    request_parameters={'login[sis_user_id]':student_number},
                                                                    request_method = 'PUT'
                                                                   )
                        else:
                            print("Matched {0} with {1}".format(student_name, user_name))
                            print("Could not link student to canvas user account")
                else:
                    print("Could not find student: " + student_name)
            return "success"

@canvas_blueprint.route('/students', methods=['GET', 'POST'])
@login_required
def student_search():
    if(request.method == 'POST'):
        try:
            search_term = request.form['search_term']
        except Exception as error:
            raise error
        else:
            search_results = search_students(search_term)
            return search_results.text
    else:
        return render_template('student_search.html')
