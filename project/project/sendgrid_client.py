import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_email(subject, to_email, content):
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