---
titulo: "07 - Glosario"
tipo: nota
proyecto: pod-agents
estado: en-desarrollo
actualizado_en: 2026-08-14
tags:
  - pod-agents
  - glosario
  - referencia
---

# Glosario de términos

Todos los términos técnicos y de negocio que aparecen en este manual, en orden
alfabético. Muchos están en inglés porque así se llaman dentro del sistema (el
código va en inglés por convención del proyecto).

## Negocio y POD

**POD (Print-on-Demand):** modelo sin stock. Cuando alguien compra, un proveedor
imprime el producto y lo envía. Nosotros ponemos diseño y estrategia.

**Etsy:** el mercado online donde vendemos.

**Printify:** nuestro proveedor de impresión y envío (nuestra "fábrica"). Hoy
está simulado en el sistema.

**eRank:** herramienta externa de análisis de Etsy. Dice, para cada keyword,
cuánta gente la busca y cuánta competencia tiene. Es la fuente de datos reales
que alimenta la validación.

**Listing (listado):** la publicación de un producto en Etsy (título, fotos,
tags, precio, descripción).

**DRAFT (borrador):** estado de un listado que existe pero **no está publicado**.
El sistema siempre se detiene acá, esperando aprobación humana.

**Margen:** la ganancia sobre el precio de venta. El objetivo del negocio es
**40% mínimo**. Precio máximo por producto: **$35**.

## Keywords y validación

**Keyword (palabra clave):** un término que la gente escribe en el buscador de
Etsy. El negocio se gana eligiendo bien las keywords.

**Occasion (ocasión):** el evento que trae tráfico y que la gente busca
(`birthday`, `halloween`, `graduation`). Corto, 1–2 palabras. **Es la keyword
que importa.**

**Cross-niching (cruce de nichos):** combinar dos ideas para crear un tema de
diseño único (ej: "Halloween" × "enfermera" × "mamá" = "Halloween Nurse Mom").
Sirve para **diferenciar el diseño**, pero **no** es la palabra de búsqueda: la
gente no escribe cruces de 4 palabras.

**Niche (nicho / tema):** el nombre corto del tema en el que trabajamos, escrito
como `slug` (minúsculas y guiones, ej: `halloween-nurse-mom`). Fluye entre todos
los pasos del sistema.

**Ejes (axes):** las "dimensiones" con las que se arman las keywords: ocasión,
edad, rol, fórmula, hobby, ocupación, cohorte. El motor de keywords combina
estos ejes para generar el bloque.

**Bloque 5/12/3:** la fórmula fija del bloque de 20 keywords: **5 cortas** (head,
2 palabras) + **12 medianas** (mid, 3 palabras) + **3 largas** (long-tail, 4+
palabras).

**head / mid / long-tail:** clasificación de una keyword por cantidad de
palabras. Cortas (2), medianas (3), largas (4+). Las largas son más específicas
y menos competidas.

**searches (búsquedas):** cuánta gente busca esa keyword (demanda). Para
"servir" tiene que ser **≥ 100**.

**competition (competencia):** cuántos listados compiten por esa keyword. Cuanto
más baja, mejor.

**KD (Keyword Difficulty / dificultad):** qué tan difícil es posicionar para esa
keyword, de 0 a 100. Para "servir" tiene que ser **≤ 85**.

**Ratio R:** demanda ÷ competencia. Semáforo: **≥ 0.02 verde**, **0.01–0.02
amarillo**, **< 0.01 rojo**.

**fit / unfit / trap:** el veredicto de cada keyword. `fit` = sirve; `unfit` = no
llega al umbral; `trap` = trampa (casi nadie la busca y hay mucha competencia).

**SOP (Standard Operating Procedure):** el procedimiento operativo estándar del
negocio. La versión v1.1 define cómo se investigan y validan keywords.

**Survival (supervivencia):** un tema "sobrevive" la validación si tiene **al
menos 2 keywords `fit`**. Si no, se descarta.

**Lead time (anticipación):** cuánto antes de una fecha hay que trabajar. El
sistema investiga **90 días antes** y publica **60 días antes**, porque Etsy
tarda ~30 días en posicionar un listado nuevo.

## Tecnología

**Agente:** una IA con un rol fijo, herramientas concretas y un formato de
salida. No es un chat abierto: tiene un trabajo acotado.

**Strands Agents:** la librería que coordina a los agentes y define el orden en
que trabajan. El "director de orquesta". Ver [[03 - Qué es Strands Agents]].

**Graph (grafo):** el patrón que usamos: una cadena ordenada de agentes con
compuertas de control. Predecible, siempre corre igual.

**System prompt (rol):** el texto de instrucciones que define cómo se comporta
un agente. Se edita para ajustar su comportamiento. Ver [[04 - Los agentes]].

**Tool (herramienta):** una acción concreta que un agente puede ejecutar (ej:
revisar marcas registradas). Es código, no imaginación de la IA.

**Ollama:** el programa que corre el modelo de IA local y gratis en la Mac.

**qwen3.5:9b:** el modelo de lenguaje (la IA) que usamos localmente. Gratis y
privado; a cambio, menos potente que los de la nube.

**Postgres:** la base de datos donde se guarda todo (keywords, decisiones,
taxonomía de nichos). La memoria del negocio.

**Docker:** el programa que corre la base de datos de forma aislada en la Mac.

**Mock (simulado):** una integración que finge estar conectada y devuelve datos
de ejemplo. Hoy Printify y Etsy están mockeados para poder probar sin gastar ni
publicar.

**CSV:** un archivo de texto con datos en tabla. eRank exporta los resultados en
este formato y el sistema los importa.

**Trazas (tracing):** las líneas que el sistema imprime mientras corre para
mostrar qué agente trabaja y cuánto tarda. Ver [[06 - La salida y cómo leerla]].

---

Volver al [[MOC - POD Agents]]
