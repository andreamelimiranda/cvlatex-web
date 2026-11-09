from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm


class RegistroForm(UserCreationForm):
    """Formulario para crear una cuenta.

    Parte del formulario que ya trae Django (usuario + contraseña dos veces)
    y le agrega el correo, que es obligatorio para poder recuperar la contraseña.
    """

    email = forms.EmailField(
        label="Correo electrónico",
        help_text="Lo usamos solo para que puedas recuperar tu contraseña.",
    )

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username", "email")
        labels = {"username": "Nombre de usuario"}

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if get_user_model().objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe una cuenta con ese correo.")
        return email
