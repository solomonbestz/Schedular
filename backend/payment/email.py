from core import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
# from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives


def send_message(email_subject, email_body, user_email, html_content):
    from_email = 'Schedular'
    to_user_list = [user_email]
    msg = EmailMultiAlternatives(email_subject, email_body, from_email, to_user_list)
    msg.attach_alternative(html_content, 'text/html')
    msg.send()
    # send_mail(email_subject, mail, from_email, to_user_list)

def notify_user(email, message):
    subject = 'Notification'
    content = 'Payment Notification' 
    message = message
    html_content = render_to_string('payment/notification.html', {'content': content, 'message': message})
    text_content = strip_tags(html_content)
    
    send_message(subject, text_content, email, html_content)