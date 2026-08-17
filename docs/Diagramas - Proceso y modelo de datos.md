---
titulo: "Diagramas - Proceso y modelo de datos"
tipo: diagramas
proyecto: pod-agents
estado: en-definicion
actualizado_en: 2026-08-16
tags:
  - pod-agents
  - diagramas
  - proceso
  - modelo-de-datos
---

# Diagramas — Proceso y modelo de datos

Dos diagramas del sistema **según las definiciones acordadas**, no según el
código actual. Donde el código todavía no coincide, está marcado.

> [!warning] Estado objetivo, no estado actual
> Estos diagramas reflejan [[Definiciones - Datos, roles y keywords]]. Varias
> piezas todavía no existen en el código: el generador por slots, las tablas
> `keyword_metrics` / `keyword_niches` / `products`, y las categorías `product` y
> `modifier` en `niche_items`.

---

## 1. Proceso completo — de la frase al listing

```mermaid
flowchart TD
    Start(["ETAPA 1 · DISCOVERY"]) --> Mode{"¿Quién elige<br/>el nicho?"}

    %% ---------- Entradas ----------
    Mode -->|"Modo IA<br/>director agent"| IA{"Vía de entrada"}
    IA -->|"Calendario"| IAa["planning_dates<br/>holiday a ~90 días<br/>publicar a 60 · 30 de ranking"]
    IA -->|"Taxonomía"| IAb["Cruce de 2 ítems de niche_items<br/>hobby × rol · rol × career<br/>solo active = TRUE"]
    Mode -->|"Modo Yo Elijo"| MAN["Input ÚNICO:<br/>la frase base manual"]

    IAa --> BASE
    IAb --> BASE
    MAN --> BASE

    BASE["<b>FRASE BASE</b><br/>2-3 palabras · round = 1<br/>ej. tennis mom"]

    %% ---------- Generación ----------
    BASE --> GEN["<b>Generador de variantes por slot</b><br/>un solo slot por vez"]

    subgraph SLOTS ["Slots · fuente: niche_items con active = TRUE"]
        direction LR
        S1["<b>ROLE</b> · replace<br/>career + family_relation<br/>tennis aunt"]
        S2["<b>PRODUCT</b> · add<br/>category = product<br/>tennis mom shirt"]
        S3["<b>MODIFIER</b> · add<br/>prefijo / sufijo<br/>funny tennis mom"]
        S4["<b>YEAR</b> · add<br/>actual o siguiente<br/>tennis mom 2027"]
    end

    SLOTS -.-> GEN
    GEN --> PRE["Pre-filtros<br/>trademark blocklist<br/>apparel trademarks"]
    PRE --> ALL["<b>TODAS las combinaciones</b><br/>sin cuota 5/12/3<br/>head/mid/long_tail solo descriptivo"]

    ALL --> STAGE[("Persistir<br/>keywords + keyword_niches<br/>base_keyword_id · slot · slot_op · round<br/>decision = pending")]
    ALL --> BLOCKS["<b>Salida</b><br/>lista completa visible<br/>+ bloques de 20 por comas"]

    %% ---------- Gate humano ----------
    BLOCKS --> GATE

    subgraph GATE ["🧑 GATE HUMANO"]
        direction LR
        G1["Pegar bloque de 20 en<br/>eRank Bulk Keyword Tool<br/>100 req/día = 2000 kw/día"] --> G2["Exportar CSV"]
    end

    GATE --> IMP["import_erank<br/>lowercase + measured_on"]
    IMP --> METRICS[("keyword_metrics<br/><b>append-only</b><br/>nunca pisa lo anterior")]

    %% ---------- Filtro ----------
    METRICS --> CLS["<b>classify</b> · una fila por vez<br/>sop_validation.py:84 · YA EXISTE"]

    CLS --> T{"¿Trampa?<br/>competition > 10.000<br/>Y searches < 20"}
    T -->|"Sí"| TRAP["decision = <b>trap</b><br/>descarte automático"]
    T -->|"No"| F{"KD ≤ 85<br/>searches ≥ 100<br/>ratio R ≥ 0,01"}
    F -->|"No"| UNFIT["decision = <b>unfit</b>"]
    F -->|"Sí"| FIT["decision = <b>FIT</b> ✅<br/>frase validada"]

    TRAP --> ROUNDEND
    UNFIT --> ROUNDEND
    FIT --> ROUNDEND

    ROUNDEND["Fin de la ronda<br/>contar sobrevivientes"]

    %% ---------- Iteración ----------
    ROUNDEND --> Q1{"¿Hubo<br/>sobrevivientes?"}
    Q1 -->|"No"| DEAD["<b>Callejón</b><br/>sin profundidad"]
    Q1 -->|"Sí"| Q2{"¿Quedan variantes<br/>por generar?"}
    Q2 -->|"Sí"| LOOP["Cada sobreviviente<br/>= NUEVA BASE<br/>round + 1"]
    Q2 -->|"No"| Q3

    LOOP --> GEN

    %% ---------- Cierre ----------
    Q3{"¿La base pasó pero<br/>TODAS las variantes de<br/>producto fallaron?"}
    Q3 -->|"Sí"| NOPROD["<b>Demanda sin producto</b><br/>busca pero no compra objetos<br/>descartar"]
    Q3 -->|"No"| OUT["<b>NICHO VALIDADO</b><br/>frase base + sobrevivientes<br/>count = listings posibles"]

    OUT --> E2(["ETAPA 2 · PRODUCCIÓN<br/>design → production → marketing → operations<br/>listing en DRAFT"])

    DEAD --> NEXTN["Siguiente candidata"]
    NOPROD --> NEXTN
```

### Cómo leerlo

- **El loop es el corazón.** `LOOP → GEN` es la iteración: cada frase que pasa el
  filtro se convierte en base de la ronda siguiente. Ahí es donde se acumulan las
  dimensiones (`tennis aunt` de la ronda 2 puede dar `tennis aunt shirt` en la 3).
- **Nada hereda.** Toda flecha que sale de `GEN` vuelve a pasar por el gate y por
  `classify`. Que la base valide no autoriza a ninguna variante.
- **El único paso manual es el gate.** Todo lo demás es determinístico o de
  agente. Ese cuello de botella es humano, no de cupo (D15).
- **`classify` ya está implementado** y no se toca. Todo lo roto está a su
  izquierda, en cómo se generan las frases.

---

## 2. Modelo de datos (ER)

```mermaid
erDiagram
    keywords ||--o{ keyword_metrics : "se mide en el tiempo"
    keywords ||--o{ keyword_niches : "participa como variante"
    keywords ||--o{ keyword_niches : "participa como base"
    niche_items ||--o{ keyword_niches : "llenó el slot"
    niche_items ||--o| products : "slug ↔ subcategory"

    keywords {
        bigserial id PK
        text keyword UK "SIEMPRE lowercase · N1"
        text keyword_type "generated · head/mid/long_tail · SIN cuota"
        timestamptz created_at
    }

    keyword_metrics {
        bigserial id PK
        bigint keyword_id FK
        text source "eRank | EverBee"
        date measured_on "cuándo MIDIÓ la fuente"
        integer search_volume "0 = menor a 20 · NULL = Unknown"
        integer avg_clicks
        numeric ctr
        integer competition
        smallint difficulty "KD 0-100"
        numeric ratio_r "generated · searches/competition"
    }

    keyword_niches {
        bigserial id PK
        bigint keyword_id FK "la variante"
        bigint base_keyword_id FK "la frase base · self-ref"
        bigint slot_item_id FK "qué ítem llenó el slot · PROPUESTO"
        text slot "role | product | modifier | year"
        text slot_op "replace | add"
        smallint round "ola de exploración · NO es measured_on"
        keyword_decision decision "pending|fit|unfit|trap|to_design|discarded"
        text validation_reason
    }

    niche_items {
        bigserial id PK
        niche_category category "+ product + modifier"
        text name "lowercase · la variante de búsqueda"
        text subcategory "producto canónico | posición del modificador"
        smallint month "solo holidays"
        text day_note
        text seasonality
        smallint popularity "ORDEN DE PRUEBA · no predicción"
        text gender "f | m | neutral"
        boolean is_gift_recipient
        boolean active "el generador filtra por acá"
    }

    products {
        bigserial id PK
        text slug UK
        text name
        text category "apparel|drinkware|bag|home|paper"
        boolean is_apparel
        numeric base_cost
        numeric avg_price
        text design_area
        text printify_blueprint
        boolean active
    }
```

### Las tres decisiones que explican este modelo

**1. `keywords` no tiene métricas.** Es solo la frase canónica. Todas las
mediciones viven en `keyword_metrics`, una fila por `(keyword, fuente, fecha)`.
Reimportar nunca pisa: apila. Es lo que habilita comparar año contra año, algo
que ni eRank ni EverBee dan.

**2. La frase base y sus variantes son la MISMA tabla.** Un nicho no es una
entidad aparte: es una fila de `keywords` que validó. Por eso `keyword_niches`
apunta dos veces a `keywords` — una como variante, otra como base
(`base_keyword_id`). Una frase de la ronda 2 que sobrevive pasa a ser base en la
ronda 3 sin moverse de tabla.

**3. `round` y `measured_on` viven en tablas distintas a propósito.** La ronda es
la ola de exploración y no cambia nunca. `measured_on` es cuándo la fuente midió,
y se agrega una fila nueva cada vez que se re-mide. Confundirlas es lo que hoy
hace que el import pise datos.

### Separación entre taxonomía y comercial

`niche_items` responde **qué medir** (la variante de búsqueda: `tee`, `shirt`,
`graphic tee`). `products` responde **cuánto deja** (costo, precio, área de
diseño, blueprint de Printify). Se vinculan por el slug del producto canónico,
que en `niche_items` vive en `subcategory`.

> [!note] Campo propuesto, todavía no definido
> `keyword_niches.slot_item_id` no está en el documento de definiciones. Lo
> agrego acá porque permite responder *"¿qué roles sobreviven más seguido?"* con
> una consulta, en vez de parsear strings. Si no interesa, se saca sin afectar al
> resto.

---

## Relacionado

- [[Definiciones - Datos, roles y keywords]]
- [[05 - Flujo del proceso]]
- [[MOC - POD Agents]]
