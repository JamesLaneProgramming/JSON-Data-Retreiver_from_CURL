from flask_login import UserMixin
import mongo_model

class User():
    authenticated = False
    active = False
    anonymous = False
    id = None

    def is_authenticated(self):
        return authenticated
    def is_active(self):
        return active
    def is_anonymous(self):
        return anonymous
    def __init__(self):
        pass
        #authenticate(username, password)
    def load_user_details(self, user_details):
        self.id = user_details['_id']
    def authenticate(self, username, password):
        user_details = mongo_model.get_user(username, password)
        if(user_details != None):
            self.load_user_details(user_details)
            self.authenticated = True
            return self
        else:
            print("No user found")
            return None
    '''
    Docstring: is_authenticated() checks whether the user's credetials
    are valid. is_authenticated() must equate to True as a criteria of
    login_required().
    Returns
    -------
    is_authenticated(Bool):
        Returns True if the user has provided valid credentials.
        Returns False if the user's credentials are invalid.

    Docstring: is_active checks whether the user's account has special
    restrictions in place. For example, if the account has been suspended.
    Returns
    -------
    is_active(Bool):
        Returns True if the user's account is active(No restrictions in
        place).
        Returns False if the user's account has been
        deactivated(Restrictions in place).
    
    Docstring: If particular functionality does not require an
    authenticated User, is_anonymous() may be useful.
    Returns
    -------
    is_anonymous(Bool):
        Returns True if the user is an anonymous user.
        Returns False if the user is authenticated.
    '''
    def get_id(self):
        '''
        Docstring
        ---------
        get_id() returns the Unicode ID of the User.
        Returns
        -------
        ID(Unicode String):
            The ID associated with the User account.
        '''
        return str(self.id)

    def get(user_id):
        #Return MongoDB user from db
        user_details = mongo_model.get_user_by_id(user_id)
        if(user_details != None):
            user = User()
            user.load_user_details(user_details)
            #Is the following line dangerous????
            user.authenticated = True
            return user
        else:
            print("No user with that id found")
    def create(username, password):
        user_details = mongo_model.create_user(username, password)
        if(user_details != None):
            user = User()
            user.load_user_details(user_details)
            return user
