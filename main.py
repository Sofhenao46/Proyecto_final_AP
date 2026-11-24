
import streamlit as st
import backend.logica as back
import frontend.app as ui

def main():
    ui.configurar()

    if "usuario" in st.session_state:
        if "df" not in st.session_state:
            st.session_state["df"] = back.cargar_bovinos()

        ui.pantalla_principal()
    else:
        ui.pantalla_login()

if __name__ == "__main__":
    main()
    