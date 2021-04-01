from django.contrib.auth.forms import UserCreationForm

from django.contrib.auth import get_user_model

from posts.models import Post
from django.forms import ModelForm

User = get_user_model()


class CreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("first_name", "last_name", "username", "email")
