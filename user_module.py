from flask_login import UserMixin
import mongo_model

class User(UserMixin):
    is_authenticated = False
    is_active = False
    is_anonymous = False

    def __init__(self, name, id):
        self.name = name
        self.id = id
        #authenticate(username, password)
    def load_user_details(self, user_details):
        pass
    def authenticate(username, password):
        user_details = mongo_model.get_user(username, password)
        if(user_details != None):
            user = User(user_details['username'], user_details['_id'])
            user.id = user_details['_id']
            user.is_authenticated = True
            return user
        else:
            print("No user found")
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
        return str(self.id).decode("utf-8")

    def get(user_id):
        #Return MongoDB user from db
        user_details = mongo_model.get_user_by_id(user_id)
        if(user_details != None):
            return user_details

