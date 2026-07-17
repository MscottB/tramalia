import { strict as afirmar } from "node:assert";
import { test as prueba } from "node:test";

import { validarEntornoAprobacion } from "../../scripts/verificar_aprobacion_capturas_ux.mjs";

const MENSAJE_ESPERADO =
  "Los snapshots solo se aprueban en Playwright 1.61.1 noble.";
const MENSAJE_COMPARACION_ESPERADO =
  "La aprobacion exige TRAMALIA_COMPARAR_CAPTURAS=1.";

prueba("acepta Linux con el marcador exacto de la imagen canonica", () => {
  afirmar.doesNotThrow(() =>
    validarEntornoAprobacion("linux", "1.61.1-noble", "1"),
  );
});

for (const [plataforma, marcador] of [
  ["linux", undefined],
  ["linux", "1.61.1"],
  ["win32", "1.61.1-noble"],
  ["darwin", "1.61.1-noble"],
]) {
  prueba(`rechaza ${plataforma} con marcador ${String(marcador)}`, () => {
    afirmar.throws(
      () => validarEntornoAprobacion(plataforma, marcador, "1"),
      (error) => error instanceof Error && error.message === MENSAJE_ESPERADO,
    );
  });
}

for (const comparacion of [undefined, "", "0", "true"]) {
  prueba(`rechaza comparacion explicita ${String(comparacion)}`, () => {
    afirmar.throws(
      () => validarEntornoAprobacion("linux", "1.61.1-noble", comparacion),
      (error) =>
        error instanceof Error &&
        error.message === MENSAJE_COMPARACION_ESPERADO,
    );
  });
}
