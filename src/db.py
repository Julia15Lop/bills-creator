import os
import pandas as pd
import numpy as np
import streamlit as st
from supabase import create_client, Client

# Desactivar transportes propensos a errores de red en Windows/Streamlit
os.environ["HTTP2_DISABLE"] = "1"
os.environ["GRPC_ENABLE_FORK_SUPPORT"] = "1"

@st.cache_resource
def get_supabase_client() -> Client:
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Error de conexión con Supabase: {e}")
        return None

# --- FUNCIONES DE FACTURAS ---

def get_facturas_df() -> pd.DataFrame:
    supabase = get_supabase_client()
    if not supabase:
        return pd.DataFrame()
    
    try:
        res = supabase.table("facturas_encabezado").select("*").order("id", desc=True).execute()
        if not res.data:
            return pd.DataFrame()
        return pd.DataFrame(res.data).replace({np.nan: None})
    except Exception as e:
        st.error(f"Error al obtener facturas: {e}")
        return pd.DataFrame()

def save_facturas_df(df: pd.DataFrame):
    supabase = get_supabase_client()
    if not supabase or df.empty:
        return

    df_clean = df.copy().replace({np.nan: None})
    records = df_clean.to_dict(orient="records")
    
    to_update = []
    to_insert = []
    
    for row in records:
        clean_row = {k: v for k, v in row.items() if str(v) != 'nan' and v is not None}

        # 1. Normalizar campos a los nombres REALES de la base de datos
        if "fecha" in clean_row:
            clean_row["fecha_emision"] = clean_row.pop("fecha")
            
        if "cliente" in clean_row:
            clean_row["id_cliente"] = clean_row.pop("cliente")

        # 2. Eliminar columnas calculadas o fakes de la vista que no existen en Supabase
        for col_fake in ["Fecha", "Emisor", "Cliente", "Total sin IVA", "Total con IVA", "Fecha_dt", "Mes_Año_Str", "Trimestre"]:
            clean_row.pop(col_fake, None)

        clean_row["user_key"] = clean_row.get("user_key") or "arturo"

        # 3. Clasificar entre UPDATE e INSERT
        row_id = clean_row.get("id")
        if row_id is not None and str(row_id).isdigit() and int(row_id) > 0:
            clean_row["id"] = int(row_id)
            to_update.append(clean_row)
        else:
            clean_row.pop("id", None)
            if not clean_row.get("numero_factura"):
                clean_row["numero_factura"] = obtener_siguiente_numero_factura()
            to_insert.append(clean_row)

    if to_update:
        supabase.table("facturas_encabezado").upsert(to_update).execute()
        
    if to_insert:
        supabase.table("facturas_encabezado").insert(to_insert).execute()

# --- FUNCIONES DE CATÁLOGO DE PRECIOS ---

def get_precios_df() -> pd.DataFrame:
    supabase = get_supabase_client()
    if not supabase:
        return pd.DataFrame()
    
    try:
        res = supabase.table("catalogo_precios").select("*").execute()
        if not res.data:
            return pd.DataFrame()
        return pd.DataFrame(res.data).replace({np.nan: None})
    except Exception as e:
        st.error(f"Error al obtener precios: {e}")
        return pd.DataFrame()

def save_precios_df(df: pd.DataFrame):
    supabase = get_supabase_client()
    if not supabase or df.empty:
        return

    df_clean = df.copy().replace({np.nan: None})
    records = df_clean.to_dict(orient="records")
    
    to_update = []
    to_insert = []
    
    for row in records:
        clean_row = {k: v for k, v in row.items() if str(v) != 'nan' and v is not None}
        clean_row["user_key"] = clean_row.get("user_key") or "arturo"
        
        row_id = clean_row.get("id")
        if row_id is not None and str(row_id).isdigit() and int(row_id) > 0:
            clean_row["id"] = int(row_id)
            to_update.append(clean_row)
        else:
            clean_row.pop("id", None)
            to_insert.append(clean_row)

    if to_update:
        supabase.table("catalogo_precios").upsert(to_update).execute()
        
    if to_insert:
        supabase.table("catalogo_precios").insert(to_insert).execute()

# --- CONTADOR Y ELIMINACIÓN ---

def delete_precio_by_id(precio_id: int) -> bool:
    """Elimina un producto del catálogo en Supabase por su ID."""
    supabase = get_supabase_client()
    if not supabase or not precio_id:
        return False
    try:
        supabase.table("catalogo_precios").delete().eq("id", precio_id).execute()
        return True
    except Exception as e:
        st.error(f"Error al borrar producto #{precio_id}: {e}")
        return False

def obtener_siguiente_numero_factura(emisor_key: str) -> int:
    supabase = get_supabase_client()
    if not supabase:
        return 1
    try:
        # Consulta el ultimo_numero del emisor (arturo o carmen)
        res = supabase.table("emisor_config").select("ultimo_numero").eq("user_key", emisor_key.lower().strip()).execute()
        if res.data and len(res.data) > 0:
            ultimo = res.data[0].get("ultimo_numero") or 0
            return int(ultimo) + 1
        return 1
    except Exception as e:
        print(f"Error consultando contador para {emisor_key}: {e}")
        return 1

def incrementar_contador_factura(emisor_key: str):
    supabase = get_supabase_client()
    if not supabase:
        return
    try:
        siguiente_numero = obtener_siguiente_numero_factura(emisor_key)
        # Actualiza el ultimo_numero directamente en emisor_config
        supabase.table("emisor_config").update({"ultimo_numero": siguiente_numero}).eq("user_key", emisor_key.lower().strip()).execute()
    except Exception as e:
        print(f"Error actualizando contador para {emisor_key}: {e}")

def delete_factura_by_id(factura_id: int) -> bool:
    """Elimina una factura y sus líneas asociadas en Supabase."""
    supabase = get_supabase_client()
    if not supabase or not factura_id:
        return False
    
    try:
        # 1. Borrar líneas secundarias
        supabase.table("facturas_lineas").delete().eq("factura_id", factura_id).execute()
        # 2. Borrar encabezado principal
        supabase.table("facturas_encabezado").delete().eq("id", factura_id).execute()
        return True
    except Exception as e:
        st.error(f"Error al eliminar la factura #{factura_id}: {e}")
        return False