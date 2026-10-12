# CIVILTEK — Plan de cierre del producto

Estado: desarrollo. No afirmar que existe automatización productiva hasta verificarla.

## Producto objetivo
Consultora multidisciplinaria para Chile: captar oportunidades, recibir solicitudes, organizar especialistas IA, producir DOCX/XLSX/PDF verificables, auditar y entregar a revisión humana. Los documentos que requieren firma profesional deben validarse por personal habilitado.

## Implementado en repositorio (requiere pruebas integradas)
- Autenticación administrativa con cookie HttpOnly de siete días.
- Registro de clientes y solicitudes (interfaz interna).
- Oficina con director, especialistas y auditor, ejecutada bajo demanda.
- Registro persistente SQLite de expedientes.
- Radar de licitaciones ChileCompra con ticket de servidor, filtro y deduplicación.
- Exportación Word de expedientes.

## Bloqueadores de operación real
1. Comprobar que Railway despliega y que /api/health, /clientes, /oficina, /oportunidades cargan.
2. Ejecutar tests de endpoints y sesiones; comprobar cookies detrás del proxy y persistencia del volumen.
3. Configurar ticket gratuito MERCADOPUBLICO_TICKET en Railway; no exponerlo en navegador ni GitHub.
4. Verificar OpenRouter/free y límites del proveedor con llamadas reales.
5. Aislar clientes con cuentas separadas, roles, permisos, auditoría de acceso y controles de privacidad antes de habilitar portal externo.
6. Incorporar documentos fuente y referencias verificables; no inventar normativa ni datos.
7. Implementar tareas asíncronas con cola, reintentos y scheduler; evitar ejecutar trabajos largos en petición HTTP.
8. Habilitar plantillas reales Word/Excel/PDF, motor de matrices y APU, control de versiones y trazabilidad.
9. Preparar aprobación humana y prohibición de envío automático de ofertas, documentos oficiales o compromisos financieros.
10. Pruebas end-to-end y monitoreo de errores/costos.

## Fuentes oficiales priorizadas
- ChileCompra: https://www.chilecompra.cl/api/ (ticket, cuota diaria).
- BCN LeyChile: https://www.bcn.cl/leychile/ (verificar acceso automático).
- SNIFA: https://snifa.sma.gob.cl/Home (datos abiertos).
- SEIA: https://www.sea.gob.cl/informacion-estadistica-del-seia (consultas públicas).
- IDE MMA: https://ide.mma.gob.cl/servicios-de-interoperabilidad (WMS/WFS).
- DGA: https://dga.mop.gob.cl/estadisticas-estaciones-dga/ (reportes).
- Banco Central BDE: https://si3.bcentral.cl/estadisticas/Principal1/Web_Services/index_API_sec1_es.htm (cuenta API).
- IDE Chile: https://www.ide.cl/ (geodatos).
- Listado comunitario: https://github.com/juanbrujo/listado-apis-publicas-en-chile (verificar enlaces obsoletos).

## Orden de entrega
Fase 1: estabilidad y pruebas; radar real; control de errores y gastos.
Fase 2: ingesta de archivos, expediente, director, especialistas, auditor y exportación profesional.
Fase 3: scheduler de búsquedas, clasificación de oportunidades, alertas y preparación asistida de ofertas.
Fase 4: portal multiempresa seguro, aprobaciones y facturación.
Fase 5: servicios especializados (legal, prevención, medioambiente, calidad MOP, APU) con fuentes normativas y revisión de expertos.

## Criterio de finalización
Una empresa puede solicitar un servicio, adjuntar antecedentes, recibir un expediente trazable con entregables editables y referencias, obtener revisión y aprobarlo; el sistema detecta oportunidades periódicamente, registra sus fuentes y funciona sin supervisión manual continua, salvo decisiones y aprobaciones.
