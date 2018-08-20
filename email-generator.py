def open_file(file_DIR):
    try:
        file_Object = open(file_DIR, "r")
        generate_emails(file_Object)
        file_Object.close()
    except IOError as err:
        raise err
    except EOFError as err:
        print("No data was read, EOFError returned")
        raise err

def generate_email(name, company_email_suffix):
    '''
    DOCSTRING

    Arguments
    ---------
    name(String):
        A name to be used in the email generation
    company_email_suffix(String):
        The suffix used by the company to generate emails. E.G.
        companyname.edu.au
    Returns
    -------
    generated_email(String):
        A generated email based on name(Argument) and
        company_email_suffix(Argument)
    '''
    first_name = name.split(' ')[0]
    last_name = name.split(' ')[1]
    new_email = "{0}.{1}@{2}.com".format(first_name,last_name,
                                         company_email_suffix)
    print("Generated Email: " + new_email)
    return new_email
if __name__ == '__main__':
    main()
else:
    print("This module is imported")
