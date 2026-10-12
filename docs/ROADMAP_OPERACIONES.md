# Civiltek · Arquitectura de operaciones (octubre 2026)

## Referencias
- OpenAI Agents SDK: https://openai.github.io/openai-agents-js/guides/multi-agent/
- OpenAI Agents SDK (human review, tools and orchestration): https://developers.openai.com/api/docs/guides/agents/sdk
- Procore workflows: https://www.procore.com/library/construction-workflows
- Autodesk project management: https://construction.autodesk.com/workflows/construction-project-management/
- ChileCompra API: https://www.chilecompra.cl/api/

## Problemas reales que debe resolver
1. Construcción/MOP: estados de pago, cubicaciones, protocolos, no conformidades, cartas, consultas técnicas, control de cambios, avances.
2. Empresas de ingeniería: presupuestos y APU, revisión de antecedentes, control de versiones, entregables, informes, programación.
3. Consultoras: recepción de clientes, asignación de trabajos, revisión humana, emisión de informes, facturación futura.
4. Licitaciones: descubrimiento de oportunidades, análisis de bases, admisibilidad, vencimientos, oferta, trazabilidad.
5. Administración: responsables, fechas, evidencia, historial y tablero de pendientes.

## Principios de producto
- Cada agente debe ejecutar tareas verificables, no simular actividad mediante animaciones.
- El director distribuye; especialistas generan borradores; auditor revisa; una persona autoriza lo externo.
- Separar *datos de contrato* de *supuestos* y *cálculos*.
- Nunca enviar cartas, ofertas ni documentos oficiales sin aprobación humana explícita.
- Guardar trazabilidad de estados, responsables y decisiones.
- Medir tiempos, tasa de errores, costo por encargo y revisiones.

## Implementado en esta fase
- API de operaciones con 7 plantillas, estados y transiciones controladas.
- Historial persistente de eventos, etapas y aprobaciones.
- Interfaz de operaciones y acceso desde el panel.
- Pruebas automatizadas de transiciones y controles.
- Se conserva el pipeline Director → Especialistas → Auditor ya existente.

## Próximas fases (no implementadas)
- Cola de trabajo asíncrona con persistencia y recuperación tras reinicio.
- Integración entre el flujo de operaciones y ejecución real de agentes.
- Roles separados por usuario/empresa y control de permisos.
- Extracción verificable de PDF/Word/Excel con citas a documentos fuente.
- Conectores Drive/Gmail/Libro de Obras; notificaciones y SLA.
- Métricas de calidad, costos, latencia y evaluación de agentes.
- Despliegue probado, monitoreo y pruebas de integración con OpenRouter.
