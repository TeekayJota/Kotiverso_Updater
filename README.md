# 🎮 Kotimanager  

**Minecraft Multi-Profile Updater — v2.1.0**

Gestor de entornos de Minecraft diseñado para comunidades que buscan simplicidad, orden y sincronización automática.

Kotimanager permite alternar instantáneamente entre **modpacks pesados** y el **perfil personal del usuario**, garantizando que todos los jugadores tengan:

- 📁 Los mismos archivos  
- ☕ La versión correcta de Java  
- ⚙️ Sin configuración manual  

---

## 🚀 ¿Qué hace Kotimanager?

- ✔ Aísla perfiles para evitar sobrescrituras accidentales  
- ✔ Detecta automáticamente instalaciones de Java  
- ✔ Sincroniza archivos mediante hashes SHA-256  
- ✔ Permite restaurar el perfil personal en segundos  
- ✔ Optimiza descargas masivas con múltiples hilos  

---

## 🆕 Novedades en la v2.1.0

### 🏬 Sistema de Bodegas Inteligente

Los perfiles se aíslan automáticamente en carpetas con sufijos como:

```
mods_deceasedcraft
mods_user
resourcepacks_deceasedcraft
```

Nunca más perderás tus carpetas personales al cambiar de modpack.

---

### ☕ Detección Multinivel de Java

El sistema busca automáticamente instalaciones de:

- Java 8  
- Java 17  
- Java 21  

Detecta versiones instaladas desde:

- Microsoft  
- Adoptium  
- Oracle  

Si el JDK ya está presente, evita descargas innecesarias.

---

### 🔄 Restauración de Perfil Personal

Permite:

- Mover archivos del modpack a su bodega  
- Recuperar el perfil `user` (vanilla/personal)  
- Volver al estado original en segundos  

---

### ⚡ Modo Turbo Optimizado

- Hasta 8 hilos concurrentes  
- Conexiones persistentes (HTTP Keep-Alive)  
- Optimizado para packs con miles de archivos pequeños  

Resultado: menor latencia y mayor velocidad de sincronización.

---

## 🏗 Arquitectura del Sistema

### 🖥 Cliente (Updater)

#### `ui.py`

Interfaz moderna con CustomTkinter que incluye:

- Selector dinámico de perfiles  
- Barra de progreso con ETA  
- Indicador de velocidad  

#### `core.py`

Motor de sincronización que:

- Gestiona el cambio de carpetas  
- Verifica integridad con SHA-256  
- Elimina archivos obsoletos  
- Realiza sincronización incremental  

#### `prerequisites.py`

Encargado de:

- Buscar Java en PATH  
- Escanear rutas comunes en Windows  
- Instalar silenciosamente archivos `.msi` si es necesario  

---

### ☁ Administrador (Nube)

#### `index.json`

Define:

- IDs de perfil  
- Versiones de Java requeridas  
- URLs de manifiestos  

En el repositorio encontrarás un archivo `index.json.example` como referencia para estructurar correctamente el índice.

#### `creador_manifest.py`

Herramienta para el administrador que:

- Escanea carpetas locales  
- Genera hashes SHA-256  
- Produce manifiestos listos para subir a S3 / R2  

---

## 🛠 Instalación y Setup (Desarrollo)

### Requisitos

- Python 3.10+  
- Acceso a un bucket compatible con S3 (probado con Cloudflare R2)  

---

### 🔐 Configuración del Entorno

En lugar de crear manualmente el archivo, revisa:

```
.env.example
```

Este archivo contiene todas las variables necesarias para la conexión al bucket y al índice remoto.  

Simplemente crea tu propio `.env` basándote en ese ejemplo.

---

## 📦 Compilación para Usuarios (Producción)

Para distribuir el ejecutable sin requerir Python ni archivo `.env`:

```bash
pyinstaller --noconsole --onefile --uac-admin --icon=icon.ico --name "Kotimanager" --collect-all customtkinter ui.py
```

Se recomienda inyectar la variable `URL_INDEX` directamente en el código o vía argumento CLI para builds finales.

---

## 🔎 Flujo de Funcionamiento

1. El usuario selecciona un perfil.  
2. Kotimanager verifica Java.  
3. Aísla las carpetas activas.  
4. Compara hashes SHA-256.  
5. Descarga únicamente los archivos necesarios.  
6. El entorno queda listo para jugar.  

---

## 🔐 Transparencia

- No se recolectan datos del usuario.  
- El movimiento de carpetas ocurre exclusivamente dentro de `.minecraft`.  
- La instalación de Java proviene de fuentes oficiales.  
- El almacenamiento en R2 es administrado por el equipo del servidor.  

---

## 📄 Licencia

Este proyecto se distribuye bajo la siguiente licencia:

**PolyForm Noncommercial 1.0.0**

Copyright © 2026 Jonas  

Uso permitido únicamente para fines no comerciales.  
La redistribución o modificación debe respetar los términos establecidos por la licencia.

Para más detalles, consulta el archivo `LICENSE` incluido en el repositorio.