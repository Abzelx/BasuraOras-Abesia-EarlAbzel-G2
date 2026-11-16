from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailOrUsernameBackend(ModelBackend):
    """Lets people log in with either their username or their email (case-insensitive)."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        if not username or password is None:
            return None

        users = User._default_manager.filter(username__iexact=username)
        if "@" in username:
            users = User._default_manager.filter(email__iexact=username)

        user = users.first()
        if user is None:
            User().set_password(password)  # same timing for unknown users (Django's own trick)
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
