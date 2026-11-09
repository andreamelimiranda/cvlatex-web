from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import RegistroForm


def registro(request):
    """Crea una cuenta nueva y deja a la persona con la sesión iniciada."""
    if request.user.is_authenticated:
        return redirect("mis_cvs")

    siguiente = request.POST.get("next") or request.GET.get("next") or ""
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            messages.success(request, f"¡Bienvenida/o a MICV, {usuario.username}!")
            # Solo volvemos a direcciones de nuestro propio sitio (seguridad).
            if url_has_allowed_host_and_scheme(siguiente, allowed_hosts={request.get_host()}):
                return redirect(siguiente)
            return redirect("mis_cvs")
    else:
        form = RegistroForm()
    return render(request, "registration/registro.html", {"form": form, "next": siguiente})
