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
import os, sys
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
from urllib.parse import urlparse, urljoin
from flask import Flask, flash, render_template, request, abort, redirect, \
    url_for, send_from_directory, copy_current_request_context, \
    has_request_context
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from flask_mongoengine import MongoEngine
#Should not import canvas_API_request function. Instead create an endpoint for specific action.
from hubspot_webhooks.hubspot_webhook_model import Hubspot_Webhook
from assessments.assessment_model import Criterion
from assignment_mapping.assignment_mapping_model import Assignment_Mapping
from learning_outcomes.learning_outcome_model import Learning_Outcome
from subjects.subject_model import Subject
from overdue_assignments.overdue_assignment_model import Overdue_Assignment
from enrollments.enrollment_model import Enrollment
from grades.grade_model import Grade
from subject_grades.subject_grade_model import Subject_Grade
from hubspot_requests.hubspot_request_model import Hubspot_Request

application = Flask(__name__, template_folder='templates')
CORS(application)
#Cross origin requests can be enabled for resources using the @cross_origin decorator method

#Set application secret key to secure against CSRF
application.config['SECRET_KEY'] = os.environ.get('Application_Secret_Key').encode('utf-8')
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

@application.route('/')
def home():
    return render_template('home.html')

from project.users.views import users_blueprint

application.register_blueprint(users_blueprint, prefix='users')
