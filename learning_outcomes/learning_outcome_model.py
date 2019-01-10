from mongoengine import Document, IntField, FloatField

class Learning_Outcome(Document):
    meta = {'collection': 'learning_outcomes'}
    learning_id = IntField(required=True)
    grade = FloatField(required=True)

    def set_grade(self, grade):
        self.grade = grade

