# OKF Adoption Plan — Open Knowledge Format Migration

## Status

Draft — awaiting review. Created 2026-06-18.

---

## 1. Contexto y motivación

### ¿Qué es OKF?

El **Open Knowledge Format (OKF)** es una especificación abierta publicada por Google Cloud el
12 de junio de 2026 (v0.1, autores: Sam McVeety y Amir Hormati). Formaliza el patrón "LLM
wiki" que ya existe en proyectos como este (CLAUDE.md / AGENTS.md) como un estándar portable y
vendor-neutral.

**Principio central:** el conocimiento de un proyecto se representa como un **directorio de
archivos Markdown con YAML frontmatter**, sin SDK, sin query language, sin registry. Un
ingeniero puede `cat` un concepto; un agente puede ingestarlo verbatim en contexto.

### Referencia oficial

| Recurso | URL |
|---------|-----|
| Repo oficial | https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf |
| Spec (SPEC.md) | https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md |
| Google Cloud Blog | https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing/ |

### Relación con otros protocolos

```
MCP (Anthropic/OpenAI)  →  cómo el agente conecta tools y data en runtime
OKF (Google Cloud)      →  qué sabe el agente sobre esas fuentes ANTES de tocarlas
CLAUDE.md / AGENTS.md   →  contexto de proceso; OKF lo complementa con contexto estructurado
```

---

## 2. Formato OKF — Spec resumida

Cada concepto es exactamente un archivo Markdown con dos partes:

```markdown
---
type: <string>         # REQUERIDO — el único campo obligatorio
title: <string>        # recomendado
description: <string>  # recomendado
resource: <url|path>   # URL o path al artefacto que describe
tags: [a, b, c]        # lista para filtrado
timestamp: YYYY-MM-DD  # última actualización del concepto
# campos extra: permitidos; consumidores deben tolerar claves desconocidas
---

Cuerpo Markdown libre. Puede incluir tablas, listas, ejemplos, links estándar.
```

**Reglas de la spec:**
- El directorio de entries se llama convencionalmente `knowledge/` o `docs/knowledge/`
- Cada concept = un archivo; nunca multi-concepto por archivo
- Los links son Markdown estándar `[text](path)` — no wikilinks propietarios
- Los productores pueden agregar campos; los consumidores DEBEN tolerar claves desconocidas
- No hay schema registry, no hay validador oficial en v0.1

---

## 3. Diagnóstico: estado actual del proyecto vs OKF

### 3.1 Lo que ya existe y es OKF-compatible

| Artefacto actual | Equivalente OKF | Estado |
|------------------|-----------------|--------|
| `CLAUDE.md` | Archivo de contexto raíz | Compatible — sin frontmatter |
| `AGENTS.md` | Archivo de contexto raíz | Compatible — sin frontmatter |
| `docs/obsidian/ADR-*.md` | `type: ADR` entries | Tiene contenido; falta frontmatter |
| `docs/obsidian/00 - Project Overview.md` | `type: Index` | Tiene contenido; falta frontmatter |
| `docs/obsidian/*.md` (módulos) | `type: Module` | Tiene contenido; falta frontmatter |
| `docs/adr/ADR-*.md` | `type: ADR` (fuente) | Tiene contenido; falta frontmatter |
| `specs/calibration/*.yaml` | `type: Calibration` | YAML puro — no OKF |
| `plans/*.yaml` | `type: ExperimentPlan` | YAML puro — no OKF |
| `docs/plans/*.md` | `type: Plan` | Tiene contenido; falta frontmatter |
| `.claude/projects/.../memory/*.md` | `type: AgentMemory` | Ya usa `---` frontmatter propio |

### 3.2 Gaps identificados

1. **Sin frontmatter estructurado**: todos los archivos `.md` existentes carecen de bloque `---`
   con `type`. Los agentes leen todo el contexto cargado sin poder filtrar por tipo.

2. **Wikilinks Obsidian vs links Markdown**: el vault usa `[[ADR-028 Memory-Mapping-First
   Integration]]`; OKF requiere `[ADR-028](../adr/ADR-028.md)`. Tensión de formato.

3. **Artefactos de calibración en YAML puro**: `specs/calibration/` contiene datos de
   calibración en YAML sin capa descriptiva para agentes.

4. **Integration bundle sin entry OKF**: el nuevo artefacto de ADR-028
   (`integration_bundle.schema.json`) no tiene descripción de concepto estructurada.

5. **Vocabulario de `type` no definido**: sin un vocabulario acordado, cada contribuidor
   inventará tipos distintos, degradando la utilidad del filtrado.

### 3.3 Lo que NO debe migrar a OKF

- `evidence/private/` — gitignoreado, privado, nunca en el vault de conocimiento
- `specs/traces/gng_trace.json` — artefacto de datos privados intermedios
- Frames, AVI, savestates — bloqueados por ADR-001/003 y guardrails
- ROMs, sprites, audio original — prohibido por las guardrails del proyecto
- Archivos de configuración de herramientas (`.venv/`, `pyproject.toml`, etc.)

---

## 4. Vocabulario de tipos para este proyecto

Definir el vocabulario antes de la migración evita drift. Los tipos propuestos son:

| type | Descripción | Archivos típicos |
|------|-------------|-----------------|
| `ADR` | Architectural Decision Record | `docs/adr/ADR-*.md`, `docs/obsidian/ADR-*.md` |
| `Module` | Descripción de un módulo o capa de la arquitectura | `docs/obsidian/Vision Layer.md`, etc. |
| `Plan` | Plan de implementación de un workstream | `docs/plans/*.md` |
| `Process` | Proceso operativo o workflow reproducible | `docs/obsidian/*.md` de proceso |
| `Calibration` | Constantes calibradas y su metodología | Wrappers sobre `specs/calibration/*.yaml` |
| `GameEntity` | Arquetipo de entidad del juego observada | Futuros docs de entidades |
| `IntegrationBundle` | Bundle declarativo de integración por juego (ADR-028) | `blackbox.local.integration_bundle.example.yaml` + wrapper |
| `ExperimentPlan` | Plan de experimento de calibración aislado (ADR-024) | Wrappers sobre `plans/sequences/gng_exp_*.yaml` |
| `AssetRecipe` | Receta de asset original con restricciones de originalidad | `packages/asset-factory/` |
| `Constraint` | Guardrail o restricción legal/técnica inviolable | Clean-room rules, ADR-001 |
| `Index` | Documento de índice del vault | `00 - Project Overview.md` |
| `AgentMemory` | Memoria persistente del agente (sistema propio del proyecto) | `.claude/.../memory/*.md` |

---

## 5. Plan de migración

La migración es **incremental y no destructiva**: agregar frontmatter a archivos existentes
no rompe ningún workflow. La prioridad es por impacto en la calidad del contexto del agente.

### Fase 0 — Infraestructura (prerrequisito, sin migraciones aún)

**Objetivo:** dejar la infraestructura lista antes de tocar archivos.

| Tarea | Descripción | Esfuerzo |
|-------|-------------|----------|
| F0.1 | Crear `docs/knowledge/` como directorio raíz del vault OKF | Bajo |
| F0.2 | Definir y documentar el vocabulario de tipos (esta sección §4) | Bajo |
| F0.3 | Agregar `docs/knowledge/` al `CLAUDE.md` como fuente de contexto estructurado | Bajo |
| F0.4 | Decidir estrategia de coexistencia Obsidian ↔ OKF (ver §6) | Medio |

**Criterio de aceptación F0:** existe `docs/knowledge/README.md` con el vocabulario de tipos
definido y al menos un archivo de ejemplo con frontmatter válido.

---

### Fase 1 — ADRs (alto impacto, bajo riesgo)

**Objetivo:** los 28 ADRs son los documentos más críticos para el agente. Tenerlos con
frontmatter permite filtrar `type: ADR` sin cargar CLAUDE.md completo.

**Estrategia:** crear entries OKF en `docs/knowledge/adr/` que apunten a los ADRs fuente en
`docs/adr/` como `resource:`. No duplicar contenido; el OKF es la capa de metadatos.

**Ejemplo de entry:**

```markdown
---
type: ADR
title: ADR-028 Memory-Mapping-First Integration
description: Declares the MAME RAM tap (ADR-026) as the default entity position/state source.
  Demotes CV pipeline (ADR-012/013/021/022) and human pickers (ADR-019/020) to fallback.
  Introduces declarative per-game integration bundle.
resource: ../../adr/ADR-028-memory-mapping-first-integration.md
tags: [adr, architecture, memory-tap, integration, ram, accepted]
timestamp: 2026-06-18
status: Accepted
supersedes: [ADR-025, ADR-027]
demotes_to_fallback: [ADR-012, ADR-013, ADR-019, ADR-020, ADR-021, ADR-022]
---

ADR-028 establece el memory tap de MAME (Lua + cheat DB) como fuente principal de posición
y estado de entidades. La pipeline CV queda como fallback para juegos sin mapa de memoria.

Ver [ADR-026](../../adr/ADR-026-internal-state-observation-boundary.md) para el boundary
de clean-room del memory tap.
```

| Tarea | ADRs | Esfuerzo |
|-------|------|----------|
| F1.1 | ADRs activos de arquitectura core (001–011) | Medio |
| F1.2 | ADRs de visión y calibración (012–024) | Medio |
| F1.3 | ADRs de integración (026, 028) | Bajo |

**Criterio de aceptación F1:** 28 entries `type: ADR` en `docs/knowledge/adr/`, cada uno con
`resource:` apuntando al ADR fuente, `status:`, y `tags:` correctos.

---

### Fase 2 — Módulos de arquitectura

**Objetivo:** los module notes de `docs/obsidian/` describen las capas del sistema. Son la
segunda fuente de contexto más leída por agentes.

**Estrategia:** agregar frontmatter directamente en los archivos Obsidian existentes (no
duplicar). Mantener wikilinks Obsidian en el cuerpo; el frontmatter agrega la capa OKF.

**Ejemplo:**

```markdown
---
type: Module
title: Vision Layer
description: OpenCV + MOG2 background subtraction pipeline for entity detection in MAME frames.
  Demoted to fallback by ADR-028; primary source is now the memory tap.
resource: ../../packages/vision/
tags: [module, vision, opencv, mog2, cv-fallback]
timestamp: 2026-06-10
governed_by: [ADR-006, ADR-012, ADR-013, ADR-021, ADR-022]
status: fallback  # demoted by ADR-028
---
```

| Tarea | Archivos | Esfuerzo |
|-------|----------|----------|
| F2.1 | `Vision Layer.md`, `Guardrails.md`, `MAME Runner.md` | Bajo |
| F2.2 | `Asset Factory.md`, `Behavioral Validation.md`, `Source Profile.md` | Bajo |
| F2.3 | `Input Plan.md`, `Preflight.md`, `Private vs Public Boundary.md` | Bajo |
| F2.4 | `Public Original Game Definition Layer.md`, `React Native Prototype.md` | Bajo |

**Criterio de aceptación F2:** todos los module notes tienen frontmatter válido con `type:
Module`, `governed_by:` listando los ADRs aplicables, y `status:` si aplica.

---

### Fase 3 — Integration Bundle y nuevos artefactos (ADR-028)

**Objetivo:** los artefactos de T30 (integration bundle, address search) son nuevos y deben
nacer OKF-compliant desde el primer día. Esta fase se ejecuta en paralelo con T30.

| Tarea | Descripción | Esfuerzo |
|-------|-------------|----------|
| F3.1 | Entry `type: IntegrationBundle` para `gng` cuando el bundle esté completo | Bajo |
| F3.2 | Entry `type: Process` para el address search workflow (ADR-028) | Bajo |
| F3.3 | Entry `type: Constraint` para las clean-room rules del memory tap (ADR-026) | Bajo |

**Criterio de aceptación F3:** cualquier agente que ejecute T30+ puede cargar
`docs/knowledge/` y encontrar el bundle GNG, el proceso de address search y las constraints
del memory tap sin leer CLAUDE.md completo.

---

### Fase 4 — Calibraciones y entidades

**Objetivo:** los artefactos de `specs/calibration/` contienen constantes calibradas
valiosas para agentes de asset design y validación. Necesitan una capa descriptiva.

**Estrategia:** crear entries OKF en `docs/knowledge/calibration/` con `resource:` apuntando
a los YAML de calibración. El YAML sigue siendo la fuente de verdad; OKF es la descripción.

**Ejemplo:**

```markdown
---
type: Calibration
title: GNG Physics Calibration
description: Horizontal and vertical velocity constants for Arthur's projectiles and jump arc.
  Calibrated via T10.7 (ADR-024 designed isolation experiments).
resource: ../../specs/calibration/gng_physics_calibration.yaml
tags: [calibration, physics, gng, projectile, jump]
timestamp: 2026-06-10
method: ADR-024  # designed isolation experiment
validated_by: human  # ADR-019 human-validated candidates
game: gng
---
```

| Tarea | Descripción | Esfuerzo |
|-------|-------------|----------|
| F4.1 | Inventariar todos los archivos en `specs/calibration/` | Bajo |
| F4.2 | Crear entries OKF por cada artefacto de calibración | Medio |
| F4.3 | Entry `type: GameEntity` para las firmas de entidades calibradas | Medio |

**Criterio de aceptación F4:** un agente de asset design puede consultar `type: Calibration`
y obtener todas las constantes de GNG con su método de validación, sin acceder a `specs/`.

---

### Fase 5 — Planes y procesos

**Objetivo:** los planes de implementación en `docs/plans/` son relevantes para handoffs.
Agregar frontmatter permite a un agente filtrar planes activos vs archivados.

| Tarea | Descripción | Esfuerzo |
|-------|-------------|----------|
| F5.1 | Frontmatter en planes activos (`memory_mapping_first_rearchitecture_plan.md`, etc.) | Bajo |
| F5.2 | Frontmatter en plans archivados (con `status: archived`) | Bajo |
| F5.3 | Entry `type: Process` para boot sequence, frame extraction workflow | Bajo |

---

## 6. Decisión de diseño: coexistencia Obsidian ↔ OKF

Esta es la decisión de mayor impacto. Dos opciones:

### Opción A — Frontmatter in-place en archivos Obsidian (recomendada)

Agregar el bloque `---` directamente a los archivos `docs/obsidian/*.md`. Obsidian procesa
el frontmatter YAML nativamente desde v1.0 — lo muestra en el panel de propiedades y no
rompe el renderizado. Los wikilinks `[[...]]` se mantienen en el cuerpo.

- **Ventaja:** una sola fuente de verdad; no hay archivos duplicados
- **Ventaja:** Obsidian muestra el frontmatter como propiedades del documento
- **Desventaja:** los wikilinks en el cuerpo no son OKF-puro (OKF prefiere Markdown links)
- **Tensión:** los wikilinks `[[ADR-028 Memory-Mapping-First Integration]]` son Obsidian,
  no Markdown estándar. Los agentes los pueden leer pero no navegar programáticamente.

**Veredicto:** aceptable. OKF no prohíbe wikilinks en el cuerpo — solo aplica el frontmatter
como contrato. El cuerpo es libre.

### Opción B — Vault OKF separado en `docs/knowledge/`

Crear archivos OKF en `docs/knowledge/` que apunten con `resource:` a los archivos Obsidian
fuente. Sin modificar el vault Obsidian.

- **Ventaja:** separación limpia; el vault Obsidian no se toca
- **Desventaja:** doble mantenimiento — si el ADR se actualiza hay que actualizar dos archivos
- **Desventaja:** los entries serían mayormente metadatos vacíos que apuntan a otro lugar

**Veredicto:** preferible solo para artefactos que NO son Markdown (YAML de calibración,
JSON de schemas, etc.) — ahí un wrapper OKF tiene sentido claro.

### Decisión propuesta

**Opción A** para archivos `.md` (agregar frontmatter in-place).
**Opción B** para artefactos no-Markdown (YAML, JSON) — crear wrappers `.md` en
`docs/knowledge/`.

---

## 7. Impacto en el workflow de agentes

### Antes de OKF (estado actual)

```
Agente inicia tarea
  → lee CLAUDE.md completo (4000+ tokens)
  → lee AGENTS.md completo
  → navega docs/obsidian/ buscando el módulo relevante
  → no puede filtrar por tipo de documento
```

### Después de OKF (estado objetivo)

```
Agente inicia tarea con scope "calibración de física"
  → carga docs/knowledge/ índice (tokens mínimos)
  → filtra type: Calibration, type: ADR → obtiene 3-5 archivos relevantes
  → carga solo esos archivos con contexto preciso
  → CLAUDE.md se carga solo si el agente necesita contexto de proceso
```

### Beneficio para este proyecto específico

Con ADR-028 activo, la arquitectura tiene dos capas de fuentes de verdad (memory tap vs CV
fallback). Los agentes que trabajan en T30+ necesitan saber qué ADRs están `status: accepted`
vs `status: fallback` sin leer los 28 ADRs. OKF permite ese filtrado directamente.

---

## 8. Criterios de éxito global

| Criterio | Indicador |
|----------|-----------|
| Cobertura de ADRs | 28/28 entries `type: ADR` en `docs/knowledge/adr/` |
| Cobertura de módulos | 10/10 module notes con frontmatter válido |
| Nuevos artefactos | Cualquier nuevo artefacto arquitectural nace con frontmatter OKF |
| Filtrado por tipo | Un agente puede cargar `type: ADR status: accepted` sin leer CLAUDE.md |
| Calibraciones accesibles | Todos los artefactos de `specs/calibration/` tienen entry OKF |
| Sin duplicación de contenido | Ningún entry OKF duplica el cuerpo del archivo fuente |
| Compatibilidad Obsidian | El vault Obsidian sigue funcionando sin cambios de UX |

---

## 9. Riesgos y mitigaciones

| Riesgo | Probabilidad | Mitigación |
|--------|-------------|------------|
| OKF v0.1 cambia el schema antes de que completemos la migración | Media | Los campos extra son tolerados; cambios en `type` solo requieren renombrar strings |
| Drift entre OKF entry y archivo fuente (descripción desactualizada) | Alta | Revisar entries OKF como parte del checklist de actualización de ADRs |
| Wikilinks en cuerpo rompen consumo programático | Baja | OKF no parsea el cuerpo; solo el frontmatter. Wikilinks son cuerpo libre |
| Sobrecarga de mantenimiento en Fase 4 (calibraciones) | Media | Ejecutar Fase 4 solo cuando un agente activo necesite ese contexto |
| Vocabulario de `type` drift entre contribuidores | Media | Publicar el vocabulario §4 en `docs/knowledge/README.md` como fuente canónica |

---

## 10. Orden de ejecución recomendado

```
F0 (infraestructura)           ← hacer ahora, no bloquea nada
  ↓
F1 (ADRs)                      ← mayor ROI; contexto más crítico para agentes
  ↓
F3 (Integration Bundle / T30)  ← ejecutar en paralelo con T30, no esperarlo
  ↓
F2 (módulos Obsidian)          ← bajo esfuerzo, medio impacto
  ↓
F5 (planes y procesos)         ← oportunista: agregar al actualizar planes existentes
  ↓
F4 (calibraciones)             ← diferir hasta que un agente lo necesite
```

---

## 11. Próximos pasos inmediatos

1. **Revisar y aprobar** este plan (Matias)
2. **Decidir** Opción A vs B para el vault Obsidian (§6) — recomendación: Opción A
3. **Ejecutar F0**: crear `docs/knowledge/`, vocabulario, ejemplo
4. **Ejecutar F1**: entries OKF para los ADRs, empezando por ADR-028, ADR-026, ADR-001
5. **Integrar F3 en T30**: el integration bundle de GNG nace OKF-compliant

---

## Referencias

- [OKF SPEC.md — GoogleCloudPlatform](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
- [Google Cloud Blog — How the Open Knowledge Format can improve data sharing](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing/)
- [ADR-028 Memory-Mapping-First Integration](../adr/ADR-028-memory-mapping-first-integration.md)
- [ADR-001 Clean-Room Layered Architecture](../adr/ADR-001-four-layer-clean-room-architecture.md)
- [Memory-Mapping-First Re-Architecture Plan](./memory_mapping_first_rearchitecture_plan.md)
- [CLAUDE.md](../../CLAUDE.md)
- [AGENTS.md](../../AGENTS.md)
