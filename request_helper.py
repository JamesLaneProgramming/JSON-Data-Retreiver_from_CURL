from flask import request, url_for, redirect
from werkzeug.security import safe_str_cmp
import hashlib
from urllib.parse import urlparse, urljoin
'''
Handle request Exceptions.
try:
    #request
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
    return #response
'''

def generate_cookie_signature(cookie):
    #https://stackoverflow.com/questions/22463939/demystify-flask-app-secret-ke://stackoverflow.com/questions/22463939/demystify-flask-app-secret-key
    try:
        cookie_bytes = str(cookie).encode('utf8')
        application_secret_key = str(application.config['SECRET_KEY'])
    except Exception as error:
        print(error)
    else:
        cookie_signature = sha256(cookie_bytes + application_secret_key).hexdigest()
        return cookie_signature

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

def _build_cors_preflight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add('Access-Control-Allow-Headers', "*")
    response.headers.add('Access-Control-Allow-Methods', "*")
    return response

def _corsify_response(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response
