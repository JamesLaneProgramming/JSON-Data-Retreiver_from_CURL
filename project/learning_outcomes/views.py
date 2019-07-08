@application.route('/learning_outcomes', methods=['GET', 'POST'])
@login_required
def learning_outcomes():
    if(request.method == 'GET'):
        learning_outcomes = json.loads(Learning_Outcome.read())
        return render_template('learning_outcomes.html',
                               learning_outcomes=learning_outcomes)
    elif(request.method == 'POST'):
        try:
            learning_outcome_name = request.form['learning_outcome_name_field']
            learning_outcome_description = request.form['learning_outcome_description_field']
        except Exception as error:
            raise error
        try:
            learning_outcome = Learning_Outcome(
                             learning_outcome_name,
                             learning_outcome_description
                            ).save()
            return learning_outcome.to_json()
        except Exception as error:
            return abort(500)
    else:
        return abort(405)
