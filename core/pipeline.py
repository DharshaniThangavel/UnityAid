from .models import Role
from django.contrib.auth import get_user_model

User = get_user_model()

def save_user_role(backend, user, response, *args, **kwargs):
    if not user:
        return
    if user.is_superuser:
        user.role = Role.SUPER_ADMIN
        user.save()
    elif not user.role:
        user.role = Role.PUBLIC
        user.save()


def associate_by_email(backend, details, user=None, *args, **kwargs):
    """
    If a user with this email already exists,
    connect Google login to that existing account
    instead of creating a new one.
    """
    if user:
        return

    email = details.get('email')
    if not email:
        return

    try:
        existing_user = User.objects.get(email=email)
        return {'user': existing_user}
    except User.DoesNotExist:
        return
    except User.MultipleObjectsReturned:
        return