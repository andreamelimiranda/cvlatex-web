from django import forms

from .models import CV


class RenombrarForm(forms.ModelForm):
    """Formulario para cambiar el nombre de un CV guardado."""

    class Meta:
        model = CV
        fields = ["titulo"]
        labels = {"titulo": "Nuevo nombre"}
        widgets = {"titulo": forms.TextInput(attrs={"autofocus": True})}
