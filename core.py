import os
import hashlib
import requests
from requests.adapters import HTTPAdapter
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from dotenv import load_dotenv
load_dotenv()

# --- CONFIGURACIÓN ---
MODO_PRUEBA = os.getenv("MODO_PRUEBA", "False").lower() == "true"

if MODO_PRUEBA:
    RUTA_MINECRAFT = os.getenv("RUTA_ENTORNO_PRUEBAS")
else:
    RUTA_MINECRAFT = os.path.join(os.getenv('APPDATA'), '.minecraft')

ELEMENTOS_GESTIONADOS = ['mods', 'config', 'versions', 'fancymenu_data', 'defaultconfigs', 'resourcepacks', 'options.txt', 'shaderpacks']
ARCHIVO_ESTADO = os.path.join(RUTA_MINECRAFT, "perfil_activo.txt")

progreso_lock = Lock()
descargado_global = 0

def obtener_hash_sha256(ruta_archivo):
    sha256 = hashlib.sha256()
    try:
        with open(ruta_archivo, "rb") as f:
            for bloque in iter(lambda: f.read(4096), b""):
                sha256.update(bloque)
        return sha256.hexdigest()
    except: return None

# AÑADIMOS EL PARÁMETRO "SESSION"
def descargar_hilo(datos_archivo, callback_ui, total_bytes, inicio_sync, session):
    global descargado_global
    ruta, datos, ruta_local = datos_archivo
    nombre_fichero = os.path.basename(ruta)
    os.makedirs(os.path.dirname(ruta_local), exist_ok=True)
    
    intentos = 0
    max_intentos = 3
    
    while intentos < max_intentos:
        try:
            # USAMOS LA SESIÓN COMPARTIDA EN VEZ DE REQUESTS.GET
            # Bajamos el timeout a 30s porque ahora la conexión ya está abierta
            with session.get(datos["url"], stream=True, timeout=30) as r:
                r.raise_for_status()
                with open(ruta_local, "wb") as f:
                    # Doblamos el chunk_size a 64KB para exprimir la fibra
                    for trozo in r.iter_content(chunk_size=65536): 
                        if trozo:
                            f.write(trozo)
                            with progreso_lock:
                                descargado_global += len(trozo)
                                if callback_ui:
                                    porc = descargado_global / total_bytes
                                    transcurrido = time.time() - inicio_sync
                                    vel = descargado_global / transcurrido if transcurrido > 0 else 0
                                    eta = int((total_bytes - descargado_global) / vel) if vel > 0 else 0
                                    callback_ui(f"⬇️ {nombre_fichero}", porc, eta)
            return True
        except Exception as e:
            intentos += 1
            if intentos == max_intentos:
                print(f"❌ Error definitivo en {nombre_fichero}: {e}")
            else:
                time.sleep(1)
    
    return False

def cambiar_perfil(perfil_destino):
    os.makedirs(RUTA_MINECRAFT, exist_ok=True)
    perfil_actual = "user"
    if os.path.exists(ARCHIVO_ESTADO):
        with open(ARCHIVO_ESTADO, 'r', encoding='utf-8') as f:
            perfil_actual = f.read().strip()
    
    if perfil_actual == perfil_destino: return

    for elemento in ELEMENTOS_GESTIONADOS:
        ruta_base = os.path.join(RUTA_MINECRAFT, elemento)
        ruta_guardada = os.path.join(RUTA_MINECRAFT, f"{elemento}_{perfil_actual}")
        ruta_destino = os.path.join(RUTA_MINECRAFT, f"{elemento}_{perfil_destino}")

        if os.path.exists(ruta_base): os.rename(ruta_base, ruta_guardada)
        if os.path.exists(ruta_destino): os.rename(ruta_destino, ruta_base)
        else:
            if "." not in elemento: os.makedirs(ruta_base, exist_ok=True)

    with open(ARCHIVO_ESTADO, 'w', encoding='utf-8') as f:
        f.write(perfil_destino)

# --- FUNCIÓN TURBO ---
def sincronizar_archivos(url_manifest, callback_ui=None, hilos=5, descargar_shaders=False):
    global descargado_global
    descargado_global = 0
    
    try:
        r = requests.get(url_manifest, timeout=10)
        manifest = r.json()
    except: return False

    archivos_remotos = manifest.get("files", {})
    pendientes = []
    total_bytes = 0
    
    # ---------------------------------------------------------
    # 1. LIMPIADOR DE MODS FANTASMAS (Mantenimiento del Servidor)
    # ---------------------------------------------------------
    carpetas_estrictas = ["mods"] # Aquí limpiamos lo que no deba estar
    if descargar_shaders: carpetas_estrictas.append("shaderpacks")

    for carpeta in carpetas_estrictas:
        ruta_carpeta = os.path.join(RUTA_MINECRAFT, carpeta)
        if os.path.exists(ruta_carpeta):
            for archivo in os.listdir(ruta_carpeta):
                ruta_completa = os.path.join(ruta_carpeta, archivo)
                if os.path.isfile(ruta_completa):
                    ruta_web = f"{carpeta}/{archivo}" # Ej: mods/archivo.jar
                    # Si el mod físico no está en la nube, ¡a la basura!
                    if ruta_web not in archivos_remotos:
                        try: os.remove(ruta_completa)
                        except: pass

    # ---------------------------------------------------------
    # 2. FILTRO DE DESCARGAS (El motor inteligente)
    # ---------------------------------------------------------
    for ruta, datos in archivos_remotos.items():
        # Filtro de shaders
        if "shaderpacks" in ruta and not descargar_shaders:
            continue

        ruta_local = os.path.join(RUTA_MINECRAFT, os.path.normpath(ruta))
        
        # FILTRO OPTIONS: Si ya existe en este perfil, ni lo tocamos.
        if "options.txt" in ruta and os.path.exists(ruta_local):
            continue

        if obtener_hash_sha256(ruta_local) != datos["hash"]:
            pendientes.append((ruta, datos, ruta_local))
            total_bytes += datos.get("size", 0)

    if not pendientes: return True

    inicio_sync = time.time()
    exito_total = True

    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(pool_connections=hilos, pool_maxsize=hilos, max_retries=1)
    session.mount('https://', adapter)

    with ThreadPoolExecutor(max_workers=hilos) as executor:
        futures = [executor.submit(descargar_hilo, p, callback_ui, total_bytes, inicio_sync, session) for p in pendientes]
        for future in as_completed(futures):
            if future.result() is False:
                exito_total = False

    session.close()

    return exito_total