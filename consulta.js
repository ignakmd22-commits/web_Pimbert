// Envío del formulario de consulta a la base de datos (POST /api/consultas).
// Si el sitio se abre sin servidor (doble clic en el HTML) o el servidor no responde,
// se usa el respaldo de siempre: copiar el mensaje al portapapeles.
(() => {
  const form = document.getElementById('inquiryForm');
  const estado = document.getElementById('formStatus');
  if (!form || !estado) return;
  const boton = form.querySelector('.form-submit');
  const sinServidor = location.protocol === 'file:';

  if (sinServidor) {
    document.querySelector('.contact-hint span').textContent =
      'Estás viendo el sitio sin servidor: el formulario solo prepara un mensaje para copiar y no guarda nada. Para guardar las consultas, iniciá servidor.py.';
    form.querySelector('.form-subtitle').textContent =
      'Completá los datos disponibles y copiá un mensaje listo para enviar.';
    boton.firstChild.textContent = 'Copiar mensaje de consulta ';
  }

  const mensaje = (d) => [
    'Hola, Pimbert. Quisiera recibir información sobre Deslizora.',
    d.nombre ? `Nombre: ${d.nombre}` : '',
    d.contacto ? `Contacto: ${d.contacto}` : '',
    d.institucion ? `Institución o empresa: ${d.institucion}` : '',
    `Ámbito de uso: ${form.elements.environment.selectedOptions[0].textContent}`,
    d.ancho ? `Ancho aproximado de la pizarra: ${d.ancho}` : '',
    d.alto ? `Alto aproximado de la pizarra: ${d.alto}` : '',
    d.detalles ? `Detalles: ${d.detalles}` : '',
    'Quedo pendiente de más información. ¡Gracias!'
  ].filter(Boolean).join('\n');

  async function copiar(texto) {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(texto);
      return;
    }
    const aux = document.createElement('textarea');
    aux.value = texto;
    aux.setAttribute('readonly', '');
    aux.style.cssText = 'position:fixed;opacity:0';
    document.body.appendChild(aux);
    aux.select();
    const ok = document.execCommand('copy');
    aux.remove();
    if (!ok) throw new Error('No se pudo copiar');
  }

  form.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    const f = new FormData(form);
    const d = {
      nombre: f.get('name'), contacto: f.get('contact'), institucion: f.get('place'),
      ancho: f.get('width'), alto: f.get('height'),
      tipo_espacio_id: Number(f.get('environment')), detalles: f.get('notes')
    };

    if (!sinServidor) {
      boton.disabled = true;
      estado.textContent = 'Enviando…';
      try {
        const r = await fetch('/api/consultas', {
          method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(d)
        });
        const j = await r.json().catch(() => ({}));
        if (r.ok && j.ok) {
          estado.textContent = `¡Gracias! Tu consulta (N.º ${j.id}) quedó registrada. Te vamos a responder al contacto que dejaste.`;
          form.reset();
          boton.disabled = false;
          return;
        }
        if (j.error) {  // error de validación o límite de envíos: se le muestra tal cual
          estado.textContent = j.error;
          boton.disabled = false;
          return;
        }
      } catch (_) { /* sin conexión con el servidor: sigue el respaldo */ }
      boton.disabled = false;
    }

    try {
      await copiar(mensaje(d));
      estado.textContent = sinServidor
        ? 'Mensaje copiado. Pegalo en el canal de contacto oficial de Pimbert para enviarlo.'
        : 'No pudimos conectar con el servidor, pero copiamos tu mensaje. Pegalo en el canal de contacto oficial de Pimbert.';
    } catch (_) {
      estado.textContent = 'No se pudo enviar ni copiar automáticamente. Podés seleccionar y copiar tus datos manualmente.';
    }
  });
})();
