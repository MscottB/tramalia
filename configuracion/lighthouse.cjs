const { chromium } = require("playwright");

module.exports = {
  ci: {
    assert: {
      assertions: {
        "categories:accessibility": ["error", { minScore: 0.95 }],
        "categories:best-practices": ["error", { minScore: 0.9 }],
        "categories:performance": ["error", { minScore: 0.85 }],
        "categories:seo": ["error", { minScore: 0.9 }],
      },
    },
    collect: {
      chromePath: chromium.executablePath(),
      numberOfRuns: 3,
      staticDistDir: "./site",
      url: [
        "http://localhost/",
        "http://localhost/en/",
        "http://localhost/interfaz/",
      ],
    },
    upload: {
      outputDir: ".artefactos/ux/lighthouse",
      target: "filesystem",
    },
  },
};
