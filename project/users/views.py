from flask import redirect, render_template, request, url_for, Blueprint, make_response
from routing_module import get_redirect_target, redirect_back
from werkzeug.security import safe_str_cmp
from project import application
from project.users.user_model import User
from project.hubspot_requests.hubspot_request_model import Hubspot_Request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from os import environ
from functools import wraps
import hashlib
import datetime
from canvas_module import update_canvas_email, create_canvas_login, canvas_API_request
from canvas_module import enroll_canvas_student, extract_rubric_data, search_students



users_blueprint = Blueprint(
    'users',
    __name__,
    template_folder = 'templates'
)

@application.route('/login', methods=['GET','POST'])
def login():
    if(request.method == 'POST'):
        try:
            username = str(request.values.get('username'))
            password = str(request.values.get('password'))
        except Exception as error:
            next = get_redirect_target()
            return redirect(url_for('login'), next=next)
        else:
            #Inform users of username/password constrains.
            if(safe_str_cmp(username.encode('utf-8'), password.encode('utf-8'))):
                user = User.authenticate(username, password)
                if user is not None and user.is_authenticated:
                    login_status = login_user(user)
                    #http://flask.pocoo.org/docs/1.0/patterns/flashing/
                    flash('Logged in successfully.')
                    next = get_redirect_target()
                    return redirect_back('home', next=next)
                else:
                    next = get_redirect_target()
                    return redirect(url_for('signup'))
            else:
                next = get_redirect_target()
                return redirect(url_for('login'), next=next)
    else:
        return render_template('login.html')

@application.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@application.route('/signup', methods=['GET', 'POST'])
def signup():
    if(request.method == 'POST'):
        try:
            username = str(request.form['username'])
            password = str(request.form['password'])
            safeword = str(request.form['safeword'])
            next = get_redirect_target()
        except Exception as error:
            raise error
        else:
            if username is not "" or password is not "" or safeword is not "" and \
                    safe_str_cmp(username.encode('utf-8'), password.encode('utf-8'), safeword.encode('utf-8')):
                if(User.objects(username=username)):
                    flash("Username already taken")
                    return redirect(url_for('signup', next=next))
                elif(safeword == str(environ.get('safeword'))):
                    new_user = User.create(username.encode('utf-8'), password.encode('utf-8'))
                    User.authenticate(username, password)
                    return redirect_back('home', next=next)
                else:
                    flash("safeword was incorrect, could not create account")
                    return redirect(url_for('signup', next=next))
            else:
                flash("username, password or safeword cannot be empty")
                return redirect(url_for('signup', next=next))
    else:
        return render_template('signup.html')

def require_hubspot_signature_validation(func):
    #https://developers.hubspot.com/docs/faq/validating-requests-from-hubspot
    #https://developers.hubspot.com/docs/methods/webhooks/webhooks-overview
    @wraps(func)
    def validate_hubspot_response_signature(*args, **kwargs):
        try:
            hubspot_client_secret = environ.get('hubspot_client_secret')
            hubspot_request_signature = request.headers.get('X-HubSpot-Signature')
            request_method = request.method
            request_uri = request.base_url
            print("Request URI: ", request_uri)
            request_body = request.get_data(as_text=True)
            print("Request Body: ", request_body)
        except Exception as error:
            raise error
        else:
            try:
                hash_string = hubspot_client_secret + request_method + request_uri + request_body
                encoded_hash_string = hash_string.encode('utf-8')
                request_signature = hashlib.sha256(encoded_hash_string).hexdigest()
            except Exception as error:
                print(error)
                return "Could not create signature"
            else:
                if(hubspot_request_signature == request_signature):
                    print("Hubspot Signature Verified")
                    return func(*args, **kwargs)
                else:
                    print(hubspot_request_signature, request_signature)
                    print('Unauthenticated')
                    #Replace next line when hubspot works
                    return func(*args, **kwargs)
    return validate_hubspot_response_signature

def require_hubspot_access_token(func):
    @wraps(func)
    def update_hubspot_access_token(*args, **kwargs):
        if request.cookies.get('hubspot_access_token') is None:
            '''
            https://tools.ietf.org/html/rfc6749#section-1.5
            '''
            print("Hubspot access token not in cookies")
            return redirect(url_for('refresh_access_token'))
        else:
            try:
                hubspot_access_token_expiry = current_user.hubspot_access_token_expiry
                last_hubspot_access_token_refresh = current_user.last_hubspot_access_token_refresh
                '''TODO: Implement logic if access token revolked but expiry is
                still valid
                '''
            except Exception as error:
                print('Could not update cookie with user access token, refreshing access token')
            else:
                if(last_hubspot_access_token_refresh + datetime.timedelta(minutes=hubspot_access_token_expiry) < datetime.datetime.utcnow()):
                    return redirect(url_for('refresh_access_token'))
                else:
                    return func(*args, **kwargs)
    return update_hubspot_access_token

@application.route('/request_refresh_token', methods=['GET'])
@login_required
def request_refresh_token():
    try:
        code = str(request.args.get('code'))
        client_id = str(environ.get('hubspot_client_id'))
        client_secret = str(environ.get('hubspot_client_secret'))
        '''
        redirect_uri must match the redirect_uri used to intitiate the OAuth
        connection

        '''
        redirect_uri = url_for('request_refresh_token', _external=True,
                               _scheme='https')
    except Exception as error:
        flash('Could not find auth code in request arguments')
        return redirect(url_for('authenticate_hubspot'))
    else:
        _headers = {
                    'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'
                   }
        data = {
                'grant_type':'authorization_code',
                'client_id': client_id,
                'client_secret': client_secret,
                'redirect_uri': redirect_uri,
                'code': code
               }
        post_request = requests.post(
                                     'https://api.hubapi.com/oauth/v1/token',
                                     headers=_headers,
                                     data=data
                                    )
        try:
            refresh_token = post_request.json()['refresh_token']
            access_token_expiry = post_request.json()['expires_in']
        except Exception as error:
            raise error
        else:
            User.set_refresh_token(current_user.id,
                refresh_token)
            return redirect(url_for('refresh_access_token'))

@application.route('/refresh_access_token', methods=['GET'])
@login_required
def refresh_access_token():
    try:
        client_id = str(environ.get('hubspot_client_id'))
        client_secret = str(environ.get('hubspot_client_secret'))
    except Exception as error:
        flash('client_id or client_secret environment variables cannot be found')
        print('client_id or client_secret environment variables cannot be found')
        return redirect(url_for('refresh_access_code'))
    else:
        try:
            refresh_token = current_user.hubspot_refresh_token
        except Exception as error:
            return redirect(url_for('authenticate_hubspot'))
        else:
            if(refresh_token != ""):
                endpoint = "https://api.hubapi.com/oauth/v1/token"
                headers = {
                           "Content-Type": "application/x-www-form-urlencoded",
                           "charset": "utf-8"
                          }
                data = {
                        "grant_type": "refresh_token",
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "refresh_token": refresh_token
                       }

                post_request = requests.post(
                                             endpoint,
                                             headers=headers,
                                             data=data
                                            )
                try:
                    access_token = post_request.json()['access_token']
                    access_token_expiry = post_request.json()['expires_in']
                except ValueError as error:
                    #TODO: Redirect to where?
                    print("Post request response did not contain an access token")
                #KeyError missing access_token
                except Exception as error:
                    #TODO: Redirect to where?
                    print(error)
                else:
                    next = get_redirect_target()
                    response = make_response(redirect_back('home', next=next))
                    response.set_cookie('hubspot_access_token', access_token)
                    User.set_access_token_expiry(current_user.id, access_token_expiry)
                    return response
            else:
                return redirect(url_for('authenticate_hubspot'))

@application.route('/students', methods=['GET', 'POST'])
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

@require_hubspot_signature_validation
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
    try:
        course_ID = str(request.args.get('course_id'))
        section_ID = str(request.args.get('section_id'))
    except Exception as error:
        print("Invalid course_id or section_id")
        return "Invalid course_id or section_id"
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
                                return creation_response.text
                        else:
                            return str(creation_response.text)

                        #Endpoint will return 422 if student_id doesn't exist
                        #return redirect(url_for('enroll_user_in_course', user_id=user_ID, course_id=course_ID, section_id=section_ID))
                        url = url_for('enroll_user_in_course', _external=True, _schema='https')
                        _data = {
                                "user_id": user_ID,
                                "course_id": course_ID,
                                "section_id": section_ID
                                }
                        try:
                            user_enrollment_request = requests.post(url, data=_data)
                        except ConnectionError as error:
                            print("DNS Failure, Refused Connection, etc.")
                            return abort(500)
                        except requests.exceptions.Timeout as error:
                            print("Request timed out, please try again")
                            return abort(500)
                        except requests.exceptions.TooManyRedirects as error:
                            print("Too many redirects.", error)
                            return abort(500)
                        except Exception as error:
                            print(error)
                            return abort(500)
                        else:
                            return user_enrollment_request.text
                else:
                    flash("JSON data not a dictionary")
                    return abort(400)
            else:
                flash("Could not parse JSON, Bad Request")
                return abort(400)

@application.route('/enroll_user', methods=['POST'])
def enroll_user_in_course():
    #Arguments passed through the data parameter will be form-encoded
    try:
        #Convert ImmutableMultiDict to Dict
        request_arguments = request.form.to_dict()
        print(request_arguments)
        course_ID = str(request_arguments['course_id'])
        section_ID = str(request_arguments['section_id'])
        user_ID = str(request_arguments['user_id'])
    except Exception as error:
        print(error)
        return abort(500)
    else:
        user_enrollment_request = enroll_canvas_student(user_ID, course_ID, section_ID)
        return user_enrollment_request.text
'''
@application.route('/sis_id_update', methods=['GET', 'POST'])
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
                #Check if best_fit_student returns array.
                #Return a list of students for the user to chose.
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
'''
