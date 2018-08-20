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

def generate_emails(names, company_email_suffix):
    '''
    DOCSTRING

    Arguments
    ---------
    names(Array):
        An array of names to be used in the email generation
    company_email_suffix(String):
        The suffix used by the company to generate emails. E.G.
        companyname.edu.au
    Returns
    -------
    generated_emails(Array):
        An array of generated emails based on names(Argument) and
        company_name(Argument)
    '''
    generated_emails = []
    for each in names:
        first_name = each.split(' ')[0]
        last_name = each.split(' ')[1]
        new_email = "{0}.{1}@{2}.com".format(first_name,last_name,
                                             company_email_suffix)
        generated_emails.append(new_email)
        print("Generated Email: " + new_email)
    return generated_emails
if __name__ == '__main__':
    main()
else:
    print("This module is imported")
