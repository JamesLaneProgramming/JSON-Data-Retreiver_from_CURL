@application.route('/check_overdue', methods=['GET'])
def check_overdue():
    check_overdue_assignments()

def check_overdue_assignments():
    print("Background Scheduler Working")
    for enrollment in Enrollment.objects():
        user_assignment_data(enrollment.canvas_course_id, enrollment.canvas_user_id)
