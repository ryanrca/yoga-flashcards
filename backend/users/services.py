import uuid
from django.core.mail import send_mail
from django.conf import settings
from .models import User


class UserService:
    """Service class for user-related operations."""

    @staticmethod
    def send_verification_email(user):
        """Send email verification to user."""
        token = str(uuid.uuid4())
        user.email_verification_token = token
        user.save()
        
        # In a real application, you would send an actual email
        # For now, we'll just log the verification token
        print(f"Email verification token for {user.email}: {token}")
        
        # TODO: Implement actual email sending
        # verification_url = f"{settings.FRONTEND_URL}/verify-email/{token}"
        # send_mail(
        #     'Verify your email',
        #     f'Click here to verify your email: {verification_url}',
        #     settings.DEFAULT_FROM_EMAIL,
        #     [user.email],
        #     fail_silently=False,
        # )

    @staticmethod
    def verify_email(token):
        """Verify user email with token."""
        try:
            user = User.objects.get(email_verification_token=token)
            user.email_verified = True
            user.email_verification_token = None
            user.save()
            return user
        except User.DoesNotExist:
            return None
