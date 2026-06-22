import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from src.engine import procesar_factura
from src.bills_gen import generar_ods
from src.utils import limpiar_precio

def render_bills_view(username):
    PATH_COUNTERS = 'data/counters.json'
    PATH_PRECIOS = 'data/listado_precios_clientes.xlsx' 
    TALLAS_COLS = ["T-34", "T-36", "T-38", "T-40", "T-42", "T-44"]

    # 1. Cargar contadores
    if not os.path.exists(PATH_COUNTERS):
        st.error(f"No se encuentra {PATH_COUNTERS}")
        return

    with open(PATH_COUNTERS, 'r', encoding='utf-8') as f:
        data_raw = json.load(f)
        contadores = {str(k).strip().lower(): v for k, v in data_raw.items()}

    def calcular_total_pedido(pedido_df, df_p):
        COL_NOMBRE_EXCEL = 'NOMBRE ARTÍCULO'
        COL_PRECIO_EXCEL = 'PRECIO CLIENTE'
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
                
                # Buscamos la prenda en tu columna 'NOMBRE ARTÍCULO'
                match = df_p[df_p[COL_NOMBRE_EXCEL].astype(str).str.strip().str.upper() == nombre_clean]
                
                if not match.empty:
                    # Usamos tu columna 'PRECIO CLIENTE'
                    p_unitario = limpiar_precio(match.iloc[0][COL_PRECIO_EXCEL])
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

    # 2. Sidebar
    with st.sidebar:
        st.header("⚙️ Configuración")
        user_id = str(username).strip().lower()
        emisor_key = user_id if user_id != "admin" else st.selectbox("Emisor:", list(contadores.keys()))
        
        # Cargar clientes dinámicos desde el Excel si está disponible
        clientes_disp = ["belinda", "woven"]
        if os.path.exists(PATH_PRECIOS):
            try:
                df_p = pd.read_excel(PATH_PRECIOS)
                if 'ID_CLIENTE' in df_p.columns:
                    clientes_disp = sorted(df_p['ID_CLIENTE'].dropna().astype(str).str.strip().unique().tolist())
            except:
                pass
        
        cliente = st.selectbox("Cliente:", clientes_disp)
        
        # Si cambia el cliente, limpiamos el pedido actual
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

    # Cargar prendas asociadas al cliente seleccionado para el autocompletado/sugerencia
    lista_prendas = []
    if os.path.exists(PATH_PRECIOS):
        try:
            df_p = pd.read_excel(PATH_PRECIOS)
            COL_NOMBRE_EXCEL = 'NOMBRE ARTÍCULO'
            df_client = df_p[df_p['ID_CLIENTE'].astype(str).str.strip().str.lower() == cliente.lower()]
            lista_prendas = sorted(df_client[COL_NOMBRE_EXCEL].dropna().astype(str).str.strip().unique().tolist())
        except Exception as e:
            st.error(f"Error al cargar las prendas del cliente: {e}")

    # 3. Tabla de Pedido
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
                help="Selecciona o busca el nombre de la prenda en la lista de precios"
            ),
            **{t: st.column_config.NumberColumn(t, min_value=0, default=0) for t in TALLAS_COLS}
        }
    )

    # 4. Botones de Calcular Pre-total y Generar Factura
    st.divider()
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("🧮 Calcular Pre-total", use_container_width=True):
            if not os.path.exists(PATH_PRECIOS):
                st.error(f"No se encuentra el archivo: {PATH_PRECIOS}")
            else:
                try:
                    df_p = pd.read_excel(PATH_PRECIOS)
                    total_acumulado, prendas_sin_precio, _ = calcular_total_pedido(pedido_editado, df_p)
                    
                    if prendas_sin_precio:
                        st.session_state.pre_total_err = f"❌ No encontré el precio para: {', '.join(prendas_sin_precio)}. Asegúrate de que el nombre en la tabla sea IGUAL al del Excel."
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

    # Mostrar métricas del Pre-total si están guardadas en el estado
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
        if not os.path.exists(PATH_PRECIOS):
            st.error(f"No se encuentra el archivo: {PATH_PRECIOS}")
        else:
            df_p = pd.read_excel(PATH_PRECIOS)
            total_acumulado, prendas_sin_precio, pedido_limpio = calcular_total_pedido(pedido_editado, df_p)

            if not pedido_limpio:
                st.warning("⚠️ No hay cantidades en la tabla.")
            elif prendas_sin_precio:
                st.error(f"❌ No encontré el precio para: {', '.join(prendas_sin_precio)}")
                st.info("Asegúrate de que el nombre en la tabla sea IGUAL al del Excel.")
            else:
                try:
                    st.divider()
                    c1, c2 = st.columns([2, 1])
                    
                    total_con_iva = round(total_acumulado * 1.21, 2)
                    with c2:
                        st.metric("PRECIO FINAL (con IVA)", f"{total_con_iva:,.2f} €")
                        if total_con_iva > objetivo:
                            st.warning(f"⚠️ ¡Ojo! Te has pasado del objetivo por {(total_con_iva - objetivo):.2f} €")

                    # Generar Factura
                    datos_fiscales = contadores[emisor_key]
                    res = procesar_factura(emisor_key, cliente, fecha_str, objetivo, pedido_limpio, df_p, datos_fiscales)
                    ruta = generar_ods(res)
                    
                    with c1:
                        st.success(f"✅ Factura Nº {res['factura']} generada.")
                        with open(ruta, "rb") as f:
                            st.download_button("📥 Descargar Factura", f, file_name=os.path.basename(ruta))
                    
                    # Registrar la factura en Excel
                    try:
                        from src.utils import registrar_factura
                        registrar_factura(
                            n_factura=res['factura'],
                            fecha=fecha_str,
                            emisor=emisor_key.upper(),
                            cliente=cliente.upper(),
                            total_sin_iva=total_acumulado,
                            total_con_iva=total_con_iva,
                            ruta_archivo=os.path.basename(ruta)
                        )
                    except Exception as reg_err:
                        st.warning(f"⚠️ No se pudo registrar la factura en el historial: {reg_err}")
                    
                    # Actualizar JSON
                    contadores[emisor_key]['ultimo_numero'] = res['factura']
                    with open(PATH_COUNTERS, 'w', encoding='utf-8') as f:
                        json.dump(contadores, f, indent=2, ensure_ascii=False)
                    
                    st.balloons()
                except Exception as e:
                    st.error(f"Error en el motor: {e}")