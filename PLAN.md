# Civiltek Oficina Virtual

Aplicación web estática, adaptable a tablet y PC. **Versión 0.2**: panel de tareas, proyectos y calculadora de APU con IVA configurable.

## Funciones actuales
- Registrar proyectos y encargos asignados a siete roles.
- Filtrar encargos y actualizar su estado.
- Calcular un APU con insumos, unidades, cantidades, precios, gastos generales, utilidad e IVA.
- Exportar e importar respaldo JSON.
- Persistencia en el navegador con localStorage.

## Límites importantes
Esta versión **no ejecuta agentes IA**. Los roles son organizadores de tareas. No hay autenticación, sincronización entre dispositivos, integración Google Drive ni almacenamiento en servidor. Los datos se guardan solo en el navegador; no ingresar documentos confidenciales o personales.

## Uso
Abrir `index.html` en un navegador moderno. No requiere instalación ni claves API.

## Próximos hitos
1. Backend con usuarios, almacenamiento privado y auditoría.
2. Integración de proveedores IA con claves almacenadas en servidor.
3. Documentos reales DOCX/XLSX/PDF y revisión humana.
4. Integraciones Drive y Gmail con autorización explícita.

## Seguridad
Nunca publicar claves API en el repositorio ni en JavaScript de frontend. Mantener repositorio privado hasta contar con autenticación y revisión de seguridad.
