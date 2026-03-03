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

# Carpetas estándar que siempre queremos aislar por perfil
ELEMENTOS_BASE = ['mods', 'config', 'versions', 'fancymenu_data', 'defaultconfigs', 'resourcepacks', 'shaderpacks', 'options.txt']
ARCHIVO_ESTADO = os.path.join(RUTA_MINECRAFT, "perfil_activo.txt")

progreso_lock = Lock()
descargado_global = 0

def obtener_hash_sha256(ruta_archivo):
    sha256 = hashlib.sha256()
    try:
        if not os.path.exists(ruta_archivo): return None
        with open(ruta_archivo, "rb") as f:
            for bloque in iter(lambda: f.read(4096), b""):
                sha256.update(bloque)
        return sha256.hexdigest()
    except: return None

def descargar_hilo(datos_archivo, callback_ui, total_bytes, inicio_sync, session):
    global descargado_global
    ruta, datos, ruta_local = datos_archivo
    nombre_fichero = os.path.basename(ruta)
    os.makedirs(os.path.dirname(ruta_local), exist_ok=True)
    
    intentos = 0
    max_intentos = 3
    
    while intentos < max_intentos:
        try:
            with session.get(datos["url"], stream=True, timeout=30) as r:
                r.raise_for_status()
                with open(ruta_local, "wb") as f:
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
        except:
            intentos += 1
            time.sleep(1)
    return False

def cambiar_perfil(perfil_destino, elementos_adicionales=None):
    """Mueve las carpetas del perfil actual a su backup y restaura las del destino."""
    os.makedirs(RUTA_MINECRAFT, exist_ok=True)
    
    elementos_finales = list(set(ELEMENTOS_BASE + (elementos_adicionales or [])))
    
    perfil_actual = "user"
    if os.path.exists(ARCHIVO_ESTADO):
        with open(ARCHIVO_ESTADO, 'r', encoding='utf-8') as f:
            perfil_actual = f.read().strip()
    
    if perfil_actual == perfil_destino: return

    for elemento in elementos_finales:
        ruta_base = os.path.join(RUTA_MINECRAFT, elemento)
        ruta_guardada = os.path.join(RUTA_MINECRAFT, f"{elemento}_{perfil_actual}")
        ruta_destino = os.path.join(RUTA_MINECRAFT, f"{elemento}_{perfil_destino}")

        es_archivo = "." in elemento

        # Guardar lo actual en su bodega
        if os.path.exists(ruta_base): 
            try:
                if os.path.exists(ruta_guardada):
                    # Si ya existe el backup, lo borramos antes de renombrar para evitar colisión
                    import shutil
                    if os.path.isdir(ruta_guardada): shutil.rmtree(ruta_guardada)
                    else: os.remove(ruta_guardada)
                os.rename(ruta_base, ruta_guardada)
            except: pass
            
        # Restaurar lo que viene de la bodega de destino
        if os.path.exists(ruta_destino): 
            try: os.rename(ruta_destino, ruta_base)
            except: pass
        else:
            # Si el destino no existe (es nuevo), creamos carpeta vacía (si no es archivo)
            if not es_archivo: os.makedirs(ruta_base, exist_ok=True)

    with open(ARCHIVO_ESTADO, 'w', encoding='utf-8') as f:
        f.write(perfil_destino)

def sincronizar_archivos(url_manifest, perfil_id, callback_ui=None, hilos=5, descargar_shaders=False):
    global descargado_global
    descargado_global = 0
    
    # 1. PROTECCIÓN Y CAMBIO DE PERFIL (Siempre se ejecuta)
    # Detectamos raíces si tenemos el manifest, si no, usamos las base
    raices_detectadas = []
    archivos_remotos = {}

    if url_manifest:
        try:
            r = requests.get(url_manifest, timeout=10)
            manifest = r.json()
            archivos_remotos = manifest.get("files", {})
            set_raices = set()
            for ruta in archivos_remotos.keys():
                raiz = ruta.split('/')[0] if '/' in ruta else ruta
                set_raices.add(raiz)
            raices_detectadas = list(set_raices)
        except: 
            if perfil_id != "user": return False

    if callback_ui: callback_ui("🔄 Protegiendo perfiles...", 0, 0)
    cambiar_perfil(perfil_id, elementos_adicionales=raices_detectadas)

    # 2. FRENO DE MANO PARA PERFIL USER
    if perfil_id == "user" or not url_manifest:
        if callback_ui: callback_ui("✨ Perfil Personal restaurado.", 1, 0)
        return True

    # 3. LIMPIEZA DE ARCHIVOS OBSOLETOS
    for carpeta in raices_detectadas:
        if carpeta == "shaderpacks" and not descargar_shaders: continue
        if "." in carpeta: continue 
        
        ruta_local_folder = os.path.join(RUTA_MINECRAFT, carpeta)
        if os.path.exists(ruta_local_folder):
            for f in os.listdir(ruta_local_folder):
                ruta_f = os.path.join(ruta_local_folder, f)
                if os.path.isfile(ruta_f):
                    if f"{carpeta}/{f}" not in archivos_remotos:
                        try: os.remove(ruta_f)
                        except: pass

    # 4. FILTRADO DE DESCARGAS
    pendientes = []
    total_bytes = 0
    for ruta, datos in archivos_remotos.items():
        if "shaderpacks" in ruta and not descargar_shaders: continue
        
        ruta_local = os.path.join(RUTA_MINECRAFT, os.path.normpath(ruta))
        if "options.txt" in ruta and os.path.exists(ruta_local): continue

        if obtener_hash_sha256(ruta_local) != datos["hash"]:
            pendientes.append((ruta, datos, ruta_local))
            total_bytes += datos.get("size", 0)

    if not pendientes: return True

    # 5. DESCARGA MULTIHILO
    inicio_sync = time.time()
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(pool_connections=hilos, pool_maxsize=hilos, max_retries=1)
    session.mount('https://', adapter)

    with ThreadPoolExecutor(max_workers=hilos) as executor:
        futures = [executor.submit(descargar_hilo, p, callback_ui, total_bytes, inicio_sync, session) for p in pendientes]
        exito_total = all(f.result() for f in as_completed(futures))

    session.close()
    return exito_total