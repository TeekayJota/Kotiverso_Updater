import os
import boto3
import json
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURACIÓN DESDE ENTORNO ---
ACCESS_KEY = os.getenv("R2_ACCESS_KEY")
SECRET_KEY = os.getenv("R2_SECRET_KEY")
ENDPOINT_URL = os.getenv("R2_ENDPOINT_URL")
NOMBRE_BUCKET = os.getenv("R2_BUCKET_NAME")
PREFIJO_NUBE = os.getenv("R2_PREFIJO_NUBE")

RUTA_DATOS_MC = os.getenv("LOCAL_RUTA_DATOS_MC")
RUTA_MANIFEST_LOCAL = os.getenv("LOCAL_RUTA_MANIFEST_LOCAL")

def obtener_manifiesto_remoto(s3):
    """Descarga el manifiesto de la nube y extrae la sección de archivos."""
    try:
        ruta_s3 = f"{PREFIJO_NUBE}/manifest.json"
        obj = s3.get_object(Bucket=NOMBRE_BUCKET, Key=ruta_s3)
        contenido = obj['Body'].read().decode('utf-8')
        datos = json.loads(contenido)
        
        if "files" in datos:
            print("✅ Manifiesto remoto cargado correctamente.")
            return datos["files"] 
        else:
            print("⚠️ El manifiesto no tiene la sección 'files'.")
            return {}
    except Exception as e:
        print(f"❌ No se pudo leer el manifiesto remoto: {e}")
        return {}

def sincronizar_eficiente():
    if not RUTA_DATOS_MC or not os.path.exists(RUTA_DATOS_MC):
        print("❌ ERROR: La ruta local de Minecraft no es válida. Revisa tu .env")
        return

    s3 = boto3.client('s3', endpoint_url=ENDPOINT_URL, 
                     aws_access_key_id=ACCESS_KEY, 
                     aws_secret_access_key=SECRET_KEY, 
                     region_name="auto")

    print("🔍 Obteniendo manifiesto remoto...")
    manifiesto_remoto = obtener_manifiesto_remoto(s3)

    print(f"📦 Escaneando archivos locales...")
    archivos_locales_detectados = set()
    subidos = 0
    saltados = 0

    for raiz, _, archivos in os.walk(RUTA_DATOS_MC):
        for nombre in archivos:
            ruta_local = os.path.join(raiz, nombre)
            relativa = os.path.relpath(ruta_local, RUTA_DATOS_MC).replace("\\", "/")
            ruta_s3 = f"{PREFIJO_NUBE}/{relativa}"
            
            archivos_locales_detectados.add(relativa)
            
            necesita_subir = False
            if relativa not in manifiesto_remoto:
                necesita_subir = True 
            else:
                if os.path.getsize(ruta_local) != manifiesto_remoto[relativa]['size']:
                    necesita_subir = True 

            if necesita_subir:
                print(f"⬆️ Actualizando: {ruta_s3}")
                s3.upload_file(ruta_local, NOMBRE_BUCKET, ruta_s3)
                subidos += 1
            else:
                saltados += 1

    print("-" * 50)
    print("🧹 Buscando archivos obsoletos en R2...")
    
    archivos_en_nube = set(manifiesto_remoto.keys())
    archivos_a_eliminar = archivos_en_nube - archivos_locales_detectados
    
    eliminados = 0
    for archivo_viejo in archivos_a_eliminar:
        if archivo_viejo == "manifest.json": continue
        
        ruta_s3_borrar = f"{PREFIJO_NUBE}/{archivo_viejo}"
        try:
            print(f"🗑️ Eliminando de R2: {ruta_s3_borrar}")
            s3.delete_object(Bucket=NOMBRE_BUCKET, Key=ruta_s3_borrar)
            eliminados += 1
        except Exception as e:
            print(f"❌ Error al borrar {archivo_viejo}: {e}")

    print("-" * 50)
    print("🧠 Actualizando manifiesto en la nube...")
    s3.upload_file(RUTA_MANIFEST_LOCAL, NOMBRE_BUCKET, f"{PREFIJO_NUBE}/manifest.json")

    print(f"✅ Sincronización terminada.")
    print(f"📈 Subidos: {subidos} | ⏩ Saltados: {saltados} | 🗑️ Eliminados: {eliminados}")

if __name__ == "__main__":
    sincronizar_eficiente()