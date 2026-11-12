import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Ganadería WJ",
    page_icon="🐄",
    layout="wide"

)

st.title("Ganadería WJ")

if "mensaje" in st.session_state:
    st.success(st.session_state.pop("mensaje"))

# Datos de ejemplo (se crean solo la primera vez)
if "df" not in st.session_state:
    st.session_state["df"] = pd.DataFrame({
        "Identificacion": ["A-001", "A-002", "A-003", "A-004"],
        "Sexo": ["Macho", "Hembra", "Macho", "Hembra"],
        "Color": ["Negro", "Pintada", "Blanco", "Café"],
        "Peso entrada": [250, 300, 280, 320],
        "Estado": ["En finca", "En finca", "Vendido", "Vendido"],
        "Peso salida": [None, None, 360, 400],
        "Precio venta": [None, None, 2800000, 3500000],
    })

df = st.session_state["df"]
en_finca = df[df["Estado"] == "En finca"]
vendidos = df[df["Estado"] == "Vendido"]

# Barra lateral
st.sidebar.title("Filtros")
sexo = st.sidebar.selectbox("Sexo", ["Todos", "Macho", "Hembra"])
df_filtrado = df if sexo == "Todos" else df[df["Sexo"] == sexo]

# Métricas
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("En finca", len(en_finca))

with col2:
    st.metric("Vendidos", len(vendidos))

with col3:
    st.metric("Total vendido", f"${vendidos['Precio venta'].sum():,.0f}")

# Pestañas
tab1, tab2, tab3 = st.tabs(["Resumen", "Registrar bovino", "Registrar venta"])

with tab1:
    st.dataframe(df_filtrado)
    st.bar_chart(df_filtrado["Sexo"].value_counts())

    if not vendidos.empty:
        st.subheader("Peso de entrada vs peso de salida")
        st.bar_chart(vendidos.set_index("Identificacion")[["Peso entrada", "Peso salida"]])

with tab2:
    with st.form("registro", clear_on_submit=True):
        identificacion = st.text_input("Identificación")
        sexo_nuevo = st.selectbox("Sexo del bovino", ["Macho", "Hembra"])
        color = st.text_input("Color")
        peso = st.number_input("Peso de entrada (kg)", min_value=0.0)
        guardar = st.form_submit_button("Registrar")

    if guardar:
        identificacion = identificacion.strip().upper()
        if identificacion == "" or color.strip() == "" or peso <= 0:
            st.error("Completa todos los campos")
        elif identificacion in df["Identificacion"].values:
            st.warning("Este bovino ya está registrado")
        else:
            nuevo = pd.DataFrame([{
                "Identificacion": identificacion, "Sexo": sexo_nuevo, "Color": color.strip(),
                "Peso entrada": peso, "Estado": "En finca", "Peso salida": None, "Precio venta": None,
            }])
            st.session_state["df"] = pd.concat([df, nuevo], ignore_index=True)
            st.session_state["mensaje"] = f"Bovino {identificacion} registrado"
            st.rerun()

with tab3:
    if en_finca.empty:
        st.info("No hay bovinos en la finca para vender")
    else:
        with st.form("venta", clear_on_submit=True):
            elegido = st.selectbox("Bovino a vender", en_finca["Identificacion"])
            peso_salida = st.number_input("Peso de salida (kg)", min_value=0.0)
            precio = st.number_input("Valor de la venta", min_value=0.0, step=10000.0)
            vender = st.form_submit_button("Registrar venta")

        if vender:
            if peso_salida <= 0 or precio <= 0:
                st.error("El peso y el valor deben ser mayores a cero")
            else:
                fila = df[df["Identificacion"] == elegido].index[0]
                df.loc[fila, "Estado"] = "Vendido"
                df.loc[fila, "Peso salida"] = peso_salida
                df.loc[fila, "Precio venta"] = precio
                st.session_state["df"] = df
                st.session_state["mensaje"] = f"Venta de {elegido} registrada"
                st.rerun()