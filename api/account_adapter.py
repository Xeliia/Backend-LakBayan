from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom account adapter to override email verification links.
    Makes Allauth send links pointing to the React frontend instead of the Django backend.
    """

    def get_email_confirmation_url(self, request, emailconfirmation):
        """
        Generate email confirmation URL pointing to the frontend.
        
        Args:
            request: The HTTP request object
            emailconfirmation: The EmailAddress object containing the confirmation key
        
        Returns:
            str: URL like https://localhost:3000/verify-email/<key>
        """
        frontend_url = settings.FRONTEND_URL.rstrip('/')
        key = emailconfirmation.key
        return f"{frontend_url}/verify-email/{key}"
