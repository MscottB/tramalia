# 11 — Reglas de UX/UI (gate UX/UI)

Verificación delegada: Lighthouse CI · axe-core/pa11y · Playwright · Storybook (`tramalia ux`).
Se activa solo si hay frontend.

## Reglas obligatorias
- Design system / tokens: colores, tipografía, espaciado y componentes consistentes (sin valores sueltos).
- Estados obligatorios por vista: cargando, vacío, error, éxito, deshabilitado.
- Responsive: breakpoints definidos; sin scroll horizontal accidental.
- Accesibilidad WCAG AA: contraste, foco visible, navegación por teclado, ARIA, textos alternativos.
- Feedback ante latencia: spinners/skeletons; ninguna acción sin respuesta.
- Jerarquía visual clara e i18n (sin textos hardcodeados si el proyecto es multilenguaje).
