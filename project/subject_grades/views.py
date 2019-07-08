@application.route('/student_subject_grades', methods=['GET'])
@login_required
def student_subject_grades():
    if(request.method == 'GET'):
        try:
            subjects = Subject.objects().aggregate({
                    '$unwind': "$learning_outcomes"
                },
                {
                    '$lookup': {
                        "from": "Grade",
                        "let": {
                            "lo_id": "$learning_outcomes"
                        },
                        "pipeline": [{
                                "$match": {
                                    "$expr": {
                                        "$in": [ "$learning_outcomes", "$$lo_id" ]
                                    }
                                }
                        },
                        {
                            "$project": { "_id": 1 }
                        }],
                        "as": "grades"
                    }
                })
            print(list(subjects))
            '''
            for subject in subjects:
                for learning_outcome in subject.learning_outcomes:
                    subject_grade = 0
                    user_grades =
                    Grade.objects(learning_outcomes__contains=learning_outcome).aggregate([
                        {
                            $unwind: "$learning_outcomes"
                        },
                        {
                            $group: {
                                _id: { user_id: { $user_id: "$user_id"},
                                        points: { $sum: "$points"},
                            }
                        }
                    ])
                    print(grades)
                    for grade in user_grades:
                        learning_outcome_count = Grade.objects(user_id=grade.user_id, learning_outcomes__contains=learning_outcome).count()
                        learning_outcome_total = grade.sum('points')
                            if(Subject.objects(learning_outcomes__contains=learning_outcome) == subject):
                                subject_grade += grade.points
                                print('Subject Grade: ', grade.sum('points')/len(grade.learning_outcomes))
                    subject_grades = Subject_Grade(user_id=user, grade=subject_grade).save()
            '''
            return "Success"
        except Exception as error:
            print(error)
            return "Failure"

@application.route('/student_grade_graph/<student_id>')
def student_graph_grade(student_id):
    try:
        graph = pygal.Bar()
        graph.title = '% Grade Graph'
        graph_values = []
        grade_averages = []
        pipeline = {
            "$unwind": "$learning_outcomes"
        },
        {
            "$lookup": {
                "from": "$learning_outcomes",
                #Finish
            }
        }
        {
            "$group": {
                "_id": "$learning_outcomes",
                "avgPoints": {
                    "$avg": "$points"
                }
            }
        }
        for each in Grade.objects().aggregate(pipeline):
            print(each)
            try:
                print(each.avgPoints)
            except Exception:
                pass
        for each in Grade.objects(user_id=student_id).only('points'):
            graph_values.append(float(each.points))
        graph.add(str(student_id), graph_values)
        #graph_data = graph.render_data_uri()
        #return render_template("graphing.html", graph_data = graph_data)
        return graph.render_response()
    except Exception as error:
        return(str(error))
