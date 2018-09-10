#!usr/bin/python
from __future__ import print_function
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


def get_google_credentials():
    '''
    Docstring
    ---------
    Loads the token.json file from storage and retrieves credentials for use in
    google requests. If the credentials are invalid or cannot be found locally,
    a flow object will be created to regenerate the credentials.

    Returns
    -------
    creds:
        Returns credentials used for google requests.
    '''
    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', scope)
        creds = tools.run_flow(flow, store)
    return creds
def sheet_request(spreadsheet_ID, range_name):
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
    #Gets google credentials for use in service object.
    creds = get_google_credentials()
    #Using credentials, create a build for the given scope
    try:
        service = build('sheets', 'v4', http=creds.authorize(Http()))
    except Exception as e:
        raise e
    #Request data from service given spreadsheet_ID and range_name
    result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_ID,
                                                range=range_name).execute()
    #Extract values from request
    sheet_data = result.get('values', [])
    #Exit if there are no values available.
    if not sheet_data:
        sys.exit()
    else:
        return sheet_data
