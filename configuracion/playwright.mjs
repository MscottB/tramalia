import { defineConfig } from "@playwright/test";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const raizRepositorio = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const raizArtefactos = resolve(raizRepositorio, ".artefactos", "ux", "playwright");

export default defineConfig({
  expect: {
    timeout: 5_000,
  },
  forbidOnly: Boolean(process.env.CI),
  outputDir: resolve(raizArtefactos, "resultados"),
  projects: [{ name: "chromium", use: { browserName: "chromium" } }],
  reporter: [
    ["list"],
    ["html", { open: "never", outputFolder: resolve(raizArtefactos, "reporte") }],
  ],
  snapshotPathTemplate: "{testDir}/{testFilePath}-snapshots/{arg}{ext}",
  testDir: resolve(raizRepositorio, "pruebas", "ux"),
  testMatch: "**/*.spec.mjs",
  timeout: 30_000,
  use: {
    baseURL: "http://127.0.0.1:8765",
    colorScheme: "light",
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
    viewport: { height: 900, width: 1440 },
  },
  webServer: {
    command:
      "node scripts/servir_documentacion.mjs --raiz site --puerto 8765 --host 127.0.0.1",
    cwd: raizRepositorio,
    reuseExistingServer: !process.env.CI,
    timeout: 30_000,
    url: "http://127.0.0.1:8765",
  },
  workers: process.env.CI ? 1 : undefined,
});
