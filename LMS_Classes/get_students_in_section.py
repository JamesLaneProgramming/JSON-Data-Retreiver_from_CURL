def get_students_in_section(canvas_bearer_token, course_id, section_id):
    students = []

    pagination_level = 200
    domain = 'https://coderacademy.instructure.com'
    API_request = '/api/v1/courses/{0}/sections'.format(course_id)
    payload = {'per_page':pagination_level, 
               'include[]': 'students'
              }
    headers = {'Authorization' : 'Bearer {0}'.format(canvas_bearer_token)}
    print("Requesting {0} endpoint".format(domain + API_request))
    response = requests.get(
                            domain + API_request,
                            params=payload,
                            headers=headers
                           )
    #Converts the request into text format
    response = response.text
    #Converts the response text into JSON
    response = json.loads(response)
    #section is an dictionary that contains information about the section.
    #Contains a field for students
    for section in response:
        #filters the sections by name
        if section['id'] == section_id:
            print(section['id'])
            #student is a dictionary of student data.
            #Check if section['students'] = null
            for enrolled_student in section['students']:
                print(enrolled_student['name'])
    print("Found {0} students in section: {1}".format(len(students),
                                                      section_id))
    return students
