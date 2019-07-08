@application.route('/subjects', methods=['GET', 'POST'])
@login_required
def subjects():
    if(request.method == 'GET'):
        subjects = json.loads(Subject.read())
        learning_outcomes = json.loads(Learning_Outcome.read())
        return render_template('subjects.html',
                               subjects=subjects,
                               learning_outcomes=learning_outcomes)
    elif(request.method == 'POST'):
        try:
            subject_code = request.form['subject_code_field']
            subject_name = request.form['subject_name_field']
            subject_description = request.form['subject_description_field']
            learning_outcome_ids = request.form.getlist('subject_learning_outcomes_field[]')
        except Exception as error:
            raise error

        subject_learning_outcomes = []
        for each_learning_outcome_id in learning_outcome_ids:
            subject_learning_outcomes.append(Learning_Outcome.index(each_learning_outcome_id))

        subject = Subject(
                          subject_code,
                          subject_name,
                          subject_description,
                          subject_learning_outcomes
                         ).save()
        return subject.to_json()
    else:
        return abort(405)
