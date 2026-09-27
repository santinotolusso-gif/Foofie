// Menú de navegación en pantallas chicas
document.addEventListener('DOMContentLoaded', function () {
  var boton = document.getElementById('boton-menu');
  var menu = document.getElementById('menu-movil');
  if (boton && menu) {
    boton.addEventListener('click', function () {
      menu.classList.toggle('abierto');
    });
  }

  // Indicador de carga: se muestra apenas se envía un formulario de
  // búsqueda y desaparece solo cuando llega la nueva página.
  var formularios = document.querySelectorAll('.form-con-carga');
  formularios.forEach(function (form) {
    form.addEventListener('submit', function () {
      var spinner = document.getElementById('spinner-busqueda');
      if (spinner) spinner.classList.add('activo');
    });
  });
});
