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
    if os.path.exists(FILE_INVENTARIO):
        inventario = pd.read_csv(FILE_INVENTARIO)
    else:
        # Lista inicial por defecto la primera vez
        inventario = pd.DataFrame([
            {"Insumo": "Lavandina (Lts)", "Stock Actual": 50.0},
            {"Insumo": "Detergente (Lts)", "Stock Actual": 30.0},
            {"Insumo": "Papel Higiénico (Rollos)", "Stock Actual": 120.0},
            {"Insumo": "Bolsas de Consorcio (U)", "Stock Actual": 200.0},
            {"Insumo": "Desinfectante de Pisos (Lts)", "Stock Actual": 40.0}
        ])
        inventario.to_csv(FILE_INVENTARIO, index=False)
    
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

# Cargar los datos
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
        stock_disponible = df_inventario.loc[df_inventario["Insumo"] == insumo_sel, "Stock Actual"].values[0]
        
        if cantidad > stock_disponible:
            st.sidebar.error(f"❌ Stock insuficiente. Solo quedan {stock_disponible} unidades.")
        else:
            df_inventario.loc[df_inventario["Insumo"] == insumo_sel, "Stock Actual"] -= cantidad
            nueva_entrega = pd.DataFrame([{
                "Fecha": pd.to_datetime(fecha_entrega),
                "Insumo": insumo_sel,
                "Cantidad Entregada": cantidad,
                "Destino/Personal": destino
            }])
            df_entregas = pd.concat([df_entregas, nueva_entrega], ignore_index=True)
            guardar_datos(df_inventario, df_entregas)
            st.sidebar.success("✅ Entrega registrada.")
            st.rerun()

# --- CUERPO PRINCIPAL ---
tab1, tab2, tab3 = st.tabs(["📊 Stock Actual", "📈 Historial y Descargas", "⚙️ Gestión de Insumos (Llegadas/Nuevos)"])

# PESTAÑA 1: Estado del Inventario
with tab1:
    st.header("Estado actual del depósito")
    st.dataframe(df_inventario, use_container_width=True, hide_index=True)
    
    stock_bajo = df_inventario[df_inventario["Stock Actual"] <= 10]
    if not stock_bajo.empty:
        st.warning("⚠️ **¡Atención!** Los siguientes insumos tienen un stock crítico (10 unidades o menos):")
        st.dataframe(stock_bajo, hide_index=True)

# PESTAÑA 2: Reportes y Descargas
with tab2:
    st.header("Reportes y Exportación de Planillas")
    if df_entregas.empty:
        st.info("Aún no se han registrado movimientos de entrega.")
    else:
        df_entregas["Fecha"] = pd.to_datetime(df_entregas["Fecha"])
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
            df_filtrado = df_entregas[(df_entregas["Fecha"].dt.date >= fecha_inicio) & (df_entregas["Fecha"].dt.date <= fecha_fin)]
            nombre_archivo = f"reporte_{fecha_inicio}_al_{fecha_fin}.csv"

        st.markdown("---")
        if df_filtrado.empty:
            st.warning("No hay registros para el período seleccionado.")
        else:
            df_mostrar = df_filtrado.copy()
            df_mostrar["Fecha"] = df_mostrar["Fecha"].dt.strftime('%Y-%m-%d')
            st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
            
            csv_data = df_filtrado.to_csv(index=False).encode('utf-8')
            st.download_button(label="📥 Descargar esta planilla en CSV", data=csv_data, file_name=nombre_archivo, mime='text/csv')

# PESTAÑA 3: Gestión e Ingresos Avanzados
with tab3:
    st.header("⚙️ Panel de Actualización de Mercadería")
    
    col_izq, col_der = st.columns(2)
    
    # SUB-SECCIÓN A: Llegada de mercadería existente
    with col_izq:
        st.subheader("📦 Registrar Ingreso de Stock")
        st.caption("Usá esto cuando llegue un pedido de insumos que ya están en la lista.")
        with st.form("form_ingreso_stock", clear_on_submit=True):
            insumo_ingreso = st.selectbox("Insumo que llegó", df_inventario["Insumo"].unique())
            cantidad_ingreso = st.number_input("Cantidad que ingresa", min_value=0.1, step=1.0, format="%.1f")
            boton_ingresar = st.form_submit_button("➕ Sumar al Stock")
            
            if boton_ingresar:
                df_inventario.loc[df_inventario["Insumo"] == insumo_ingreso, "Stock Actual"] += cantidad_ingreso
                guardar_datos(df_inventario, df_entregas)
                st.success(f"✅ Se sumaron {cantidad_ingreso} unidades a {insumo_ingreso}.")
                st.rerun()

    # SUB-SECCIÓN B: Agregar un producto totalmente nuevo
    with col_der:
        st.subheader("✨ Agregar Nuevo Insumo al Sistema")
        st.caption("Usá esto si compraste un artículo nuevo que no figura en el stock actual.")
        with st.form("form_nuevo_producto", clear_on_submit=True):
            nuevo_nombre = st.text_input("Nombre del Insumo (con su unidad)", placeholder="Ej: Guantes de Látex (Pares)")
            stock_inicial = st.number_input("Stock Inicial con el que ingresa", min_value=0.0, step=1.0, format="%.1f")
            boton_crear = st.form_submit_button("💾 Crear Insumo")
            
            if boton_crear:
                nuevo_nombre = nuevo_nombre.strip()
                if nuevo_nombre == "":
                    st.error("Por favor, ingresá un nombre válido.")
                elif nuevo_nombre in df_inventario["Insumo"].values:
                    st.error("Este insumo ya existe en el sistema.")
                else:
                    nuevo_item = pd.DataFrame([{"Insumo": nuevo_nombre, "Stock Actual": stock_inicial}])
                    df_inventario = pd.concat([df_inventario, nuevo_item], ignore_index=True)
                    guardar_datos(df_inventario, df_entregas)
                    st.success(f"🎉 '{nuevo_nombre}' ha sido agregado al inventario.")
                    st.rerun()
                    
    st.markdown("---")
    # SUB-SECCIÓN C: Modificación Manual Directa (Auditoría de Stock)
    st.subheader("✏️ Corrección Manual de Inventario")
    st.caption("Si hiciste un conteo físico en el depósito y los números no coinciden con la app, podés forzar y corregir el valor exacto acá.")
    
    col_mod1, col_mod2, col_mod3 = st.columns([2, 1, 1])
    with col_mod1:
        insumo_a_modificar = st.selectbox("Seleccionar insumo a corregir", df_inventario["Insumo"].unique(), key="mod_insumo")
    with col_mod2:
        valor_actual = df_inventario.loc[df_inventario["Insumo"] == insumo_a_modificar, "Stock Actual"].values[0]
        nuevo_valor_fijo = st.number_input("Nuevo Stock Real Exacto", min_value=0.0, value=float(valor_actual), step=1.0, format="%.1f")
    with col_mod3:
        st.write("") # Espacio para alinear el botón
        st.write("") 
        boton_modificar = st.button("🔧 Corregir Valor Fijo", use_container_width=True)
        
    if boton_modificar:
        df_inventario.loc[df_inventario["Insumo"] == insumo_a_modificar, "Stock Actual"] = nuevo_valor_fijo
        guardar_datos(df_inventario, df_entregas)
        st.success(f"🔧 Stock de '{insumo_a_modificar}' corregido manualmente a {nuevo_valor_fijo}.")
        st.rerun()
