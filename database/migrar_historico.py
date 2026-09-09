import os
import sys
import pandas as pd
from datetime import datetime
from supabase import create_client

# 1. Función para leer credenciales de .streamlit/secrets.toml
def obtener_credenciales():
    url, key = None, None
    ruta_secrets = os.path.join(".streamlit", "secrets.toml")
    
    if os.path.exists(ruta_secrets):
        with open(ruta_secrets, "r", encoding="utf-8") as f:
            for linea in f:
                if "SUPABASE_URL" in linea and "=" in linea:
                    url = linea.split("=")[1].strip().strip('"').strip("'")
                elif "SUPABASE_KEY" in linea and "=" in linea:
                    key = linea.split("=")[1].strip().strip('"').strip("'")
    
    # Fallback a variables de entorno si no están en el archivo
    url = url or os.getenv("SUPABASE_URL")
    key = key or os.getenv("SUPABASE_KEY")
    return url, key

print("⏳ Iniciando proceso de migración...", flush=True)

url, key = obtener_credenciales()

if not url or not key:
    print("❌ Error: No se encontraron las credenciales en .streamlit/secrets.toml", flush=True)
    sys.exit(1)

print(f"🔗 Conectando a Supabase ({url})...", flush=True)
supabase = create_client(url, key)

# 2. Cargar Excel
PATH_EXCEL = "data/registro_facturas.xlsx"
if not os.path.exists(PATH_EXCEL):
    PATH_EXCEL = "registro_facturas.xlsx"

if not os.path.exists(PATH_EXCEL):
    print(f"❌ Error: No se encuentra el archivo Excel en {PATH_EXCEL}", flush=True)
    sys.exit(1)

df = pd.read_excel(PATH_EXCEL)

emisor_map = {"ARTURO CASTRO GARCIA": "arturo"}
cliente_map = {"BELINDA WINGS": "belinda", "WOVEN LABEL": "woven"}

registros = []
max_num_factura = 0

for _, row in df.iterrows():
    date_str = str(row['Fecha']).strip()
    dt = datetime.strptime(date_str, '%d/%m/%y')
    fecha_iso = dt.strftime('%Y-%m-%d')
    
    user_key = emisor_map.get(str(row['Emisor']).strip().upper(), "arturo")
    id_cliente = cliente_map.get(str(row['Cliente']).strip().upper(), str(row['Cliente']).strip().lower())
    
    num_fac_int = int(row['Nº Factura'])
    if num_fac_int > max_num_factura:
        max_num_factura = num_fac_int

    base = float(row['Total sin IVA'])
    total = float(row['Total con IVA'])
    iva = round(total - base, 2)
    
    registros.append({
        "user_key": user_key,
        "numero_factura": str(num_fac_int),
        "id_cliente": id_cliente,
        "fecha_emision": fecha_iso,
        "base_imponible": base,
        "iva_importe": iva,
        "total_factura": total
    })

print(f"📦 Subiendo {len(registros)} facturas a Supabase...", flush=True)

# 3. Inserción en la base de datos
try:
    res = supabase.table("facturas_encabezado").insert(registros).execute()
    if res.data:
        print(f"✅ ¡Éxito! Se han migrado {len(res.data)} facturas.", flush=True)
        
        # 4. Actualizar el contador de facturas
        print(f"🔄 Actualizando último número de factura a {max_num_factura}...", flush=True)
        supabase.table("emisor_config").update({"ultimo_numero": max_num_factura}).eq("user_key", "arturo").execute()
        print("🚀 Proceso finalizado correctamente.", flush=True)
    else:
        print("⚠️ La respuesta de Supabase no devolvió datos insertados.", flush=True)
except Exception as e:
    print(f"❌ Error durante la inserción en Supabase: {e}", flush=True)