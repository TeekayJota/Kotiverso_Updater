import os
import boto3
import json
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURACIÓN ESTÁTICA (LLAVES) ---
ACCESS_KEY = os.getenv("R2_ACCESS_KEY")
SECRET_KEY = os.getenv("R2_SECRET_KEY")
ENDPOINT_URL = os.getenv("R2_ENDPOINT_URL")
NOMBRE_BUCKET = os.getenv("R2_BUCKET_NAME")

# --- RUTAS LOCALES ---
RUTA_DATOS_MC = os.getenv("LOCAL_RUTA_DATOS_MC")
RUTA_MANIFEST_LOCAL = os.getenv("LOCAL_RUTA_MANIFEST_LOCAL")
RUTA_INDEX_LOCAL = "index.json" # El index debe estar en la carpeta del manager

def obtener_manifiesto_remoto(s3, prefijo):
    """Descarga el manifiesto de la carpeta específica del pack en el R2."""
    try:
        ruta_s3 = f"{prefijo}/manifest.json"
        obj = s3.get_object(Bucket=NOMBRE_BUCKET, Key=ruta_s3)
        contenido = obj['Body'].read().decode('utf-8')
        datos = json.loads(contenido)
        
        if "files" in datos:
            print(f"✅ Manifiesto remoto de '{prefijo}' cargado.")
            return datos["files"] 
        return {}
    except Exception:
        print(f"ℹ️ No hay manifiesto previo en '{prefijo}'. Se subirá todo como nuevo.")
        return {}

def sincronizar_eficiente():
    # 1. Cargar Index para saber qué packs existen
    if not os.path.exists(RUTA_INDEX_LOCAL):
        print("❌ ERROR: No se encuentra index.json localmente.")
        return

    with open(RUTA_INDEX_LOCAL, "r", encoding="utf-8") as f:
        datos_index = json.load(f)
    
    packs = {p["id"]: p for p in datos_index["modpacks"]}
    print("\n--- PROYECTOS DISPONIBLES ---")
    for pid in packs.keys(): print(f" > {pid}")
    
    eleccion = input("\n¿Qué pack vas a subir al R2? (Escribe el ID): ").lower()
    
    if eleccion not in packs:
        print("❌ ID no reconocido en el index.json")
        return

    # Seteamos el prefijo dinámicamente según la elección
    prefijo_nube = packs[eleccion]["prefijo_nube"]

    if not RUTA_DATOS_MC or not os.path.exists(RUTA_DATOS_MC):
        print(f"❌ ERROR: La ruta local {RUTA_DATOS_MC} no existe.")
        return

    # 2. Inicializar S3
    s3 = boto3.client('s3', endpoint_url=ENDPOINT_URL, 
                     aws_access_key_id=ACCESS_KEY, 
                     aws_secret_access_key=SECRET_KEY, 
                     region_name="auto")

    print(f"\n🚀 Iniciando subida para: {eleccion.upper()}")
    print(f"📂 Carpeta destino en R2: /{prefijo_nube}")
    
    manifiesto_remoto = obtener_manifiesto_remoto(s3, prefijo_nube)

    print(f"📦 Escaneando archivos locales...")
    archivos_locales_detectados = set()
    subidos = 0
    saltados = 0

    # 3. Subida inteligente (Compara tamaño)
    for raiz, _, archivos in os.walk(RUTA_DATOS_MC):
        for nombre in archivos:
            ruta_local = os.path.join(raiz, nombre)
            relativa = os.path.relpath(ruta_local, RUTA_DATOS_MC).replace("\\", "/")
            ruta_s3 = f"{prefijo_nube}/{relativa}"
            
            archivos_locales_detectados.add(relativa)
            
            necesita_subir = False
            if relativa not in manifiesto_remoto:
                necesita_subir = True 
            else:
                if os.path.getsize(ruta_local) != manifiesto_remoto[relativa]['size']:
                    necesita_subir = True 

            if necesita_subir:
                print(f"⬆️ Subiendo: {relativa}")
                s3.upload_file(ruta_local, NOMBRE_BUCKET, ruta_s3)
                subidos += 1
            else:
                saltados += 1

    print("-" * 50)
    print(f"🧹 Limpiando archivos obsoletos en /{prefijo_nube}...")
    
    archivos_en_nube = set(manifiesto_remoto.keys())
    archivos_a_eliminar = archivos_en_nube - archivos_locales_detectados
    
    eliminados = 0
    for archivo_viejo in archivos_a_eliminar:
        if archivo_viejo == "manifest.json": continue
        
        ruta_s3_borrar = f"{prefijo_nube}/{archivo_viejo}"
        try:
            print(f"🗑️ Eliminando: {archivo_viejo}")
            s3.delete_object(Bucket=NOMBRE_BUCKET, Key=ruta_s3_borrar)
            eliminados += 1
        except Exception as e:
            print(f"❌ Error al borrar {archivo_viejo}: {e}")

    print("-" * 50)
    print(f"🧠 Subiendo nuevo manifiesto a /{prefijo_nube}/manifest.json...")
    s3.upload_file(RUTA_MANIFEST_LOCAL, NOMBRE_BUCKET, f"{prefijo_nube}/manifest.json")

    print(f"\n✅ Sincronización de '{eleccion}' terminada.")
    print(f"📈 Resumen: Subidos: {subidos} | Saltados: {saltados} | Eliminados: {eliminados}")

if __name__ == "__main__":
    sincronizar_eficiente()