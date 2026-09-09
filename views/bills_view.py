import streamlit as st
import pandas as pd
import os
from datetime import datetime
from src.engine import procesar_factura
from src.bills_gen import generar_ods
from src.utils import limpiar_precio
from src.db import (
    get_precios_df, 
    obtener_siguiente_numero_factura, 
    incrementar_contador_factura,
    get_supabase_client
)

supabase = get_supabase_client()

def render_bills_view(username):
    TALLAS_COLS = ["T-34", "T-36", "T-38", "T-40", "T-42", "T-44"]

    # --- 1. Cargar catálogo de precios desde Supabase ---
    try:
        df_precios = get_precios_df()
    except Exception as e:
        st.error(f"Error al conectar con el catálogo de precios en Supabase: {e}")
        return

    if df_precios.empty:
        st.warning("⚠️ No hay precios cargados en la base de datos de Supabase.")
        return

    # Normalización de columnas para compatibilidad
    col_nombre = 'nombre_articulo' if 'nombre_articulo' in df_precios.columns else 'articulo'
    col_precio = 'precio_cliente' if 'precio_cliente' in df_precios.columns else 'precio'
    col_cliente = 'id_cliente' if 'id_cliente' in df_precios.columns else 'cliente'

    # --- Funciones Auxiliares ---
    def calcular_total_pedido(pedido_df, df_p):
        pedido_limpio = {}
        total_acumulado = 0.0
        prendas_sin_precio = []

        for _, row in pedido_df.iterrows():
            nombre = row["Nombre Prenda"]
            if pd.isna(nombre) or str(nombre).strip() == "":
                continue
            
            nombre_clean = str(nombre).strip().upper()
            cantidades = {t: int(row[t] or 0) for t in TALLAS_COLS if int(row[t] or 0) > 0}
            
            if cantidades:
                pedido_limpio[nombre_clean] = cantidades
                
                # Búsqueda en el DataFrame de Supabase
                match = df_p[df_p[col_nombre].astype(str).str.strip().str.upper() == nombre_clean]
                
                if not match.empty:
                    p_unitario = limpiar_precio(match.iloc[0][col_precio])
                    total_acumulado += sum(cantidades.values()) * p_unitario
                else:
                    prendas_sin_precio.append(nombre_clean)
        return total_acumulado, prendas_sin_precio, pedido_limpio

    def limpiar_campos():
        st.session_state.df_pedido = pd.DataFrame(columns=["Nombre Prenda"] + TALLAS_COLS)
        if "editor_key_suffix" not in st.session_state:
            st.session_state.editor_key_suffix = 0
        st.session_state.editor_key_suffix += 1
        if "pre_total_data" in st.session_state:
            del st.session_state.pre_total_data
        if "pre_total_err" in st.session_state:
            del st.session_state.pre_total_err

    # --- 2. Sidebar de Configuración ---
    with st.sidebar:
        st.header("⚙️ Configuración")
        user_id = str(username).strip().lower()
        emisor_key = user_id if user_id != "admin" else "arturo"
        
        # Clientes dinámicos desde Supabase
        clientes_disp = ["belinda", "woven"]
        if col_cliente in df_precios.columns:
            unicos = df_precios[col_cliente].dropna().astype(str).str.strip().unique().tolist()
            if unicos:
                clientes_disp = sorted(unicos)
        
        cliente = st.selectbox("Cliente:", clientes_disp)
        
        if "prev_cliente" not in st.session_state:
            st.session_state.prev_cliente = cliente
        elif st.session_state.prev_cliente != cliente:
            st.session_state.prev_cliente = cliente
            limpiar_campos()
            st.rerun()
            
        objetivo = st.number_input("Objetivo (€):", value=2500)
        fecha_sel = st.date_input("Fecha:", datetime.now())
        fecha_str = fecha_sel.strftime('%d/%m/%y')
        
        st.divider()
        if st.button("➕ Nueva Factura", use_container_width=True):
            limpiar_campos()
            st.rerun()

    # Obtener prendas asociadas al cliente desde Supabase
    df_client = df_precios[df_precios[col_cliente].astype(str).str.strip().str.lower() == cliente.lower()]
    lista_prendas = sorted(df_client[col_nombre].dropna().astype(str).str.strip().unique().tolist())

    # --- 3. Tabla de Pedido ---
    st.write(f"### 📋 Pedido: {emisor_key.upper()}")
    
    if 'df_pedido' not in st.session_state:
        st.session_state.df_pedido = pd.DataFrame(columns=["Nombre Prenda"] + TALLAS_COLS)

    suffix = st.session_state.get("editor_key_suffix", 0)
    
    pedido_editado = st.data_editor(
        st.session_state.df_pedido,
        num_rows="dynamic",
        use_container_width=True,
        key=f"ed_{emisor_key}_{suffix}", 
        column_config={
            "Nombre Prenda": st.column_config.SelectboxColumn(
                "Nombre Prenda",
                options=lista_prendas,
                required=True,
                help="Selecciona el nombre de la prenda en la lista de precios"
            ),
            **{t: st.column_config.NumberColumn(t, min_value=0, default=0) for t in TALLAS_COLS}
        }
    )

    # --- 4. Botones de Operación ---
    st.divider()
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("🧮 Calcular Pre-total", use_container_width=True):
            try:
                total_acumulado, prendas_sin_precio, _ = calcular_total_pedido(pedido_editado, df_precios)
                if prendas_sin_precio:
                    st.session_state.pre_total_err = f"❌ Sin precio para: {', '.join(prendas_sin_precio)}."
                    st.session_state.pre_total_data = None
                else:
                    st.session_state.pre_total_err = None
                    st.session_state.pre_total_data = {
                        "total_sin_iva": total_acumulado,
                        "total_con_iva": round(total_acumulado * 1.21, 2)
                    }
            except Exception as e:
                st.session_state.pre_total_err = f"Error al calcular: {e}"
                st.session_state.pre_total_data = None

    if "pre_total_err" in st.session_state and st.session_state.pre_total_err:
        st.error(st.session_state.pre_total_err)
    elif "pre_total_data" in st.session_state and st.session_state.pre_total_data:
        data = st.session_state.pre_total_data
        total_sin_iva = data["total_sin_iva"]
        total_con_iva = data["total_con_iva"]
        
        st.info("📊 **Cálculo del Total Actual (Pre-Factura):**")
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric("Total sin IVA", f"{total_sin_iva:,.2f} €")
        with col_m2:
            st.metric("Total con IVA (21%)", f"{total_con_iva:,.2f} €")
        with col_m3:
            diferencia = objetivo - total_con_iva
            if diferencia >= 0:
                st.metric("Restante para Objetivo", f"{diferencia:,.2f} €")
            else:
                st.metric("Excedido del Objetivo", f"{abs(diferencia):,.2f} €", delta=f"-{abs(diferencia):,.2f} €", delta_color="inverse")
        st.divider()

    with col_btn2:
        btn_generar = st.button("🚀 Generar Factura", type="primary", use_container_width=True)
        
    if btn_generar:
        total_acumulado, prendas_sin_precio, pedido_limpio = calcular_total_pedido(pedido_editado, df_precios)

        if not pedido_limpio:
            st.warning("⚠️ No hay cantidades en la tabla.")
        elif prendas_sin_precio:
            st.error(f"❌ No encontré el precio para: {', '.join(prendas_sin_precio)}")
        else:
            try:
                st.divider()
                c1, c2 = st.columns([2, 1])
                total_con_iva = round(total_acumulado * 1.21, 2)
                
                with c2:
                    st.metric("PRECIO FINAL (con IVA)", f"{total_con_iva:,.2f} €")
                    if total_con_iva > objetivo:
                        st.warning(f"⚠️ Te has pasado del objetivo por {(total_con_iva - objetivo):.2f} €")

                # Obtener el número de factura directamente desde Supabase
                num_factura_siguiente = obtener_siguiente_numero_factura(emisor_key)

                # Generar archivo ODS localmente para descarga
                datos_fiscales = {"nombre_fiscal": emisor_key.upper()}
                res = procesar_factura(emisor_key, cliente, fecha_str, objetivo, pedido_limpio, df_precios, datos_fiscales)
                res['factura'] = num_factura_siguiente  # Forzar el número incremental de Supabase
                ruta = generar_ods(res)
                
                with c1:
                    st.success(f"✅ Factura Nº {res['factura']} generada con éxito.")
                    with open(ruta, "rb") as f:
                        st.download_button("📥 Descargar Factura", f, file_name=os.path.basename(ruta))

                # ========================================================
                # REGISTRO EN SUPABASE (ENCABEZADO + LINEAS + CONTADORES)
                # ========================================================
                if supabase:
                    try:
                        # 1. Insertar Factura (Encabezado con nombres reales de columnas)
                        factura_payload = {
                            "numero_factura": str(res['factura']),
                            "fecha_emision": fecha_sel.isoformat(),
                            "user_key": emisor_key,
                            "id_cliente": cliente,
                            "base_imponible": total_acumulado,
                            "total_factura": total_con_iva,
                            "estado": "Pendiente"
                        }
                        
                        res_fac = supabase.table("facturas_encabezado").insert(factura_payload).execute()
                        
                        if res_fac.data:
                            factura_id = res_fac.data[0]["id"]
                            
                            # 2. Insertar Detalles de Líneas
                            lineas_payload = []
                            for prenda_nombre, desgloses in pedido_limpio.items():
                                for talla, cantidad in desgloses.items():
                                    lineas_payload.append({
                                        "factura_id": factura_id,
                                        "prenda": prenda_nombre,
                                        "talla": talla,
                                        "cantidad": cantidad
                                    })
                            
                            if lineas_payload:
                                supabase.table("facturas_lineas").insert(lineas_payload).execute()
                            
                            # 3. Incrementar Contador en Supabase
                            incrementar_contador_factura(emisor_key)
                            
                            st.info("✅ Factura, desglose y contador guardados correctamente en Supabase.")
                    except Exception as sp_err:
                        st.error(f"Error al sincronizar con Supabase: {sp_err}")

                st.balloons()
            except Exception as e:
                st.error(f"Error en el proceso de generación: {e}")