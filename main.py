import streamlit as st
import backend.logica as logic
import frontend.app as ui


# Función principal de la aplicación
def main():

    # Configuramos la página y sus estilos
    ui.configurar()

    # Revisamos si el usuario ya inició sesión
    if "usuario" in st.session_state:

        # Cargamos los bovinos si todavía no están en la sesión
        if "df" not in st.session_state:
            st.session_state["df"] = logic.cargar_bovinos()

        # Mostramos la pantalla principal
        ui.pantalla_principal()

    else:
        # Si no ha iniciado sesión, mostramos el login
        ui.pantalla_login()


# Iniciamos la aplicación
if __name__ == "__main__":
    main()
