import AxeBuilder from "@axe-core/playwright";
import { expect as esperar, test as prueba } from "@playwright/test";

const RUTAS = [
  { idioma: "es", nombre: "inicio ES", ruta: "/" },
  { idioma: "en", nombre: "inicio EN", ruta: "/en/" },
  { idioma: "es", nombre: "interfaz ES", ruta: "/interfaz/" },
  { idioma: "en", nombre: "interfaz EN", ruta: "/en/interfaz/" },
];

const ALTERNATIVAS_ESPERADAS = {
  "/": {
    en: "https://MscottB.github.io/tramalia/en/",
    es: "https://MscottB.github.io/tramalia/",
  },
  "/en/": {
    en: "https://MscottB.github.io/tramalia/en/",
    es: "https://MscottB.github.io/tramalia/",
  },
  "/en/interfaz/": {
    en: "https://MscottB.github.io/tramalia/en/interfaz/",
    es: "https://MscottB.github.io/tramalia/interfaz/",
  },
  "/interfaz/": {
    en: "https://MscottB.github.io/tramalia/en/interfaz/",
    es: "https://MscottB.github.io/tramalia/interfaz/",
  },
};

const TEMAS = [
  { esquemaColor: "light", esquemaMaterial: "default", nombre: "claro" },
  { esquemaColor: "dark", esquemaMaterial: "slate", nombre: "oscuro" },
];

const VISTAS = [
  { alto: 800, ancho: 320 },
  { alto: 844, ancho: 390 },
  { alto: 1024, ancho: 768 },
  { alto: 900, ancho: 1440 },
];

const VISTAS_FOCO = [
  {
    alto: 844,
    ancho: 390,
    busquedaCompacta: true,
    navegacionCompacta: true,
    nombre: "movil",
  },
  {
    alto: 900,
    ancho: 1024,
    busquedaCompacta: false,
    navegacionCompacta: true,
    nombre: "tablet",
  },
  {
    alto: 900,
    ancho: 1440,
    busquedaCompacta: false,
    navegacionCompacta: false,
    nombre: "desktop",
  },
];

const ETIQUETAS_AXE = [
  "wcag2a",
  "wcag2aa",
  "wcag21a",
  "wcag21aa",
  "wcag22aa",
  "best-practice",
];

function detalleViolaciones(violaciones) {
  return violaciones
    .map(
      (violacion) =>
        `${violacion.id}: ${violacion.nodes.map((nodo) => nodo.target.join(" ")).join(", ")}`,
    )
    .join("\n");
}

async function esperarFuentes(pagina) {
  await pagina.evaluate(async () => {
    await document.fonts.ready;
  });
}

async function fijarPaletaClara(pagina) {
  await pagina.addInitScript(() => {
    localStorage.setItem(
      "/.__palette",
      JSON.stringify({
        color: {
          accent: "custom",
          media: "(prefers-color-scheme: light)",
          primary: "custom",
          scheme: "default",
        },
        index: 0,
      }),
    );
  });
}

async function esperarPaletaClara(pagina) {
  const paleta = pagina.locator('[data-md-component="palette"]');
  const cuerpo = pagina.locator("body");
  const opcionClara = paleta.locator('input[data-md-color-scheme="default"]');
  await esperar
    .poll(() =>
      pagina.evaluate(() => typeof window.component$?.subscribe === "function"),
    )
    .toBe(true);
  await opcionClara.evaluate((elemento) => elemento.click());
  await esperar
    .poll(() =>
      pagina.evaluate(() => {
        const valor = localStorage.getItem("/.__palette");
        return valor === null ? null : JSON.parse(valor);
      }),
    )
    .toEqual({
      color: {
        accent: "custom",
        media: "(prefers-color-scheme: light)",
        primary: "custom",
        scheme: "default",
      },
      index: 0,
    });
  await esperar(opcionClara).toBeChecked();
  await esperar(cuerpo).toHaveAttribute("data-md-color-scheme", "default");
  await esperar(paleta.locator('label[title="Modo oscuro"]')).toBeVisible();
  await esperar(paleta.locator('label[title="Modo claro"]')).toBeHidden();
  await esperar
    .poll(() =>
      cuerpo.evaluate((elemento) =>
        elemento.hasAttribute("data-md-color-switching"),
      ),
    )
    .toBe(false);
  await pagina.evaluate(
    () =>
      new Promise((resolver) => {
        requestAnimationFrame(() => requestAnimationFrame(resolver));
      }),
  );
}

function canalesColor(valor) {
  const hexadecimal = valor.match(/^#([0-9a-f]{6})$/i);
  if (hexadecimal) {
    return [0, 2, 4].map((indice) =>
      Number.parseInt(hexadecimal[1].slice(indice, indice + 2), 16),
    );
  }
  const rgb = valor.match(/^rgba?\((\d+),\s*(\d+),\s*(\d+)/);
  if (!rgb) throw new Error(`Color no reconocido: ${valor}`);
  return rgb.slice(1, 4).map(Number);
}

function luminanciaRelativa(canales) {
  const lineales = canales.map((canal) => {
    const normalizado = canal / 255;
    return normalizado <= 0.04045
      ? normalizado / 12.92
      : ((normalizado + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * lineales[0] + 0.7152 * lineales[1] + 0.0722 * lineales[2];
}

function relacionContraste(primerColor, segundoColor) {
  const primera = luminanciaRelativa(canalesColor(primerColor));
  const segunda = luminanciaRelativa(canalesColor(segundoColor));
  return (Math.max(primera, segunda) + 0.05) / (Math.min(primera, segunda) + 0.05);
}

async function analizarFocoActivo(pagina) {
  return pagina.evaluate(() => {
    const elemento = document.activeElement;
    if (!(elemento instanceof HTMLElement) || elemento === document.body) {
      return null;
    }
    const esPaleta =
      elemento instanceof HTMLInputElement && elemento.name === "__palette";
    const elementoVisual = esPaleta
      ? elemento.nextElementSibling
      : elemento;
    if (!(elementoVisual instanceof HTMLElement)) return null;
    const estilo = getComputedStyle(elementoVisual);
    const rectangulo = elementoVisual.getBoundingClientRect();
    const fondoComputado = estilo.backgroundColor;
    const componentesFondo = fondoComputado.match(
      /^rgba?\([^,]+,[^,]+,[^,]+(?:,\s*([\d.]+))?\)$/,
    );
    const fondoEsSolido =
      fondoComputado !== "transparent" &&
      Number(componentesFondo?.[1] ?? 1) >= 0.9;
    return {
      altoVista: document.documentElement.clientHeight,
      anchoVista: document.documentElement.clientWidth,
      colorFoco: estilo.outlineColor,
      desplazamiento: Number.parseFloat(estilo.outlineOffset) || 0,
      esActivadorBusqueda: elemento.matches(
        'button[data-tramalia-control="__search"]',
      ),
      esBusqueda:
        elemento.matches('button[data-tramalia-control="__search"]') ||
        elemento.matches(".md-search__input") ||
        Boolean(elemento.closest(".md-search")),
      esCabecera: Boolean(elemento.closest("header")),
      esEnlacePrincipal: elemento.matches(".md-content a[href]"),
      esIdioma: Boolean(elemento.closest(".md-select")),
      esMenu: elemento.matches('button[data-tramalia-control="__drawer"]'),
      esNavegacion: elemento.matches(
        ".md-tabs__link, .md-nav__link, .md-source",
      ),
      esPaleta,
      esSalto: elemento.matches("a.md-skip"),
      etiqueta: elemento.tagName,
      firma: Array.from(document.querySelectorAll("*")).indexOf(elemento),
      fondoComputado: fondoEsSolido ? fondoComputado : "",
      fondoFoco: fondoEsSolido
        ? fondoComputado
        : estilo.getPropertyValue("--tramalia-fondo-foco").trim(),
      grosor: Number.parseFloat(estilo.outlineWidth) || 0,
      nombre:
        elemento.getAttribute("aria-label") ??
        elementoVisual.getAttribute("title") ??
        elemento.textContent?.trim().replace(/\s+/g, " ").slice(0, 80) ??
        elemento.tagName,
      rectangulo: {
        abajo: rectangulo.bottom,
        arriba: rectangulo.top,
        derecha: rectangulo.right,
        izquierda: rectangulo.left,
      },
    };
  });
}

function afirmarFocoVisibleNoRecortado(foco) {
  esperar(foco, "No hay un elemento interactivo enfocado.").not.toBeNull();
  esperar(foco.grosor, `Foco sin grosor suficiente en ${foco.nombre}`).toBeGreaterThanOrEqual(
    2,
  );
  esperar(
    foco.rectangulo.derecha - foco.rectangulo.izquierda,
    `Foco sin ancho visible en ${foco.nombre}`,
  ).toBeGreaterThan(0);
  esperar(
    foco.rectangulo.abajo - foco.rectangulo.arriba,
    `Foco sin alto visible en ${foco.nombre}`,
  ).toBeGreaterThan(0);
  const expansion = Math.max(0, foco.grosor + foco.desplazamiento);
  esperar(
    foco.rectangulo.izquierda - expansion,
    `Foco recortado a la izquierda en ${foco.nombre}`,
  ).toBeGreaterThanOrEqual(-1);
  esperar(
    foco.rectangulo.arriba - expansion,
    `Foco recortado arriba en ${foco.nombre}`,
  ).toBeGreaterThanOrEqual(-1);
  esperar(
    foco.rectangulo.derecha + expansion,
    `Foco recortado a la derecha en ${foco.nombre}`,
  ).toBeLessThanOrEqual(foco.anchoVista + 1);
  esperar(
    foco.rectangulo.abajo + expansion,
    `Foco recortado abajo en ${foco.nombre}`,
  ).toBeLessThanOrEqual(foco.altoVista + 1);
  esperar(
    foco.fondoFoco,
    `El foco de ${foco.nombre} no declara su fondo adyacente.`,
  ).toMatch(/^(?:#[0-9a-f]{6}|rgba?\()/i);
  esperar(
    relacionContraste(foco.colorFoco, foco.fondoFoco),
    `Contraste insuficiente del foco de ${foco.nombre}: ${foco.colorFoco} sobre ${foco.fondoFoco}`,
  ).toBeGreaterThanOrEqual(3);
}

async function alcanzarConTab(pagina, objetivo, limite = 120) {
  for (let indice = 0; indice < limite; indice += 1) {
    await pagina.keyboard.press("Tab");
    if (await objetivo.evaluate((elemento) => document.activeElement === elemento)) {
      const foco = await analizarFocoActivo(pagina);
      afirmarFocoVisibleNoRecortado(foco);
      return;
    }
  }
  throw new Error(`No se alcanzo por teclado el control ${await objetivo.evaluate((elemento) => elemento.outerHTML)}`);
}

async function recorrerCicloDeFoco(
  pagina,
  { busquedaCompacta, navegacionCompacta },
) {
  await pagina.evaluate(() => {
    if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
  });
  const componentes = new Set();
  const secuencia = [];
  let firmaSalto = null;
  let cerroCiclo = false;

  for (let indice = 0; indice < 120; indice += 1) {
    await pagina.keyboard.press("Tab");
    await pagina.evaluate(
      () => new Promise((resolver) => requestAnimationFrame(() => resolver())),
    );
    const foco = await analizarFocoActivo(pagina);
    if (foco === null) continue;
    secuencia.push(foco);
    afirmarFocoVisibleNoRecortado(foco);
    if (foco.esSalto) {
      if (firmaSalto === foco.firma) {
        cerroCiclo = true;
        break;
      }
      firmaSalto = foco.firma;
    }
    for (const componente of [
      "esBusqueda",
      "esActivadorBusqueda",
      "esCabecera",
      "esEnlacePrincipal",
      "esIdioma",
      "esMenu",
      "esNavegacion",
      "esPaleta",
      "esSalto",
    ]) {
      if (foco[componente]) componentes.add(componente);
    }
  }

  esperar(cerroCiclo, "La tabulacion no completo un ciclo en 120 pasos.").toBe(true);
  esperar(secuencia[0]?.esSalto, "El enlace de salto no abre el orden de foco.").toBe(
    true,
  );
  esperar(
    secuencia.at(-1)?.esSalto,
    "El ciclo de foco no regresa al enlace de salto.",
  ).toBe(true);

  const indiceDe = (componente) =>
    secuencia.findIndex((foco) => foco[componente]);
  const indiceCabecera = indiceDe("esCabecera");
  const indiceContenido = indiceDe("esEnlacePrincipal");
  const indiceIdioma = indiceDe("esIdioma");
  const indiceMenu = indiceDe("esMenu");
  const indiceNavegacion = indiceDe("esNavegacion");
  const indicePaleta = indiceDe("esPaleta");
  const indiceBusqueda = indiceDe("esBusqueda");
  esperar(indiceCabecera, "La cabecera debe preceder al contenido.").toBeLessThan(
    indiceContenido,
  );
  esperar(indicePaleta, "La paleta debe preceder al idioma.").toBeLessThan(
    indiceIdioma,
  );
  esperar(indiceIdioma, "El idioma debe preceder a la busqueda.").toBeLessThan(
    indiceBusqueda,
  );
  esperar(
    indiceContenido,
    "El contenido debe preceder al retorno al enlace de salto.",
  ).toBeLessThan(secuencia.length - 1);
  for (const componente of [
    "esBusqueda",
    "esCabecera",
    "esEnlacePrincipal",
    "esIdioma",
    "esPaleta",
    "esSalto",
  ]) {
    esperar(componentes, `No se alcanzo ${componente} por teclado.`).toContain(componente);
  }
  if (navegacionCompacta) {
    esperar(componentes, "El menu movil no se alcanzo por teclado.").toContain("esMenu");
    esperar(indiceMenu, "El menu compacto debe preceder a la paleta.").toBeLessThan(
      indicePaleta,
    );
  } else {
    esperar(componentes, "La navegacion desktop no se alcanzo por teclado.").toContain(
      "esNavegacion",
    );
    esperar(
      componentes,
      "El activador de menu no debe tabular junto a la navegacion desktop.",
    ).not.toContain("esMenu");
    esperar(
      indiceNavegacion,
      "La navegacion desktop debe preceder al contenido.",
    ).toBeLessThan(indiceContenido);
  }
  if (busquedaCompacta) {
    esperar(
      componentes,
      "El activador de busqueda movil no se alcanzo por teclado.",
    ).toContain("esActivadorBusqueda");
  } else {
    esperar(
      componentes,
      "El activador de busqueda no debe tabular junto al campo visible.",
    ).not.toContain("esActivadorBusqueda");
  }
}

async function comprobarControlesDeCabecera(
  pagina,
  ruta,
  { busquedaCompacta, navegacionCompacta },
) {
  await fijarPaletaClara(pagina);
  await pagina.goto(ruta);
  await esperarPaletaClara(pagina);
  const opcionClara = pagina.locator("#__palette_0");
  const opcionOscura = pagina.locator("#__palette_1");
  const idioma = await pagina.locator("html").getAttribute("lang");
  await esperar(opcionClara).toHaveAccessibleName(
    idioma === "en" ? "Light theme" : "Tema claro",
  );
  await esperar(opcionOscura).toHaveAccessibleName(
    idioma === "en" ? "Dark theme" : "Tema oscuro",
  );
  await alcanzarConTab(pagina, opcionClara);
  await pagina.keyboard.press("ArrowRight");
  await esperar(opcionOscura).toBeChecked();
  await esperar(opcionOscura).toBeFocused();
  await esperar(pagina.locator("body")).toHaveAttribute(
    "data-md-color-scheme",
    "slate",
  );
  afirmarFocoVisibleNoRecortado(await analizarFocoActivo(pagina));
  await pagina.keyboard.press("ArrowLeft");
  await esperar(opcionClara).toBeChecked();
  await esperar(opcionClara).toBeFocused();
  await esperar(pagina.locator("body")).toHaveAttribute(
    "data-md-color-scheme",
    "default",
  );
  await pagina.keyboard.press("Space");
  await esperar(opcionClara).toBeChecked();

  await pagina.goto(ruta);
  const selectorIdioma = pagina.locator(".md-select > button");
  const panelIdioma = pagina.locator(".md-select__inner");
  await esperar(selectorIdioma).toHaveAttribute("aria-expanded", "false");
  await esperar(panelIdioma).toBeHidden();
  await alcanzarConTab(pagina, selectorIdioma);
  await pagina.keyboard.press("Enter");
  await esperar(selectorIdioma).toHaveAttribute("aria-expanded", "true");
  await esperar(panelIdioma).toBeVisible();
  const primerIdioma = pagina.locator(".md-select__link").first();
  await esperar(primerIdioma).toBeFocused();
  afirmarFocoVisibleNoRecortado(await analizarFocoActivo(pagina));
  await pagina.keyboard.press("Escape");
  await esperar(selectorIdioma).toHaveAttribute("aria-expanded", "false");
  await esperar(panelIdioma).toBeHidden();
  await esperar(selectorIdioma).toBeFocused();

  await pagina.keyboard.press("Space");
  await esperar(selectorIdioma).toHaveAttribute("aria-expanded", "true");
  await esperar(primerIdioma).toBeFocused();
  await pagina.keyboard.press("Escape");
  await esperar(panelIdioma).toBeHidden();

  await selectorIdioma.click();
  await esperar(selectorIdioma).toHaveAttribute("aria-expanded", "true");
  await esperar(panelIdioma).toBeVisible();
  await pagina.locator(".md-content a[href]").first().focus();
  await esperar(selectorIdioma).toHaveAttribute("aria-expanded", "false");
  await esperar(panelIdioma).toBeHidden();

  await pagina.goto(ruta);
  const controlMenu = pagina.locator(
    'button[data-tramalia-control="__drawer"]',
  );
  if (navegacionCompacta) {
    await esperar(controlMenu).toHaveRole("button");
    await esperar(controlMenu).toHaveAttribute("aria-expanded", "false");
    await alcanzarConTab(pagina, controlMenu);
    await pagina.keyboard.press("Enter");
    await esperar(pagina.locator("#__drawer")).toBeChecked();
    await esperar(controlMenu).toHaveAttribute("aria-expanded", "true");
    await esperar
      .poll(() =>
        pagina.evaluate(() =>
          Boolean(document.activeElement?.closest("nav.md-nav--primary")),
        ),
      )
      .toBe(true);
    afirmarFocoVisibleNoRecortado(await analizarFocoActivo(pagina));
    await pagina.keyboard.press("Escape");
    await esperar(pagina.locator("#__drawer")).not.toBeChecked();
    await esperar(controlMenu).toHaveAttribute("aria-expanded", "false");
    await esperar(controlMenu).toBeFocused();
    await controlMenu.click();
    await esperar(pagina.locator("#__drawer")).toBeChecked();
    await esperar(controlMenu).toHaveAttribute("aria-expanded", "true");
    await esperar(controlMenu).toBeFocused();
    await pagina.keyboard.press("Escape");
    await esperar(pagina.locator("#__drawer")).not.toBeChecked();
    await esperar(controlMenu).toHaveAttribute("aria-expanded", "false");
    await esperar(controlMenu).toBeFocused();
  } else {
    await esperar(controlMenu).toBeHidden();
  }

  await pagina.goto(ruta);
  const controlBusqueda = pagina.locator(
    'button[data-tramalia-control="__search"]',
  );
  if (busquedaCompacta) {
    await esperar(controlBusqueda).toHaveRole("button");
    await esperar(controlBusqueda).toHaveAttribute("aria-expanded", "false");
    await alcanzarConTab(pagina, controlBusqueda);
    await pagina.keyboard.press("Enter");
    await esperar(pagina.locator("#__search")).toBeChecked();
    await esperar(controlBusqueda).toHaveAttribute("aria-expanded", "true");
    await esperar(pagina.locator(".md-search__input")).toBeFocused();
    afirmarFocoVisibleNoRecortado(await analizarFocoActivo(pagina));
    await pagina.keyboard.press("Escape");
    await esperar(pagina.locator("#__search")).not.toBeChecked();
    await esperar(controlBusqueda).toHaveAttribute("aria-expanded", "false");
    await esperar(controlBusqueda).toBeFocused();
    await controlBusqueda.click();
    await esperar(pagina.locator("#__search")).toBeChecked();
    await esperar(pagina.locator(".md-search__input")).toBeFocused();
    await pagina.keyboard.press("Escape");
    await esperar(controlBusqueda).toBeFocused();
  } else {
    await esperar(controlBusqueda).toBeHidden();
    const busqueda = pagina.locator(".md-search__input");
    await alcanzarConTab(pagina, busqueda);
    await pagina.keyboard.type("interfaz");
    await esperar(busqueda).toHaveValue("interfaz");
  }
}

for (const paginaDocumental of RUTAS) {
  prueba(`${paginaDocumental.nombre} declara idioma, titulo y landmarks`, async ({
    page: pagina,
  }) => {
    await pagina.goto(paginaDocumental.ruta);

    await esperar(pagina.locator("html")).toHaveAttribute("lang", paginaDocumental.idioma);
    await esperar(pagina.locator("h1").first()).toBeVisible();
    const salto = pagina.locator("a.md-skip");
    const destinoSalto = await salto.getAttribute("href");
    esperar(destinoSalto).toMatch(/^#[^\s]+$/);
    const destinoExiste = await salto.evaluate((elemento) => {
      const destino = elemento.getAttribute("href")?.slice(1);
      return Boolean(destino && document.getElementById(destino));
    });
    esperar(destinoExiste).toBe(true);
    await esperar(pagina.locator("header").first()).toBeVisible();
    await esperar(pagina.locator("nav").first()).toBeAttached();
    await esperar(pagina.locator("main").first()).toBeVisible();
    await esperar(pagina.locator("footer").first()).toBeAttached();
  });

  prueba(`${paginaDocumental.nombre} ofrece orden de teclado y foco visible no recortado`, async ({
    page: pagina,
  }) => {
    for (const vista of VISTAS_FOCO) {
      await pagina.setViewportSize({ height: vista.alto, width: vista.ancho });
      await pagina.goto(paginaDocumental.ruta);
      await recorrerCicloDeFoco(pagina, vista);
      await comprobarControlesDeCabecera(
        pagina,
        paginaDocumental.ruta,
        vista,
      );
    }

    await pagina.setViewportSize({ height: 900, width: 1440 });
    await pagina.goto(paginaDocumental.ruta);
    const salto = pagina.locator("a.md-skip");
    const destinoSalto = await salto.getAttribute("href");
    esperar(destinoSalto).toMatch(/^#[^\s]+$/);
    await pagina.keyboard.press("Tab");
    await pagina.keyboard.press("Enter");
    await esperar.poll(() => pagina.evaluate(() => location.hash)).toBe(destinoSalto);
  });

  for (const tema of TEMAS) {
    prueba(`${paginaDocumental.nombre} no presenta violaciones axe en tema ${tema.nombre}`, async ({
      page: pagina,
    }) => {
      await pagina.emulateMedia({ colorScheme: tema.esquemaColor });
      for (const vista of [
        { alto: 900, ancho: 1024, nombre: "tablet" },
        { alto: 900, ancho: 1440, nombre: "desktop" },
      ]) {
        await pagina.setViewportSize({ height: vista.alto, width: vista.ancho });
        await pagina.goto(paginaDocumental.ruta);
        await esperarFuentes(pagina);
        await esperar(pagina.locator("body")).toHaveAttribute(
          "data-md-color-scheme",
          tema.esquemaMaterial,
        );

        const llamadaPrincipal = pagina.locator(
          ".md-content .md-button--primary",
        ).first();
        if ((await llamadaPrincipal.count()) > 0) {
          await llamadaPrincipal.focus();
          const focoLlamada = await analizarFocoActivo(pagina);
          esperar(
            focoLlamada.fondoComputado,
            "El CTA primario debe contrastarse contra su fondo computado real.",
          ).not.toBe("");
          afirmarFocoVisibleNoRecortado(focoLlamada);
        }

        const resultado = await new AxeBuilder({ page: pagina })
          .withTags(ETIQUETAS_AXE)
          .analyze();
        esperar(
          resultado.violations,
          `${vista.nombre}: ${detalleViolaciones(resultado.violations)}`,
        ).toEqual([]);
      }
    });
  }

  for (const vista of VISTAS) {
    prueba(`${paginaDocumental.nombre} no desborda a ${vista.ancho}x${vista.alto}`, async ({
      page: pagina,
    }) => {
      await pagina.setViewportSize({ height: vista.alto, width: vista.ancho });
      await pagina.goto(paginaDocumental.ruta);
      const medidas = await pagina.evaluate(() => ({
        anchoCliente: document.documentElement.clientWidth,
        anchoDocumento: document.documentElement.scrollWidth,
      }));
      esperar(medidas.anchoDocumento).toBeLessThanOrEqual(medidas.anchoCliente);
    });
  }

  prueba(`${paginaDocumental.nombre} conserva reflow con texto al 200 por ciento`, async ({
    page: pagina,
  }) => {
    await pagina.setViewportSize({ height: 900, width: 1280 });
    await pagina.goto(paginaDocumental.ruta);
    await pagina.addStyleTag({ content: "html { font-size: 200% !important; }" });
    const medidas = await pagina.evaluate(() => ({
      anchoCliente: document.documentElement.clientWidth,
      anchoDocumento: document.documentElement.scrollWidth,
    }));
    esperar(medidas.anchoDocumento).toBeLessThanOrEqual(medidas.anchoCliente);
  });
}

prueba("controles adaptativos conservan semantica, foco y estados accesibles", async ({
  page: pagina,
}) => {
  const auditarEstadoAbierto = async (nombreEstado) => {
    const resultado = await new AxeBuilder({ page: pagina })
      .withTags(ETIQUETAS_AXE)
      .analyze();
    esperar(
      resultado.violations,
      `${nombreEstado}: ${detalleViolaciones(resultado.violations)}`,
    ).toEqual([]);
  };

  await pagina.setViewportSize({ height: 844, width: 390 });
  await pagina.goto("/interfaz/");

  const controlMenu = pagina.locator(
    'button[data-tramalia-control="__drawer"]',
  );
  const panelMenu = pagina.locator(".md-sidebar--primary");
  await controlMenu.focus();
  await pagina.keyboard.press("Enter");
  await esperar(controlMenu).toHaveAttribute("aria-expanded", "true");
  await esperar.poll(() => panelMenu.evaluate((elemento) => elemento.inert)).toBe(
    false,
  );
  await auditarEstadoAbierto("drawer movil abierto");
  await pagina.keyboard.press("Escape");
  await esperar(controlMenu).toHaveAttribute("aria-expanded", "false");
  await esperar(controlMenu).toBeFocused();

  const controlBusqueda = pagina.locator(
    'button[data-tramalia-control="__search"]',
  );
  const panelBusqueda = pagina.locator(".md-search");
  await controlBusqueda.focus();
  await pagina.keyboard.press("Enter");
  await esperar(controlBusqueda).toHaveAttribute("aria-expanded", "true");
  await esperar(pagina.locator(".md-search__input")).toBeFocused();
  await esperar
    .poll(() => panelBusqueda.evaluate((elemento) => elemento.inert))
    .toBe(false);
  await auditarEstadoAbierto("busqueda movil abierta");
  await pagina.keyboard.press("Escape");
  await esperar(controlBusqueda).toHaveAttribute("aria-expanded", "false");
  await esperar(controlBusqueda).toBeFocused();

  const selectorIdioma = pagina.locator(".md-select > button");
  const panelIdioma = pagina.locator(".md-select__inner");
  await selectorIdioma.focus();
  await pagina.keyboard.press("Enter");
  await esperar(selectorIdioma).toHaveAttribute("aria-expanded", "true");
  await esperar(panelIdioma).toBeVisible();
  await auditarEstadoAbierto("selector de idioma abierto");
  await pagina.keyboard.press("Escape");

  await pagina.setViewportSize({ height: 900, width: 1300 });
  await pagina.goto("/interfaz/");
  const enlaceLateral = pagina
    .locator(".md-sidebar--primary .md-nav__link[href]:visible")
    .first();
  await enlaceLateral.focus();
  await esperar(enlaceLateral).toBeFocused();
  await pagina.setViewportSize({ height: 900, width: 1200 });
  await esperar(controlMenu).toBeFocused();
  await esperar.poll(() => panelMenu.evaluate((elemento) => elemento.inert)).toBe(
    true,
  );
  await pagina.setViewportSize({ height: 900, width: 1300 });
  await esperar(controlMenu).toBeHidden();
  await esperar
    .poll(() =>
      pagina.evaluate(() =>
        Boolean(
          document.activeElement?.matches("a[href]") &&
            document.activeElement.closest(".md-sidebar--primary"),
        ),
      ),
    )
    .toBe(true);
  await esperar.poll(() => panelMenu.evaluate((elemento) => elemento.inert)).toBe(
    false,
  );

  await pagina.setViewportSize({ height: 900, width: 1000 });
  await pagina.goto("/interfaz/");
  const campoBusqueda = pagina.locator(".md-search__input");
  await campoBusqueda.focus();
  await esperar(campoBusqueda).toBeFocused();
  await pagina.setViewportSize({ height: 900, width: 900 });
  if (await pagina.locator("#__search").isChecked()) {
    await esperar(campoBusqueda).toBeFocused();
    await esperar(controlBusqueda).toHaveAttribute("aria-expanded", "true");
    await esperar
      .poll(() => panelBusqueda.evaluate((elemento) => elemento.inert))
      .toBe(false);
  } else {
    await esperar(controlBusqueda).toBeFocused();
    await esperar(controlBusqueda).toHaveAttribute("aria-expanded", "false");
    await esperar
      .poll(() => panelBusqueda.evaluate((elemento) => elemento.inert))
      .toBe(true);
  }
  if (await pagina.locator("#__search").isChecked()) {
    await pagina.keyboard.press("Escape");
  }
  await esperar(controlBusqueda).toBeFocused();
  await pagina.setViewportSize({ height: 900, width: 1000 });
  await esperar(controlBusqueda).toBeHidden();
  await esperar(campoBusqueda).toBeFocused();
  await esperar
    .poll(() => panelBusqueda.evaluate((elemento) => elemento.inert))
    .toBe(false);
});

prueba("no publica planes internos en el sitio ni en la busqueda", async ({
  request: solicitud,
}) => {
  const rutaInterna =
    "/superpowers/plans/2026-07-12-01-base-pruebas-ci/";
  const respuestaInterna = await solicitud.get(rutaInterna);
  esperar(respuestaInterna.status()).toBe(404);

  const respuestaIndice = await solicitud.get("/search/search_index.json");
  esperar(respuestaIndice.ok()).toBe(true);
  const indice = await respuestaIndice.json();
  esperar(
    indice.docs.some(({ location: ubicacion }) =>
      ubicacion.startsWith("superpowers/"),
    ),
  ).toBe(false);
});

prueba("publica metadatos multilingues absolutos sin fuentes externas bloqueantes", async ({
  page: pagina,
}) => {
  for (const paginaDocumental of RUTAS) {
    await pagina.goto(paginaDocumental.ruta);
    const alternativas = await pagina
      .locator('head link[rel="alternate"][hreflang]')
      .evaluateAll((elementos) =>
        elementos.map((elemento) => ({
          href: elemento.getAttribute("href"),
          idioma: elemento.getAttribute("hreflang"),
        })),
      );
    esperar(
      Object.fromEntries(
        alternativas.map(({ href, idioma }) => [idioma, href]),
      ),
    ).toEqual(ALTERNATIVAS_ESPERADAS[paginaDocumental.ruta]);
    await esperar(
      pagina.locator('head link[href*="fonts.googleapis.com"]'),
    ).toHaveCount(0);
  }

  await pagina.goto("/");
  await esperar(
    pagina.locator('.md-tabs__link[href="instalacion/"]'),
  ).toHaveText("Primeros pasos");
});

prueba("entrega el tema claro inicial sin depender de JavaScript", async ({
  page: pagina,
}) => {
  await pagina.emulateMedia({ colorScheme: "light" });
  await pagina.route(/\/assets\/javascripts\/bundle\..+\.min\.js$/, (ruta) =>
    ruta.abort(),
  );
  await pagina.goto("/", { waitUntil: "domcontentloaded" });
  await esperar(pagina.locator("body")).toHaveAttribute(
    "data-md-color-scheme",
    "default",
  );
  await esperar(pagina.locator("#__palette_0")).toBeChecked();
  await esperar(pagina.locator("#__palette_0")).toHaveAccessibleName(
    "Tema claro",
  );
  await esperar(pagina.locator("#__palette_1")).not.toBeChecked();
  await esperar(pagina.locator("#__palette_1")).toHaveAccessibleName(
    "Tema oscuro",
  );
});

prueba("hero de inicio claro conserva contraste legible", async ({ page: pagina }) => {
  await pagina.emulateMedia({ colorScheme: "light" });
  await pagina.goto("/");
  const resumen = pagina.locator(".tramalia-hero__content > p:has(> strong)");
  await esperar(resumen).toBeVisible();
  const colores = await resumen.evaluate((elemento) => {
    const estilo = getComputedStyle(elemento);
    return {
      fondo: getComputedStyle(document.body)
        .getPropertyValue("--md-default-bg-color")
        .trim(),
      texto: estilo.color,
    };
  });
  esperar(colores.texto).toBe("rgb(95, 90, 115)");
  esperar(relacionContraste(colores.texto, colores.fondo)).toBeGreaterThanOrEqual(4.5);
});

prueba("hero de inicio desktop mantiene titulo y CTA primario en el viewport", async ({
  page: pagina,
}) => {
  await pagina.setViewportSize({ height: 900, width: 1440 });
  await pagina.goto("/");
  await esperarFuentes(pagina);

  const titulo = pagina.locator(".tramalia-hero h1");
  const lineasTitulo = await titulo.evaluate((elemento) => {
    const estilo = getComputedStyle(elemento);
    return elemento.getBoundingClientRect().height / Number.parseFloat(estilo.lineHeight);
  });
  esperar(lineasTitulo).toBeLessThanOrEqual(5);

  const ctaPrimario = pagina.locator(".tramalia-hero .md-button--primary");
  const cajaCta = await ctaPrimario.boundingBox();
  esperar(cajaCta).not.toBeNull();
  esperar(cajaCta.y + cajaCta.height).toBeLessThanOrEqual(900);
});

prueba("movimiento reducido neutraliza animaciones y conserva la navegacion", async ({
  page: pagina,
}) => {
  await pagina.emulateMedia({ reducedMotion: "reduce" });
  await pagina.goto("/");

  const duracionMaxima = await pagina.evaluate(() => {
    function segundos(valor) {
      return valor.split(",").reduce((maximo, fragmento) => {
        const tiempo = fragmento.trim();
        const factor = tiempo.endsWith("ms") ? 0.001 : 1;
        return Math.max(maximo, (Number.parseFloat(tiempo) || 0) * factor);
      }, 0);
    }

    return Array.from(document.querySelectorAll("*"), (elemento) => {
      const estilo = getComputedStyle(elemento);
      return Math.max(segundos(estilo.animationDuration), segundos(estilo.transitionDuration));
    }).reduce((maximo, duracion) => Math.max(maximo, duracion), 0);
  });
  esperar(duracionMaxima).toBeLessThanOrEqual(0.00001);

  const enlaceInterfaz = pagina.locator('a[href="interfaz/"]:visible').first();
  await enlaceInterfaz.focus();
  await pagina.keyboard.press("Enter");
  await esperar(pagina).toHaveURL(/\/interfaz\/$/);
  await esperar(pagina.locator("h1").first()).toBeVisible();
});

const COMPARAR_CAPTURAS =
  process.platform === "linux" && process.env.TRAMALIA_COMPARAR_CAPTURAS === "1";

for (const captura of [
  { alto: 844, ancho: 390, nombre: "inicio-390x844.png", ruta: "/" },
  { alto: 900, ancho: 1440, nombre: "inicio-1440x900.png", ruta: "/" },
  { alto: 844, ancho: 390, nombre: "interfaz-390x844.png", ruta: "/interfaz/" },
  { alto: 900, ancho: 1440, nombre: "interfaz-1440x900.png", ruta: "/interfaz/" },
]) {
  prueba(`captura canonica ${captura.nombre}`, async ({ page: pagina }) => {
    prueba.skip(
      !COMPARAR_CAPTURAS,
      "Las capturas canonicas solo se comparan en Linux cuando se solicita explicitamente.",
    );
    await pagina.setViewportSize({ height: captura.alto, width: captura.ancho });
    let solicitudesGithubBloqueadas = 0;
    await pagina.route(/^https:\/\/api\.github\.com\//, async (rutaExterna) => {
      solicitudesGithubBloqueadas += 1;
      await rutaExterna.abort("blockedbyclient");
    });
    await fijarPaletaClara(pagina);
    await pagina.goto(captura.ruta);
    await esperarFuentes(pagina);
    await esperar(pagina.locator("body")).toHaveAttribute(
      "data-md-color-scheme",
      "default",
    );
    await esperarPaletaClara(pagina);

    const enlaceRepositorio = pagina.locator(
      '.md-header__source a.md-source[href="https://github.com/MscottB/tramalia"]',
    );
    await esperar(enlaceRepositorio).toHaveCount(1);
    await esperar(enlaceRepositorio.locator(".md-source__repository")).toContainText(
      "tramalia",
    );
    if (captura.ancho >= 1220) {
      await esperar(enlaceRepositorio).toBeVisible();
    }

    // Estrellas, forks y version son datos externos mutables y no pertenecen al baseline.
    await esperar.poll(() => solicitudesGithubBloqueadas).toBe(2);
    await esperar(pagina.locator(".md-source__facts")).toHaveCount(0);
    await esperar(pagina.locator(".md-source__repository--active")).toHaveCount(0);
    await esperar(pagina).toHaveScreenshot(captura.nombre, {
      animations: "disabled",
      caret: "hide",
      fullPage: false,
    });
  });
}
