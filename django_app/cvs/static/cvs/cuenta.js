/*
 * MICV · conexión entre el editor y la cuenta de la persona.
 *
 * Django agrega este archivo al final de cada página pública. Hace tres cosas:
 *   1. Muestra «Entrar / Crear cuenta» o «Mis CVs / Salir» en el encabezado.
 *   2. En el editor, agrega el botón «Guardar en mi cuenta».
 *   3. Abre un CV guardado cuando la dirección trae ?cv=ID (desde «Mis CVs»).
 *
 * El editor (index.html) ya tiene en su propio código las variables y
 * funciones `data`, `example`, `drawForm`, `save` y `hideTemplateChooser`.
 * Como los dos son scripts clásicos de la misma página, este archivo puede
 * usarlas directamente.
 */
(function () {
  'use strict';

  const CLAVE_CV_ACTUAL = 'micv-cv-actual';
  const esEditor = typeof drawForm === 'function' && typeof example !== 'undefined';
  let usuario = null;

  // ---------- utilidades ----------
  function leerCookie(nombre) {
    const par = document.cookie.split('; ').find(c => c.startsWith(nombre + '='));
    return par ? decodeURIComponent(par.split('=')[1]) : '';
  }

  async function api(url, opciones = {}) {
    const resp = await fetch(url, {
      credentials: 'same-origin',
      ...opciones,
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': leerCookie('csrftoken'), // protección CSRF de Django
        ...(opciones.headers || {}),
      },
    });
    let cuerpo = {};
    try { cuerpo = await resp.json(); } catch (e) { /* respuesta sin JSON */ }
    return { ok: resp.ok, estado: resp.status, cuerpo };
  }

  function leerCvActual() {
    try { return JSON.parse(sessionStorage.getItem(CLAVE_CV_ACTUAL)) || null; } catch (e) { return null; }
  }
  function guardarCvActual(cv) {
    try {
      if (cv) sessionStorage.setItem(CLAVE_CV_ACTUAL, JSON.stringify({ id: cv.id, titulo: cv.titulo }));
      else sessionStorage.removeItem(CLAVE_CV_ACTUAL);
    } catch (e) { /* almacenamiento bloqueado: no pasa nada */ }
  }

  function crear(etiqueta, atributos = {}, texto = '') {
    const el = document.createElement(etiqueta);
    for (const [k, v] of Object.entries(atributos)) el.setAttribute(k, v);
    if (texto) el.textContent = texto;
    return el;
  }

  function formularioSalir() {
    const form = crear('form', { method: 'post', action: '/cuenta/salir/', class: 'micv-salir' });
    form.appendChild(crear('input', { type: 'hidden', name: 'csrfmiddlewaretoken', value: leerCookie('csrftoken') }));
    form.appendChild(crear('button', { type: 'submit' }, 'Salir'));
    return form;
  }

  // ---------- 1. enlaces de cuenta en el encabezado ----------
  function dibujarEnlaces() {
    const caja = crear('div', { class: 'micv-cuenta', 'aria-label': 'Tu cuenta' });
    if (usuario) {
      caja.appendChild(crear('a', { href: '/mis-cvs/', class: 'micv-cuenta-principal' }, 'Mis CVs'));
      caja.appendChild(formularioSalir());
    } else {
      const volver = encodeURIComponent(location.pathname + location.search);
      caja.appendChild(crear('a', { href: '/cuenta/entrar/?next=' + volver }, 'Entrar'));
      caja.appendChild(crear('a', { href: '/cuenta/registro/?next=' + volver, class: 'micv-cuenta-principal' }, 'Crear cuenta'));
    }
    // Las guías tienen <header class="site-header"> con <nav>; el editor tiene un <header> simple.
    const nav = document.querySelector('.site-header nav');
    if (nav) nav.appendChild(caja);
    else {
      const header = document.querySelector('body > header, header');
      if (header) { header.classList.add('micv-header-con-cuenta'); header.appendChild(caja); }
    }
  }

  // ---------- 2. botón «Guardar en mi cuenta» en el editor ----------
  let aviso = null;

  function mostrarAviso(texto, tipo = 'info', enlace = null) {
    if (!aviso) return;
    aviso.textContent = texto;
    aviso.className = 'micv-aviso ' + tipo;
    if (enlace) {
      aviso.append(' ');
      aviso.appendChild(crear('a', { href: enlace.href }, enlace.texto));
    }
  }

  function dibujarBotonGuardar() {
    const pdf = document.getElementById('pdf');
    if (!pdf || !pdf.parentElement) return;
    const boton = crear('button', { type: 'button', id: 'guardarEnCuenta', class: 'micv-guardar' }, '☁ Guardar en mi cuenta');
    pdf.parentElement.insertBefore(boton, pdf);
    aviso = crear('p', { class: 'micv-aviso', role: 'status', 'aria-live': 'polite' });
    pdf.parentElement.after(aviso);

    const actual = leerCvActual();
    if (usuario && actual) mostrarAviso('Editando «' + actual.titulo + '». Los cambios se guardan al tocar «Guardar en mi cuenta».');
    else if (!usuario) mostrarAviso('Crea una cuenta gratis para guardar tus CVs y abrirlos desde cualquier dispositivo.');

    boton.addEventListener('click', guardarEnCuenta);
  }

  async function guardarEnCuenta() {
    if (!usuario) {
      // El borrador queda en este navegador, así que al volver no se pierde nada.
      location.href = '/cuenta/entrar/?next=' + encodeURIComponent('/');
      return;
    }
    const boton = document.getElementById('guardarEnCuenta');
    boton.disabled = true;
    mostrarAviso('Guardando…');
    try {
      const actual = leerCvActual();
      let r;
      if (actual) {
        r = await api('/api/cvs/' + actual.id + '/', { method: 'PUT', body: JSON.stringify({ datos: data }) });
        if (r.estado === 404) r = null; // lo borraron desde otro lado: creamos uno nuevo
      }
      if (!r) {
        const titulo = (data.name || 'Mi CV').trim() + ' – ' + new Date().toLocaleDateString('es-CL');
        r = await api('/api/cvs/', { method: 'POST', body: JSON.stringify({ titulo, datos: data }) });
      }
      if (!r.ok) throw new Error(r.cuerpo.error || 'No se pudo guardar (error ' + r.estado + ').');
      guardarCvActual(r.cuerpo);
      const hora = new Date().toLocaleTimeString('es-CL', { hour: '2-digit', minute: '2-digit' });
      mostrarAviso('✓ Guardado en tu cuenta a las ' + hora + ' como «' + r.cuerpo.titulo + '».', 'ok',
        { href: '/mis-cvs/', texto: 'Ver mis CVs' });
    } catch (err) {
      mostrarAviso(err.message, 'error');
    } finally {
      boton.disabled = false;
    }
  }

  // ---------- 3. abrir un CV guardado (?cv=ID) o empezar uno nuevo (?nuevo=1) ----------
  function limpiarDireccion() {
    history.replaceState(null, '', location.pathname);
  }

  async function abrirDesdeDireccion() {
    const params = new URLSearchParams(location.search);

    if (params.get('nuevo') === '1') {
      guardarCvActual(null);
      data = structuredClone(example);
      drawForm(); save();
      limpiarDireccion();
      mostrarAviso('Empezaste un CV nuevo. Elige un diseño y, cuando quieras, guárdalo en tu cuenta.');
      return;
    }

    const id = params.get('cv');
    if (!id || !/^\d+$/.test(id)) return;
    if (!usuario) { location.href = '/cuenta/entrar/?next=' + encodeURIComponent('/?cv=' + id); return; }

    const r = await api('/api/cvs/' + id + '/');
    limpiarDireccion();
    if (!r.ok) { mostrarAviso(r.cuerpo.error || 'No se pudo abrir el CV.', 'error'); return; }

    // Partimos del ejemplo para que no falte ningún campo nuevo del editor.
    data = Object.assign(structuredClone(example), r.cuerpo.datos);
    drawForm(); save();
    if (typeof hideTemplateChooser === 'function') hideTemplateChooser();
    if (typeof selectImportedView === 'function') selectImportedView();
    guardarCvActual(r.cuerpo);
    mostrarAviso('Abriste «' + r.cuerpo.titulo + '». Cuando termines, toca «Guardar en mi cuenta».', 'ok');
  }

  // ---------- inicio ----------
  async function iniciar() {
    const r = await api('/api/yo/');
    if (!r.ok) return; // sin Django detrás (por ejemplo, el sitio estático): no hacemos nada
    usuario = r.cuerpo.autenticado ? r.cuerpo.usuario : null;
    if (!usuario) guardarCvActual(null);
    dibujarEnlaces();
    if (esEditor) {
      dibujarBotonGuardar();
      await abrirDesdeDireccion();
    }
  }

  iniciar().catch(err => console.warn('MICV cuentas:', err));
})();
