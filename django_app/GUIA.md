# MICV en Django · Guía para entender, probar y publicar

Esta carpeta convierte MICV en un sitio Django con **cuentas de usuario**: cada persona puede registrarse, entrar, guardar varios CVs y abrirlos desde cualquier dispositivo. El editor y las guías son **los mismos archivos `.html` de siempre** (están en la carpeta de arriba); Django los muestra y les agrega las cuentas.

---

## 1. Mapa del proyecto

```
cvlatex-web/
├── index.html, guia-cv.html, ...   ← el sitio de siempre (no se duplica)
├── render.yaml                      ← receta para publicar en Render
└── django_app/
    ├── manage.py                    ← el «control remoto» de Django
    ├── requirements.txt             ← paquetes que hay que instalar
    ├── build.sh                     ← pasos que corre Render al publicar
    ├── micv/                        ← configuración del proyecto
    │   ├── settings.py              ← ajustes (base de datos, idioma, seguridad)
    │   └── urls.py                  ← mapa principal de direcciones
    ├── cuentas/                     ← app de registro y contraseñas
    │   ├── forms.py                 ← formulario de registro (con correo)
    │   ├── views.py                 ← vista de registro
    │   ├── urls.py                  ← /cuenta/entrar/, /cuenta/registro/, ...
    │   └── tests.py                 ← pruebas automáticas
    ├── cvs/                         ← app de los currículums
    │   ├── models.py                ← la tabla CV (usuario, título, datos)
    │   ├── views.py                 ← páginas públicas, «Mis CVs» y la API
    │   ├── urls.py                  ← /mis-cvs/, /api/cvs/, ...
    │   ├── admin.py                 ← cómo se ven los CVs en /admin/
    │   ├── static/cvs/cuenta.js     ← conecta el editor con la cuenta
    │   └── tests.py                 ← pruebas automáticas
    └── templates/                   ← plantillas HTML de Django
        ├── base.html                ← encabezado y pie comunes
        ├── registration/            ← entrar, registro, contraseñas
        └── (cvs/templates/cvs/)     ← Mis CVs, renombrar, borrar
```

## 2. Cómo viaja una visita (el ciclo de Django)

1. El navegador pide una dirección, por ejemplo `/mis-cvs/`.
2. `micv/urls.py` y `cvs/urls.py` buscan qué **vista** la atiende: `views.mis_cvs`.
3. La vista revisa si hay sesión (`@login_required`), pide los datos al **modelo** (`request.user.cvs.all()`) y los entrega a una **plantilla** (`cvs/mis_cvs.html`).
4. La plantilla arma el HTML y Django lo devuelve al navegador.

Modelo → Vista → Plantilla, unidos por las URL. Es la idea central de todo el proyecto.

## 3. Cómo se conecta el editor con la cuenta

El editor está hecho en JavaScript y guarda el CV en un objeto llamado `data`. Django agrega al final de cada página el archivo `cuenta.js`, que:

- pregunta a `/api/yo/` si hay sesión y muestra «Entrar / Crear cuenta» o «Mis CVs / Salir»;
- agrega el botón **«☁ Guardar en mi cuenta»**, que envía `data` a la API:
  - `POST /api/cvs/` crea un CV nuevo,
  - `PUT /api/cvs/<id>/` actualiza el que estás editando;
- cuando abres un CV desde «Mis CVs» (`/?cv=<id>`), lo descarga con `GET /api/cvs/<id>/` y lo carga en el editor.

Seguridad: cada consulta filtra por `usuario=request.user`, así nadie puede ver ni borrar CVs ajenos, y todas las peticiones que modifican datos llevan el token **CSRF** de Django.

## 4. Probarlo en tu computador (Windows)

Abre una terminal en la carpeta `django_app` y ejecuta, una línea a la vez:

```bash
python -m venv .venv
.venv\Scripts\activate            # en Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate          # crea la base de datos db.sqlite3
python manage.py createsuperuser  # tu cuenta para entrar a /admin/
python manage.py runserver
```

Abre **http://127.0.0.1:8000/** en el navegador. Prueba:

- **Crear cuenta** → se abre «Mis CVs» (vacío).
- **Crear CV** → elige un diseño, edita y toca **«☁ Guardar en mi cuenta»**.
- **Mis CVs** → aparece tu CV; ábrelo, renómbralo o bórralo.
- **http://127.0.0.1:8000/admin/** → ves todas las cuentas y CVs.
- **¿Olvidaste tu contraseña?** → en tu computador el correo no se envía: se imprime en la terminal (búscalo ahí con el enlace).

Para correr las pruebas automáticas (20 pruebas):

```bash
python manage.py test
```

Cuando cambies `models.py`, crea y aplica la migración:

```bash
python manage.py makemigrations
python manage.py migrate
```

## 5. Publicarlo gratis (Render + Neon)

Django necesita un servidor encendido y una base de datos, algo que Cloudflare Workers no ofrece. La combinación gratuita recomendada:

- **Render** (servidor web gratis). Ojo: se «duerme» tras 15 minutos sin visitas y tarda cerca de un minuto en despertar; tiene 750 horas gratis al mes.
- **Neon** (PostgreSQL gratis, 1 GB). Se usa en vez de la base gratis de Render porque **la de Render se borra a los 30 días**; la de Neon no expira.

Pasos:

1. **Neon:** crea una cuenta en neon.com, crea un proyecto y copia la «connection string» (empieza con `postgresql://...`).
2. **Render:** crea una cuenta en render.com con tu GitHub → **New → Blueprint** → elige el repositorio `cvlatex-web`. Render lee `render.yaml` y crea el servicio `micv` desde la rama `django`.
3. Cuando te pida `DATABASE_URL`, pega la dirección de Neon.
4. (Opcional) Agrega en **Environment** las variables `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL` y `DJANGO_SUPERUSER_PASSWORD` para crear tu cuenta de administración al publicar. El plan gratis no tiene consola, por eso se hace así.
5. Espera a que termine el «deploy» y abre la dirección `https://micv-xxxx.onrender.com`. Pruébalo completo ahí antes de tocar el dominio.

### Correo para recuperar contraseñas

Sin configurar nada, el sitio funciona pero no envía correos. Para activarlo con Gmail: crea una **contraseña de aplicación** en tu cuenta de Google (Seguridad → Verificación en dos pasos → Contraseñas de aplicaciones) y agrega en Render:

```
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=tu-correo@gmail.com
EMAIL_HOST_PASSWORD=la-contraseña-de-aplicación
DEFAULT_FROM_EMAIL=MICV <tu-correo@gmail.com>
```

### Cambiar micvpremium.cl al nuevo sitio (solo cuando todo funcione)

1. En Render: **Settings → Custom Domains** → agrega `micvpremium.cl` y `www.micvpremium.cl`. Render te muestra los registros DNS que necesita.
2. En Cloudflare: **DNS** del dominio → crea o cambia los registros que indicó Render. Si el registro queda «Proxied» (nube naranja), pon el modo SSL en **Full**.
3. Desvincula el dominio del Worker `micv` en Cloudflare para que no responda los dos.
4. Mientras no hagas esto, micvpremium.cl sigue funcionando igual que hoy.

## 6. Qué estudiar en el libro para entender cada parte

Si sigues «Django for Beginners» (5.ª edición), estos capítulos explican las piezas de este proyecto:

| Capítulo del libro | Dónde lo ves en MICV |
|---|---|
| 2–4 (proyectos «Hello, World», sitio personal y de empresa) | `urls.py`, `views.py`, `templates/base.html` |
| 5–6 (Message Board y Blog: modelos, admin, pruebas) | `cvs/models.py`, `cvs/admin.py`, `tests.py` |
| 7 (Forms) | `cvs/forms.py`, `cuentas/forms.py`, `_formulario.html` |
| 8 y 10 (User Accounts, User Authentication) | `cuentas/`, `templates/registration/` |
| 12 (Password Change and Reset) | las rutas `contrasena/...` en `cuentas/urls.py` |
| 14 (Permissions and Authorization) | `@login_required` y el filtro `usuario=request.user` |
| 16 (Deployment) | `settings.py` (variables de entorno), `build.sh`, `render.yaml` |

### Ejercicios para practicar

1. Agrega un campo `notas` al modelo `CV`, crea la migración y muéstralo en «Mis CVs».
2. Agrega un botón «Duplicar» en «Mis CVs» que cree una copia de un CV.
3. Escribe una prueba que verifique que un usuario no puede renombrar un CV ajeno.
