@application.route('/upload_provisioning_csv', methods=['GET', 'POST'])
@login_required
def upload_provisioning_csv():
    if(request.method == 'GET'):
        return render_template('enrollment_csv_uploader.html')
    if(request.method == 'POST'):
        # https://openpyxl.readthedocs.io/en/stable/
        if 'File' not in request.files:
            flash("No file uploaded")
            return redirect(url_for(update_sis_id))
        uploaded_file = request.files['File']
        if(uploaded_file.filename == ""):
            flask("No selected file")
            return redirect(url_for(update_sis_id))
        if uploaded_file:
            data_stream = pandas.read_csv(uploaded_file.stream)
            for i in range(0, len(data_stream.index) - 1):
                try:
                    canvas_course_id = data_stream['canvas_course_id'][i]
                    canvas_user_id = data_stream['canvas_user_id'][i]
                    #Add base_role_type to distinguish between student and
                    #teacher
                except Exception as error:
                    raise error
                else:
                    if(Enrollment.objects(canvas_course_id=canvas_course_id, canvas_user_id=canvas_user_id)):
                        pass
                    else:
                        new_enrollment = Enrollment(int(canvas_course_id), int(canvas_user_id))
                        new_enrollment.save()
            return "Success"

#Needs development
@application.route('/create_provisioning_report', methods=['GET', 'POST'])
@login_required
def create_provisioning_report():
    if(request.method == 'GET'):
        domain = 'https://coderacademy.instructure.com'
        endpoint = '/api/v1/accounts/1/reports/users/provisioning_csv'
        request_parameters = {
            'parameters[enrollments]': 'true'
        }
        provisioning_report = canvas_API_request(domain + endpoint, request_parameters=request_parameters, method='POST')
        return provisioning_report.text

@application.route('/uploads/<file_name>')
def uploaded_file(file_name):
    return send_from_directory(app.config['UPLOAD_FOLDER'], file_name)

@application.route('/mail')
def send_simple_message():
    mail_request = requests.post(
        "https://api.mailgun.net/v3/sandboxbd63b75742724ec48a7ff11a143eae19.mailgun.org/messages",
        auth=("api", "412c248f4efdd95f34e8b541726e1b7e-29b7488f-07e4e4c0"),
        data={"from": "Excited User <postmaster@sandboxbd63b75742724ec48a7ff11a143eae19.mailgun.org>",
            "to": ["james.lane@redhilleducation.com", "postmaster@sandboxbd63b75742724ec48a7ff11a143eae19.mailgun.org"],
            "subject": "Hello",
            "text": "Testing some Mailgun awesomness!"})
    return mail_request.text
