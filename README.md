# Kotimanager: Minecraft Multi-Profile Updater (v2.1.0)

Kotimanager es un gestor de entornos de Minecraft diseñado para comunidades que buscan simplicidad. Permite saltar entre modpacks pesados y el perfil personal del usuario de forma instantánea, garantizando que todos tengan los mismos archivos y la versión de Java correcta sin intervención manual.

## Novedades de la v2.1.0
- **Sistema de Bodegas Inteligente:** Ahora el programa aísla los perfiles en carpetas con sufijos (ej. mods_deceasedcraft, mods_user). Nunca más perderás tus carpetas personales al cambiar de modpack.
- **Detección Multinivel de Java:** El manager ahora rastrea instalaciones de Java 8, 17 y 21 en todo el disco duro (Microsoft, Adoptium, Oracle), evitando descargas innecesarias si el usuario ya tiene el JDK.
- **Restauración de Perfil Personal:** Opción nativa para volver al estado original del usuario (user) moviendo los archivos de la nube a su bodega y recuperando el vanilla/personal al instante.
- **Modo Turbo Optimizado:** Gestión de hasta 8 hilos concurrentes con sesiones persistentes (HTTP Keep-Alive) para minimizar la latencia en packs con miles de archivos pequeños.

## Arquitectura del Sistema
### 1. El Cliente (Updater)
- ui.py: Interfaz moderna con CustomTkinter. Incluye selector dinámico de perfiles y barra de progreso con cálculo de ETA y velocidad.
- core.py: El motor de sincronización. Realiza el baile de carpetas, verifica hashes SHA-256 y gestiona la limpieza de archivos obsoletos.
- prerequisites.py: El guardian del entorno. Busca versiones de Java en el PATH y en rutas comunes de Windows. Si no existen, realiza una instalación silenciosa de archivos .msi.

### 2. El Administrador (Nube)
- index.json: El cerebro en la nube. Define IDs de perfil, versiones de Java requeridas y URLs de manifiestos.
- creador_manifest.py: Herramienta para el admin que escanea carpetas locales y genera el mapa de hashes para subir al bucket S3/R2.

## Instalacion y Setup (Desarrollo)
### Requisitos
- Python 3.10+
- Acceso a un bucket compatible con S3 (Actualmente usa: Cloudflare R2).

### Configuracion del Entorno (.env)
Crea un archivo .env en la raiz para habilitar la conexion:

R2_ACCESS_KEY=tu_key
R2_SECRET_KEY=tu_secret
R2_ENDPOINT_URL=https://tu-id.r2.cloudflarestorage.com
R2_BUCKET_NAME=nombre-del-bucket
URL_INDEX=https://tu-dominio.com/index.json

## Compilacion para Usuarios (Produccion)
Para distribuir a los jugadores sin que necesiten Python ni archivos .env, se recomienda compilar inyectando la URL del indice directamente en el codigo o via CLI:

pyinstaller --noconsole --onefile --uac-admin --icon=icon.ico --name "Kotimanager" --collect-all customtkinter ui.py

## Transparencia
El codigo es abierto para garantizar que:
1. No se recolectan datos del usuario.
2. El movimiento de carpetas es estrictamente dentro de .minecraft.
3. La instalacion de Java es segura y proviene de fuentes oficiales (R2 administrado).