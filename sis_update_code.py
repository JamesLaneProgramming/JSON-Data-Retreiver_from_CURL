'''
cell_range = selected_sheet['C2': 'C96']
for each_row in cell_range:
    for cell in each_row:
        student_email = cell.value
        student_number = (student_email).split('@')[0
        user_id = json.loads(search_students(student_email).text)['id']
        sis_id = student_numbe
        #GET USERS LOGIN ID.
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
                                                request_parameters={'login[sis_user_id]':sis_id},
                                                request_method = 'PUT'
                                               )
        return user_login_details.text
'''
