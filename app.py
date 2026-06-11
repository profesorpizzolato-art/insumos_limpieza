import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# Configuración de la página
st.set_page_config(page_title="Control de Insumos de Limpieza", layout="wide")

# --- ARCHIVOS LOCALES PARA ALMACENAMIENTO ---
FILE_INVENTARIO = "inventario.csv"
FILE_ENTREGAS = "entregas.csv"

# --- FUNCIONES DE CARGA Y GUARDADO ---
def cargar_datos():
    # Inicializar Inventario si no existe el archivo
    if os.path.exists(FILE_INVENTARIO):
        inventario = pd.read_csv(FILE_INVENTARIO)
    else:
        # Stock inicial por defecto la primera vez
        inventario = pd.DataFrame([
            {"Insumo": "Lavandina (Lts)", "Stock Actual": 50.0},
            {"Insumo": "Detergente (Lts)", "Stock Actual": 30.0},
            {"Insumo": "Papel Higiénico (Rollos)", "Stock Actual": 120.0},
            {"Insumo": "Bolsas de Consorcio (U)", "Stock Actual": 200.0},
            {"Insumo": "Desinfectante de Pisos (Lts)", "Stock Actual": 40.0}
        ])
        inventario.to_csv(FILE_INVENTARIO, index=False)
    
    # Inicializar Historial de Entregas si no existe
    if os.path.exists(FILE_ENTREGAS):
        entregas = pd.read_csv(FILE_ENTREGAS)
        entregas["Fecha"] = pd.to_datetime(entregas["Fecha"])
    else:
        entregas = pd.DataFrame(columns=["Fecha", "Insumo", "Cantidad Entregada", "Destino/Personal"])
        entregas.to_csv(FILE_ENTREGAS, index=False)
        
    return inventario, entregas

def guardar_datos(inventario, entregas):
    inventario.to_csv(FILE_INVENTARIO, index=False)
    entregas.to_csv(FILE_ENTREGAS, index=False)

# Cargar los datos al iniciar/refrescar la app
df_inventario, df_entregas = cargar_datos()

# --- TÍTULO PRINCIPAL ---
st.title("🧽 Sistema de Control de Insumos de Limpieza")
st.markdown("---")

# --- PANEL LATERAL: Registro de Entregas Diarias ---
st.sidebar.header("📋 Registrar Entrega Diaria")
with st.sidebar.form("form_entrega", clear_on_submit=True):
    fecha_entrega = st.date_input("Fecha de Entrega", datetime.now())
    insumo_sel = st.selectbox("Seleccionar Insumo", df_inventario["Insumo"].unique(), key="entrega_insumo")
    cantidad = st.number_input("Cantidad a entregar", min_value=0.1, step=1.0, format="%.1f")
    destino = st.text_input("Destinado a / Retirado por", placeholder="Ej: Sector Oficinas / Juan Pérez")
    
    boton_registrar = st.form_submit_button("Registrar Entrega")

    if boton_registrar:
        # Obtener stock actual del elemento seleccionado
        stock_disponible = df_inventario.loc[df_inventario["Insumo"] == insumo_sel, "Stock Actual"].values[0]
        
        if cantidad > stock_disponible:
            st.sidebar.error(f"❌ Stock insuficiente. Solo quedan {stock_disponible} unidades.")
        else:
            # 1. Descontar del inventario interno
            df_inventario.loc[df_inventario["Insumo"] == insumo_sel, "Stock Actual"] -= cantidad
            
            # 2. Registrar en el historial interno
            nueva_entrega = pd.DataFrame([{
                "Fecha": pd.to_datetime(fecha_entrega),
                "Insumo": insumo_sel,
                "Cantidad Entregada": cantidad,
                "Destino/Personal": destino
            }])
            df_entregas = pd.concat([df_entregas, nueva_entrega], ignore_index=True)
            
            # 3. Guardar físicamente en los archivos CSV
            guardar_datos(df_inventario, df_entregas)
            st.sidebar.success("✅ Entrega registrada y stock actualizado.")
            st.rerun()

# --- CUERPO PRINCIPAL (Pestañas) ---
tab1, tab2, tab3 = st.tabs(["📊 Stock Actual", "📈 Historial y Descargas", "➕ Reponer Stock"])

# PESTAÑA 1: Estado del Inventario
with tab1:
    st.header("Estado actual del depósito")
    st.dataframe(df_inventario, use_container_width=True, hide_index=True)
    
    # Alerta de stock bajo (Menos de 10 unidades)
    stock_bajo = df_inventario[df_inventario["Stock Actual"] <= 10]
    if not stock_bajo.empty:
        st.warning("⚠️ **¡Atención!** Los siguientes insumos tienen un stock crítico (10 unidades o menos):")
        st.dataframe(stock_bajo, hide_index=True)

# PESTAÑA 2: Reportes, Filtros y Descargas
with tab2:
    st.header("Reportes y Exportación de Planillas")
    
    if df_entregas.empty:
        st.info("Aún no se han registrado movimientos de entrega.")
    else:
        # Asegurar formato correcto de fecha
        df_entregas["Fecha"] = pd.to_datetime(df_entregas["Fecha"])
        
        col1, col2 = st.columns(2)
        with col1:
            filtro_tipo = st.radio("Ver reporte por:", ["Día Específico", "Rango Semanal / Personalizado"])
        
        if filtro_tipo == "Día Específico":
            dia_sel = st.date_input("Selecciona el día", datetime.now())
            df_filtrado = df_entregas[df_entregas["Fecha"].dt.date == dia_sel]
            nombre_archivo = f"reporte_diario_{dia_sel}.csv"
        else:
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                fecha_inicio = st.date_input("Desde", datetime.now() - timedelta(days=7))
            with col_f2:
                fecha_fin = st.date_input("Hasta", datetime.now())
            
            df_filtrado = df_entregas[
                (df_entregas["Fecha"].dt.date >= fecha_inicio) & 
                (df_entregas["Fecha"].dt.date <= fecha_fin)
            ]
            nombre_archivo = f"reporte_{fecha_inicio}_al_{fecha_fin}.csv"

        st.markdown("---")
        st.subheader("Datos filtrados")
        
        if df_filtrado.empty:
            st.warning("No hay registros de entregas para la fecha o rango seleccionado.")
        else:
            # Clonar para visualización limpia sin horas
            df_mostrar = df_filtrado.copy()
            df_mostrar["Fecha"] = df_mostrar["Fecha"].dt.strftime('%Y-%m-%d')
            st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
            
            # Botón de descarga de la planilla filtrada
            csv_data = df_filtrado.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar esta planilla en CSV (Excel)",
                data=csv_data,
                file_name=nombre_archivo,
                mime='text/csv',
            )

# PESTAÑA 3: Carga de nuevo Stock (Entrada de mercadería)
with tab3:
    st.header("Ingreso de Mercadería / Actualizar Stock")
    st.write("Utilizá esta sección cuando se compren o ingresen nuevos insumos al depósito.")
    
    with st.form("form_ingreso", clear_on_submit=True):
        insumo_ingreso = st.selectbox("Insumo que ingresa", df_inventario["Insumo"].unique(), key="ingreso_insumo")
        cantidad_ingreso = st.number_input("Cantidad que ingresa", min_value=1.0, step=1.0)
        boton_ingresar = st.form_submit_button("Aumentar Stock")
        
        if boton_ingresar:
            # Sumar la cantidad al inventario
            df_inventario.loc[df_inventario["Insumo"] == insumo_ingreso, "Stock Actual"] += cantidad_ingreso
            # Guardar el cambio en el archivo
            guardar_datos(df_inventario, df_entregas)
            st.success(f"✅ Se agregaron {cantidad_ingreso} unidades a {insumo_ingreso}.")
            st.rerun()
