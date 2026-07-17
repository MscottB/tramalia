import { pathToFileURL } from "node:url";

const MENSAJE_ENTORNO_INVALIDO =
  "Los snapshots solo se aprueban en Playwright 1.61.1 noble.";
const MENSAJE_COMPARACION_INVALIDA =
  "La aprobacion exige TRAMALIA_COMPARAR_CAPTURAS=1.";

export function validarEntornoAprobacion(plataforma, marcador, comparacion) {
  if (plataforma !== "linux" || marcador !== "1.61.1-noble") {
    throw new Error(MENSAJE_ENTORNO_INVALIDO);
  }
  if (comparacion !== "1") {
    throw new Error(MENSAJE_COMPARACION_INVALIDA);
  }
}

function esEjecucionDirecta() {
  return Boolean(process.argv[1]) && pathToFileURL(process.argv[1]).href === import.meta.url;
}

if (esEjecucionDirecta()) {
  try {
    // El marcador evita aprobaciones accidentales; la imagen fijada aporta la reproducibilidad.
    validarEntornoAprobacion(
      process.platform,
      process.env.TRAMALIA_IMAGEN_PLAYWRIGHT,
      process.env.TRAMALIA_COMPARAR_CAPTURAS,
    );
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error));
    process.exitCode = 1;
  }
}
