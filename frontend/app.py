import streamlit as st
import backend.logica as back
from pathlib import Path

# Colores de la aplicación
verde = "#1F4D36"
dorado = "#C58B2A"

# Ubicación del logo
carpeta = Path(__file__).resolve().parent.parent
logo = carpeta / "assets" / "logo.jpeg"


# Mostramos el logo si está guardado en la carpeta
def mostrar_logo(ancho=130, lateral=False):
    if logo.is_file():
        try:
            if lateral:
                st.sidebar.image(str(logo), width=ancho)
            else:
                st.image(str(logo), width=ancho)
        except Exception:
            pass


# Configuración de la página y sus colores
def configurar():
    st.set_page_config(page_title="Ganadería WJ", page_icon="🐄", layout="wide")

    st.markdown("""
    <style>
        #MainMenu, footer {visibility: hidden;}

        [data-testid="stMetric"] {
            background: white;
            border-left: 6px solid #1F4D36;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 1px 4px rgba(0, 0, 0, 0.15);
        }

        .stButton > button, .stFormSubmitButton > button {
            background: #1F4D36;
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: bold;
        }

        .stButton > button:hover, .stFormSubmitButton > button:hover {
            background: #C58B2A;
            color: white;
        }
    </style>
    """, unsafe_allow_html=True)


# Pantalla para entrar o crear una cuenta
def pantalla_login():

    # Centramos el formulario en la página
    vacio1, centro, vacio2 = st.columns([1, 1.5, 1])

    with centro:
        mostrar_logo(130)
        st.title("Ganadería WJ")

        tab_entrar, tab_crear = st.tabs(["Iniciar sesión", "Crear cuenta"])

        # Inicio de sesión
        with tab_entrar:
            with st.form("login"):
                usuario = st.text_input("Usuario")
                clave = st.text_input("Contraseña", type="password")
                entrar = st.form_submit_button("Entrar")

            if entrar:
                if not usuario.strip() or not clave:
                    st.warning("Escribe tu usuario y contraseña.")
                else:
                    ok, respuesta = back.validar_login(usuario, clave)

                    if ok:
                        st.session_state["usuario"] = respuesta
                        st.rerun()
                    else:
                        st.error(respuesta)

        # Registro de usuarios nuevos
        with tab_crear:
            with st.form("crear_cuenta"):
                nombre = st.text_input("Nombre completo")
                usuario_nuevo = st.text_input("Usuario")
                clave_nueva = st.text_input("Contraseña", type="password")
                clave_repetida = st.text_input("Repite la contraseña", type="password")
                crear = st.form_submit_button("Crear cuenta")

            if crear:
                if not nombre.strip() or not usuario_nuevo.strip():
                    st.warning("Completa tu nombre y usuario.")
                elif not clave_nueva or not clave_repetida:
                    st.warning("Escribe y confirma tu contraseña.")
                else:
                    ok, mensaje = back.registrar_usuario(nombre, usuario_nuevo, clave_nueva, clave_repetida)

                    if ok:
                        st.success(mensaje)
                    else:
                        st.error(mensaje)


# Pantalla principal de la ganadería
def pantalla_principal():

    # Cargamos los datos de los bovinos
    df = st.session_state["df"]

    # Barra lateral para filtrar los animales
    mostrar_logo(100, lateral=True)
    st.sidebar.title("Filtros")
    sexo = st.sidebar.selectbox("Sexo", ["Todos", "Macho", "Hembra"])
    df_filtrado = back.filtrar_sexo(df, sexo)

    # Botón para cerrar sesión
    if st.sidebar.button("Cerrar sesión"):
        st.session_state.clear()
        st.rerun()

    # Encabezado de la página
    col_logo, col_titulo = st.columns([1, 8])

    with col_logo:
        mostrar_logo(90)

    with col_titulo:
        st.title("Ganadería WJ")
        st.write("Bienvenido, " + str(st.session_state["usuario"]))

    # Mostramos los mensajes después de guardar información
    if "mensaje" in st.session_state:
        st.success(st.session_state.pop("mensaje"))

    # Datos generales de la finca
    en_finca, vendidos, total, ganancia = back.calcular_metricas(df)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("En finca", en_finca)
    col2.metric("Vendidos", vendidos)
    col3.metric("Total vendido", f"${total:,.0f}")
    col4.metric("Ganancia de peso promedio", f"{ganancia:,.0f} kg")

    # Secciones de la aplicación
    tab1, tab2, tab3 = st.tabs(["Resumen", "Registrar bovino", "Registrar venta"])

    # Resumen de los animales registrados
    with tab1:
        st.subheader("Bovinos registrados")
        st.dataframe(df_filtrado, use_container_width=True)

        col_a, col_b = st.columns(2)

        with col_a:
            st.subheader("Bovinos por sexo")

            if not df_filtrado.empty:
                cantidad_sexo = df_filtrado["Sexo"].value_counts()
                st.bar_chart(cantidad_sexo, color=verde)
            else:
                st.info("No hay bovinos para mostrar.")

        with col_b:
            st.subheader("Peso de entrada y salida")
            tabla_vendidos = df[df["Estado"] == "Vendido"]

            if not tabla_vendidos.empty:
                pesos = tabla_vendidos.set_index("Identificacion")[["Peso entrada", "Peso salida"]]
                st.bar_chart(pesos, color=[verde, dorado])
            else:
                st.info("Todavía no hay ventas registradas.")

    # Registro de bovinos nuevos
    with tab2:
        st.subheader("Registrar un bovino")

        with st.form("registro", clear_on_submit=True):
            identificacion = st.text_input("Identificación")
            sexo_nuevo = st.selectbox("Sexo del bovino", ["Macho", "Hembra"])
            color = st.text_input("Color")
            peso = st.number_input("Peso de entrada (kg)", min_value=0.0)
            guardar = st.form_submit_button("Registrar")

        if guardar:
            if not identificacion.strip():
                st.warning("Escribe la identificación del bovino.")
            elif not color.strip():
                st.warning("Escribe el color del bovino.")
            elif peso <= 0:
                st.warning("El peso debe ser mayor que cero.")
            else:
                ok, mensaje, df_nuevo = back.agregar_bovino(df, identificacion, sexo_nuevo, color, peso)

                if ok:
                    st.session_state["df"] = df_nuevo
                    st.session_state["mensaje"] = mensaje
                    st.rerun()
                else:
                    st.error(mensaje)

    # Registro de ventas
    with tab3:
        st.subheader("Registrar una venta")

        # Solo se pueden vender animales que estén en la finca
        en_la_finca = df[df["Estado"] == "En finca"]

        if en_la_finca.empty:
            st.info("No hay bovinos disponibles para vender.")
        else:
            with st.form("venta", clear_on_submit=True):
                elegido = st.selectbox("Bovino a vender", en_la_finca["Identificacion"])
                peso_salida = st.number_input("Peso de salida (kg)", min_value=0.0)
                precio = st.number_input("Valor de la venta", min_value=0.0, step=10000.0)
                vender = st.form_submit_button("Registrar venta")

            if vender:
                if peso_salida <= 0:
                    st.warning("El peso de salida debe ser mayor que cero.")
                elif precio <= 0:
                    st.warning("El valor de la venta debe ser mayor que cero.")
                else:
                    ok, mensaje, df_nuevo = back.vender_bovino(df, elegido, peso_salida, precio)

                    if ok:
                        st.session_state["df"] = df_nuevo
                        st.session_state["mensaje"] = mensaje
                        st.rerun()
                    else:
                        st.error(mensaje)
