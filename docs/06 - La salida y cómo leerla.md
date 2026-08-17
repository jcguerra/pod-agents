---
titulo: "06 - La salida y cómo leerla"
tipo: nota
proyecto: pod-agents
estado: en-desarrollo
actualizado_en: 2026-08-14
tags:
  - pod-agents
  - salida
  - resultados
---

# La salida del sistema y cómo leerla

El sistema muestra sus resultados **en la terminal** (una ventana de texto). No
tiene todavía una interfaz visual (está planeada). Esta nota explica qué imprime
en cada etapa y **qué significa cada parte**, para que puedas leer un resultado
sin ayuda.

## Mientras corre: las "trazas"

Durante toda la ejecución, el sistema imprime una línea por cada paso, para que
veas el proceso por dentro:

```
▶  design         │ start
   ↳ tool check_trademark(phrase='...')      ok   0.01s
   ↳ tool generate_design_concept(brief=...) ok   0.02s
✔  design         │ end                            6.20s
```

Cómo leerlo:

- `▶ ... start` / `✔ ... end`: un agente **empezó** y **terminó**. El número del
  final es cuánto tardó.
- `↳ tool ...`: el agente usó una **herramienta** (una acción concreta). `ok`
  significa que salió bien; `ERR` que falló.

Esto es solo para seguir el progreso; el resultado importante viene al final.

---

## Salida de la Etapa 1 (descubrimiento)

Al terminar `discover`, ves tres cosas:

**1. La decisión del director** — la ocasión, el tema de diseño y el nombre
corto (`slug`) del tema:

```
Occasion: 'halloween'  |  Niche: 'halloween-nurse-mom'  |  Year: 2026
```

**2. El bloque de 20 keywords**, agrupado por tipo:

```
Keyword block (5 head / 12 mid / 3 long-tail):
  [head    |occasion   ] halloween shirt
  [mid     |role       ] halloween nurse shirt
  [long_tail|formula   ] funny halloween nurse mom gift
  ...
```

- **head / mid / long_tail** = keywords cortas (2 palabras), medianas (3) y
  largas (4+). La mezcla 5/12/3 es una fórmula fija del negocio.
- La etiqueta del medio (`occasion`, `role`, `formula`...) es el **eje** del que
  salió esa palabra. Ver [[07 - Glosario]] → *ejes*.

**3. Las instrucciones del próximo paso** (la compuerta humana): qué correr en
eRank y qué comando usar para importar.

---

## Salida de la validación (lo más importante de leer)

Cuando corrés la Etapa 2, lo primero que ves es el **reporte de validación**.
Este es el corazón de la decisión de negocio. Se ve así:

```
SOP analysis for 'halloween-nurse-mom' — 3 fit keyword(s)
(survival needs >=2 with KD<=85, searches>=100):
  [fit  |mid      ] halloween nurse shirt — searches=1400, comp=1200, KD=52, R=1.17
  [unfit|head     ] nurse gift            — searches=90,   comp=8000, KD=88, R=0.01
  [trap |long_tail] cute nurse halloween  — searches=10,   comp=45000, KD=70, R=0.0
VERDICT: SURVIVES
```

### Qué significa cada columna

| Dato | Qué es | Regla |
|---|---|---|
| **decision** | Veredicto de esa keyword | `fit` (sirve), `unfit` (no sirve), `trap` (trampa) |
| **searches** | Cuánta gente la busca (demanda) | Tiene que ser **≥ 100** para servir |
| **comp** | Cuántos listados compiten (competencia) | Cuanto más baja, mejor |
| **KD** | Dificultad de posicionar (0–100) | Tiene que ser **≤ 85** para servir |
| **R** | Ratio demanda ÷ competencia | ≥ 0.02 verde · 0.01–0.02 amarillo · < 0.01 rojo |

### Las tres decisiones posibles por keyword

- **`fit` (sirve):** pasa el filtro principal (búsquedas ≥ 100 **y** dificultad
  ≤ 85). Estas son las palabras que valen.
- **`unfit` (no sirve):** no llega al umbral. No la usamos.
- **`trap` (trampa):** parece atractiva pero es una emboscada — casi nadie la
  busca **y** la estantería está llena de competencia. Se descarta siempre.

### El veredicto final

- **`VERDICT: SURVIVES`** → el tema tiene **al menos 2 keywords `fit`**. El
  sistema sigue a producción.
- **`VERDICT: FAILED`** → menos de 2 keywords buenas. El sistema se detiene y hay
  que armar otra ronda. Ver [[05 - Flujo del proceso]] → *bucle de reintento*.

> [!info] ¿Por qué "al menos 2"?
> Un solo acierto puede ser suerte o un dato borde. Con dos o más keywords
> buenas, el tema tiene demanda real y sostenible. Es una regla del SOP v1.1 del
> negocio, no un número arbitrario.

---

## Salida de la Etapa 2 (producción)

Si el tema sobrevive, al final ves el **resultado de cada agente**, uno debajo
del otro:

```
### design ###
- Brief: ilustración vectorial minimalista, 2 colores...
- Trademark check: OK, sin coincidencias en la blocklist
- Generated concept: concept_v1.svg (300 DPI, 4500x5400px)

### production ###
- Product created: remera, costo base $12.50, 3 mockups, tallas S–XXL
- Meets margin?: sí

### marketing ###
- Title: Funny Halloween Nurse Mom Shirt...
- Tags (13): halloween nurse, nurse mom, ...
- Description: ...
- Price: $24.99

### operations ###
- Listing status (DRAFT): [DRAFT created, pending human approval]
- Pending human approval: publicar en Etsy
```

### Cómo leer cada bloque

- **design:** el concepto visual + la **revisión de marcas** (que no use marcas
  registradas) + el archivo generado.
- **production:** el producto creado en el proveedor, su **costo** y si **cumple
  el margen** del 40%.
- **marketing:** el **título**, los **13 tags**, la **descripción** y el
  **precio** (siempre dentro del tope de $35).
- **operations:** el estado final. **Siempre dice DRAFT (borrador)** y lista lo
  que queda pendiente de aprobación humana.

> [!important] La última palabra la tenés vos
> El sistema nunca termina en "publicado". Termina en **borrador**. Ese es el
> punto en el que una persona revisa el listado en Etsy y decide si sale al aire.
> Los datos de Printify y Etsy hoy son de ejemplo (simulados); cuando se conecten
> de verdad, este mismo formato mostrará datos reales.

---

Siguiente: [[07 - Glosario]] · Volver al [[MOC - POD Agents]]
