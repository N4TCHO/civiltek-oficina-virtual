# Civiltek 0.4 — Instalación y despliegue

## Estado actual
El código incluye interfaz local de proyectos, tareas, APU y cartas; API privada FastAPI con SQLite; generación DOCX; y ejecución opcional de siete perfiles IA mediante OpenRouter.

**No se ha desplegado ni probado extremo a extremo.** Los agentes realizan una llamada individual al proveedor IA; no son autónomos, no navegan Drive/Gmail y no envían cartas por su cuenta.

## Ejecutar en computador
Requiere Python 3.12 o superior.

1. Descargar o clonar el repositorio privado.
2. Crear entorno virtual: `python -m venv .venv`.
3. Activarlo e instalar dependencias: `pip install -r requirements.txt`.
4. Crear archivo `.env` local (no subir a GitHub) con un token aleatorio de al menos 32 caracteres.
5. Configurar variables de entorno según `.env.example` (el archivo .env no se carga automáticamente; usar un gestor de variables de entorno).
6. Iniciar: `uvicorn backend.main:app --host 127.0.0.1 --port 8000`.
7. Abrir `http://127.0.0.1:8000` y `http://127.0.0.1:8000/agentes`.

## Despliegue
- Usar alojamiento Python/Docker con HTTPS, volumen persistente para `CIVILTEK_DB_PATH` y variables secretas.
- Establecer `CIVILTEK_ADMIN_TOKEN` con un secreto aleatorio único (mínimo 32 caracteres).
- Para ejecutar IA, establecer `OPENROUTER_API_KEY` y opcionalmente `OPENROUTER_MODEL`. La suscripción a ChatGPT/Claude **no** incluye créditos de API.
- Configurar copias de seguridad del volumen SQLite.
- **No usar la aplicación para datos confidenciales o clientes reales antes de implementar autenticación multiusuario, control de acceso, límites de solicitudes y revisión de seguridad.**
- No usar servicios con almacenamiento efímero para documentos o registros importantes.

## API disponible
- `GET /api/health`: estado.
- `GET /api/records?kind=project`: consultar registros.
- `POST /api/records`: crear registros.
- `PUT /api/records/{id}`: modificar.
- `DELETE /api/records/{id}`: eliminar.
- `POST /api/agents/run`: borrador de especialista IA (requiere OpenRouter).
- `POST /api/letters/docx`: generar carta Word.

Todos los endpoints, excepto health, requieren encabezado `Authorization: Bearer <CIVILTEK_ADMIN_TOKEN>`.

## Limitaciones técnicas
La interfaz principal aún guarda sus datos en el navegador y no utiliza la API de registros. El token es único para el administrador; no existe recuperación de contraseñas, usuarios, permisos por proyecto, registro de auditoría ni integración Drive. El cálculo APU es referencial y no reemplaza una base de datos MOP validada.
