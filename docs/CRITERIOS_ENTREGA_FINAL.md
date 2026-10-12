# Civiltek · Criterios de entrega de producto
Fecha de revisión: 2026-10-12

## Estado actual (implementado en repositorio; producción no verificada)
- Autenticación de administrador con cookie segura.
- Clientes, solicitudes, expedientes, agentes Director/Especialistas/Auditor con OpenRouter.
- Gestión de operaciones con 7 plantillas, etapas, historial y aprobación.
- Estados de pago: cantidades, montos, saldos, Excel y versiones guardadas.
- APU: materiales, mano de obra, equipos, transporte, otros, indirectos, utilidad y Excel.
- Licitaciones: expedientes, extracción de texto PDF/DOCX/XLSX/TXT, matriz preliminar de palabras clave con extractos y Excel.
- Pruebas unitarias y de integración simulada en tests/test_smoke.py; estado CI no confirmado.

## No se considera completo ni validado
- APU masivos a partir del presupuesto oficial y bases; rendimientos y costos verificables.
- Vinculación automática de partidas, cubicaciones, recursos y planificación.
- Interpretación estructurada de requisitos de bases con referencias exactas, revisión de anexos y detección de contradicciones.
- Generación de PCdC, PIE, planes de seguridad, ambientales, carta Gantt y carta de oferta desde plantillas profesionales.
- Cola asíncrona persistente de agentes con reintentos, monitoreo, costos y notificaciones.
- Gestión multiempresa/multiusuario, permisos por rol y aislamiento de datos.
- OCR de PDFs escaneados y planos, interpretación geométrica y cálculos de cantidades.
- Integración verificada con ChileCompra, Google Drive, correo y libro de obras.
- Seguridad: límites de consumo de IA, copias de seguridad, revisión de accesos y análisis de dependencias.
- CI exitoso, despliegue Railway confirmado, pruebas E2E en navegador y aceptación del usuario.

## Criterios de aceptación final
1. CI en verde y versión Railway desplegada con /api/health accesible.
2. Cargar un paquete real de bases y anexos; cada requisito citado a documento y ubicación.
3. Generar APU de todas las partidas sin inventar precios ni rendimientos; identificar datos faltantes.
4. Entregar presupuesto, Gantt, planes, matrices y cartas editables, con auditoría cruzada.
5. Reanudar un trabajo de agentes después de reiniciar servidor, con trazabilidad.
6. Autorización humana obligatoria para documentos oficiales, envíos y ofertas.
7. Respaldo y restauración de datos probado; acceso multiusuario seguro.
8. Documentación de despliegue, administración y uso.
