---
titulo: "Definiciones - Datos, roles y keywords"
tipo: definiciones
proyecto: pod-agents
estado: en-definicion
actualizado_en: 2026-08-16
tags:
  - pod-agents
  - definiciones
  - datos
  - keywords
---

# Definiciones — Datos, roles y keywords

Acumulador de **decisiones de diseño pendientes** detectadas al analizar la base
actual. Cada punto tiene un ID (`N1`, `H1`, `R1`…) para referenciarlo en
conversación. Esta nota **no es documentación del sistema que existe**: es la
lista de lo que hay que ajustar y por qué.

> [!warning] Documento vivo
> Se va a ir completando con más definiciones. Los puntos marcados como
> `abierto` necesitan una decisión antes de implementarse.

---

## N — Normalización y capitalización

> **Hecho verificado:** eRank normaliza a minúscula. El export
> `eRank-Bulk-Keywords-6.csv` devuelve las 20 filas en minúscula, sin una sola
> mayúscula, sin importar cómo se pegó la keyword. EverBee y la búsqueda de Etsy
> se comportan igual. **La capitalización no cambia los resultados de búsqueda.**
> Pero sí rompe la integridad de la base.

| ID | Definición | Por qué | Dónde |
|---|---|---|---|
| **N1** | **Minúscula es el canon** para todo dato de keyword y para `niche_items.name`. | Es lo que devuelve eRank; guardar otra cosa garantiza que no matchee. | `keywords`, `niche_items` |
| **N2** | Aplicar `.lower()` al leer el CSV, no solo `.strip()`. | Hoy `Grandma Halloween Shirt` staged + `grandma halloween shirt` importada = **dos filas**, y la original queda en `pending` para siempre. | `tools/import_erank.py:35` |
| **N2b** | **Normalizar el seed** de la taxonomía a minúscula (hoy `mom_name` va en minúscula y el resto capitalizado). | Sin esto, el `UNIQUE (category, name, subcategory)` no hace su trabajo: deja pasar `Aunt` y `aunt` como dos ítems distintos. Es la contraparte de N2 aguas arriba; ver también [[#R — Taxonomía de roles\|R10]]. | `db/seed_niches.py` |
| **N3** | La capitalización es **solo presentación** (texto del diseño, título del listing). Si se necesita, va en una columna `display_name` aparte, nunca en la clave. | Separar dato de presentación. | futuro |
| **N4** | Partir los nombres con barra en filas separadas: `Pop/Pop-Pop`, `Granny/Grannie`, `Abuela/Abuelita`. | Son dos keywords metidas en una; así no sirven como keyword directa. | `db/seed_niches.py` |
| **N5** | ~~El `niche` pasa a ser un slug corto y estable inventado por el sistema.~~ → **Superado por D2:** el nicho no se inventa, *es* la frase base que validó en eRank; el slug se deriva de ella. | El problema que originó el punto sigue vigente (cada corrida inventa un string distinto → duplicación masiva, ver H2), pero la solución es otra. | todo el pipeline |

> [!note] Nota al pie de N3 — la capitalización del título no es SEO
> Escribir el título del listing como `Grandma Halloween Shirt` en vez de
> `grandma halloween shirt` es una decisión **estética**, no de posicionamiento:
> el buscador de Etsy normaliza a minúscula igual que eRank, así que las dos
> formas rankean idéntico. Está perfecto hacerlo (se ve más prolijo y profesional
> en la galería), pero conviene tenerlo claro para **no invertir tiempo ahí
> creyendo que rinde SEO**. El posicionamiento se juega en qué keywords elegís,
> no en cómo las capitalizás.

---

## H — Histórico de métricas (modelo de datos)

> **Hecho verificado:** el upsert actual es `ON CONFLICT (keyword, niche)
> DO UPDATE`. Con el mismo nicho **pisa** las métricas viejas (se pierden); con
> otro nicho **crea fila nueva**. En la base hoy: `dad shirt`, `new mom gift`,
> `grandma gift` y varias más están **5 veces**, una por nicho.

| ID | Definición | Por qué | Dónde |
|---|---|---|---|
| **H1** | Separar **dimensión** de **hecho**: `keywords` (una fila por keyword canónica, sin métricas) + `keyword_metrics` (append-only, una fila por medición) + `keyword_niches` (relación N:M keyword ↔ nicho). | Las métricas son una serie temporal y estacional. Pisarlas destruye el activo del negocio. | `db/init/003_*.sql` |
| **H2** | El **nicho sale de la identidad** de la keyword. Una keyword existe una sola vez; el nicho es un tag. | Es la causa directa de la duplicación 5×. | `keywords` |
| **H3** | `keyword_metrics` lleva `measured_on DATE` y `UNIQUE (keyword_id, source, measured_on)`. | Da histórico real e idempotencia: reimportar el mismo CSV el mismo día no hace nada. | `keyword_metrics` |
| **H4** | **Nunca `UPDATE` sobre una medición.** Toda medición nueva es un `INSERT`. | Append-only. Una medición es un hecho pasado, no cambia. | `tools/import_erank.py` |
| **H5** | Vista `keyword_latest` con la última medición por keyword. | El código existente (`analyze()`, agentes, Streamlit) sigue leyendo "una fila por keyword" sin enterarse del cambio. | vista SQL |
| **H6** | **Regla de frescura (TTL): 90 días.** Una keyword con última medición más vieja se considera stale y se re-mide antes de decidir. | Hoy no se distingue un dato de ayer de uno del año pasado: `updated_at` es "cuándo tocamos la fila", no "cuándo se midió". | `sop_validation` / gate |
| **H7** | Separar dos "decisiones": la **del SOP** (derivada de las métricas, recalculable) y la **de curaduría** (`to_design` / `discarded`, la elige una persona y vive en `keyword_niches`). | Hoy conviven en la misma columna y el SOP pisa la decisión humana al re-analizar. | `keyword_niches` |
| **H8** | Comparación **año contra año, mismo mes**, como métrica de primera clase. | Ni eRank ni EverBee la dan; sale gratis una vez que hay histórico. Es ventaja propia. | reporting |

---

## R — Taxonomía de roles

> **Hecho verificado:** los roles hoy viven solo en `family_relation`: 49 ítems
> en 5 subcategorías (`mom_name` 11, `dad_name` 9, `grandmother_name` 10,
> `grandfather_name` 10, `other_family` 9).

| ID | Definición | Por qué | Prioridad |
|---|---|---|---|
| **R1** | Agregar **`grandma`** y **`grandpa`**. | **No existen en la taxonomía.** Están Nana, Mimi, Memaw, Gramps, Papaw… pero faltan las dos keywords de mayor volumen del eje. Peor: `DEFAULT_ROLES` en `tools/keyword_gen.py:36` arranca con `grandma`/`grandpa`, o sea que el motor usa dos roles que la base no conoce. | **bloqueante** |
| **R2** | Simetría mom/dad: si `mom_name` tiene `bonus mom` y `stepmother`, `dad_name` necesita `bonus dad`, `stepdad`, `stepfather`. | Hoy la asimetría hace que los diseños para papá pierdan la mitad de las variantes. | alta |
| **R3** | Completar faltantes por subcategoría existente: `stepmom`, `mami`, `papi`, `padre`, `Gigi`, `Yaya`, `Lola`, `Oma`, `Nonna`, `Gram`, `Opa`, `Nonno`, `Son`, `Daughter`, `Auntie`, `Tia`, `Tio`, `Sibling`, `Twin`, `Big/Little Brother`, `Big/Little Sister`, `Godmother`, `Godfather`, `Godson`, `Goddaughter`. | Cobertura del eje `family_role`. | media |
| **R4** | Subcategorías **nuevas**: `spouse`, `in_law`, `milestone`, `pet_parent`, `service`, `status`. Ver detalle abajo. | `milestone` (boy mom, new mom, soccer mom, girl dad) es de los ejes que más venden en POD y hoy no existe. | alta |
| **R5** | Cada rol lleva `gender` (f/m/neutral), `is_gift_recipient` (regalo vs autocompra) y `popularity`. | Permite filtrar qué rol tiene sentido para el nicho y rankearlo, en vez de tomar el primero. | media |
| **R6** | Completar `career` con los ausentes: `librarian`, `firefighter`, `emt`, `chef`, `baker`, `bartender`, `barber`, `esthetician`, `nail technician`, `flight attendant`, `pilot`, `photographer`, `realtor`, `welder`, `farmer`, `speech therapist`. | Todos con volumen fuerte en Etsy y hoy ausentes. | media |
| **R7** | Renombrar `Patrol Officer` → `police officer`. | Es el nombre del catálogo BLS, no el que busca la gente. Igual revisar el resto de la lista con el mismo criterio. | media |
| **R8** | **El rol sale del nicho, no de un default fijo.** `DEFAULT_ROLES` deja de ser `["mom","dad","grandma","grandpa"]` y se deriva del nicho elegido. | Para "Halloween Nurse Mom" el rol es `nurse mom`, no `dad`. Es la causa raíz del problema ya registrado de roles genéricos. | **alta** |
| **R9** | Los **modificadores** son una lista aparte que se multiplica con cualquier rol: `best <role> ever`, `world's best`, `#1`, `funny`, `tired`, `blessed`, `proud`, `<role> life`, `<role> in training`, `<role> to be`, `<role> est <year>`, `promoted to <role>`. | De ahí salen las mid y long-tail sin inflar la taxonomía. | media |
| **R10** | Normalizar el case de todos los ítems de la taxonomía. Es el mismo punto que **N2b**, listado acá por pertenecer también al trabajo de roles. | El `UNIQUE (category, name, subcategory)` no protege contra `Aunt` vs `aunt`. Ver N1 y N2b. | alta |

### Detalle de las subcategorías nuevas (R4)

- **`spouse`** — wife, husband, wifey, hubby, fiance, fiancee, bride, groom, bride to be, girlfriend, boyfriend, partner, newlywed
- **`in_law`** — mother in law, father in law, son in law, daughter in law, sister in law, brother in law
- **`milestone`** — new mom, first time mom, mom to be, dad to be, grandma to be, boy mom, girl mom, girl dad, twin mom, single mom, working mom, stay at home mom, autism mom, soccer mom, dance mom, cheer mom, baseball mom, band mom, promoted to big brother, promoted to grandma
- **`pet_parent`** — dog mom, dog dad, cat mom, cat dad, fur mama, pet parent, dog grandma, plant mom
- **`service`** — army mom, military wife, police wife, firefighter dad, veteran, coach, first responder
- **`status`** — graduate, class of \<year\>, retired, bestie, best friend, coworker, boss lady, teammate

---

## P — Producto y sus variantes de búsqueda

> **Estado actual:** el producto **no existe como dato**. La palabra `shirt` está
> escrita a mano en todos los templates (`tools/keyword_gen.py:83-127`) y también
> dentro del apparel test (`tools/sop_validation.py:119`). No hay tabla de
> productos ni de variantes.

En `grandma halloween shirt`, `shirt` es el **producto**. Igual que el rol, es un
eje propio: el mismo diseño se vende como t-shirt, sweatshirt, mug, tote bag o
blanket, y **cada producto se busca con varios términos distintos**.

| ID | Definición | Por qué | Prioridad |
|---|---|---|---|
| **P1** | Crear el producto como entidad persistida: tabla `products` (producto canónico) + `product_terms` (sus variantes de búsqueda). | Hoy es un string hardcodeado; no se puede rankear, medir ni variar por nicho. | alta |
| **P2** | **Las variantes NO son sinónimos de display: son keywords distintas que se miden por separado.** `tee`, `shirt` y `t-shirt` tienen volumen, competencia y KD diferentes en eRank. | El objetivo no es "escribirlo lindo": es descubrir con datos cuál de los términos rankea mejor. La tabla de variantes es un **generador de candidatos a medir**. | alta |
| **P3** | Cada producto tiene un término `is_primary`: el que usan los templates y el título por defecto. Los demás se miden como alternativas. | Hace falta un default determinístico mientras no haya datos del nicho. | alta |
| **P4** | **Generalizar el apparel test a "product demand test":** `X` vs `X <producto>`, no solo `X shirt`. | Hoy un nicho con volumen que no funciona en remera se descarta, aunque sea un gran nicho de **mug** o **blanket**. El veredicto correcto es "no es apparel → probar drinkware", no "descartado". | **alta** |
| **P5** | `keyword_gen` toma el término de producto de la base, no del literal `"shirt"`. | Es el mismo problema que R8 con los roles: un default fijo tapando el dato real. | alta |
| **P6** | El eje de producto se mide en un **bloque de calibración** aparte (ej. `shirt` vs `tee` vs `tshirt` sobre 2-3 frases representativas) y el ganador se reusa entre nichos. | **No es por falta de cupo:** eRank da 100 requests/día × 20 keywords = **2000 keywords/día**, holgado. El límite real es el **trabajo manual** del gate: cada request es pegar, exportar CSV e importar a mano. Re-medir las mismas variantes en cada nicho gasta round-trips humanos, no cupo. | media |
| **P7** | `products` guarda también el lado de **producción**: `base_cost`, `avg_price`, `design_area`, y a futuro el blueprint de Printify. | El producto es a la vez un término de búsqueda y un ítem con costo. Habilita el `calculate_margin` que ya está pendiente. | media |
| **P8** | Marcar qué productos admiten qué tipo de diseño (`design_area`). | Un arte pensado para el pecho de una remera no funciona envuelto en una taza. Evita fan-out a productos donde el diseño no aplica. | media |
| **P9** | Todas las variantes en minúscula (N1). Ojo con `t-shirt` vs `t shirt`: el guion cambia el conteo de palabras y por lo tanto el `keyword_type` (head/mid/long_tail) que calcula la columna generada. | El `keyword_type` maneja el reparto 5/12/3 del bloque; una variante con guion puede correr una keyword de `head` a `mid` sin que se note. | media |

### Semilla inicial de productos y variantes

| Producto (slug) | Categoría | Variantes de búsqueda |
|---|---|---|
| `t-shirt` | apparel | shirt, tshirt, t-shirt, tee, graphic tee |
| `sweatshirt` | apparel | sweatshirt, crewneck, pullover, sweater |
| `hoodie` | apparel | hoodie, hooded sweatshirt |
| `mug` | drinkware | mug, coffee mug, cup |
| `tumbler` | drinkware | tumbler, travel mug, water bottle |
| `tote-bag` | bag | tote bag, tote, canvas bag |
| `blanket` | home | blanket, throw blanket, fleece blanket |
| `pillow` | home | pillow, throw pillow, cushion |
| `poster` | paper | poster, wall art, print |
| `sticker` | paper | sticker, decal, vinyl sticker |
| `ornament` | home | ornament, christmas ornament |

### Estructura propuesta

```sql
products(id, slug UNIQUE, name, category, is_apparel, popularity,
         base_cost, avg_price, design_area, active)

product_terms(id, product_id -> products, term, is_primary,
              UNIQUE (product_id, term))
```

Las mediciones de cada `term` no viven acá: son keywords normales y van a
`keyword_metrics` como cualquier otra (H1). `product_terms` solo dice **qué hay
que medir**; el histórico dice **cuál ganó**.

---

## D — Discovery por slots (modelo de nicho y profundidad)

> **Este bloque redefine qué es un nicho.** Reemplaza el modelo de "cruce
> conceptual" (ocasión × nicho) por uno de **frase medida + slots**. Supera a N5
> y anula la cuota 5/12/3 de `tools/keyword_gen.py`.

**Fórmula corta:** *cada combinación es un nicho nuevo hasta que se pruebe lo
contrario.*

| ID | Definición | Por qué |
|---|---|---|
| **D1** | El nicho es una **frase exacta con volumen propio medido** (2-3 palabras), no un cruce conceptual. Tiene fila propia en `keywords` con sus searches y su KD, como cualquier otra keyword. | Hoy el `niche` es una etiqueta de agrupación que **nunca se mide**. Si el nicho no tiene métricas propias, no se sabe si existe. |
| **D2** | El slug del nicho **se deriva de la frase ganadora**, no se inventa. *(reemplaza N5)* | No hace falta un identificador paralelo: la frase que validó ya es el identificador. |
| **D3** | **Sin herencia.** Ninguna dimensión (rol, career, producto, año) escala por default. Que `tennis mom` valide **no autoriza** a `tennis aunt`: se prueba como si fuera un nicho nuevo. | Es el bug de fondo del motor actual: `DEFAULT_ROLES` asumió que el rol es palanca libre y generó roles genéricos sin validar ninguno. Ver R8. |
| **D4** | Cuatro slots, con dos operaciones distintas: **ROLE reemplaza**, **PRODUCT / MODIFIER / YEAR suman**. Ver tabla abajo. | La diferencia entre reemplazar y sumar no es representable hoy y es lo que define cómo se genera cada variante. |
| **D5** | Los roles salen de las categorías `career` + `family_relation` de `niche_items`, **filtrando por `active = TRUE`**. | Son 151 ítems hoy (102 career + 49 family_relation). El filtro por `active` importa porque la tabla se va a **depurar**: dar de baja un ítem debe sacarlo del generador sin borrar el histórico. |
| **D6** | Productos y modificadores entran a `niche_items` como **categorías nuevas**. En productos: `subcategory` = producto canónico, `name` = variante de búsqueda (`t-shirt` / `tee`). En modificadores: `subcategory` = **posición** (prefijo / sufijo). | Con todos los slots en una tabla, el generador es una sola consulta uniforme por slot. La posición del modificador es necesaria para saber si se arma `funny tennis mom` o `tennis mom era`. Los datos comerciales del producto quedan fuera (ver P7). |
| **D7** | Campos de **linaje**, en `keyword_niches`: `base_keyword_id`, `slot`, `slot_op` (`replace`/`add`), `round`. | Describen la frase **como variante de una base**, no la frase en sí — por eso no van en `keywords` ni en `keyword_metrics`. Sin ellos no hay forma de contar profundidad ni de saber si un nicho está agotado. |
| **D8** | **`round` ≠ `measured_on`.** La ronda es la ola de exploración; `measured_on` es cuándo eRank midió. Una frase de la ronda 2 re-medida seis meses después por el TTL (H6) **sigue siendo de la ronda 2**. | Es lo que garantiza que el import no pise nada: las métricas se apilan por fecha (H3/H4) y la ronda queda registrada aparte, en otra tabla. |
| **D9** | **Se elimina la cuota 5/12/3.** `head` / `mid` / `long_tail` se conserva como **clasificación descriptiva** (la columna generada de la DB), pero sin límite por tipo: se generan **todas** las combinaciones posibles. | Una cuota fija deja afuera N posibilidades que podrían rendir bien, y no es la idea. La clasificación sigue sirviendo para leer y ordenar; la cuota no sirve para nada. |
| **D10** | Salida del generador: **la lista completa visible** + las keywords **separadas por comas en bloques de 20**, listas para pegar en el Bulk Keyword Tool. | El humano necesita ver todo el universo generado y además tener el formato exacto que consume eRank. |
| **D11** | El filtro se aplica **por fila**: KD ≤ 85, searches ≥ 100, ratio R ≥ 0.01, descarte automático de trampa (competition > 10.000 con searches < 20). **Ya está implementado y no se toca.** | `classify()` en `tools/sop_validation.py:84` ya hace exactamente esto. Todo lo que está roto está **aguas arriba** del filtro, en cómo se generan las frases. |
| **D12** | **Iteración:** los sobrevivientes de la ronda N son las bases de la ronda N+1. Se termina cuando no hay sobrevivientes **o** no quedan variantes por generar. | El nicho se agota por evidencia, no por una cuota arbitraria de rondas. |
| **D13** | **Profundidad** = cuántas frases exactas, cada una testeada individualmente, sobreviven el filtro compartiendo el mismo asset visual. Output por nicho: frase base + lista de sobrevivientes + `count` = **número real de listings posibles**. | Es la métrica que decide si vale la pena diseñar. Si no hay profundidad, no es nicho: es callejón. |
| **D14** | **UI, modo "Yo elijo":** un solo input, **la frase base**. Se eliminan los dos campos cruzados (`Ocasión` × `Nicho`). **Modo IA:** dos vías de entrada — cruzar 2 ítems de `niche_items`, **o** anclar en una holiday respetando el lead time de 90 días. | Hoy la UI cruza *palabras* (`streamlit_app.py:122`), y el nicho empieza en una **frase**. El lead time se mantiene intacto: sugerir a 90 días, publicar a 60, para que queden ~30 días de posicionamiento antes de la fecha. |
| **D15** | **Vigilar el costo manual del gate.** Ronda 2 de una base ≈ 151 roles + ~35 productos + ~12 modificadores + 2 años ≈ **200 frases = 10 bloques**. Ronda 3 con 30 sobrevivientes ≈ **1000 frases = 50 bloques**. | El cupo de eRank aguanta (2000 keywords/día). El límite real es el tiempo humano: cada bloque es pegar, exportar CSV e importar. Ver P6. |
| **D16** | `popularity` deja de ser una **predicción** y pasa a ser **orden de prueba**: qué variante se mide primero cuando hay 200 candidatas. | Consecuencia directa de D3: si nada escala gratis, la popularidad no promete resultado, solo prioriza la cola. Resuelve parte de **A3**. |
| **D17** | **Apparel test: reconvertirlo, no cablearlo.** Hoy es **código muerto** — `apparel_test` no tiene `@tool` y su único call site es `sop_validation.py:191`, dentro del bloque `__main__`. Nunca corre en el pipeline. Además es *pairwise* y `analyze()` recorre fila por fila, así que estructuralmente no encaja. Queda **superado** por medir cada producto como frase propia (P4/D4). Lo que sobrevive es un **veredicto de nicho**: si la base pasa el filtro pero **todas** sus variantes de producto fallan → hay búsquedas pero no demanda de producto. | Si ya se mide `tennis mom shirt`, `tennis mom mug` y `tennis mom blanket` como frases propias, no hay que *inferir* si la demanda es de producto: está medida. Pero el caso "busca y no compra objetos" hoy no existe en ningún lado y es una señal de descarte valiosa. |

### Los cuatro slots (D4)

Base fija de ejemplo: **`tennis mom`**. Se reemplaza o se suma **un solo slot por vez**.

| Slot | Operación | Ejemplos |
|---|---|---|
| **ROLE** | `replace` | `tennis aunt`, `tennis grandma`, `tennis dad`, `tennis nurse` |
| **PRODUCT** | `add` | `tennis mom shirt`, `tennis mom sweatshirt`, `tennis mom mug` |
| **MODIFIER** | `add` | `funny tennis mom` (prefijo), `tennis mom era` / `tennis mom life` (sufijo) |
| **YEAR / COHORT** | `add` | `tennis mom 2027` (año actual o siguiente, según lead time) |

> [!warning] Rol es reemplazo, no suma
> `tennis aunt` **no** es "tennis mom + aunt": es la misma frase con la palabra de
> rol swapeada. Sumar dimensiones en la misma frase (`funny tennis aunt shirt`)
> recién aparece en rondas posteriores, cuando un sobreviviente se convierte en
> la nueva base (D12).

### Proceso completo

1. **Entrada** — modo "Yo elijo": la frase base es manual. Modo IA: cruce de 2 ítems de `niche_items` (`active = TRUE`) o holiday con lead time de 90 días → candidatas de 2-3 palabras.
2. **Generación** — todas las combinaciones posibles, sin cuota por tipo (D9).
3. **Salida** — lista completa + bloques de 20 separados por comas (D10).
4. **Medición** — Bulk Keyword Tool de eRank, 20 por request.
5. **Filtro** — `classify()` por fila: KD ≤ 85, searches ≥ 100, R ≥ 0.01, sin trampa (D11).
6. **Sobrevivientes** — cada uno es base de la ronda siguiente (D12).
7. **Cierre** — sin sobrevivientes o sin variantes por generar. Output: base + sobrevivientes + count (D13).

### Impacto en el código (para cuando se implemente)

- `build_keyword_block` y `compose_keyword_block` (`tools/keyword_gen.py`) se reemplazan por un **generador de variantes por slot**.
- `DEFAULT_ROLES` desaparece (ya cubierto por R8).
- `analyze()` (`tools/import_erank.py`) suma un paso a nivel nicho para D17.
- `_stage_block_ui(occasion, niche, ...)` (`streamlit_app.py:105`) cambia de firma por D14.
- **`classify()` no se toca.**

---

## Decisiones abiertas

Necesitan una definición del negocio antes de implementarse:

- **A1** — ¿Cómo se forma el `niche_slug` canónico? (¿`holiday-role`? ¿incluye producto? ¿incluye año?)
- **A2** — ¿EverBee **reemplaza** a eRank como fuente, o **complementa**? Define si `source` es una dimensión que convive (dos mediciones del mismo día, una por fuente) o si hay una fuente primaria. Nota: EverBee no da Keyword Difficulty.
- **A3** — ¿`popularity` se sigue cargando a mano, o se deriva de las métricas medidas una vez que haya histórico? *(D16 ya definió **para qué sirve** — orden de prueba, no predicción; falta definir **de dónde sale el número**.)*
- **A4** — Los roles compuestos de alto volumen (`dog mom`, `nurse mom`, `army mom`) ¿se guardan como ítem propio con su `popularity`, o se generan siempre por cruce en tiempo de ejecución?
- **A5** — ¿El producto forma parte del `niche_slug` (`halloween-nurse-mom-shirt`) o es un eje independiente que se cruza después? Impacta cómo se agrupan las mediciones.
- **A6** — ¿Qué productos entran al catálogo inicial? Debería salir de lo que el proveedor (Printify) ofrece con buen margen, no de una lista teórica.
- **A7** — `CLAUDE.md` todavía describe el bloque **5/12/3** como SOP vigente, en dos lugares. **D9 lo anula.** Falta decidir si se corrige `CLAUDE.md` o si esta nota queda como única fuente de verdad. Mientras tanto, hay una regla del proyecto contradiciendo a otra.

---

## Relacionado

- [[MOC - POD Agents]]
- [[07 - Glosario]]
