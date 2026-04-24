from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q
from .models import CitizenProfile

User = get_user_model()

class CustomAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Try to fetch the user by searching the username or email field
            user = User.objects.get(Q(username=username) | Q(email=username))
        except User.DoesNotExist:
            # If not found, try to find by phone number in CitizenProfile
            try:
                profile = CitizenProfile.objects.get(phone=username)
                user = profile.user
            except CitizenProfile.DoesNotExist:
                return None
            
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
