import { strict as afirmar } from "node:assert";
import { mkdtemp, mkdir, rm, symlink, writeFile } from "node:fs/promises";
import { get } from "node:http";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test as prueba } from "node:test";

import { iniciarServidorDocumentacion } from "../../scripts/servir_documentacion.mjs";

function solicitar(puerto, ruta) {
  return new Promise((resolver, rechazar) => {
    const solicitud = get(
      { host: "127.0.0.1", port: puerto, path: ruta },
      (respuesta) => {
        const fragmentos = [];
        respuesta.on("data", (fragmento) => fragmentos.push(fragmento));
        respuesta.on("end", () => {
          resolver({
            cuerpo: Buffer.concat(fragmentos).toString("utf8"),
            encabezados: respuesta.headers,
            estado: respuesta.statusCode,
          });
        });
      },
    );
    solicitud.on("error", rechazar);
  });
}

async function cerrar(servidor) {
  await new Promise((resolver, rechazar) => {
    servidor.close((error) => (error ? rechazar(error) : resolver()));
  });
}

prueba("sirve la raiz, directorios e MIME desde una raiz confinada", async (contexto) => {
  const base = await mkdtemp(join(tmpdir(), "tramalia-docs-"));
  const raiz = join(base, "site");
  await mkdir(join(raiz, "interfaz"), { recursive: true });
  await writeFile(join(raiz, "index.html"), "<h1>Inicio</h1>", "utf8");
  await writeFile(join(raiz, "interfaz", "index.html"), "<h1>Interfaz</h1>", "utf8");
  await writeFile(join(raiz, "estilos.css"), "body { color: black; }", "utf8");

  const servidor = await iniciarServidorDocumentacion({
    host: "127.0.0.1",
    puerto: 0,
    raiz,
  });
  contexto.after(async () => {
    if (servidor.listening) await cerrar(servidor);
    await rm(base, { recursive: true, force: true });
  });

  const direccion = servidor.address();
  afirmar.notEqual(direccion, null);
  afirmar.equal(typeof direccion, "object");
  afirmar.equal(direccion.address, "127.0.0.1");

  const inicio = await solicitar(direccion.port, "/");
  afirmar.equal(inicio.estado, 200);
  afirmar.match(inicio.encabezados["content-type"], /^text\/html; charset=utf-8$/);
  afirmar.equal(inicio.cuerpo, "<h1>Inicio</h1>");

  const interfaz = await solicitar(direccion.port, "/interfaz/");
  afirmar.equal(interfaz.estado, 200);
  afirmar.equal(interfaz.cuerpo, "<h1>Interfaz</h1>");

  const estilos = await solicitar(direccion.port, "/estilos.css");
  afirmar.equal(estilos.estado, 200);
  afirmar.match(estilos.encabezados["content-type"], /^text\/css; charset=utf-8$/);
});

prueba("responde 404 y rechaza traversal despues de decodificar la URL", async (contexto) => {
  const base = await mkdtemp(join(tmpdir(), "tramalia-docs-"));
  const raiz = join(base, "site");
  await mkdir(raiz);
  await writeFile(join(raiz, "index.html"), "inicio", "utf8");
  await writeFile(join(base, "secreto.txt"), "no servir", "utf8");

  const servidor = await iniciarServidorDocumentacion({
    host: "127.0.0.1",
    puerto: 0,
    raiz,
  });
  contexto.after(async () => {
    if (servidor.listening) await cerrar(servidor);
    await rm(base, { recursive: true, force: true });
  });
  const direccion = servidor.address();
  afirmar.notEqual(direccion, null);
  afirmar.equal(typeof direccion, "object");

  afirmar.equal((await solicitar(direccion.port, "/ausente.txt")).estado, 404);
  afirmar.equal((await solicitar(direccion.port, "/%2e%2e/secreto.txt")).estado, 403);
  afirmar.equal((await solicitar(direccion.port, "/%2f..%2fsecreto.txt")).estado, 403);
  afirmar.equal(
    (await solicitar(direccion.port, "/%252e%252e%252fsecreto.txt")).estado,
    403,
  );
});

prueba("rechaza un enlace de directorio que sale de la raiz documental", async (contexto) => {
  const base = await mkdtemp(join(tmpdir(), "tramalia-docs-"));
  const raiz = join(base, "site");
  const exterior = join(base, "exterior");
  await mkdir(raiz);
  await mkdir(exterior);
  await writeFile(join(raiz, "index.html"), "inicio", "utf8");
  await writeFile(join(exterior, "index.html"), "no servir", "utf8");
  await symlink(
    exterior,
    join(raiz, "escape"),
    process.platform === "win32" ? "junction" : "dir",
  );

  const servidor = await iniciarServidorDocumentacion({
    host: "127.0.0.1",
    puerto: 0,
    raiz,
  });
  contexto.after(async () => {
    if (servidor.listening) await cerrar(servidor);
    await rm(base, { recursive: true, force: true });
  });
  const direccion = servidor.address();
  afirmar.notEqual(direccion, null);
  afirmar.equal(typeof direccion, "object");

  afirmar.equal((await solicitar(direccion.port, "/escape/")).estado, 403);
});

prueba("rechaza hosts no loopback y permite un cierre limpio", async () => {
  const base = await mkdtemp(join(tmpdir(), "tramalia-docs-"));
  const raiz = join(base, "site");
  await mkdir(raiz);
  await writeFile(join(raiz, "index.html"), "inicio", "utf8");

  await afirmar.rejects(
    iniciarServidorDocumentacion({ host: "0.0.0.0", puerto: 0, raiz }),
    /loopback/,
  );

  const servidor = await iniciarServidorDocumentacion({
    host: "127.0.0.1",
    puerto: 0,
    raiz,
  });
  await cerrar(servidor);
  afirmar.equal(servidor.listening, false);
  await rm(base, { recursive: true, force: true });
});
