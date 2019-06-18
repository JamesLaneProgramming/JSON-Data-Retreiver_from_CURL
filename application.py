from __future__ import print_function
from __future__ import unicode_literals
'''
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
'''
#TODO: Setup workflow for OAuth2 refresh tokens

import os, sys
from os import environ
import datetime
import dateutil.parser
import pytz
import sys
import requests
import json
import hashlib
import pandas
from werkzeug import secure_filename
from werkzeug.security import safe_str_cmp
from openpyxl import Workbook, load_workbook
from functools import wraps
from urllib.parse import urlparse, urljoin
from flask import Flask, flash, render_template, request, abort, redirect, \
    url_for, make_response, send_from_directory, copy_current_request_context, \
    has_request_context
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from flask_mongoengine import MongoEngine
#Should not import canvas_API_request function. Instead create an endpoint for specific action.
from canvas_module import update_canvas_email, create_canvas_login, canvas_API_request
from canvas_module import enroll_canvas_student, extract_rubric_data, search_students
from users.user_model import User
from hubspot_webhooks.hubspot_webhook_model import Hubspot_Webhook
from assessments.assessment_model import Criterion
from assignment_mapping.assignment_mapping_model import Assignment_Mapping
from learning_outcomes.learning_outcome_model import Learning_Outcome
from subjects.subject_model import Subject
from overdue_assignments.overdue_assignment_model import Overdue_Assignment
from enrollments.enrollment_model import Enrollment
from grades.grade_model import Grade

application = Flask(__name__, template_folder='templates')
CORS(application)
#Cross origin requests can be enabled for resources using the @cross_origin decorator method

#Set application secret key to secure against CSRF
application.secret_key = 'super secret key'
application.config['SESSION_TYPE'] = 'filesystem'
application.config['UPLOAD_FOLDER'] = '/uploads'

#Configure mongodb server connection
application.config['MONGODB_SETTINGS'] = {
    'db': 'canvas_integration',
    'host': 'ds125684.mlab.com:25684',
    'username': 'James',
    'password': environ.get('mongoDB_Password'),
    'authentication_source': 'canvas_integration'
}

#Initialise the mongo engine.
db = MongoEngine(application)

#Configure flask-login
login_manager = LoginManager()
login_manager.session_protection = 'strong'

#Redirect to login view when a user has yet to authenticate.
login_manager.login_view = 'login'
login_manager.init_app(application)

#user_loader callback used to load a user from a session ID.
@login_manager.user_loader
def load_user(user_id):
    return User.objects(pk=user_id).first()

@application.route('/mail')
def send_simple_message():
    mail_request = requests.post(
        "https://api.mailgun.net/v3/sandboxbd63b75742724ec48a7ff11a143eae19.mailgun.org/messages",
        auth=("api", "412c248f4efdd95f34e8b541726e1b7e-29b7488f-07e4e4c0"),
        data={"from": "Excited User <postmaster@sandboxbd63b75742724ec48a7ff11a143eae19.mailgun.org>",
            "to": ["james.lane@redhilleducation.com", "postmaster@sandboxbd63b75742724ec48a7ff11a143eae19.mailgun.org"],
            "subject": "Hello",
            "text": "Testing some Mailgun awesomness!"})
    return mail_request.text

def main():
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=check_overdue_assignments, trigger="interval", days=1)
    scheduler.start()
    application.debug = True
    port = int(os.environ.get('PORT', 5000))
    application.run(host='0.0.0.0', port=port, use_reloader=False)
    #Set up Flask Scheduler.

@application.route('/')
def home():
    return render_template('home.html')

@application.route('/login', methods=['GET','POST'])
def login():
    if(request.method == 'POST'):
        try:
            username = str(request.values.get('username'))
            password = str(request.values.get('password'))
        except Exception as error:
            return redirect(url_for('login'))
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
                return redirect(url_for('signup'), next=next)
    else:
        return render_template('login.html')

#See http://flask.pocoo.org/snippets/62
def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    target_url = urlparse(urljoin(request.host_url, target))
    return target_url.scheme in ('http', 'https') and \
           ref_url.netloc == target_url.netloc

def get_redirect_target():
    for target in request.values.get('next'), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return target

def redirect_back(endpoint, **values):
    target = request.args.get('next')
    if not target or not is_safe_url(target):
        target = url_for(endpoint, **values)
    return redirect(target)

def check_if_parameter_in_request_data(request, parameter_to_check, allow_empty_value=True, allow_none_value=True):
    if parameter_to_check not in request.files:
        return False
    elif(request.files[parameter_to_check] == ""):
        if(allow_empty_values):
            return True
        else:
            return False
    elif(request.files[parameter_to_check] == None):
        if(allow_none_values):
            return True
        else:
            return False
    else:
        return True

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
        except Exception as error:
            raise error
        else:
            if username is not "" or password is not "" or safeword is not "" and \
                    safe_str_cmp(username.encode('utf-8'), password.encode('utf-8'), safeword.encode('utf-8')):
                if(User.objects(username=username)):
                    flash("Username already taken")
                    next = get_redirect_target()
                    return redirect(url_for('signup', next=next))
                elif(safeword == str(environ.get('safeword'))):
                    new_user = User.create(username, password)
                    User.authenticate(username, password)
                    next = get_redirect_target()
                    return redirect_back('home', next=next)
                else:
                    next = get_redirect_target()
                    flash("safeword was incorrect, could not create account")
                    return redirect(url_for('signup', next=next))
            else:
                flash("username, password or safeword cannot be empty")
                next = get_redirect_target()
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
        code = request.args.get('code')
        client_id = environ.get('hubspot_client_id')
        client_secret = environ.get('hubspot_client_secret')
        '''
        redirect_uri must match the redirect_uri used to intitiate the OAuth
        connection

        '''
        redirect_uri = url_for('request_refresh_token', _external=True,
                               _scheme='https')
    except Exception as error:
        raise error
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
            User.set_refresh_token(
                                   current_user.id, 
                                   refresh_token
                                  )
            return redirect(url_for('refresh_access_token'))

@application.route('/refresh_access_token', methods=['GET'])
@login_required
def refresh_access_token():
    try:
        client_id = str(environ.get('hubspot_client_id'))
        client_secret = str(environ.get('hubspot_client_secret'))
    except Exception as error:
        print('client_id or client_secret environment variables cannot be found')
        raise error
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
                    print("Post request response did not contain an access token")
                #KeyError missing access_token
                except Exception as error:
                    print(post_request.text)
                    raise error
                else:
                    next = get_redirect_target()
                    response = make_response(redirect_back('home', next=next))
                    response.set_cookie('hubspot_access_token', access_token)
                    User.set_access_token_expiry(current_user.id, access_token_expiry)
                    return response
            else:
                return redirect(url_for('authenticate_hubspot'))

@application.route('/hubspot')
@login_required
def authenticate_hubspot():
    '''
    Hubspot OAuth workflow:

    Direct users to https://app.hubspot.com/oauth/authorize with the following
    query parameters:
        -client_id
        -scope
        -redirect_uri

    They will be prompted to authenticate and authorise the application.

    Users will be redirected to the redirect_uri with a code query parameter.
    
    Use the code above to request access token and refresh token.
    Headers = Content-Type: application/x-www-form-urlencoded;charset=utf-8
    Data:
        -grant_type=authorisation_code
        -client_id
        -client_secret
        -redirect_uri
        -code
    POST https://app.hubspot.com/oauth/v1/token
    '''
    try:
        client_id = environ.get('hubspot_client_id')
        scope = environ.get('hubspot_scopes')
        redirect_uri = url_for('request_refresh_token', _external=True,
                               _scheme='https')
    except Exception as error:
        raise error
    return redirect('https://app.hubspot.com/oauth/authorize?client_id={0}&scope={1}&redirect_uri={2}'.format(client_id,
                                                                                                  scope,
                                                                                                  redirect_uri))

@application.route('/hubspot/workflows', methods=['GET'])
@require_hubspot_access_token
@login_required
def workflows():
    try:
        access_token = request.cookies.get('hubspot_access_token')
    except Exception as error:
        raise error
    else:
        endpoint = 'https://api.hubapi.com/automation/v3/workflows'
        request_headers = {
                           "Content-Type": "application/json",
                           "Authorization": "Bearer " + str(access_token)
                          }
        workflow_request = requests.get(endpoint, headers=request_headers)
        return workflow_request.text

@application.route('/hubspot/workflow_history/<workflow_id>')
@require_hubspot_access_token
@login_required
def workflow_history(workflow_id):
    access_token = request.cookies.get('hubspot_access_token')
    domain = 'https://api.hubapi.com'
    endpoint = '/automation/v3/logevents/workflows/{0}/filter'
    request_url = domain + endpoint.format(workflow_id)
    request_headers = {
                       "Content-Type": "application/json",
                       "Authorization": "Bearer " + str(access_token)
                      }
    request_body = {
                    "types": ["ENROLLED"]
                   }
    try:
        put_request = requests.put(
                             request_url, 
                             headers=request_headers,
                             params=request_body
                            )
        if put_request.status_code == 401:
            return redirect(url_for('authenticate_hubspot'))
        else:
            return put_request.text
    except Exception as error:
        return redirect(url_for('home'))

@application.route('/upload_provisioning_csv', methods=['GET', 'POST'])
@login_required
def upload_provisioning_csv():
    if(request.method == 'GET'):
        return render_template('enrollment_csv_uploader.html')
    if(request.method == 'POST'):
        # https://openpyxl.readthedocs.io/en/stable/
        if 'File' not in request.files:
            flash("No file uploaded")
            return redirect(url_for(update_sis_id))
        uploaded_file = request.files['File']
        if(uploaded_file.filename == ""):
            flask("No selected file")
            return redirect(url_for(update_sis_id))
        if uploaded_file:
            data_stream = pandas.read_csv(uploaded_file.stream)
            for i in range(0, len(data_stream.index) - 1):
                try:
                    canvas_course_id = data_stream['canvas_course_id'][i]
                    canvas_user_id = data_stream['canvas_user_id'][i]
                    #Add base_role_type to distinguish between student and
                    #teacher
                except Exception as error:
                    raise error
                else:
                    if(Enrollment.objects(canvas_course_id=canvas_course_id, canvas_user_id=canvas_user_id)):
                        pass
                    else:
                        new_enrollment = Enrollment(int(canvas_course_id), int(canvas_user_id))
                        new_enrollment.save()
            return "Success"

@application.route('/check_overdue', methods=['GET'])
def check_overdue():
    check_overdue_assignments()

def check_overdue_assignments():
    print("Background Scheduler Working")
    for enrollment in Enrollment.objects():
        user_assignment_data(enrollment.canvas_course_id, enrollment.canvas_user_id)

#Needs development
@application.route('/create_provisioning_report', methods=['GET', 'POST'])
@login_required
def create_provisioning_report():
    if(request.method == 'GET'):
        domain = 'https://coderacademy.instructure.com'
        endpoint = '/api/v1/accounts/1/reports/users/provisioning_csv'
        request_parameters = {
            'parameters[enrollments]': 'true'
        }
        provisioning_report = canvas_API_request(domain + endpoint, request_parameters=request_parameters, method='POST')
        return provisioning_report.text

def user_assignment_data(course_id, user_id):
        print(course_id, user_id)
        domain = 'https://coderacademy.instructure.com'
        endpoint = '/api/v1/courses/{0}/analytics/users/{1}/assignments'.format(str(course_id), str(user_id))
        print(domain + endpoint)
        assignment_request = canvas_API_request(domain + endpoint)
        if(assignment_request.status_code == 200):
            try:
                user_assignment_data = json.loads(assignment_request.text)
            except JSONDecodeError as error:
                raise error
            except Exception as error:
                raise error
            else:
                user_non_submissions = []
                for user_assignment in user_assignment_data:
                    try:
                        submission = user_assignment['submission']
                    except Exception as error:
                        print("Assignment Does not require submission")
                        continue
                    else:
                        if(user_assignment['submission']['submitted_at'] == None):
                            try:
                                if(user_assignment['due_at'] != None):
                                    due_date = dateutil.parser.isoparse(user_assignment['due_at'])
                                else:
                                    print("No due date set for assignment")
                                    continue
                                date_now = dateutil.parser.isoparse(datetime.datetime.utcnow().replace(tzinfo=pytz.utc).isoformat())
                            except Exception as error:
                                print(error)
                                continue
                            else:
                                if(date_now > due_date):
                                    #Check if database entry for this users
                                    #assignment has already been created
                                    if(Overdue_Assignment.objects(course_id=course_id, assignment_id=user_assignment['assignment_id'], user_id=user_id)):
                                        print("Overdue Assignment already in database")
                                    else:
                                        try:
                                            overdue_assignment = \
                                                Overdue_Assignment(int(course_id),
                                                int(user_assignment['assignment_id']),
                                                int(user_id), 
                                                due_date, 
                                                date_now)
                                            overdue_assignment.save()
                                        except Exception as error:
                                            raise error
                                        else:
                                            print("Overdue assignment created in database")
                                else:
                                    print('Assignment not due yet. Days until due: {0}'.format(date_now - due_date).days)
                        else:
                            if(user_assignment['submission']['score']):
                                response = 'Student has submitted for {0} with a score of {1}'
                                response = response.format(user_assignment['title'], user_assignment['submission']['score'])
                                print(response)
                            else:
                                response = 'Student has submitted for {0} but has not been graded'.format(user_assignment['title'])
                                print(response)
                return str(user_non_submissions)
        elif(assignment_request.status_code == 404):
            print("This resource does not exist")
        else:
            return assignment_request.status_code

@application.route('/user-in-a-course-level-assignment-data', methods=['GET', 'POST'])
@login_required
def user_assignment_data_endpoint():
    if(request.method == 'GET'):
        return render_template('user-assignment-data.html')
    elif(request.method == 'POST'):
        try:
            course_id = str(int(request.values.get('course_id')))
            user_id = str(int(request.values.get('user_id')))
        except Exception as error:
            raise error
        else:
            return user_assignment_data(course_id, user_id)
            #Get assignment details
   
@application.route('/list-assignment-extensions', methods=['GET', 'POST'])
@login_required
def list_assignment_extensions():
    '''
    https://community.canvaslms.com/thread/34922-why-is-the-assignment-dueat-value-that-of-the-last-override
    '''
    if(request.method == 'GET'):
        return render_template('list_assignment_extensions.html')
    elif(request.method == 'POST'):
        try:
            course_id = str(request.values.get('course_id'))
            assessment_id = str(request.values.get('assessment_id'))
        except Exception as error:
            raise error
        else:
            #Get assignment details
            domain = 'https://coderacademy.instructure.com'
            endpoint = '/api/v1/courses/{0}/assignments/{1}'
            endpoint = endpoint.format(course_id, assessment_id)
            request_parameters = {
                'all_dates':1
            }
            assignment_request = canvas_API_request(domain + endpoint,
                                                    request_parameters=request_parameters)
            if(assignment_request.status_code == 200):
                assignment_object = json.loads(assignment_request.text)
                print(assignment_object)
                if(assignment_object['all_dates']):
                    print(assignment_object['all_dates'])
                try:
                    assignment_object_due_date = assignment_object['due_at']
                except Exception as error:
                    raise error
                else:
                    if(assignment_object_due_date is None):
                        print("No due date could be extracted from json data")
                    else:
                        assignment_due_at = dateutil.parser.parse(assignment_object_due_date)
                        
                        #Get assignment overrides
                        domain = 'https://coderacademy.instructure.com'
                        endpoint = '/api/v1/courses/{0}/assignments/{1}/overrides'
                        endpoint = endpoint.format(course_id, assessment_id)
                        request_parameters = {}
                        overrides_request = canvas_API_request(domain + endpoint)
                        overrides_object = json.loads(overrides_request.text)
                        assignment_extension_ids = []
                        for override_object in overrides_object:
                            override_due_at = dateutil.parser.parse(override_object['due_at'])
                            print("Original due date: ", assignment_due_at, ". Override due date: ", override_due_at)
                            if override_due_at > assignment_due_at:
                                override_student_list = get_student_id_list_from_assignment_override_object(override_object,
                                                                                                            course_id)
                                assignment_extension_ids.extend(override_student_list)
                            else:
                                print("Assignment override was not due after assignment, no extentsion was given")
                        return ''.join(i for i in assignment_extension_ids if not assignment_extensions_ids.index(i) == 0)
            else:
                return abort(status_code)
def get_student_id_list_from_assignment_override_object(override_object,
                                                        course_id):
    if not isinstance(course_id, str):
        print("Course ID not a string instance")
    list_of_student_ids = []
    if 'student_ids' in override_object:
        for student_id in override_object['student_ids']:
            list_of_student_ids.append(str(student_id))
    elif 'group_id' in override_object:
        group_id = override_object['group_id']
        domain = 'https://coderacademy.instructure.com'
        endpoint = '/api/v1/groups/{0}/users'.format(group_id)
        uconsole.log(formData);roup_request = canvas_API_request(domain + endpoint)
        for student in group_request:
            list_of_student_ids.append(student['id'])
    elif 'course_section_id' in override_object:
        section_id = override_object['course_section_id']
        domain = 'https://coderacademy.instructure.com'
        endpoint = '/api/v1/courses/{0}/sections/{1}'.format(course_id,
                                                                section_id)
        request_parameters = {'include[]': 'students'}
        course_section_request = canvas_API_request(domain + endpoint,
                                                    request_parameters=request_parameters)
        for student in course_section_request:
            list_of_student_ids.append(student['id'])
    else:
        print('No id in override object')
        print(override_object)
    return ''.join(str(i) + ', ' for i in list_of_student_ids)

@application.route('/retreive_rubric_assessment', methods=['GET', 'POST'])
@login_required
def retreive_rubric_assessment():
    '''
    Docstring
    ---------
        GET
        ---
            Returns
            -------
            rubric_data.html(Template):
                Returns a HTML form to handle user input and post specified course_id and assessment_id.
        POST
        ----
            Arguments
            ---------
            course_id:
                Requires a valid Canvas course_id.
            assessment_id:
                Requires a valid assessment_id.
    '''
    if(request.method == 'GET'):
        return render_template('rubric_data.html')
    elif(request.method == 'POST'):
        try:
            course_id = str(request.values.get('course_id'))
            assignment_id = str(request.values.get('assessment_id'))
        #Handle Conversion error.
        except Exception as error:
            raise error
        else:
            if(course_id is not None and assignment_id is not None):
                try:
                    rubric_data = extract_rubric_data(course_id, assignment_id)
                except Exception as error:
                    print("Unexpected error in extract_rubric_data method")
                    return abort(500)
                else:
                    if(rubric_data is not None):
                        submissions = rubric_data.json()
                        criteria = []
                        for i in range(0, 1):
                            try:
                                for criterion_id in submissions[i]['rubric_assessment'].keys():
                                    if(Assignment_Mapping.objects(criterion_id=criterion_id).count() == 0):
                                        criteria.append(criterion_id)
                                    else:
                                        print('Criteria: {0}, is already mapped'.format(criterion_id))
                            except Exception as error:
                                print(error)
                        if(len(criteria) != 0):
                            learning_outcomes = json.loads(Learning_Outcome.read())
                            return render_template(
                                'map_rubric_assessment.html',
                                course_id=course_id,
                                assignment_id=assignment_id,
                                criteria=criteria,
                                learning_outcomes=learning_outcomes
                            )
                        else:
                            for i in range(0, len(submissions)):
                                try:
                                    for criterion_id, criterion_values in submissions[i]['rubric_assessment'].items():
                                        learning_outcome_ids = []
                                        print(criterion_id, criterion_values)
                                        assignment_mapping_learning_outcomes = Assignment_Mapping.objects(criterion_id=criterion_id)
                                        for assignment_mapping_learning_outcome in assignment_mapping_learning_outcomes:
                                            learning_outcome_ids.append(Learning_Outcome.index(assignment_mapping_learning_outcome.id))
                                        grade = Grade(str(submissions[i]['user_id']),
                                            learning_outcome_ids,
                                            float(criterion_values['points'])).save()
                                except Exception as error:
                                    print("Error: ", error)
                            return "Finished"
            else:
                print('Invalid or missing arguments parsed')
                return redirect(url_for('retreive_rubric_assessment'))

@application.route('/subjects', methods=['GET', 'POST'])
@login_required
def subjects():
    if(request.method == 'GET'):
        subjects = json.loads(Subject.read())
        learning_outcomes = json.loads(Learning_Outcome.read())
        return render_template('subjects.html',
                               subjects=subjects,
                               learning_outcomes=learning_outcomes)
    elif(request.method == 'POST'):
        try:
            subject_code = request.form['subject_code_field']
            subject_name = request.form['subject_name_field']
            subject_description = request.form['subject_description_field']
            learning_outcome_ids = request.form.getlist('subject_learning_outcomes_field[]')
        except Exception as error:
            raise error

        subject_learning_outcomes = []
        for each_learning_outcome_id in learning_outcome_ids:
            subject_learning_outcomes.append(Learning_Outcome.index(each_learning_outcome_id))

        subject = Subject(
                          subject_code,
                          subject_name, 
                          subject_description,
                          subject_learning_outcomes
                         ).save()
        return subject.to_json()
    else:
        return abort(405)

@application.route('/learning_outcomes', methods=['GET', 'POST'])
@login_required
def learning_outcomes():
    if(request.method == 'GET'):
        learning_outcomes = json.loads(Learning_Outcome.read())
        return render_template('learning_outcomes.html', 
                               learning_outcomes=learning_outcomes)
    elif(request.method == 'POST'):
        try:
            learning_outcome_name = request.form['learning_outcome_name_field']
            learning_outcome_description = request.form['learning_outcome_description_field']
        except Exception as error:
            raise error
        try:
            learning_outcome = Learning_Outcome(
                             learning_outcome_name,
                             learning_outcome_description
                            ).save()
            return learning_outcome.to_json()
        except Exception as error:
            return abort(500)
    else:
        return abort(405)

@application.route('/criterion', methods=['GET', 'POST'])
@login_required
def criterion():
    if(request.method == 'GET'):
        criterion = json.loads(Criterion.read())
        learning_outcomes = json.loads(Learning_Outcome.read())
        return render_template('criterion.html',
                              criterion=criterion,
                              learning_outcomes=learning_outcomes)
    elif(request.method == 'POST'):
        try:
            criterion_name = request.form['criterion_name_field']
            criterion_description = request.form['criterion_description_field']
            criterion_points = request.form['criterion_points_field']
            criterion_learning_outcomes = request.form.getlist('criterion_learning_outcomes_field[]')
        except Exception as error:
            raise error

        try:
            criterion = Criterion(criterion_name=criterion_name,
                                  criterion_description=criterion_description,
                                  criterion_points=criterion_points,
                                  criterion_learning_outcomes=criterion_learning_outcomes).save()
            return "Success"
        except Exception as error:
            raise error

@application.route('/rubrics', methods=['GET', 'POST'])
@login_required
def rubrics():
    if(request.method == 'GET'):
        return render_template('rubrics.html')
    else:
        try:
            #Is it safer to convert to int first to validate?
            course_id = str(request.values.get('course_id'))
        except Exception as error:
            raise error
        else:
            rubrics = canvas_API_request("https://coderacademy.instructure.com/api/v1/courses/{0}/rubrics".format(course_id), request_parameters={'course_id':course_id})
            #How should you handle canvas_API_request returning error?
            #json.loads(rubrics)
            #if error not in json_data?
            return render_template(
                'rubrics.html',
                rubrics=json.loads(rubrics.text), 
                course_id=course_id
            )

@application.route('/map_rubric/<rubric_id>', methods=['GET', 'POST'])
@login_required
def map_rubric(rubric_id):
    if(request.method == 'GET'):
        try:
            course_id = str(request.values.get('course_id'))
            rubric_id = str(rubric_id)
            print("Course_ID: " + course_id + ", Rubric_ID: " + rubric_id)
        except Exception as error:
            raise error
        else:
            """
            
            cription: "(Optional) If 'full' is included in the 'style' parameter, returned assessments will have their full details contained in their data hash. 
            If the user does not request a style, this key will be absent.",
            #           "type": "array",
            #           "items": { "type": "object" }
            #         }
            """
            #https://coderacademy.instructure.com/api/v1/courses/144/rubrics/45?include[]=assessments
            request_url = 'https://coderacademy.instructure.com/api/v1/courses/{0}/rubrics/{1}'.format(course_id, rubric_id)
            request_parameters = {
                        'include[]': 'assessments',
                        'style': 'full'
                    }
            print(request_url)
            try:
                rubric_data = canvas_API_request(request_url, request_parameters=request_parameters)
                criteria = rubric_data.json()
                print(criteria)
            except Exception as error:
                raise error
            else:
                #Generate dictionary of rubric_data criterion. ID and Name
                learning_outcomes = json.loads(Learning_Outcome.read())
                return render_template(
                        'map_rubric.html',
                        criteria=criteria,
                        learning_outcomes=learning_outcomes
                        )
    else:
        pass

@application.route('/map_rubric_assessment', methods=['GET', 'POST'])
@login_required
def map_rubric_assessment():
    if(request.method == 'GET'):
        learning_outcomes = json.loads(Learning_Outcome.read())
        
    elif(request.method == 'POST'):
        pass

@application.route('/map_criterion', methods=['POST'])
@login_required
def map_criterion():
    if(request.method == 'POST'):
        try:
            learning_outcome_list = request.form.getlist('subject_learning_outcomes_field[]')
            criterion_id = request.form['criterion_id']
        except Exception as error:
            raise error
        else:
            selected_learning_outcomes = []
            for learning_outcome_id in learning_outcome_list:
                learning_outcome = Learning_Outcome.index(learning_outcome_id)
                selected_learning_outcomes.append(learning_outcome)
            new_assignment_mapping = Assignment_Mapping(criterion_id, selected_learning_outcomes).save()
        return "Success"

def _build_cors_preflight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add('Access-Control-Allow-Headers', "*")
    response.headers.add('Access-Control-Allow-Methods', "*")
    return response

def _corsify_response(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

@application.route('/map_rubric_criterion', methods=['POST', 'OPTIONS'])
@login_required
def map_rubric_criterion():
    if(request.method == "OPTIONS"):
        return _build_cors_preflight_response()
    elif(request.method == "POST"):
        return _corsify_response(make_response("It Worked"))
        print(request.get_data())

@application.route('/assessments', methods=['GET', 'POST'])
@login_required
def assessments():
    if(request.method == 'GET'):
        assessments = json.loads(Assessment.read())
        return render_template('assessments.html', 
                               assessments = assessments)
    else:
        #Create new assessment.
        pass

#TODO: Refactor with new rubric mapping workflow.
def map_rubric_data(submission_data):
    grades = {}
    assignment_mappings = json.loads(Assignment_Mapping.read())
    for each_submission_item in submission_data:
        try:
            submission_ID = each_submission_item['id']
            student_ID = each_submission_item['user_id']
            submission_assignment_ID = each_submission_item['assignment_id']
            submission_rubric_assessment = each_submission_item['rubric_assessment'] 
            best_fit_student = canvas_API_request('https://coderacademy.instructure.com/api/v1/users/{0}'.format(student_ID))
            student_name = json.loads(best_fit_student.text)['name']
        except Exception as error:
            print("This student does not have a rubric_assessment")
            pass
        else:
            for each, value in submission_rubric_assessment.items():
                print(each, value)
                if(each == Assignment_Mapping.objects(criterion_id=each)):
                    print("Mapping Found")

'''
submission = submission_object(
        submission_ID, 
        submission_assignment_ID,
        submission_rubric_assessment
        )
submission_grades = []
for each_criteria in submission.criteria:
    try:
        learning_outcome = Learning_Outcome(int(each_criteria.id),
                                            float(each_criteria.points)).save()
    except Exception as error:
        #Some points are marked blank and cannot be converted. 
        pass
    else:
        submission_grades.append(learning_outcome)
        assessment = Rubric_Assessment.create(
                each_submission_item['user_id'],
                Assessment.objects(assessment_id=667),
                submission_grades
                ).save()
learning_outcome_count = 0
grade_total = 0
for each_learning_outcome in assessment.grades:
    learning_outcome_count = learning_outcome_count + 1
    grade_total = grade_total + 1
    if(grade_total == 15):
        print(grade_total)
    if(grade_total == 36):
        print(grade_total)
'''
class submission_object():
    def __init__(self, submission_ID, submission_assessment_ID,
                 submission_rubric_assessment):
        self.criteria = []
        self.id = submission_ID
        self.assessment_ID = submission_assessment_ID
        for key, value in submission_rubric_assessment.items():
            try:
                points = value['points']
                comments = value['comments']
            except KeyError as error:
                pass
            except Exception as error:
                raise error
            else:
                criterion_object = criterion(key, points, comments)
                self.criteria.append(criterion_object)

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
                try:
                    Hubspot_Webhook.create(json_data)
                except Exception as error:
                    pass
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
        course_ID = str(request_arguments['course_id'])
        section_ID = str(request_arguments['section_id'])
        user_ID = str(request_arguments['user_id'])
    except Exception as error:
        print(error)
        return abort(500)
    else:
        user_enrollment_request = enroll_canvas_student(user_ID, course_ID, section_ID)
        return user_enrollment_request.text

@application.route('/test', methods=['GET'])
def testing():
    test_request = canvas_API_request('https://coderacademy.instructure.com/api/v1/sections/sis_section_id:GenTech-19-01-Brisbane/enrollments')
    return test_request.text

#TODO: File upload uri with student
#url https://coderacademy/
#uri /users/:id
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

@application.route('/uploads/<file_name>')
def uploaded_file(file_name):
    return send_from_directory(app.config['UPLOAD_FOLDER'], file_name)

#Opens the YAML file at the specified directory and returns the scriptable YAML object.
def get_config(_dir):
    '''
    Arguments
    ---------
    _dir(String):
        Takes a directory method argument used to load configuration.
    Returns
    -------
    file_content:
        Reads the file specified by the _dir string and returns the contents
        using yaml.load(). Alternatively you could use yaml.safe_load().
    '''
    
    file_content = None

    #Checks whether the _dir method argument is a string. isinstance() supports DataTypes that inherit the String base class.
    assert isinstance(_dir, str)
    
    #Check if the directory method argument exists in the current filesystem.
    if os.path.exists(_dir):
        with open(_dir, 'r') as config_file:
            try:
                print('config accessed and read')
                #Load the configuration into a scriptable object.
                file_content = yaml.load(config_file)
            except IOError as error:
                raise error
                sys.exit(0)
            except EOFError as error:
                raise error
                sys.exit(0)
            except ImportError as error:
                print("YAML module could not be imported, please ensure that YAML module has been installed and is in the requirements.txt file")
            except Exception as error:
                raise error
            if(file_content != None):
                return file_content
            else:
                print("Could not load configuration from file but no errors were thrown")
    else:
        print('_dir method argument is not a valid directory in the current filesystem')

def google_request(spreadsheet_ID, range_name, scope):
    '''
    Arguments
    ---------
    spreadsheet_ID(String):
        Takes a string agrument that represents the google spreadsheet
        identifier.
    range_name(String):
        Take a string argument that represents the google sheet ranges to
        retreive data from. Format for the string is as follows:
            '<sheet_name>!<start_range>:<end_range>'
    scope(Google)
    '''
    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', scope)
        creds = tools.run_flow(flow, store)
    service = build('sheets', 'v4', http=creds.authorize(Http()))

    result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_ID,
                                                range=range_name).execute()
    sheet_data = result.get('values', [])
    
    if not sheet_data:
        sys.exit()
    else:
        return sheet_data

if __name__ == "__main__":
    main()
