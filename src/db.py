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
    
    sanitized_records = []
    for row in records:
        # Eliminar valores nulos explícitos
        clean_row = {k: v for k, v in row.items() if str(v) != 'nan' and v is None}

        # Si el 'id' es nulo o 0, lo borramos para que la DB asigne el siguiente id autoincremental
        if "id" in clean_row and not clean_row["id"]:
            del clean_row["id"]

        # Garantizar que numero_factura no vaya nulo si es una fila nueva
        if "numero_factura" not in clean_row or not clean_row["numero_factura"]:
            clean_row["numero_factura"] = clean_row.get("numero_factura") or obtener_siguiente_numero_factura()

        # Unificar fechas y emisores
        fecha_val = clean_row.get("fecha") or clean_row.get("fecha_emision")
        if fecha_val:
            clean_row["fecha"] = str(fecha_val)
            clean_row["fecha_emision"] = str(fecha_val)

        clean_row["user_key"] = clean_row.get("user_key") or "arturo"

        if clean_row:
            sanitized_records.append(clean_row)

    if sanitized_records:
        supabase.table("facturas_encabezado").upsert(sanitized_records).execute()        

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
        # Si tiene un ID numérico válido > 0 se actualiza; si es nuevo (None/0) se inserta sin enviar 'id'
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

# --- CONTADOR DE FACTURAS (DESDE SUPABASE) ---

def obtener_siguiente_numero_factura(user_key: str = "arturo") -> str:
    supabase = get_supabase_client()
    if not supabase:
        return "215"
    try:
        res = supabase.table("emisor_config").select("ultimo_numero").eq("user_key", user_key).execute()
        if res.data and res.data[0].get("ultimo_numero") is not None:
            return str(res.data[0]["ultimo_numero"] + 1)
        return "1"
    except Exception:
        return "215"

def incrementar_contador_factura(user_key: str = "arturo"):
    supabase = get_supabase_client()
    if not supabase:
        return
    try:
        siguiente = int(obtener_siguiente_numero_factura(user_key))
        supabase.table("emisor_config").update({"ultimo_numero": siguiente}).eq("user_key", user_key).execute()
    except Exception as e:
        st.error(f"Error al actualizar contador: {e}")

def delete_factura_by_id(factura_id: int) -> bool:
    """Elimina una factura y sus líneas asociadas en Supabase."""
    supabase = get_supabase_client()
    if not supabase or not factura_id:
        return False
    
    try:
        # 1. Borrar líneas secundarias asociadas
        supabase.table("facturas_lineas").delete().eq("factura_id", factura_id).execute()
        # 2. Borrar encabezado principal
        supabase.table("facturas_encabezado").delete().eq("id", factura_id).execute()
        return True
    except Exception as e:
        st.error(f"Error al eliminar la factura #{factura_id}: {e}")
        return False