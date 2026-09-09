import streamlit as st
import pandas as pd
from supabase import create_client

print("🔄 Conectando a Supabase...")

# Read keys via Streamlit Secrets
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
except KeyError as e:
    print(f"❌ No se encontró la clave en .streamlit/secrets.toml: {e}")
    exit()

# Verify that the URL and KEY are strings
url = str(url).strip()
key = str(key).strip()

try:
    supabase = create_client(url, key)
    print("✅ Conexión establecida con éxito a Supabase.")
except Exception as e:
    print(f"❌ Error al iniciar el cliente de Supabase: {e}")
    exit()

# Read Excel and prepare dataframe
print("📄 Cargando 'data/listado_precios_clientes.xlsx'...")
try:
    df = pd.read_excel('data/listado_precios_clientes.xlsx')
    
    df_preparado = pd.DataFrame({
        'user_key': 'arturo',
        'codigo_articulo': df['ID'].fillna('').astype(str),
        'coleccion': df['COLECCIÓN'].fillna('').astype(str),
        'nombre_articulo': df['NOMBRE ARTÍCULO'].astype(str).str.strip().str.upper(),
        'categoria': df['CATEGORÍA'].fillna('').astype(str),
        'id_cliente': df['ID_CLIENTE'].astype(str).str.strip(),
        'precio_cliente': pd.to_numeric(df['PRECIO CLIENTE'], errors='coerce').fillna(0.0),
        'precio_confeccion': pd.to_numeric(df['PRECIO CONFECCIÓN'], errors='coerce').fillna(0.0)
    })
    
    registros = df_preparado.to_dict(orient='records')
    print(f"📦 Prenda(s) preparada(s): {len(registros)}")
except Exception as e:
    print(f"❌ Error al procesar el Excel: {e}")
    exit()

# Upload to Supabase
print("🚀 Subiendo catálogo a Supabase...")
try:
    response = supabase.table("catalogo_precios").insert(registros).execute()
    print(f"🎉 ¡ÉXITO! Se han cargado {len(registros)} artículos en 'catalogo_precios'.")
except Exception as e:
    print(f"❌ Error en la inserción a la base de datos: {e}")