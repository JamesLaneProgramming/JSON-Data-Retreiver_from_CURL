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
import pygal
from werkzeug import secure_filename
from openpyxl import Workbook, load_workbook
from flask import Flask, flash, render_template, request, abort, redirect, \
    url_for, make_response, send_from_directory, copy_current_request_context, \
    has_request_context
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_cors import CORS
from request_helper import get_redirect_target, redirect_back, _build_cors_preflight_response, _corsify_response
from apscheduler.schedulers.background import BackgroundScheduler
from flask_mongoengine import MongoEngine
#Should not import canvas_API_request function. Instead create an endpoint for specific action.
from canvas.canvas_module import update_canvas_email, create_canvas_login, canvas_API_request
from canvas.canvas_module import enroll_canvas_student, extract_rubric_data, search_students
from users.user_model import User
from hubspot_webhooks.hubspot_webhook_model import Hubspot_Webhook
from assessments.assessment_model import Criterion
from assignment_mapping.assignment_mapping_model import Assignment_Mapping
from learning_outcomes.learning_outcome_model import Learning_Outcome
from subjects.subject_model import Subject
from overdue_assignments.overdue_assignment_model import Overdue_Assignment
from enrollments.enrollment_model import Enrollment
from grades.grade_model import Grade
from subject_grades.subject_grade_model import Subject_Grade

from hubspot.hubspot_authentication import hubspot_blueprint, require_hubspot_signature_validation,
from canvas.canvas_module import canvas_blueprint
from users.user_authentication import user_authentication_blueprint

application = Flask(__name__, template_folder='templates')
application.register_blueprint(hubspot_authentication_blueprint, url_prefix='/hubspot/authentication')
application.register_blueprint(canvas_blueprint, url_prefix='/canvas')
application.register_blueprint(user_authentication_blueprint, prefix='/users/authentication')

#Cross origin requests can be enabled for resources using the @cross_origin decorator method
CORS(application)

#Set application secret key to secure against CSRF
application.config['SECRET_KEY'] = environ.get('Application_Secret_Key').encode('utf-8')
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
login_manager.login_view = 'users/authentication/login'
login_manager.init_app(application)

#user_loader callback used to load a user from a session ID.
@login_manager.user_loader
def load_user(user_id):
    return User.objects(pk=user_id).first()

def main():
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=check_overdue_assignments, trigger="interval", days=1)
    scheduler.start()
    application.debug = True
    port = int(os.environ.get('PORT', 5000))
    application.run(host='0.0.0.0', port=port, use_reloader=False)

@application.route('/')
def home():
    return render_template('home.html')

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

@application.route('/pygalexample/')
def pygalexample():
    try:
        graph = pygal.Bar()
        graph.title = '% Grade Graph'
        graph.x_labels = ['2011','2012','2013','2014','2015','2016']
        graph.add('Python', [15, 31, 89, 200, 356, 900])
        graph.add('Java', [15, 45, 76, 80,  91,  95])
        graph.add('C++', [5, 51, 54, 102, 150, 201])
        graph.add('All others combined!', [5, 15, 21, 55, 92, 105])
        #graph_data = graph.render_data_uri()
        #return render_template("graphing.html", graph_data = graph_data)
        return graph.render_response()
    except Exception as error:
        return(str(error))

@application.route('/student_grade_graph/<student_id>')
def student_graph_grade(student_id):
    try:
        graph = pygal.Bar()
        graph.title = '% Grade Graph'
        graph_values = []
        grade_averages = []

        for each in Grade.objects().aggregate({
            "$unwind": "$learning_outcomes"
        },
        {
            "$group": {
                "_id": "$learning_outcomes",
                "avgPoints": {
                    "$avg": "$points"
                }
            }
        }):
            print(each)

        for each in Grade.objects(user_id=student_id).only('points'):
            graph_values.append(float(each.points))
        graph.add(str(student_id), graph_values)
        #graph_data = graph.render_data_uri()
        #return render_template("graphing.html", graph_data = graph_data)
        return graph.render_response()
    except Exception as error:
        return(str(error))

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
                    return rubric_data.text
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
                                    #1 canvas user not graded, handle error
                                    print("Error: ", error)
                            return "Finished"
            else:
                print('Invalid or missing arguments parsed')
                return redirect(url_for('retreive_rubric_assessment'))

@application.route('/student_subject_grades', methods=['GET'])
@login_required
def student_subject_grades():
    if(request.method == 'GET'):
        try:
            subjects = Subject.objects().aggregate({
                '$unwind': "$learning_outcomes"
            },
            {
                '$lookup': {
                    "from": "Grade",
                    "localField": "learning_outcomes",
                    "foreignField": "learning_outcomes",
                    "as": "grades"
                }
            })
            '''
            "let": {
                "lo_id": "$learning_outcomes"
            },
            "pipeline": [{
                    "$match": {
                        "$expr": {
                            "$in": [ "$learning_outcomes", "$$lo_id._id" ]
                        }
                    }
                }
            ],
            '''
            print(list(subjects))
            '''
            for subject in subjects:
                for learning_outcome in subject.learning_outcomes:
                    subject_grade = 0
                    user_grades =
                    Grade.objects(learning_outcomes__contains=learning_outcome).aggregate([
                        {
                            $unwind: "$learning_outcomes"
                        },
                        {
                            $group: {
                                _id: { user_id: { $user_id: "$user_id"},
                                        points: { $sum: "$points"},
                            }
                        }
                    ])
                    print(grades)
                    for grade in user_grades:
                        learning_outcome_count = Grade.objects(user_id=grade.user_id, learning_outcomes__contains=learning_outcome).count()
                        learning_outcome_total = grade.sum('points')
                            if(Subject.objects(learning_outcomes__contains=learning_outcome) == subject):
                                subject_grade += grade.points
                                print('Subject Grade: ', grade.sum('points')/len(grade.learning_outcomes))
                    subject_grades = Subject_Grade(user_id=user, grade=subject_grade).save()
            '''
            return "Success"
        except Exception as error:
            print(error)
            return "Failure"

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

if __name__ == "__main__":
    main()
