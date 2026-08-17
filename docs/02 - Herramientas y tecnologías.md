---
titulo: "02 - Herramientas y tecnologías"
tipo: nota
proyecto: pod-agents
estado: en-desarrollo
actualizado_en: 2026-08-14
tags:
  - pod-agents
  - stack
  - herramientas
---

# Con qué está construido el sistema

Esta nota explica, sin tecnicismos, cada pieza que usa el sistema y **por qué se
eligió**. La idea es que puedas entender de qué depende el proyecto y qué cuesta
(en dinero y en complejidad) cada parte.

## Tabla resumen

| Pieza | Qué es, en simple | Por qué la usamos | ¿Cuesta dinero? |
|---|---|---|---|
| **Strands Agents** | El "director de orquesta" que coordina a los agentes | Organiza el flujo paso a paso de forma ordenada y predecible | Gratis (librería) |
| **Ollama + qwen3.5** | El "cerebro" de IA corriendo en la Mac, sin internet | Costo cero por uso y privacidad; corre en nuestra máquina | Gratis |
| **Postgres (en Docker)** | La base de datos donde se guarda todo | Memoria del negocio: keywords, decisiones, taxonomía | Gratis (local) |
| **eRank** | Herramienta externa de datos de Etsy | Da la demanda y competencia reales de cada keyword | Suscripción aparte |
| **Printify** | Proveedor que imprime y envía | Es nuestra fábrica sin stock | Se paga por pedido |
| **Etsy** | El mercado donde vendemos | Es la tienda | Comisiones de Etsy |

> [!note] Estado de las integraciones
> Hoy **Printify y Etsy están simulados** (mock): el sistema hace de cuenta que
> los llama y devuelve un resultado de ejemplo, para poder probar el flujo
> completo sin gastar ni publicar nada. Conectarlos de verdad es un próximo paso.

## El cerebro de IA: Ollama con qwen3.5

Los agentes "piensan" usando un modelo de lenguaje (una IA tipo ChatGPT), pero
en vez de pagar por cada consulta a un servicio en la nube, corremos un modelo
**gratis y local** llamado `qwen3.5:9b` a través de un programa llamado
**Ollama**.

- **Ventaja:** costo cero por uso y todo queda en nuestra máquina.
- **Límite:** la máquina es una MacBook Pro M2 con 16 GB de memoria, así que
  corre **un solo modelo a la vez** y los agentes trabajan **de a uno, en fila**
  (no todos en paralelo). Para el volumen que manejamos, alcanza.

> [!tip] Opción "modelo en la nube" para el paso delicado
> El sistema está preparado para que el paso de **validación** (el que decide si
> un tema sirve) use un modelo más potente en la nube (Claude), que sigue
> instrucciones con más fidelidad. Está desactivado por defecto para que todo
> funcione sin pagar; se activa con una línea de configuración cuando queramos.

## La memoria: base de datos Postgres

Todo lo que el sistema aprende se guarda en una base de datos (Postgres, dentro
de Docker, corriendo en la misma Mac). Hoy guarda dos cosas principales:

- **Keywords** (palabras de búsqueda): cada una con su demanda, competencia,
  dificultad y la decisión que se tomó (sirve / no sirve / trampa).
- **Taxonomía de nichos**: una lista de 453 ítems (ocasiones, profesiones,
  relaciones familiares, mascotas, hobbies) que se combinan para crear temas de
  diseño únicos. Viene del "Cross-Niching Guide Book 2.0".

Que esto quede guardado es lo que convierte al sistema en un **activo que
crece**: cada corrida deja más conocimiento que la anterior.

## La fuente de datos de mercado: eRank

El sistema **no adivina** si un tema vende. Para eso usamos **eRank**, una
herramienta de análisis de Etsy que nos dice, para cada keyword, cuánta gente la
busca y cuánta competencia tiene.

eRank no tiene una conexión automática lista para usar en este flujo, así que
una persona corre las keywords en eRank y trae los resultados. Ese es el punto
donde el proceso se parte en dos y entra el humano — ver
[[05 - Flujo del proceso]].

## El orquestador: Strands Agents

Es la pieza que coordina a todos los agentes y define en qué orden trabajan.
Merece su propia nota: [[03 - Qué es Strands Agents]].

## Nota sobre el idioma del proyecto

Por convención del equipo:

- **Las conversaciones y esta documentación van en español.**
- **Todo el código va en inglés** (nombres de archivos, columnas de la base de
  datos, instrucciones de los agentes). Por eso, cuando en esta documentación
  aparece un término en inglés como `niche`, `keyword` o `DRAFT`, es porque así
  se llama dentro del sistema. El [[07 - Glosario]] los traduce todos.

---

Siguiente: [[03 - Qué es Strands Agents]] · Volver al [[MOC - POD Agents]]
