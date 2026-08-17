---
titulo: "08 - Cómo usar el formulario de Discovery"
tipo: nota
proyecto: pod-agents
estado: en-desarrollo
actualizado_en: 2026-08-15
tags:
  - pod-agents
  - keywords
  - procedimiento
  - erank
---

# Cómo usar el formulario de Discovery (bloque de 20 keywords)

Esta nota es el **manual de uso** de la primera pantalla del panel: la que genera
el bloque de 20 keywords que después se corre en eRank. Explica qué escribir en
cada campo, qué **no** escribir, por qué el resultado a veces trae palabras que
vos no elegiste, y qué conviene mejorar.

> [!important] La regla de oro
> **La ocasión NO es el cruce.** Lo que se busca en Etsy y lo que se dibuja en la
> remera son dos cosas distintas, y este formulario solo maneja **lo que se
> busca**.

## 1. El concepto que hace que todo lo demás se entienda

El SOP de investigación (basado en 340 keywords medidas y la primera venta real)
dice que hay tres cosas separadas, y confundirlas arruina el bloque:

| Concepto | Qué es | Ejemplo | ¿Va en este formulario? |
|---|---|---|---|
| **Ocasión** | El término que la gente **tipea** en el buscador de Etsy. Alto volumen, genérico. | `halloween` | **Sí**, en "Ocasión" |
| **Cruce (cross-niche)** | La intersección que hace único al **diseño**. Nadie la busca. | `developer` | **No** como keyword — va al nombre del nicho y después a los tags |
| **Personalización** | Nombre, fecha, foto. Cero búsquedas, pero es lo que cierra la venta. | `"Diego, 2026"` | No, nunca se testea en eRank |

> [!warning] El error más común
> Escribir el cruce en el campo "Ocasión". Si ponés `Halloween Developer`, le
> estás pidiendo a eRank que mida cuánta gente busca "halloween developer" en
> Etsy. Casi nadie. Volvés con 13 keywords en `Unknown` (sin datos) y quemaste
> tu cupo diario de eRank sin aprender nada.

**Por qué funciona así:** nadie entra a Etsy a buscar "regalo de halloween para
programador". Entran a buscar `halloween shirt`. Lo que hace que **te compren a
vos** y no al de al lado es que, entre 5.000 remeras de Halloween, la tuya dice
algo de programadores. El cruce gana la venta; la ocasión trae la visita.

## 2. Campo por campo

### Ocasión (término de búsqueda base)

> [!tip] Regla práctica
> **Una sola palabra.** Dos solo si la segunda es imprescindible para que se
> entienda (`mothers day`, `memorial day`). Nunca tres.

- ✅ `halloween`, `christmas`, `birthday`, `graduation`, `retirement`,
  `thanksgiving`, `anniversary`
- ⚠️ `mothers day`, `fathers day` — funcionan, pero degradan (ver abajo)
- ❌ `halloween developer`, `thanksgiving teacher mom`, `funny halloween shirt`

**Por qué importa tanto la cantidad de palabras.** El bloque se arma en tres
cajones según el largo de la keyword: **head = 2 palabras o menos**, **mid = 3**,
**long-tail = 4 o más**. Todas las plantillas del generador son
`ocasión + algo`. Entonces:

| Palabras en la ocasión | Keyword más corta posible | Cae en | Consecuencia |
|---|---|---|---|
| 1 (`halloween`) | `halloween gift` (2) | **head** ✅ | Los 5 head son de tu ocasión |
| 2 (`mothers day`) | `mothers day gift` (3) | mid ⚠️ | Los 5 head se llenan con genéricos |
| 2 (`halloween developer`) | `halloween developer gift` (3) | mid ❌ | Igual, pero los genéricos ni siquiera son relevantes |

**El antes y después real**, con el mismo sistema:

```
Ocasión = "Halloween Developer"        →  5 head genéricos, 0 con Halloween
   dad gift · dad shirt · grandma gift · grandma shirt · grandpa gift

Ocasión = "halloween"                  →  20/20 con Halloween adentro
   halloween gift · halloween mom · halloween dad · halloween grandma…
```

Con `halloween` solo, **las 20 keywords del bloque contienen la ocasión**. Con
`Halloween Developer`, solo 15, y las 5 más valiosas (las head, las que miden el
tamaño del mercado) se desperdiciaron.

### Nicho (slug corto)

> [!note] Acá va el cruce
> El campo dice "slug corto" y no explica nada. **Lo que corresponde escribir es
> el nombre del cruce**, en formato corto y con guiones: `halloween-dev`,
> `milestone-birthday`, `graduation-nurse`.

**Qué hace este campo hoy, exactamente:** es una **etiqueta de carpeta**. No
influye en absolutamente nada de la generación de keywords — solo agrupa las 20
filas en la Base de Keywords para que después puedas filtrar por nicho y para
que el importador del CSV sepa a qué grupo pertenecen los datos de eRank.

**Reglas para el slug:**

- Minúsculas, sin espacios, separado por guiones: `halloween-dev`
- Corto y estable: lo vas a tipear de nuevo al importar el CSV
- Que se entienda de qué diseño se trata dentro de 3 meses
- **Que sea el mismo** en las dos etapas (si stageaste como `halloween-dev`, el
  CSV se importa como `halloween-dev`, no `halloween-developer`)

> [!warning] Limitación conocida
> Hoy el sistema **no usa el cruce para generar keywords**. Si escribís
> `halloween-dev`, el generador nunca va a producir `developer gift` ni
> `developer halloween shirt`. Los roles que usa están fijos en el código (ver
> sección 4). Es el pendiente principal de esta pantalla.

### Año de cohorte (opcional, solo graduaciones)

**Dejalo en `0` salvo que la ocasión sea una graduación.**

Cuando ponés un año, se activa el eje **cohorte**, que genera keywords como
`class of 2027`, `senior 2027`, `graduate 2027 gift`. Es el eje que **mejor
rinde de todos** según el SOP (dificultad medida entre 23 y 48, la más baja de
todas) porque cada año se renueva la competencia desde cero.

- ✅ `graduation` + año `2027`
- ❌ `halloween` + año `2027` → generaría `class of 2027` mezclado en un bloque
  de Halloween, que no tiene ningún sentido y te come slots.

### Seasonality (opcional)

Una **etiqueta de temporada** que se guarda junto a las keywords en la base:
`Q4`, `Q1`, `summer`, `holiday`. No cambia nada del bloque generado — sirve para
que después puedas filtrar la Base de Keywords por temporada y ver, por ejemplo,
qué te funcionó en Q4 del año pasado.

Convención sugerida: usar el trimestre (`Q1`…`Q4`). Es lo que ya usa la
taxonomía de nichos internamente.

## 3. Casos completos de referencia

| Quiero vender… | Ocasión | Nicho (slug) | Año | Seasonality |
|---|---|---|---|---|
| Remeras de Halloween para programadores | `halloween` | `halloween-dev` | 0 | `Q4` |
| Regalos de cumple de 50 | `birthday` | `milestone-50` | 0 | *(vacío)* |
| Remeras para graduados 2027 enfermeros | `graduation` | `graduation-nurse` | `2027` | `Q2` |
| Tazas de Navidad para amantes del café | `christmas` | `christmas-coffee` | 0 | `Q4` |
| Regalos de jubilación para maestras | `retirement` | `retirement-teacher` | 0 | *(vacío)* |

Fijate el patrón: **la ocasión siempre es una palabra genérica y de alto
volumen; toda la especificidad vive en el slug del nicho.**

## 4. Por qué aparecen palabras que vos no elegiste

Esta es la pregunta que dispara más desconfianza en el resultado, y la respuesta
es simple: **hay palabras fijas escritas dentro del código.**

El generador tiene tres listas hardcodeadas que se usan **en todas las
búsquedas, siempre las mismas**:

| Lista | Contenido fijo | Dónde aparece |
|---|---|---|
| Roles familiares | `mom`, `dad`, `grandma`, `grandpa` | En casi todas las plantillas |
| Hobbies | `book`, `coffee`, `plant` | En `X lover gift` |
| Profesiones | `nurse`, `teacher` | En `{ocasión} nurse`, `{ocasión} teacher` |
| Edades hito | 30, 40, 50, 60, 70, 80, 90 | Solo si la ocasión es `birthday` |

### La ventaja de tenerlas fijas

1. **No son arbitrarias.** Mamá, papá, abuela y abuelo son, de lejos, los
   destinatarios de regalo más buscados en Etsy. Son un punto de partida
   defendible, no un capricho.
2. **Resultado predecible y reproducible.** El mismo input da el mismo bloque.
   Podés comparar corridas entre sí sin preguntarte si cambió el generador.
3. **Costo cero y velocidad.** Es código puro, no consulta a la IA: el bloque
   sale instantáneo y sin riesgo de que el modelo invente algo raro.
4. **Sirven de piso.** Si el cruce no tiene volumen, al menos el bloque mide
   términos que sabés que tienen mercado.

### La desventaja, que hoy pesa más

1. **No se adaptan al nicho.** Elegiste `developer` y el sistema te devuelve
   `grandpa`. El dato que más te interesa (¿hay demanda de Halloween para
   programadores?) no se mide nunca.
2. **Repetís la misma medición cada vez.** `dad gift` y `mom gift` ya los
   mediste. eRank tiene un límite de ~100 keywords por día: cada slot gastado en
   una keyword que ya está en tu base es un slot que no usaste para aprender
   algo nuevo.
3. **Ensucian la validación.** Los genéricos vuelven con dificultad 100
   (imposible rankear). Como el SOP exige al menos 2 keywords con dificultad ≤85
   para aprobar un nicho, llenar el bloque de genéricos empuja el veredicto
   hacia el rechazo aunque el nicho real sea bueno.
4. **Falso sano.** El sistema dice "20 keywords generadas" y parece que salió
   todo bien, cuando la mitad es relleno. No hay ninguna alerta.

> [!question] ¿Tiene sentido entonces?
> Como **valor por defecto**, sí. Como **única opción**, no. La respuesta
> correcta no es borrar las listas: es que el nicho elegido tenga prioridad y
> los defaults solo completen lo que falte.

## 5. El caso del eje "formula": ¿para qué sirve si es relleno?

En el bloque de `Halloween Developer` aparecieron cuatro keywords marcadas
`formula`: `new dad gift`, `new mom gift`, `new grandma gift`,
`new grandpa gift`. Ninguna menciona Halloween.

**Qué es el eje formula.** Son **fórmulas de frase de anuncio de un cambio de
vida**: `promoted to grandma`, `new dad gift`. Según el SOP es un eje **bueno**
(rinde por encima de hobby y de profesión). La lógica de negocio es real:
`promoted to grandma` es lo que busca alguien que acaba de enterarse de que va a
ser abuela. Es una compra emocional, urgente y con poca competencia.

**Por qué en tu bloque fue relleno.** Por dos razones acumuladas:

1. Sus plantillas **nunca incluyen la ocasión** por diseño (`new {rol} gift`).
   Son keywords de evento de vida, no de fecha del calendario.
2. Faltaban candidatas. El bloque necesita 12 mid y solo había 8 con
   "halloween developer" adentro. Los 4 slots vacíos se llenaron con el mejor eje
   disponible. Cohorte estaba vacío (no pusiste año), edad estaba vacío (no era
   cumpleaños) → cayó en formula.

**Cuándo el eje formula te sirve de verdad:** cuando la ocasión **es** un evento
de vida, no una fecha del calendario.

| Ocasión | ¿Formula aporta? | Por qué |
|---|---|---|
| `new baby`, `pregnancy` | ✅ Mucho | `promoted to grandma` **es** la keyword del nicho |
| `retirement`, `promotion` | ✅ Sí | `new retiree gift` es exactamente la búsqueda |
| `graduation` | 🟡 Algo | Compite con cohorte, que es mejor |
| `halloween`, `christmas` | ❌ Nada | Nadie es "promovido a" Halloween |

**Conclusión:** el eje no está mal; está **mal aplicado**. El arreglo es que las
plantillas de formula solo se activen cuando la ocasión es un evento de vida, y
que cuando no haya con qué llenar los 12 mid, el sistema **avise** en vez de
rellenar en silencio.

## 6. Cómo leer el resultado antes de ir a eRank

Después de generar, mirá la columna del medio (el eje) y hacete tres preguntas:

> [!check] Checklist de 30 segundos
> 1. **¿Los 5 head contienen mi ocasión?** Si no, la ocasión tiene demasiadas
>    palabras. Acortala y regenerá.
> 2. **¿Cuántas de las 20 contienen mi ocasión?** Menos de 15 es señal de
>    problema.
> 3. **¿Veo palabras que no tienen nada que ver (`grandpa`, `plant lover`)?**
>    Son relleno de las listas fijas. Contá cuántas: ese es tu desperdicio de
>    cupo de eRank.

**Señales de alerta concretas:**

| Lo que ves | Qué significa | Qué hacer |
|---|---|---|
| Los 5 head son `X gift` / `X shirt` sin tu ocasión | La ocasión tiene 2+ palabras | Acortar la ocasión a una palabra |
| Aparece `class of 2027` en un bloque de Halloween | Pusiste año en una ocasión no-graduación | Poner el año en `0` |
| `⚠ short by: N mid` al final | No hubo candidatas suficientes | La ocasión es muy larga o muy rara |
| Muchos `new X gift` | Se agotaron las keywords de la ocasión | Normal en ocasiones cortas; revisar si vale la pena mandarlas |

## 7. Mejoras propuestas para esta pantalla

Ordenadas por relación impacto / esfuerzo.

| # | Mejora | Ventaja | Desventaja / costo |
|---|---|---|---|
| 1 | **Separar el campo "Cruce"** del slug, con ayuda en pantalla explicando ocasión vs cruce | Elimina de raíz el error más caro; el usuario entiende qué está haciendo | Solo UI, casi sin costo |
| 2 | **Validar la ocasión al escribir**: avisar si tiene más de una palabra | Corta el error antes de gastar cupo de eRank | Puede molestar en casos legítimos (`mothers day`); debe ser aviso, no bloqueo |
| 3 | **Usar el cruce como rol** en las plantillas, antes que los defaults | Las keywords miden lo que realmente querés saber | Requiere tocar el generador; el cruce puede no funcionar gramaticalmente en toda plantilla |
| 4 | **Sacar los roles de la taxonomía** (`niche_items` ya tiene 453 ítems con carrera, hobby, familia y mascota, rankeados por popularidad) en vez de las 4 palabras fijas | Variedad real, ordenada por popularidad, sin inventar nada — la base ya existe | Depende de que Postgres esté arriba; hay que definir cuántos ítems tomar |
| 5 | **No re-stagear keywords ya medidas**: si `dad gift` ya está en la base con datos, reemplazarla por una nueva | Aprovecha el 100% del cupo diario de eRank en aprender cosas nuevas | Hay que decidir cada cuánto vale la pena re-medir (los datos envejecen) |
| 6 | **Activar los ejes según el tipo de ocasión**: formula solo en eventos de vida, cohorte solo en graduaciones | Elimina el relleno sin sentido | Requiere clasificar las ocasiones (fecha vs evento de vida) |
| 7 | **Alerta de calidad del bloque**: mostrar "solo 15/20 contienen tu ocasión" | Convierte el checklist manual de la sección 6 en algo automático | Trivial, pero hay que elegir bien el umbral |

> [!tip] Si hubiera que hacer una sola
> La **#1**. La mayoría del daño no viene del generador sino de que el
> formulario no explica qué esperar en cada campo. Un cartelito de dos líneas
> resuelve más que tres refactors.

## Mientras tanto: cómo usarlo hoy sin tocar el código

1. En **Ocasión**, escribí **una sola palabra**, en inglés, la que un comprador
   tipearía en Etsy.
2. En **Nicho**, escribí el cruce en formato slug (`halloween-dev`). Anotalo:
   lo necesitás igual al importar el CSV.
3. **Año** en `0` salvo graduaciones. **Seasonality** con el trimestre.
4. Antes de ir a eRank, corré el checklist de 30 segundos de la sección 6.
5. Acordate de que el cruce (`developer`) **no se mide en eRank**: entra después,
   en el diseño y en los tags del listado.

## Notas relacionadas

- [[05 - Flujo del proceso]] — dónde encaja esta pantalla en las dos etapas.
- [[06 - La salida y cómo leerla]] — cómo interpretar lo que devuelve el sistema.
- [[07 - Glosario]] — head, mid, long-tail, KD, ratio R, slug.
