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
                    return rubric_data
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
