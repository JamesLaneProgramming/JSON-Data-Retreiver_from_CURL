from flask import Blueprint, redirect, flash, make_response
from functools import wraps
from os import environ
import datetime
from users.user_model import User
from request_helper import get_redirect_target, redirect_back

hubspot__authentication_blueprint = Blueprint('hubspot', __name__)

'''
Routes
'''
@hubspot_authentication_blueprint.route('/')
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
        redirect_uri = url_for('request_hubspot_refresh_token', _external=True,
                               _scheme='https')
    except Exception as error:
        raise error
    return redirect('https://app.hubspot.com/oauth/authorize?client_id={0}&scope={1}&redirect_uri={2}'.format(client_id,
                                                                                                  scope,
                                                                                                  redirect_uri))

@hubspot_authentication_blueprint.route('/request_hubspot_refresh_token', methods=['GET'])
@login_required
def request_hubspot_refresh_token():
    try:
        code = str(request.args.get('code'))
        client_id = str(environ.get('hubspot_client_id'))
        client_secret = str(environ.get('hubspot_client_secret'))
        '''
        redirect_uri must match the redirect_uri used to intitiate the OAuth
        connection

        '''
        redirect_uri = url_for('request_hubspot_refresh_token', _external=True,
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
            User.set_hubspot_refresh_token(current_user.id,
                refresh_token)
            return redirect(url_for('request_hubspot_access_token'))

@hubspot_authentication_blueprint.route('/request_hubspot_access_token', methods=['GET'])
@login_required
def request_hubspot_access_token():
    try:
        client_id = str(environ.get('hubspot_client_id'))
        client_secret = str(environ.get('hubspot_client_secret'))
    except Exception as error:
        flash('client_id or client_secret environment variables cannot be found')
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
                    User.set_hubspot_access_token_expiry(current_user.id, access_token_expiry)
                    return response
            else:
                return redirect(url_for('authenticate_hubspot'))

'''
Decorators
'''
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
            return redirect(url_for('request_hubspot_access_token'))
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
                    return redirect(url_for('request_hubspot_access_token'))
                else:
                    return func(*args, **kwargs)
    return update_hubspot_access_token
