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
