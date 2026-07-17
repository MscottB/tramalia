import { readFile, realpath, stat } from "node:fs/promises";
import { createServer } from "node:http";
import { extname, isAbsolute, join, relative, resolve, sep } from "node:path";
import { pathToFileURL } from "node:url";

const HOSTS_LOOPBACK = new Set(["127.0.0.1", "::1"]);

const TIPOS_MIME = new Map([
  [".css", "text/css; charset=utf-8"],
  [".gif", "image/gif"],
  [".htm", "text/html; charset=utf-8"],
  [".html", "text/html; charset=utf-8"],
  [".ico", "image/x-icon"],
  [".jpeg", "image/jpeg"],
  [".jpg", "image/jpeg"],
  [".js", "text/javascript; charset=utf-8"],
  [".json", "application/json; charset=utf-8"],
  [".map", "application/json; charset=utf-8"],
  [".png", "image/png"],
  [".svg", "image/svg+xml; charset=utf-8"],
  [".ttf", "font/ttf"],
  [".txt", "text/plain; charset=utf-8"],
  [".webp", "image/webp"],
  [".woff", "font/woff"],
  [".woff2", "font/woff2"],
  [".xml", "application/xml; charset=utf-8"],
]);

class ErrorHttp extends Error {
  constructor(estado, mensaje) {
    super(mensaje);
    this.estado = estado;
  }
}

function estaConfinada(raiz, destino) {
  const rutaRelativa = relative(raiz, destino);
  return (
    rutaRelativa === "" ||
    (!isAbsolute(rutaRelativa) &&
      rutaRelativa !== ".." &&
      !rutaRelativa.startsWith(`..${sep}`))
  );
}

function decodificarRuta(urlCruda) {
  const rutaCruda = (urlCruda ?? "/").split(/[?#]/, 1)[0];
  let ruta = rutaCruda;
  for (let indice = 0; indice < 4; indice += 1) {
    let rutaDecodificada;
    try {
      rutaDecodificada = decodeURIComponent(ruta);
    } catch {
      throw new ErrorHttp(400, "Ruta no valida.");
    }
    if (rutaDecodificada === ruta) break;
    ruta = rutaDecodificada;
  }
  if (/%[0-9a-f]{2}/i.test(ruta)) {
    throw new ErrorHttp(400, "Ruta no valida.");
  }
  if (ruta.includes("\0")) throw new ErrorHttp(400, "Ruta no valida.");

  const segmentos = ruta.split(/[\\/]+/);
  if (segmentos.includes("..")) {
    throw new ErrorHttp(403, "Ruta fuera de la documentacion.");
  }
  return segmentos.filter((segmento) => segmento !== "" && segmento !== ".");
}

async function resolverArchivo(raizReal, urlCruda) {
  const segmentos = decodificarRuta(urlCruda);
  let candidato = join(raizReal, ...segmentos);
  if (!estaConfinada(raizReal, resolve(candidato))) {
    throw new ErrorHttp(403, "Ruta fuera de la documentacion.");
  }

  let informacion;
  try {
    informacion = await stat(candidato);
  } catch (error) {
    if (error?.code === "ENOENT" || error?.code === "ENOTDIR") {
      throw new ErrorHttp(404, "Recurso no encontrado.");
    }
    throw error;
  }
  if (informacion.isDirectory()) candidato = join(candidato, "index.html");

  let archivoReal;
  try {
    archivoReal = await realpath(candidato);
  } catch (error) {
    if (error?.code === "ENOENT" || error?.code === "ENOTDIR") {
      throw new ErrorHttp(404, "Recurso no encontrado.");
    }
    throw error;
  }
  if (!estaConfinada(raizReal, archivoReal)) {
    throw new ErrorHttp(403, "Ruta fuera de la documentacion.");
  }
  return archivoReal;
}

function responderTexto(respuesta, estado, mensaje) {
  respuesta.writeHead(estado, {
    "Content-Type": "text/plain; charset=utf-8",
    "X-Content-Type-Options": "nosniff",
  });
  respuesta.end(mensaje);
}

async function atenderSolicitud(raizReal, solicitud, respuesta) {
  if (solicitud.method !== "GET" && solicitud.method !== "HEAD") {
    responderTexto(respuesta, 405, "Metodo no permitido.");
    return;
  }

  try {
    const archivo = await resolverArchivo(raizReal, solicitud.url);
    const contenido = await readFile(archivo);
    respuesta.writeHead(200, {
      "Content-Length": contenido.byteLength,
      "Content-Type":
        TIPOS_MIME.get(extname(archivo).toLowerCase()) ?? "application/octet-stream",
      "X-Content-Type-Options": "nosniff",
    });
    respuesta.end(solicitud.method === "HEAD" ? undefined : contenido);
  } catch (error) {
    if (error instanceof ErrorHttp) {
      responderTexto(respuesta, error.estado, error.message);
      return;
    }
    responderTexto(respuesta, 500, "No se pudo servir la documentacion.");
  }
}

export async function iniciarServidorDocumentacion({ raiz, puerto, host }) {
  if (!HOSTS_LOOPBACK.has(host)) {
    throw new Error("El servidor de documentacion solo admite un host loopback.");
  }
  if (!Number.isInteger(puerto) || puerto < 0 || puerto > 65535) {
    throw new Error("El puerto debe ser un entero entre 0 y 65535.");
  }

  const raizReal = await realpath(resolve(raiz));
  const informacionRaiz = await stat(raizReal);
  if (!informacionRaiz.isDirectory()) {
    throw new Error("La raiz documental debe ser un directorio.");
  }

  const servidor = createServer((solicitud, respuesta) => {
    void atenderSolicitud(raizReal, solicitud, respuesta);
  });
  await new Promise((resolver, rechazar) => {
    servidor.once("error", rechazar);
    servidor.listen(puerto, host, () => {
      servidor.off("error", rechazar);
      resolver();
    });
  });
  return servidor;
}

function leerArgumentos(argumentos) {
  const opciones = { host: "127.0.0.1", puerto: 8765, raiz: "site" };
  for (let indice = 0; indice < argumentos.length; indice += 2) {
    const bandera = argumentos[indice];
    const valor = argumentos[indice + 1];
    if (valor === undefined) throw new Error(`Falta el valor de ${bandera}.`);
    if (bandera === "--host") opciones.host = valor;
    else if (bandera === "--puerto") opciones.puerto = Number(valor);
    else if (bandera === "--raiz") opciones.raiz = valor;
    else throw new Error(`Argumento no reconocido: ${bandera}.`);
  }
  return opciones;
}

function esEjecucionDirecta() {
  return Boolean(process.argv[1]) && pathToFileURL(process.argv[1]).href === import.meta.url;
}

async function ejecutar() {
  const opciones = leerArgumentos(process.argv.slice(2));
  const servidor = await iniciarServidorDocumentacion(opciones);
  console.log(`Documentacion disponible en http://${opciones.host}:${opciones.puerto}/`);

  const cerrar = () => {
    servidor.close((error) => {
      if (error) {
        console.error("No se pudo cerrar el servidor de documentacion.");
        process.exitCode = 1;
      }
    });
  };
  process.once("SIGINT", cerrar);
  process.once("SIGTERM", cerrar);
}

if (esEjecucionDirecta()) {
  ejecutar().catch((error) => {
    console.error(error instanceof Error ? error.message : String(error));
    process.exitCode = 1;
  });
}
