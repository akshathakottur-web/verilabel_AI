from django.contrib.auth import password_validation
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError

from .models import User


def inspector_to_dict(user):
    return {
        'user_id': user.username,
        'name': user.name,
        'role': user.role,
        'date_joined': user.date_joined,
    }


def list_inspectors():
    return [inspector_to_dict(u) for u in User.objects.filter(role='inspector').order_by('username')]


def create_inspector(data):
    """data needs user_id, name and password. Raises ValueError with a message the page can show."""
    user_id = str(data.get('user_id') or '').strip()
    name = str(data.get('name') or '').strip()
    password = data.get('password') or ''
    if not user_id or not name or not password:
        raise ValueError('user_id, name and password are all required.')
    if len(name) > 100:
        raise ValueError('The name must be at most 100 characters.')
    try:
        UnicodeUsernameValidator()(user_id)
    except ValidationError:
        raise ValueError('The ID may only have letters, digits and the characters @ . + - _ (no spaces).')
    if User.objects.filter(username=user_id).exists():
        raise ValueError('This ID is already taken.')
    try:
        password_validation.validate_password(password)
    except ValidationError as error:
        raise ValueError(' '.join(error.messages))
    user = User.objects.create_user(username=user_id, password=password, name=name, role='inspector')
    return inspector_to_dict(user)