import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Configuración de la página
st.set_page_config(page_title="Control de Insumos de Limpieza", layout="wide")

# --- INICIALIZACIÓN DE DATOS (Simulación de Base de Datos) ---
if 'inventario' not in st.session_state:
    # Stock inicial de ejemplo
    st.session_state.inventario = pd.DataFrame([
        {"Insumo": "Lavandina (Lts)", "Stock Actual": 50.0},
        {"Insumo": "Detergente (Lts)", "Stock Actual": 30.0},
        {"Insumo": "Papel Higiénico (Rallos)", "Stock Actual": 120.0},
        {"Insumo": "Bolsas de Consorcio (U)", "Stock Actual": 200.0},
        {"Insumo": "Desinfectante de Pisos (Lts)", "Stock Actual": 40.0}
    ])

if 'entregas' not in st.session_state:
    # Historial de entregas vacío
    st.session_state.entregas = pd.DataFrame(columns=["Fecha", "Insumo", "Cantidad Entregada", "Destino/Personal"])

# --- TÍTULO PRINCIPAL ---
st.title("🧽 Sistema de Control e Insumos de Limpieza")
st.markdown("---")

# --- PANEL LATERAL: Registro de Entregas ---
st.sidebar.header("📋 Registrar Entrega Diaria")
with st.sidebar.form("form_entrega", clear_on_submit=True):
    fecha_entrega = st.date_input("Fecha", datetime.now())
    insumo_sel = st.selectbox("Seleccionar Insumo", st.session_state.inventario["Insumo"].unique())
    cantidad = st.number_input("Cantidad a entregar", min_value=0.1, step=1.0, format="%.1f")
    destino = st.text_input("Destinado a / Retirado por", placeholder="Ej: Sector Oficinas / Juan Pérez")
    
    boton_registrar = st.form_submit_button("Registrar Entrega")

    if boton_registrar:
        # Verificar si hay stock suficiente
        stock_disponible = st.session_state.inventario.loc[st.session_state.inventario["Insumo"] == insumo_sel, "Stock Actual"].values[0]
        
        if cantidad > stock_disponible:
            st.error(f"❌ Stock insuficiente. Solo quedan {stock_disponible} unidades.")
        else:
            # 1. Descontar del inventario
            st.session_state.inventario.loc[st.session_state.inventario["Insumo"] == insumo_sel, "Stock Actual"] -= cantidad
            
            # 2. Registrar en el historial
            nueva_entrega = pd.DataFrame([{
                "Fecha": pd.to_datetime(fecha_entrega),
                "Insumo": insumo_sel,
                "Cantidad Entregada": cantidad,
                "Destino/Personal": destino
            }])
            st.session_state.entregas = pd.concat([st.session_state.entregas, nueva_entrega], ignore_index=True)
            st.success("✅ Entrega registrada correctamente.")

# --- CUERPO PRINCIPAL ---
tab1, tab2 = st.tabs(["📊 Stock Actual", "📈 Historial y Descargas"])

with tab1:
    st.header("Estado del Inventario")
    # Mostrar el inventario en una tabla limpia
    st.dataframe(st.session_state.inventario, use_container_width=True, hide_index=True)
    
    # Alerta de stock bajo (Ejemplo: menos de 10 unidades)
    stock_bajo = st.session_state.inventario[st.session_state.inventario["Stock Actual"] <= 10]
    if not stock_bajo.empty:
        st.warning("⚠️ ¡Atención! Los siguientes insumos tienen stock crítico (menor o igual a 10):")
        st.dataframe(stock_bajo, hide_index=True)

with tab2:
    st.header("Reportes de Entregas")
    
    if st.session_state.entregas.empty:
        st.info("Aún no se han registrado entregas.")
    else:
        # Asegurar formato de fecha para los filtros
        st.session_state.entregas["Fecha"] = pd.to_datetime(st.session_state.entregas["Fecha"])
        
        # --- FILTROS DE TIEMPO ---
        col1, col2 = st.columns(2)
        with col1:
            filtro_tipo = st.radio("Filtrar reporte por:", ["Día Específico", "Semana / Rango Personalizado"])
        
        if filtro_tipo == "Día Específico":
            dia_sel = st.date_input("Selecciona el día", datetime.now())
            df_filtrado = st.session_state.entregas[st.session_state.entregas["Fecha"].dt.date == dia_sel]
            nombre_archivo = f"reporte_diario_{dia_sel}.csv"
        else:
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                fecha_inicio = st.date_input("Desde", datetime.now() - timedelta(days=7))
            with col_f2:
                fecha_fin = st.date_input("Hasta", datetime.now())
            
            df_filtrado = st.session_state.entregas[
                (st.session_state.entregas["Fecha"].dt.date >= fecha_inicio) & 
                (st.session_state.entregas["Fecha"].dt.date <= fecha_fin)
            ]
            nombre_archivo = f"reporte_semanal_{fecha_inicio}_al_{fecha_fin}.csv"

        # --- MOSTRAR TABLA FILTRADA ---
        st.subheader("Datos del período seleccionado")
        if df_filtrado.empty:
            st.warning("No hay registros de entregas para el período seleccionado.")
        else:
            # Formatear la fecha para mostrar solo Año-Mes-Día en la tabla
            df_mostrar = df_filtrado.copy()
            df_mostrar["Fecha"] = df_mostrar["Fecha"].dt.strftime('%Y-%m-%d')
            st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
            
            # --- DESCARGA DE PLANILLAS ---
            # Convertir el dataframe filtrado a CSV
            csv = df_filtrado.to_csv(index=False).encode('utf-8')
            
            st.download_button(
                label="📥 Descargar Planilla (CSV/Excel)",
                data=csv,
                file_name=nombre_archivo,
                mime='text/csv',
            )
