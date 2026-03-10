from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

from .models import Profile
from .utils import send_html_email

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)

        if instance.email:
            try:
                send_html_email(
                    subject='Welcome to ConnectHub! 🎉',
                    template_name='emails/welcome_email.html',
                    context={'username': instance.username},
                    recipient_email=instance.email
                )
            except Exception as e:
                print("Welcome email failed:", e)