---
type: Plan
title: OKF Adoption Plan
description: Migration plan for adopting Google Cloud's Open Knowledge Format (OKF v0.1) across
  the project's documentation and knowledge artifacts. Defines type vocabulary, phased migration
  strategy, and Obsidian/OKF coexistence decision.
resource: ../plans/okf_adoption_plan.md
tags: [plan, okf, knowledge, migration, documentation, agents]
timestamp: 2026-06-18
status: Draft
---

## Qué es este plan

Define cómo adoptar el [[Open Knowledge Format (OKF)]] de Google Cloud para estructurar el
conocimiento del proyecto de forma que los agentes de IA puedan filtrarlo por tipo sin tener
que cargar todo `CLAUDE.md`.

## Motivación

Con [[ADR-028 Memory-Mapping-First Integration]] activo, los agentes que trabajan en T30+
necesitan distinguir entre ADRs `accepted` vs `fallback` sin leer los 28 ADRs. OKF permite
ese filtrado con frontmatter YAML estructurado.

## Fases

| Fase | Scope | Prioridad |
|------|-------|-----------|
| F0 | Infraestructura — `docs/knowledge/` + vocabulario | Inmediata |
| F1 | 28 ADRs → entries `type: ADR` | Alta |
| F3 | Integration Bundle (T30) — nace OKF-compliant | Alta (paralela a T30) |
| F2 | Module notes de Obsidian — frontmatter in-place | Media |
| F5 | Planes y procesos | Baja (oportunista) |
| F4 | Calibraciones YAML → wrappers OKF | Baja (diferir) |

## Decisión clave de diseño

**Opción A (recomendada):** agregar frontmatter `---` directamente en los archivos `.md`
existentes de Obsidian. Obsidian v1.0+ procesa YAML frontmatter nativamente.

**Opción B:** vault OKF separado en `docs/knowledge/` con `resource:` apuntando a los
fuentes. Reservar para artefactos no-Markdown (YAML, JSON).

## Vocabulario de tipos definido

`ADR` · `Module` · `Plan` · `Process` · `Calibration` · `GameEntity` · `IntegrationBundle` ·
`ExperimentPlan` · `AssetRecipe` · `Constraint` · `Index` · `AgentMemory`

## Documento completo

Ver [okf_adoption_plan.md](../plans/okf_adoption_plan.md) para spec detallada, ejemplos de
frontmatter, análisis de riesgos y criterios de aceptación por fase.
