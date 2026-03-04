from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
def send_html_email(subject, template_name, context, recipient_email):
    """
    Sends an email with both HTML and plain text versions.
    
    Usage:
        send_html_email(
            subject='Welcome!',
            template_name='emails/welcome_email.html',
            context={'username': user.username},
            recipient_email=user.email
        )
    """
    # Render the HTML template with context
    html_content = render_to_string(template_name, context)
    # Strip HTML tags for plain text fallback
    # (You can also create a separate .txt template)
    plain_text = f"Hello {context.get('username', '')},\n\n""Welcome to ConnectHub!\n\n""Visit: https://academy.traitz.tech"
    email = EmailMultiAlternatives(
        subject=subject,
        body=plain_text,              # Plain text version
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient_email],
    )
    email.attach_alternative(html_content, 'text/html')  # HTML version
    email.send(fail_silently=True)   # Don't crash the app if email fails