(() => {
  const consultaNavegacionMovil = window.matchMedia("(max-width: 76.234375em)");
  const consultaBusquedaMovil = window.matchMedia("(max-width: 59.984375em)");

  function nombreLocalizado(espanol, ingles) {
    return document.documentElement.lang === "en" ? ingles : espanol;
  }

  function emitirCambio(control) {
    control.dispatchEvent(new Event("input", { bubbles: true }));
    control.dispatchEvent(new Event("change", { bubbles: true }));
  }

  function enfocarDespues(elemento) {
    // El drawer termina su transicion antes de entregar un foco que sea visible.
    window.setTimeout(() => elemento?.focus(), 300);
  }

  function primerElementoVisible(contenedor, selector) {
    return Array.from(contenedor?.querySelectorAll(selector) ?? []).find(
      (elemento) =>
        elemento instanceof HTMLElement && elemento.getClientRects().length > 0,
    );
  }

  function reemplazarEtiquetaPorBoton(etiqueta, nombre, controlId) {
    if (!(etiqueta instanceof HTMLLabelElement)) return null;
    const boton = document.createElement("button");
    boton.type = "button";
    boton.className = etiqueta.className;
    boton.innerHTML = etiqueta.innerHTML;
    boton.dataset.tramaliaControl = controlId;
    boton.setAttribute(
      "aria-label",
      etiqueta.getAttribute("aria-label") ?? nombre,
    );
    const titulo = etiqueta.getAttribute("title");
    if (titulo) boton.setAttribute("title", titulo);
    etiqueta.replaceWith(boton);
    return boton;
  }

  function prepararPaleta() {
    const opciones = Array.from(
      document.querySelectorAll('input[name="__palette"]'),
    );
    const esquemaActivo = document.body.getAttribute("data-md-color-scheme");
    for (const opcion of opciones) {
      const esquema = opcion.getAttribute("data-md-color-scheme");
      opcion.setAttribute(
        "aria-label",
        esquema === "slate"
          ? nombreLocalizado("Tema oscuro", "Dark theme")
          : nombreLocalizado("Tema claro", "Light theme"),
      );
      opcion.checked = esquema === esquemaActivo;
    }
  }

  function prepararIdioma() {
    const contenedor = document.querySelector(".md-header .md-select");
    const boton = contenedor?.querySelector("button");
    const panel = contenedor?.querySelector(".md-select__inner");
    const enlaces = Array.from(contenedor?.querySelectorAll("a[href]") ?? []);
    if (!contenedor || !boton || !panel || enlaces.length === 0) return;
    boton.removeAttribute("aria-haspopup");
    panel.id ||= "selector-idioma-panel";
    boton.setAttribute("aria-controls", panel.id);

    const actualizar = (abierto) => {
      boton.setAttribute("aria-expanded", String(abierto));
      panel.hidden = !abierto;
      panel.inert = !abierto;
    };
    const abrir = (enfocarEnlace) => {
      actualizar(true);
      if (enfocarEnlace) {
        window.requestAnimationFrame(() => enlaces[0].focus());
      }
    };
    const cerrar = (devolverFoco) => {
      actualizar(false);
      if (devolverFoco) boton.focus();
    };

    actualizar(false);
    boton.addEventListener("click", (evento) => {
      const abierto = boton.getAttribute("aria-expanded") === "true";
      if (abierto) cerrar(false);
      else abrir(evento.detail === 0);
    });
    boton.addEventListener("keydown", (evento) => {
      if (evento.key !== "ArrowDown") return;
      evento.preventDefault();
      abrir(true);
    });
    contenedor.addEventListener("keydown", (evento) => {
      if (evento.key !== "Escape") return;
      evento.preventDefault();
      cerrar(true);
    });
    document.addEventListener("focusin", (evento) => {
      if (!contenedor.contains(evento.target)) cerrar(false);
    });
    document.addEventListener("pointerdown", (evento) => {
      if (!contenedor.contains(evento.target)) cerrar(false);
    });
  }

  function prepararPanel({
    boton,
    consultaCompacta,
    control,
    enfocarConPuntero = false,
    elementoInicial,
    panel,
  }) {
    if (!boton || !control || !panel) return;
    panel.id ||= `${control.id}-panel`;
    boton.setAttribute("aria-controls", panel.id);
    let estabaCompacto = consultaCompacta.matches;
    let focoPendienteDelBoton = false;

    boton.addEventListener("focus", () => {
      focoPendienteDelBoton = true;
    });
    document.addEventListener("focusin", (evento) => {
      if (evento.target !== boton && evento.target !== document.body) {
        focoPendienteDelBoton = false;
      }
    });

    const actualizar = () => {
      // En desktop el panel pertenece al layout; inert solo excluye el overlay cerrado.
      const estaCompacto = consultaCompacta.matches;
      const disponible = !estaCompacto || control.checked;
      const salioDelModoCompacto = estabaCompacto && !estaCompacto;
      if (
        !disponible &&
        document.activeElement instanceof Node &&
        panel.contains(document.activeElement)
      ) {
        boton.focus();
      }
      panel.inert = !disponible;
      boton.setAttribute("aria-expanded", String(control.checked));

      if (salioDelModoCompacto && focoPendienteDelBoton) {
        window.requestAnimationFrame(() => elementoInicial()?.focus());
        focoPendienteDelBoton = false;
      }

      const debeEnfocar = control.dataset.tramaliaDebeEnfocar === "1";
      delete control.dataset.tramaliaDebeEnfocar;
      if (debeEnfocar && control.checked) {
        enfocarDespues(elementoInicial());
      }
      estabaCompacto = estaCompacto;
    };
    control.addEventListener("change", actualizar);
    consultaCompacta.addEventListener("change", actualizar);
    boton.addEventListener("click", (evento) => {
      const activadoPorTeclado = evento.detail === 0;
      control.dataset.tramaliaDebeEnfocar = activadoPorTeclado ? "1" : "0";
      control.click();
      if (!activadoPorTeclado && enfocarConPuntero && control.checked) {
        elementoInicial()?.focus();
      }
    });
    actualizar();

    const cerrarConEscape = (evento) => {
      if (evento.key !== "Escape" || !control.checked) return;
      evento.preventDefault();
      control.checked = false;
      emitirCambio(control);
      boton.focus();
    };
    boton.addEventListener("keydown", cerrarConEscape);
    panel.addEventListener("keydown", cerrarConEscape);
  }

  function prepararPaneles() {
    const controlMenu = document.querySelector("#__drawer");
    const etiquetaMenu = document.querySelector(
      '.md-header__inner > label.md-header__button[for="__drawer"]',
    );
    const panelMenu = document.querySelector(".md-sidebar--primary");
    const botonMenu = reemplazarEtiquetaPorBoton(
      etiquetaMenu,
      nombreLocalizado("Abrir navegacion", "Open navigation"),
      "__drawer",
    );
    prepararPanel({
      boton: botonMenu,
      consultaCompacta: consultaNavegacionMovil,
      control: controlMenu,
      elementoInicial: () =>
        primerElementoVisible(
          panelMenu,
          'a[href]:not([tabindex="-1"]), [tabindex="0"]',
        ),
      panel: panelMenu,
    });

    const controlBusqueda = document.querySelector("#__search");
    const etiquetaBusqueda = document.querySelector(
      '.md-header__inner > label.md-header__button[for="__search"]',
    );
    const panelBusqueda = document.querySelector(".md-search");
    const botonBusqueda = reemplazarEtiquetaPorBoton(
      etiquetaBusqueda,
      nombreLocalizado("Abrir busqueda", "Open search"),
      "__search",
    );
    prepararPanel({
      boton: botonBusqueda,
      consultaCompacta: consultaBusquedaMovil,
      control: controlBusqueda,
      enfocarConPuntero: true,
      elementoInicial: () => panelBusqueda?.querySelector(".md-search__input"),
      panel: panelBusqueda,
    });
  }

  function prepararAccesibilidad() {
    prepararPaleta();
    prepararIdioma();
    prepararPaneles();
  }

  document.addEventListener("focusin", (evento) => {
    const elemento = evento.target;
    if (!(elemento instanceof HTMLElement)) return;
    window.requestAnimationFrame(() => {
      const rectangulo = elemento.getBoundingClientRect();
      const margen = 8;
      if (
        rectangulo.left < margen ||
        rectangulo.top < margen ||
        rectangulo.right > document.documentElement.clientWidth - margen ||
        rectangulo.bottom > document.documentElement.clientHeight - margen
      ) {
        elemento.scrollIntoView({ block: "nearest", inline: "nearest" });
      }
    });
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", prepararAccesibilidad, {
      once: true,
    });
  } else {
    prepararAccesibilidad();
  }
})();
