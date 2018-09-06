class User():
    def is_authenticated():
        '''
        Docstring: is_authenticated() checks whether the user's credetials
        are valid. is_authenticated() must equate to True as a criteria of
        login_required().
        Returns
        -------
        is_authenticated(Bool):
            Returns True if the user has provided valid credentials.
            Returns False if the user's credentials are invalid.
        '''
        pass
    def is_active():
        '''
        Docstring: is_active checks whether the user's account has special
        restrictions in place. For example, if the account has been suspended.
        Returns
        -------
        is_active(Bool):
            Returns True if the user's account is active(No restrictions in
            place).
            Returns False if the user's account has been
            deactivated(Restrictions in place).
        '''
        pass
    def is_anonymous():
        '''
        Docstring: If particular functionality does not require an
        authenticated User, is_anonymous() may be useful.
        Returns
        -------
        is_anonymous(Bool):
            Returns True if the user is an anonymous user.
            Returns False if the user is authenticated.
        '''
        pass
    def get_id():
        '''
        Docstring
        ---------
        get_id() returns the Unicode ID of the User.
        Returns
        -------
        ID(Unicode String):
            The ID associated with the User account.
        '''
        pass
