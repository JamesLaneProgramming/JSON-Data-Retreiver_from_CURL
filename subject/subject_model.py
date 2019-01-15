from mongoengine import Document, StringField, ListField, ReferenceField

class Subject(Document):
    subject_name = StringField(required=True)
    subject_description = Stringfield()
    learning_outcomes = ListField(ReferenceField('learning_outcome'))

    def create(subject_name, subject_description, learning_outcomes):
        subject = Subject(
                          subject_name, 
                          subject_description,
                          learning_outcomes
                         )
        return subject
