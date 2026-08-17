---
titulo: "MOC - POD Agents"
tipo: moc
proyecto: pod-agents
estado: en-desarrollo
actualizado_en: 2026-08-15
tags:
  - pod-agents
  - moc
  - manual
---

# MOC - POD Agents

Índice del **manual de procedimientos** del sistema `pod-agents`: un equipo de
agentes de IA que ayuda a operar una tienda Print-on-Demand (POD) en Etsy.

Esta nota no contiene información propia: es el mapa. Cada enlace lleva a la nota
donde está el detalle. Está pensada para leerse **en orden**, pero cada nota se
sostiene sola.

> [!info] Para quién es esta documentación
> Para un lector **no técnico** que necesita entender cómo funciona el sistema:
> qué hace, por qué, en qué orden, cuándo interviene una persona y qué produce.
> No hace falta saber programar para leerla.

> [!warning] Documento vivo
> El sistema está en desarrollo. Esta documentación se ajusta a medida que
> avanzamos. Cada nota tiene un campo `actualizado_en` en su encabezado: si una
> fecha quedó vieja, probablemente el contenido también.

## Ruta de lectura

1. [[01 - Qué es y qué resuelve]] — el proyecto en una página: qué problema
   ataca, cuál es el objetivo y qué gana el negocio con esto.
2. [[02 - Herramientas y tecnologías]] — con qué está construido y por qué se
   eligió cada pieza (en lenguaje llano).
3. [[03 - Qué es Strands Agents]] — el motor que coordina a los agentes,
   explicado con una analogía simple.
4. [[04 - Los agentes]] — los cinco agentes, qué hace cada uno y **cómo se
   ajustan** cuando queremos cambiar su comportamiento.
5. [[05 - Flujo del proceso]] — el recorrido completo, las dos etapas, dónde y
   por qué interviene una persona. Con diagramas.
6. [[06 - La salida y cómo leerla]] — qué muestra el sistema al terminar y qué
   significa cada parte del resultado.
7. [[07 - Glosario]] — todos los términos técnicos y de negocio, explicados.
8. [[08 - Cómo usar el formulario de Discovery]] — manual de uso de la pantalla
   que genera el bloque de 20 keywords: qué escribir en cada campo, por qué la
   ocasión no es el cruce, y cómo leer el resultado antes de ir a eRank.

## Estado del proyecto de un vistazo

| Parte | Estado |
|---|---|
| Etapa 1: elegir ocasión + generar 20 keywords | Funciona (verificado) |
| Compuerta humana (eRank) | Manual, por diseño |
| Etapa 2: diseño → producción → marketing → operaciones | Funciona (verificado) |
| Publicación real en Etsy | **No** — queda en borrador (DRAFT) a propósito |
| Integraciones reales (Printify, Etsy, imágenes) | Simuladas (mock) por ahora |

## Notas relacionadas fuera de este manual

- El **manual operativo del negocio** (el know-how real de la tienda) vive en
  `POD_Factory_OS_Manual_Operativo_v1.0.pdf`, en la carpeta padre `Joy Design/`.
  Este software es una parte de ese manual, la que se puede automatizar.
