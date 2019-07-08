@application.route('/map_rubric_criterion', methods=['POST', 'OPTIONS'])
@login_required
def map_rubric_criterion():
    if(request.method == "OPTIONS"):
        return _build_cors_preflight_response()
    elif(request.method == "POST"):
        return _corsify_response(make_response("It Worked"))
        print(request.get_data())

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
