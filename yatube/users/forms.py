from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()


class CreationForm(UserCreationForm):
    """Класс для формы регистрации"""
    class Meta(UserCreationForm.Meta):
        """Наследуется вложенный класс"""
        model = User
        fields = ('first_name', 'last_name', 'username', 'email')
