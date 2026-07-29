import streamlit as st
import pandas as pd
import os
from datetime import datetime

def render_history_view():
    PATH_REGISTRO = 'data/registro_facturas.xlsx'
    st.subheader("📊 Historial de Facturas y Cobros")

    if not os.path.exists(PATH_REGISTRO):
        st.info("ℹ️ Aún no se ha registrado ninguna factura. Las facturas nuevas que generes se guardarán aquí automáticamente.")
        return

    try:
        df_historial = pd.read_excel(PATH_REGISTRO)
    except Exception as e:
        st.error(f"Error al leer el historial: {e}")
        return

    if df_historial.empty:
        st.info("ℹ️ El registro de facturas está vacío.")
        return

    # Asegurarnos de que el formato de las columnas sea correcto
    df_historial['Nº Factura'] = df_historial['Nº Factura'].astype(str)
    
    # Procesar fechas para filtros y dashboard
    try:
        # Convertir a datetime para poder ordenar y agrupar por mes/año de forma flexible
        df_historial['Fecha_dt'] = pd.to_datetime(df_historial['Fecha'], format='mixed', dayfirst=True, errors='coerce')
        df_historial['Fecha_dt'] = df_historial['Fecha_dt'].fillna(pd.Timestamp.now())
    except Exception:
        df_historial['Fecha_dt'] = pd.Timestamp.now()

    # --- 1. DASHBOARD DE CONTABILIDAD ANUAL ---
    with st.expander("📊 Dashboard de Contabilidad Anual", expanded=True):
        # Mapeo de meses en español
        meses_es = {
            1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
            7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"
        }
        
        # Obtener años disponibles
        años_disp = sorted(list(df_historial['Fecha_dt'].dt.year.unique()), reverse=True)
        if años_disp:
            año_sel = st.selectbox("📅 Seleccionar Año para Análisis:", años_disp, key="dashboard_year")
        else:
            año_sel = datetime.now().year
            
        # Filtrar datos de ese año
        df_año = df_historial[df_historial['Fecha_dt'].dt.year == año_sel].copy()
        
        if not df_año.empty:
            # Métricas del Año
            tot_sin_iva_año = df_año['Total sin IVA'].sum()
            tot_con_iva_año = df_año['Total con IVA'].sum()
            iva_año = tot_con_iva_año - tot_sin_iva_año
            cant_facturas_año = len(df_año)
            
            st.markdown(f"#### Resumen Financiero Anual ({año_sel})")
            col_a1, col_a2, col_a3, col_a4 = st.columns(4)
            with col_a1:
                st.metric("Total Facturado (Sin IVA)", f"{tot_sin_iva_año:,.2f} €")
            with col_a2:
                st.metric("IVA Acumulado (21%)", f"{iva_año:,.2f} €")
            with col_a3:
                st.metric("Total Neto Cobrado (Con IVA)", f"{tot_con_iva_año:,.2f} €")
            with col_a4:
                st.metric("Facturas Emitidas", f"{cant_facturas_año}")
                
            st.divider()
            
            # Gráficos
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                st.markdown("📈 **Facturación Mensual (con IVA)**")
                # Agrupar por mes y rellenar meses faltantes (1 al 12)
                df_meses = df_año.groupby(df_año['Fecha_dt'].dt.month)['Total con IVA'].sum().reindex(range(1, 13), fill_value=0.0).reset_index()
                df_meses['Mes'] = df_meses['Fecha_dt'].map(meses_es)
                st.bar_chart(df_meses.set_index('Mes')['Total con IVA'], height=250)
                
            with col_g2:
                st.markdown("🎯 **Facturación por Cliente (con IVA)**")
                df_cli_año = df_año.groupby('Cliente')['Total con IVA'].sum().reset_index().sort_values(by='Total con IVA', ascending=False)
                if not df_cli_año.empty:
                    st.bar_chart(df_cli_año.set_index('Cliente')['Total con IVA'], height=250)
                else:
                    st.info("No hay datos de clientes.")
        else:
            st.info(f"No hay facturas registradas en el año {año_sel}.")

    st.write("---")

    # --- 2. FILTROS DE CONSULTA MENSUAL ---
    st.write("### 🔍 Consultas y Búsquedas")
    
    # Crear copia para aplicar filtros de visualización
    df_mostrar = df_historial.copy().sort_values(by='Fecha_dt', ascending=False)
    df_mostrar['Mes_Año_Str'] = df_mostrar['Fecha_dt'].apply(lambda x: f"{meses_es.get(x.month, '')} {x.year}")
    
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        meses_unicos = df_mostrar['Mes_Año_Str'].unique().tolist()
        opciones_mes = ["Todos"] + meses_unicos
        mes_sel = st.selectbox("📅 Filtrar por Mes/Año:", opciones_mes)

    with col_f2:
        clientes_disp = ["Todos"] + sorted(list(df_historial['Cliente'].dropna().unique()))
        cliente_sel = st.selectbox("🎯 Filtrar por Cliente:", clientes_disp)

    with col_f3:
        emisores_disp = ["Todos"] + sorted(list(df_historial['Emisor'].dropna().unique()))
        emisor_sel = st.selectbox("👤 Filtrar por Emisor:", emisores_disp)

    # Aplicar Filtros
    if mes_sel != "Todos":
        df_mostrar = df_mostrar[df_mostrar['Mes_Año_Str'] == mes_sel]
    if cliente_sel != "Todos":
        df_mostrar = df_mostrar[df_mostrar['Cliente'] == cliente_sel]
    if emisor_sel != "Todos":
        df_mostrar = df_mostrar[df_mostrar['Emisor'] == emisor_sel]

    # --- MÉTRICAS DE LA SELECCIÓN FILTRADA ---
    total_sin_iva = df_mostrar['Total sin IVA'].sum()
    total_con_iva = df_mostrar['Total con IVA'].sum()
    iva_acumulado = total_con_iva - total_sin_iva
    cant_facturas = len(df_mostrar)

    st.write("### 📈 Resumen Financiero (Selección Actual)")
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("Total Facturado (Sin IVA)", f"{total_sin_iva:,.2f} €")
    with col_m2:
        st.metric("IVA Acumulado (21%)", f"{iva_acumulado:,.2f} €")
    with col_m3:
        st.metric("Total Cobrado (Con IVA)", f"{total_con_iva:,.2f} €")
    with col_m4:
        st.metric("Facturas Emitidas", f"{cant_facturas}")

    st.divider()

    # --- TABLA DE REGISTROS EDITABLE ---
    st.write("### 📋 Registro Detallado")
    
    columnas_mostrar = ["Nº Factura", "Fecha", "Emisor", "Cliente", "Total sin IVA", "Total con IVA", "Ruta Archivo"]
    df_editor = df_mostrar[columnas_mostrar].copy()

    df_editado = st.data_editor(
        df_editor,
        use_container_width=True,
        num_rows="dynamic",
        key="editor_historial_facturas"
    )

    # --- BOTONES ---
    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 Guardar Cambios en Historial", type="primary", use_container_width=True):
            try:
                from src.utils import limpiar_precio
                
                # Obtener los cambios del editor de Streamlit
                state = st.session_state.get("editor_historial_facturas", {})
                
                if state:
                    # 1. Filas editadas
                    edited_rows = state.get("edited_rows", {})
                    for pos_str, changes in edited_rows.items():
                        pos = int(pos_str)
                        actual_idx = df_editor.index[pos]
                        for col, val in changes.items():
                            if col in ['Total sin IVA', 'Total con IVA']:
                                val = limpiar_precio(val)
                            df_historial.at[actual_idx, col] = val
                    
                    # 2. Filas eliminadas
                    deleted_rows = state.get("deleted_rows", {})
                    if deleted_rows:
                        indices_to_drop = [df_editor.index[pos] for pos in deleted_rows]
                        df_historial = df_historial.drop(index=indices_to_drop)
                    
                    # 3. Filas añadidas
                    added_rows = state.get("added_rows", {})
                    if added_rows:
                        for row in added_rows:
                            for col in ['Total sin IVA', 'Total con IVA']:
                                if col in row:
                                    row[col] = limpiar_precio(row[col])
                                else:
                                    row[col] = 0.0
                        df_added = pd.DataFrame(added_rows)
                        df_historial = pd.concat([df_historial, df_added], ignore_index=True)
                
                df_historial.to_excel(PATH_REGISTRO, engine='openpyxl', index=False)
                st.success("✅ Cambios guardados con éxito en el historial.")
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar: {e}")

    with c2:
        csv = df_editor.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            "📥 Exportar Selección a Excel/CSV",
            data=csv,
            file_name=f"historial_facturas_{mes_sel.replace(' ', '_') if mes_sel != 'Todos' else 'completo'}.csv",
            mime="text/csv",
            use_container_width=True
        )
