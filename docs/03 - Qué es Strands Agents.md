---
titulo: "03 - Qué es Strands Agents"
tipo: nota
proyecto: pod-agents
estado: en-desarrollo
actualizado_en: 2026-08-14
tags:
  - pod-agents
  - strands
  - concepto
---

# Qué es Strands Agents (el orquestador)

## La idea en una analogía

Imaginá una **cocina de restaurante**. Hay varios cocineros, cada uno experto en
una cosa: uno hace la salsa, otro la carne, otro emplata. Nadie hace todo. Y hay
un **orden fijo**: primero la salsa, después la carne, al final se emplata. Un
jefe de cocina se asegura de que cada plato pase por cada estación en el orden
correcto y de que nada se saltee.

**Strands Agents es ese jefe de cocina.** Es una librería (una herramienta de
programación) que nos deja:

1. Definir varios **agentes**, cada uno especialista en una tarea.
2. Conectarlos en un **orden** determinado.
3. Pasar el resultado de uno como entrada del siguiente.
4. Poner **compuertas** (puntos de control) que deciden si el trabajo sigue o
   se rechaza y se vuelve atrás.

## Qué es un "agente", en este contexto

Un agente es una IA con **un rol fijo y una lista de herramientas**. No es un
chat abierto: tiene un trabajo concreto, instrucciones precisas de cómo hacerlo
y un formato de salida esperado.

Cada agente del sistema tiene tres cosas:

- **Un rol** (ej: "sos el diseñador de producto"): sus instrucciones, escritas
  en un texto que se llama *system prompt*.
- **Herramientas**: acciones que puede ejecutar (ej: "revisar si una frase choca
  con una marca registrada"). Son funciones de código, no imaginación de la IA.
- **Una salida**: el resultado de su trabajo, en un formato acordado, que se lo
  pasa al siguiente.

## Por qué elegimos este patrón (y no otro)

Strands ofrece varias formas de coordinar agentes. Nosotros usamos el patrón
**"Graph"** (grafo), que es una **cadena ordenada con compuertas**. Lo elegimos
porque nuestro flujo es justamente eso: una secuencia de pasos con un punto de
control claro (la validación del tema).

> [!info] Por qué importa que sea determinístico
> Un patrón alternativo ("Swarm", enjambre) deja que los agentes decidan solos a
> quién pasarle el trabajo. Eso es más flexible pero **impredecible**. Para un
> proceso de negocio queremos lo contrario: que siempre pase lo mismo, en el
> mismo orden. Por eso: grafo, no enjambre.

## La regla de oro: la herramienta decide, no la IA

Este es el principio de diseño más importante del sistema y conviene que quede
claro:

> [!important] Las decisiones de riesgo las toma una regla fija, no la IA
> En los pasos donde una decisión equivocada cuesta dinero o problemas legales
> (¿este tema sirve?, ¿esta frase choca con una marca?), **no** dejamos que la
> IA "opine". Una porción de código con reglas fijas calcula la respuesta, y el
> agente solo la **reporta**. La IA redacta y organiza; el código decide.

Esto hace al sistema **confiable** aunque el modelo local a veces divague: los
números y los veredictos no dependen del humor del modelo, dependen de reglas
medibles. Ver los umbrales concretos en [[06 - La salida y cómo leerla]].

De hecho, dos pasos que al principio eran agentes de IA (investigar keywords y
validar el tema) **se convirtieron en código puro** justamente por esto. Hoy son
más rápidos, gratis y siempre dan el mismo resultado. Ver [[04 - Los agentes]].

## Cómo se ve en la práctica

El sistema arma dos "cadenas de cocina" separadas (por la compuerta humana que
hay en el medio):

- **Etapa 1 (descubrimiento):** un solo agente, el **director**, elige el tema.
- **Etapa 2 (producción):** cuatro agentes en fila —
  **diseño → producción → marketing → operaciones**.

Strands también nos da, de regalo, un sistema de **trazas**: mientras corre,
imprime en pantalla qué agente empezó, cuánto tardó y qué herramienta usó. Eso
nos deja ver el proceso por dentro sin adivinar.

---

Siguiente: [[04 - Los agentes]] · Volver al [[MOC - POD Agents]]
