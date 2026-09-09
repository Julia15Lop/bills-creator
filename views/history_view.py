import streamlit as st
import pandas as pd
from datetime import datetime
from src.db import get_facturas_df, save_facturas_df

def render_history_view():
    st.subheader("📊 Historial de Facturas y Cobros")

    try:
        df_historial = get_facturas_df()
    except Exception as e:
        st.error(f"Error al cargar el historial desde Supabase: {e}")
        return

    if df_historial.empty:
        st.info("ℹ️ No hay facturas en el registro de Supabase.")
        return

    # Normalización y compatibilidad de nombres de columnas
    df_historial['Nº Factura'] = df_historial.get('numero_factura', pd.Series(dtype=str)).astype(str)
    
    # Manejo de la fecha según la columna que venga de Supabase
    if 'fecha_emision' in df_historial.columns and not df_historial['fecha_emision'].isna().all():
        df_historial['Fecha'] = df_historial['fecha_emision']
    elif 'fecha' in df_historial.columns:
        df_historial['Fecha'] = df_historial['fecha']
    else:
        df_historial['Fecha'] = str(datetime.now().date())

    # Emisor y Cliente
    df_historial['Emisor'] = df_historial['user_key'] if 'user_key' in df_historial.columns else df_historial.get('emisor', 'N/A')
    
    if 'cliente' in df_historial.columns and not df_historial['cliente'].isna().all():
        df_historial['Cliente'] = df_historial['cliente']
    else:
        df_historial['Cliente'] = df_historial.get('id_cliente', 'N/A')

    # Importes
    df_historial['Total sin IVA'] = df_historial.get('base_imponible', 0.0).astype(float)
    df_historial['Total con IVA'] = df_historial.get('total_factura', 0.0).astype(float)
    
    # Estado de Cobro
    if 'estado' not in df_historial.columns:
        df_historial['estado'] = 'Pendiente'
    df_historial['estado'] = df_historial['estado'].fillna('Pendiente')

    # Conversión de fechas a datetime para gráficos y filtros
    try:
        df_historial['Fecha_dt'] = pd.to_datetime(df_historial['Fecha'], format='mixed', errors='coerce')
        df_historial['Fecha_dt'] = df_historial['Fecha_dt'].fillna(pd.Timestamp.now())
    except Exception:
        df_historial['Fecha_dt'] = pd.Timestamp.now()

    # --- 1. DASHBOARD DE CONTABILIDAD ANUAL ---
    with st.expander("Contabilidad Anual", expanded=True):
        meses_es = {
            1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
            7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"
        }
        
        años_disp = sorted(list(df_historial['Fecha_dt'].dt.year.unique()), reverse=True)
        año_sel = st.selectbox("Año para Análisis:", años_disp, key="hv_year_select") if años_disp else datetime.now().year
            
        df_año = df_historial[df_historial['Fecha_dt'].dt.year == año_sel].copy()
        
        if not df_año.empty:
            tot_sin_iva_año = df_año['Total sin IVA'].sum()
            tot_con_iva_año = df_año['Total con IVA'].sum()
            iva_año = tot_con_iva_año - tot_sin_iva_año
            cant_facturas_año = len(df_año)
            
            st.markdown(f"#### Resumen Financiero Anual ({año_sel})")
            col_a1, col_a2, col_a3, col_a4 = st.columns(4)
            col_a1.metric("Total Facturado (Sin IVA)", f"{tot_sin_iva_año:,.2f} €")
            col_a2.metric("IVA Acumulado (21%)", f"{iva_año:,.2f} €")
            col_a3.metric("Total Neto Cobrado (Con IVA)", f"{tot_con_iva_año:,.2f} €")
            col_a4.metric("Facturas Emitidas", f"{cant_facturas_año}")
                
            st.divider()
            
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                st.markdown("**Facturación Mensual (con IVA)**")
                df_meses = df_año.groupby(df_año['Fecha_dt'].dt.month)['Total con IVA'].sum().reindex(range(1, 13), fill_value=0.0).reset_index()
                df_meses.columns = ['mes_num', 'Total con IVA']
                df_meses['Mes'] = df_meses['mes_num'].apply(lambda n: f"{n:02d}-{meses_es.get(n, str(n))}")
                st.bar_chart(df_meses.sort_values('mes_num').set_index('Mes')['Total con IVA'], height=250)

            with col_g2:
                st.markdown("**Facturación por Cliente (con IVA)**")
                df_cli_año = df_año.groupby('Cliente')['Total con IVA'].sum().reset_index().sort_values(by='Total con IVA', ascending=False)
                if not df_cli_año.empty:
                    st.bar_chart(df_cli_año.set_index('Cliente')['Total con IVA'], height=250)
                else:
                    st.info("No hay datos de clientes.")
        else:
            st.info(f"No hay facturas registradas en el año {año_sel}.")

    st.write("---")

    # --- 2. FILTROS DE CONSULTA ---
    st.write("### 🔍 Consultas y Búsquedas")
    
    df_mostrar = df_historial.copy().sort_values(by='Fecha_dt', ascending=False)
    df_mostrar['Mes_Año_Str'] = df_mostrar['Fecha_dt'].apply(lambda x: f"{meses_es.get(x.month, '')} {x.year}")
    
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        mes_sel = st.selectbox("📅 Filtrar por Mes/Año:", ["Todos"] + df_mostrar['Mes_Año_Str'].unique().tolist(), key="hv_filter_month")
    with col_f2:
        cliente_sel = st.selectbox("🎯 Filtrar por Cliente:", ["Todos"] + sorted(list(df_historial['Cliente'].dropna().unique())), key="hv_filter_client")
    with col_f3:
        emisor_sel = st.selectbox("👤 Filtrar por Emisor:", ["Todos"] + sorted(list(df_historial['Emisor'].dropna().unique())), key="hv_filter_emisor")

    if mes_sel != "Todos":
        df_mostrar = df_mostrar[df_mostrar['Mes_Año_Str'] == mes_sel]
    if cliente_sel != "Todos":
        df_mostrar = df_mostrar[df_mostrar['Cliente'] == cliente_sel]
    if emisor_sel != "Todos":
        df_mostrar = df_mostrar[df_mostrar['Emisor'] == emisor_sel]

    total_sin_iva = df_mostrar['Total sin IVA'].sum()
    total_con_iva = df_mostrar['Total con IVA'].sum()
    iva_acumulado = total_con_iva - total_sin_iva

    st.write("### 📈 Resumen Financiero (Selección Actual)")
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("Total Facturado (Sin IVA)", f"{total_sin_iva:,.2f} €")
    col_m2.metric("IVA Acumulado (21%)", f"{iva_acumulado:,.2f} €")
    col_m3.metric("Total Cobrado (Con IVA)", f"{total_con_iva:,.2f} €")
    col_m4.metric("Facturas Emitidas", f"{len(df_mostrar)}")

    st.divider()

    # --- 3. INFORME TRIMESTRAL ---
    st.write("### 📝 Informe Trimestral (para el gestor)")
    df_año_trim = df_año.copy()
    df_año_trim['Trimestre'] = df_año_trim['Fecha_dt'].dt.quarter
    trimestres_disp = sorted(df_año_trim['Trimestre'].dropna().unique())
    
    if trimestres_disp:
        trim_sel = st.selectbox("Seleccionar Trimestre:", [f"Trimestre {int(t)}" for t in trimestres_disp], key="hv_filter_quarter")
        trim_num = int(trim_sel[-1])
        
        df_trim = df_año_trim[df_año_trim['Trimestre'] == trim_num]
        ingresos_brutos = df_trim['Total sin IVA'].sum()
        iva_repercutido = df_trim['Total con IVA'].sum() - ingresos_brutos
        
        col_t1, col_t2 = st.columns(2)
        col_t1.metric("Ingresos Brutos (Base Imponible)", f"{ingresos_brutos:,.2f} €")
        col_t2.metric("IVA Repercutido (Devengado al 21%)", f"{iva_repercutido:,.2f} €")
        
        col_t3, col_t4, col_t5 = st.columns(3)
        with col_t3:
            gastos_brutos = st.number_input("Total Gastos (Base Imponible) €", min_value=0.0, step=10.0, format="%.2f", key="hv_input_gastos")
        with col_t4:
            iva_soportado = st.number_input("IVA Soportado (Pagado en compras) €", min_value=0.0, step=10.0, format="%.2f", key="hv_input_iva")
        with col_t5:
            resultado_iva = iva_repercutido - iva_soportado
            st.metric("Resultado Liquidación IVA", f"{resultado_iva:,.2f} €", 
                      delta="A pagar a Hacienda" if resultado_iva > 0 else "A devolver / Compensar", delta_color="inverse")

    st.divider()

    # --- 4. TABLA DETALLADA EDITABLE CON ESTADO ---
    st.write("### 📋 Registro Detallado")
    
    columnas_base = ["id", "numero_factura", "fecha_emision", "fecha", "user_key", "cliente", "id_cliente", "base_imponible", "total_factura", "estado"]
    cols_existentes = [c for c in columnas_base if c in df_mostrar.columns]
    
    df_editor = df_mostrar[cols_existentes].copy()

    edited_df = st.data_editor(
        df_editor,
        use_container_width=True,
        num_rows="dynamic",
        key="hv_editor_table_final",
        column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "numero_factura": "Nº Factura",
            "fecha_emision": "Fecha Emisión",
            "fecha": "Fecha",
            "user_key": "Emisor",
            "cliente": "Cliente",
            "id_cliente": "ID Cliente",
            "base_imponible": st.column_config.NumberColumn("Base Imponible (€)", format="%.2f €"),
            "total_factura": st.column_config.NumberColumn("Total (€)", format="%.2f €"),
            "estado": st.column_config.SelectboxColumn(
                "Estado Cobro",
                help="Cambia el estado del cobro de la factura",
                options=["Cobrada", "Pendiente", "Anulada"],
                required=True
            )
        }
    )

    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 Guardar Cambios en Supabase", type="primary", use_container_width=True, key="hv_btn_save_final"):
            try:
                save_facturas_df(edited_df)
                st.success("✅ Cambios guardados en Supabase.")
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar: {e}")

    with c2:
        csv = edited_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Exportar Selección a CSV", data=csv, file_name="historial_facturas.csv", mime="text/csv", use_container_width=True, key="hv_btn_export_final")