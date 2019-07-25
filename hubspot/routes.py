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
