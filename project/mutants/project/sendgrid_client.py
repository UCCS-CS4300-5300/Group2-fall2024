
from inspect import signature as _mutmut_signature

def _mutmut_trampoline(orig, mutants, *args, **kwargs):
    import os
    mutant_under_test = os.environ['MUTANT_UNDER_TEST']
    if mutant_under_test == 'fail':
        from mutmut.__main__ import MutmutProgrammaticFailException
        raise MutmutProgrammaticFailException('Failed programmatically')      
    elif mutant_under_test == 'stats':
        from mutmut.__main__ import record_trampoline_hit
        record_trampoline_hit(orig.__module__ + '.' + orig.__name__)
        result = orig(*args, **kwargs)
        return result  # for the yield case
    prefix = orig.__module__ + '.' + orig.__name__ + '__mutmut_'
    if not mutant_under_test.startswith(prefix):
        result = orig(*args, **kwargs)
        return result  # for the yield case
    mutant_name = mutant_under_test.rpartition('.')[-1]
    result = mutants[mutant_name](*args, **kwargs)
    return result


from inspect import signature as _mutmut_signature

def _mutmut_yield_from_trampoline(orig, mutants, *args, **kwargs):
    import os
    mutant_under_test = os.environ['MUTANT_UNDER_TEST']
    if mutant_under_test == 'fail':
        from mutmut.__main__ import MutmutProgrammaticFailException
        raise MutmutProgrammaticFailException('Failed programmatically')      
    elif mutant_under_test == 'stats':
        from mutmut.__main__ import record_trampoline_hit
        record_trampoline_hit(orig.__module__ + '.' + orig.__name__)
        result = yield from orig(*args, **kwargs)
        return result  # for the yield case
    prefix = orig.__module__ + '.' + orig.__name__ + '__mutmut_'
    if not mutant_under_test.startswith(prefix):
        result = yield from orig(*args, **kwargs)
        return result  # for the yield case
    mutant_name = mutant_under_test.rpartition('.')[-1]
    result = yield from mutants[mutant_name](*args, **kwargs)
    return result


import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def x_send_email__mutmut_orig(subject, to_email, content):
    message = Mail(
        from_email='gameplanuccs@gmail.com',
        to_emails=to_email,
        subject=subject,
        html_content=content
    )
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        # Explicitly return a tuple with three values
        return (response.status_code, response.body, response.headers)
    except Exception as e:
        return (None, str(e), None)

def x_send_email__mutmut_1(subject, to_email, content):
    message = Mail(
        from_email='XXgameplanuccs@gmail.comXX',
        to_emails=to_email,
        subject=subject,
        html_content=content
    )
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        # Explicitly return a tuple with three values
        return (response.status_code, response.body, response.headers)
    except Exception as e:
        return (None, str(e), None)

def x_send_email__mutmut_2(subject, to_email, content):
    message = Mail(
        from_email='gameplanuccs@gmail.com',
        to_emails=None,
        subject=subject,
        html_content=content
    )
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        # Explicitly return a tuple with three values
        return (response.status_code, response.body, response.headers)
    except Exception as e:
        return (None, str(e), None)

def x_send_email__mutmut_3(subject, to_email, content):
    message = Mail(
        from_email='gameplanuccs@gmail.com',
        to_emails=to_email,
        subject=None,
        html_content=content
    )
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        # Explicitly return a tuple with three values
        return (response.status_code, response.body, response.headers)
    except Exception as e:
        return (None, str(e), None)

def x_send_email__mutmut_4(subject, to_email, content):
    message = Mail(
        from_email='gameplanuccs@gmail.com',
        to_emails=to_email,
        subject=subject,
        html_content=None
    )
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        # Explicitly return a tuple with three values
        return (response.status_code, response.body, response.headers)
    except Exception as e:
        return (None, str(e), None)

def x_send_email__mutmut_5(subject, to_email, content):
    message = Mail(
        to_emails=to_email,
        subject=subject,
        html_content=content
    )
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        # Explicitly return a tuple with three values
        return (response.status_code, response.body, response.headers)
    except Exception as e:
        return (None, str(e), None)

def x_send_email__mutmut_6(subject, to_email, content):
    message = Mail(
        from_email='gameplanuccs@gmail.com',
        subject=subject,
        html_content=content
    )
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        # Explicitly return a tuple with three values
        return (response.status_code, response.body, response.headers)
    except Exception as e:
        return (None, str(e), None)

def x_send_email__mutmut_7(subject, to_email, content):
    message = Mail(
        from_email='gameplanuccs@gmail.com',
        to_emails=to_email,
        html_content=content
    )
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        # Explicitly return a tuple with three values
        return (response.status_code, response.body, response.headers)
    except Exception as e:
        return (None, str(e), None)

def x_send_email__mutmut_8(subject, to_email, content):
    message = Mail(
        from_email='gameplanuccs@gmail.com',
        to_emails=to_email,
        subject=subject,
    )
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        # Explicitly return a tuple with three values
        return (response.status_code, response.body, response.headers)
    except Exception as e:
        return (None, str(e), None)

def x_send_email__mutmut_9(subject, to_email, content):
    message = None
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        # Explicitly return a tuple with three values
        return (response.status_code, response.body, response.headers)
    except Exception as e:
        return (None, str(e), None)

def x_send_email__mutmut_10(subject, to_email, content):
    message = Mail(
        from_email='gameplanuccs@gmail.com',
        to_emails=to_email,
        subject=subject,
        html_content=content
    )
    try:
        sg = SendGridAPIClient(os.environ.get('XXSENDGRID_API_KEYXX'))
        response = sg.send(message)
        # Explicitly return a tuple with three values
        return (response.status_code, response.body, response.headers)
    except Exception as e:
        return (None, str(e), None)

def x_send_email__mutmut_11(subject, to_email, content):
    message = Mail(
        from_email='gameplanuccs@gmail.com',
        to_emails=to_email,
        subject=subject,
        html_content=content
    )
    try:
        sg = None
        response = sg.send(message)
        # Explicitly return a tuple with three values
        return (response.status_code, response.body, response.headers)
    except Exception as e:
        return (None, str(e), None)

def x_send_email__mutmut_12(subject, to_email, content):
    message = Mail(
        from_email='gameplanuccs@gmail.com',
        to_emails=to_email,
        subject=subject,
        html_content=content
    )
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(None)
        # Explicitly return a tuple with three values
        return (response.status_code, response.body, response.headers)
    except Exception as e:
        return (None, str(e), None)

def x_send_email__mutmut_13(subject, to_email, content):
    message = Mail(
        from_email='gameplanuccs@gmail.com',
        to_emails=to_email,
        subject=subject,
        html_content=content
    )
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = None
        # Explicitly return a tuple with three values
        return (response.status_code, response.body, response.headers)
    except Exception as e:
        return (None, str(e), None)

def x_send_email__mutmut_14(subject, to_email, content):
    message = Mail(
        from_email='gameplanuccs@gmail.com',
        to_emails=to_email,
        subject=subject,
        html_content=content
    )
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        # Explicitly return a tuple with three values
        return (response.status_code, response.body, response.headers)
    except Exception as e:
        return (None, str(None), None)

x_send_email__mutmut_mutants = {
'x_send_email__mutmut_1': x_send_email__mutmut_1, 
    'x_send_email__mutmut_2': x_send_email__mutmut_2, 
    'x_send_email__mutmut_3': x_send_email__mutmut_3, 
    'x_send_email__mutmut_4': x_send_email__mutmut_4, 
    'x_send_email__mutmut_5': x_send_email__mutmut_5, 
    'x_send_email__mutmut_6': x_send_email__mutmut_6, 
    'x_send_email__mutmut_7': x_send_email__mutmut_7, 
    'x_send_email__mutmut_8': x_send_email__mutmut_8, 
    'x_send_email__mutmut_9': x_send_email__mutmut_9, 
    'x_send_email__mutmut_10': x_send_email__mutmut_10, 
    'x_send_email__mutmut_11': x_send_email__mutmut_11, 
    'x_send_email__mutmut_12': x_send_email__mutmut_12, 
    'x_send_email__mutmut_13': x_send_email__mutmut_13, 
    'x_send_email__mutmut_14': x_send_email__mutmut_14
}

def send_email(*args, **kwargs):
    result = _mutmut_trampoline(x_send_email__mutmut_orig, x_send_email__mutmut_mutants, *args, **kwargs)
    return result 

send_email.__signature__ = _mutmut_signature(x_send_email__mutmut_orig)
x_send_email__mutmut_orig.__name__ = 'x_send_email'


