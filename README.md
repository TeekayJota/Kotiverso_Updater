🎮 Kotimanager: Minecraft Multi-Profile Updater

Kotimanager es un gestor de actualizaciones y perfiles de Minecraft diseñado para comunidades y streamers. Permite sincronizar múltiples modpacks, configuraciones y versiones de Java de forma automática, garantizando que todos los jugadores tengan exactamente los mismos archivos con un solo clic.

🚀 Características Principales

Gestión Multi-Perfil: Cambia dinámicamente entre diferentes "Mundos" o versiones (ej. Kotiverso, Survival Técnico, Vanilla) sin mezclar carpetas.

Sincronización Inteligente: Basada en Hashes SHA-256. Solo descarga lo que ha cambiado o lo que falta.

Auto-Instalación de Java: Verifica y descarga el JDK 21 de forma silenciosa si el usuario no lo tiene.

Modo Turbo: Descargas concurrentes usando ThreadPoolExecutor para aprovechar conexiones de alta velocidad.

Arquitectura Cloud-Agnostic: Compatible con cualquier servicio S3 (Cloudflare R2, AWS S3, Backblaze B2, etc.).

🏗️ Arquitectura del Sistema
El proyecto se divide en dos grandes ecosistemas:

1. El Cliente (Updater)
ui.py: Interfaz visual construida con CustomTkinter. Maneja la selección de perfiles y el progreso en tiempo real.

core.py: El motor. Gestiona el renombrado de carpetas (mods -> mods_user), la comparación de hashes y la descarga multihilo.

prerequisites.py: Se encarga de la salud del entorno (Java 21).

2. El Administrador (Nube)
Para que el updater funcione, necesita leer dos tipos de archivos JSON en la nube:

index.json (El Índice Maestro): Es la lista de todos los modpacks disponibles. Define el nombre, el ID del perfil y la URL de su respectivo manifest.json.

manifest.json (El Mapa de Archivos): Contiene la lista de cada archivo individual (mods/mod.jar, config/file.txt), su Hash y su tamaño. Se genera con creador_manifest.py.

☁️ Configuración de Almacenamiento (S3 / R2)
Este proyecto utiliza Cloudflare R2 por su política de cero costos por transferencia de salida (Egress), pero es 100% compatible con Amazon S3 o similares.

Nota para desarrolladores: Si cambias de proveedor, solo necesitas actualizar el ENDPOINT_URL en tu archivo .env. El código utiliza la librería boto3, que es el estándar para servicios compatibles con S3.

🛠️ Instalación y Setup
Requisitos
Python 3.10+

Entorno virtual (venv) recomendado.

Configuración del Entorno (.env)
El proyecto depende de variables de entorno para proteger claves y rutas privadas. Crea un archivo .env basado en el siguiente ejemplo:

# Cloudflare R2 / S3 Credentials
R2_ACCESS_KEY=tu_key
R2_SECRET_KEY=tu_secret
R2_ENDPOINT_URL=https://tu-id.r2.cloudflarestorage.com
R2_BUCKET_NAME=nombre-del-bucket

# Public Distribution URLs
URL_INDEX=https://tu-dominio.com/index.json
URL_JAVA=https://tu-dominio.com/java.msi
URL_BASE_CLOUD=https://tu-dominio.com/archivos


Comandos iniciales:
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar la interfaz de usuario
python ui.py


🛡️ Transparencia y Seguridad
Este software se distribuye sin firmar (sin certificado de desarrollador), lo que puede provocar alertas de Windows SmartScreen.
¿Por qué el código es abierto? Para que cualquier miembro de la comunidad pueda verificar que:

El programa no recolecta datos personales.

Solo gestiona archivos dentro de la ruta .minecraft.

La solicitud de permisos de Administrador es exclusiva para la instalación del JDK y el movimiento de archivos de sistema.

🤝 Contribuciones
Si quieres añadir soporte para nuevos launchers o mejorar el motor de descarga:

Haz un Fork del proyecto.

Crea tu propia rama de funciones (git checkout -b feature/MejoraIncreible).

Asegúrate de no subir tu archivo .env personal.

¡Envía un Pull Request!