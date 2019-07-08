def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    target_url = urlparse(urljoin(request.host_url, target))
    return target_url.scheme in ('http', 'https') and \
           ref_url.netloc == target_url.netloc

def get_redirect_target():
    for target in request.values.get('next'), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return target

def redirect_back(endpoint, **values):
    target = request.args.get('next')
    if not target or not is_safe_url(target):
        target = url_for(endpoint, **values)
    return redirect(target)

def _build_cors_preflight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add('Access-Control-Allow-Headers', "*")
    response.headers.add('Access-Control-Allow-Methods', "*")
    return response

def _corsify_response(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

def generate_cookie_signature(cookie):
    #https://stackoverflow.com/questions/22463939/demystify-flask-app-secret-ke://stackoverflow.com/questions/22463939/demystify-flask-app-secret-key
    try:
        cookie_bytes = str(cookie).encode('utf8')
        application_secret_key = str(application.config['SECRET_KEY'])
    except Exception as error:
        print(error)
    else:
        cookie_signature = sha256(cookie_bytes + application_secret_key).hexdigest()
        return cookie_signature
