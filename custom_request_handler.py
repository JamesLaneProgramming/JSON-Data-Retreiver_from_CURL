'''
try:
    #request
except ConnectionError as error:
    print("DNS Failure, Refused Connection, etc.")
    return abort(500)
except requests.exceptions.Timeout as error:
    print("Request timed out, please try again")
    return abort(500)
except requests.exceptions.TooManyRedirects as error:
    print("Too many redirects.", error)
    return abort(500)
except Exception as error:
    print(error)
    return abort(500)
else:
    return #response
'''
