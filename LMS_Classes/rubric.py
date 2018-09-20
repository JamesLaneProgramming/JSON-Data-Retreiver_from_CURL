import json
class Rubric():
    ''' 
    Docstring
    ---------
    A Rubric object.
    '''
    #Class attributes will not be exported as they are not instance attributes.
    RUBRIC_TYPES = ["NONE", "VET", "HIGHER_ED"]
    def __init__(self, name = None, rubric_type = None):
        '''
        Docstring
        ---------
        __init__ method is used to initialise a Rubric object

        Arguments
        ---------
        rubric_name(String):
            pass
        rubric_type(String/RUBRIC_TYPE):
            rubric_type can be parsed as an argument in either format:
                String:         A string representation can be parsed.
                                value matches an element in RUBRIC_TYPES, that
                                element will be used.
                RUBRIC_TYPE:    The RUBRIC_TYPE can be passed as an object.
        '''
        #Default values for optional arguments template
        #variable = <default_value> if <argument> is None else <argument>
        self.name = "Default Rubric" if name is None else name
        self.rubric_type = Rubric.RUBRIC_TYPES[0] if rubric_type is None else rubric_type
        self.criteria = []
        if(self.rubric_type == Rubric.RUBRIC_TYPES[1]):
            #VET
            self.criteria.append(self.add_criterion("COMPETENT"))
            self.criteria.append(self.add_criterion("NOT YET COMPETENT"))
        elif(self.rubric_type == Rubric.RUBRIC_TYPES[2]):
            self.add_criterion("FAIL")
            self.add_criterion("PASS")
            self.add_criterion("CREDIT")
            self.add_criterion("DESTINCTION")
            self.add_criterion("HIGH DESTINCTION")
        else:
            self.add_criterion("Add Criterion")
    def get_rubric_name(self):
        return self.name
    def set_rubric_name(self, value):
        #Check if string
        self.name = value
    def get_rubric_type(self):
        return self.rubric_type
    def add_criterion(self, name = "Criterion"):
        new_criterion = Criterion(name)
        self.criteria.append(new_criterion)
    def export_rubric(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)
    def import_rubric(self, rubric_data):
        #Need a way to create a rubric object from json data
        self.__init__()
    #Create custom __dict__ or __repr__ methods to manage json representation.
class Criterion():
    def __init__(self, name):
        self.name = name
def Main():
    my_rubric = Rubric(name = "first_rubric")
    second_rubric = Rubric(rubric_type = "VET")
    print(second_rubric.export_rubric())
if __name__ == '__main__':
    Main()
