---
titulo: "01 - Qué es y qué resuelve"
tipo: nota
proyecto: pod-agents
estado: en-desarrollo
actualizado_en: 2026-08-14
tags:
  - pod-agents
  - vision-general
---

# Qué es el proyecto y qué problema resuelve

## En una frase

`pod-agents` es un **equipo de asistentes de inteligencia artificial** que
trabajan en cadena para hacer el trabajo repetitivo de lanzar productos en
nuestra tienda Print-on-Demand (POD) de Etsy: desde elegir sobre qué tema
conviene diseñar, hasta dejar el listado (la publicación del producto) casi
listo para revisar y publicar.

## Qué es "Print-on-Demand" (POD)

Vendemos productos (remeras, tazas, posters) con diseños propios, pero **no
tenemos stock**. Cuando alguien compra, un proveedor externo (Printify) imprime
el producto y lo envía. Nosotros ponemos el diseño, el texto y la estrategia; el
proveedor pone la fábrica y el envío.

El negocio no se gana con un diseño genial, se gana con **volumen y buena
elección de temas**: muchos listados bien orientados a lo que la gente busca.

## El problema que resuelve

Lanzar productos POD que efectivamente se vendan implica un trabajo manual,
repetitivo y fácil de hacer mal:

- Decidir **sobre qué tema** diseñar, y con cuánta anticipación (el trabajo
  estacional se prepara meses antes).
- Investigar **qué palabras busca la gente** en Etsy y cuáles tienen demanda real
  sin estar saturadas de competencia.
- Descartar temas que parecen buenos pero no lo son (mucha competencia, poca
  búsqueda, o "trampas").
- Crear el concepto de diseño, el producto, el texto de venta optimizado y dejar
  todo listo para publicar.

Hacer esto a mano, producto por producto, no escala. El sistema lo convierte en
un **proceso repetible** en el que cada paso lo hace un agente especializado, y
las decisiones de riesgo las toma una regla fija (no la "intuición" de la IA).

## El objetivo

> [!important] Objetivo del sistema
> Producir, de forma **repetible y a bajo costo**, listados de productos bien
> orientados al mercado, deteniéndose siempre antes del paso irreversible
> (publicar y pagar), para que una persona apruebe.

Concretamente, el sistema busca:

1. **Escalar por variación, no por creación desde cero.** Un diseño base se
   convierte en muchos listados. Se piensa en lotes, no en productos sueltos.
2. **Acumular conocimiento.** Cada keyword investigada y cada decisión quedan
   guardadas en una base de datos. Ese conocimiento acumulado es el activo real
   del negocio, no un producto puntual.
3. **Separar bien quién hace qué:** qué hace un agente de IA, qué hace un script
   automático y qué tiene que hacer una persona. No todo se automatiza con IA;
   mucho es simplemente una regla o una herramienta.

## Qué NO hace (a propósito)

- **No publica solo.** El sistema deja el listado en estado *borrador* (DRAFT).
  Publicar y pagar órdenes siempre requiere que una persona apruebe.
- **No inventa la demanda.** No adivina si un tema va a vender: usa datos reales
  de una herramienta externa (eRank) que una persona le trae. Ver
  [[05 - Flujo del proceso]].
- **No reemplaza el criterio del negocio.** Automatiza lo repetitivo; las
  decisiones estratégicas y la aprobación final siguen siendo humanas.

## Cómo se conecta con el manual del negocio

El know-how real de la tienda está en un manual operativo de 13 pasos (el PDF
`POD_Factory_OS_Manual_Operativo_v1.0.pdf`). Este software **automatiza la parte
generativa de ese manual** (elegir tema, investigar, diseñar, preparar el
listado). La parte de post-venta (una venta ocurre, se cumple el pedido, se
atiende al cliente) todavía no está dentro del sistema: es un próximo paso.

---

Siguiente: [[02 - Herramientas y tecnologías]] · Volver al [[MOC - POD Agents]]
