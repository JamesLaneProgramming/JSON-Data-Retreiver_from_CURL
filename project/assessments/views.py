@application.route('/assessments', methods=['GET', 'POST'])
@login_required
def assessments():
    if(request.method == 'GET'):
        assessments = json.loads(Assessment.read())
        return render_template('assessments.html',
                               assessments = assessments)
    else:
        #Create new assessment.
        pass
