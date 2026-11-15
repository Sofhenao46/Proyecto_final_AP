import os
import hashlib
import pandas as pd

carpeta = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
archivo_usuarios = os.path.join(carpeta, "data", "usuarios.csv")
archivo_bobinos = os.path.join(carpeta, "data", "bovinos.csv")


# ---------------- USUARIOS ----------------

def convertir_clave(clave):
    # convierte la contraseña en un código para no guardarla tal cual
    clave_en_bytes = clave.encode()
    resultado = hashlib.sha256(clave_en_bytes)
    return resultado.hexdigest()


def cargar_usuarios():
    if not os.path.exists(archivo_usuarios):
        return pd.DataFrame(columns=["Usuario", "Nombre", "Clave"])
    return pd.read_csv(archivo_usuarios, dtype=str)


def guardar_usuarios(df):
    os.makedirs(os.path.dirname(archivo_usuarios), exist_ok=True)
    df.to_csv(archivo_usuarios, index=False)


def registrar_usuario(nombre, usuario, clave, clave2):
    usuario = usuario.strip().lower()
    usuarios = cargar_usuarios()

    if nombre.strip() == "" or usuario == "" or clave == "":
        return False, "Completa todos los campos"
    elif len(usuario) < 4:
        return False, "El usuario debe tener mínimo 4 caracteres"
    elif len(clave) < 6:
        return False, "La contraseña debe tener mínimo 6 caracteres"
    elif clave != clave2:
        return False, "Las contraseñas no son iguales"
    elif usuario in usuarios["Usuario"].values:
        return False, "Ese usuario ya existe"
    else:
        nuevo = pd.DataFrame([{
            "Usuario": usuario,
            "Nombre": nombre.strip(),
            "Clave": convertir_clave(clave),
        }])
        usuarios = pd.concat([usuarios, nuevo], ignore_index=True)
        guardar_usuarios(usuarios)
        return True, "Cuenta creada, ya puedes iniciar sesión"


def validar_login(usuario, clave):
    usuario = usuario.strip().lower()
    usuarios = cargar_usuarios()

    fila = usuarios[usuarios["Usuario"] == usuario]

    if not fila.empty and fila.iloc[0]["Clave"] == convertir_clave(clave):
        return True, fila.iloc[0]["Nombre"]
    else:
        return False, "Usuario o contraseña incorrectos"


# ---------------- BOVINOS ----------------

def guardar_bovinos(df):
    os.makedirs(os.path.dirname(archivo_bobinos), exist_ok=True)
    df.to_csv(archivo_bobinos, index=False)


def cargar_bovinos():
    # la primera vez crea el archivo con datos de ejemplo
    if not os.path.exists(archivo_bobinos):
        df = pd.DataFrame({
            "Identificacion": ["A-001", "A-002", "A-003", "A-004"],
            "Sexo": ["Macho", "Hembra", "Macho", "Hembra"],
            "Color": ["Negro", "Pintada", "Blanco", "Café"],
            "Peso entrada": [250, 300, 280, 320],
            "Estado": ["En finca", "En finca", "Vendido", "Vendido"],
            "Peso salida": [None, None, 360, 400],
            "Precio venta": [None, None, 2800000, 3500000],
        })
        guardar_bovinos(df)
    return pd.read_csv(archivo_bobinos)
    


def filtrar_sexo(df, sexo):
    if sexo == "Todos":
        return df
    return df[df["Sexo"] == sexo]


def calcular_metricas(df):
    en_finca = len(df[df["Estado"] == "En finca"])
    vendidos = df[df["Estado"] == "Vendido"]

    total = vendidos["Precio venta"].sum()
    ganancia = (vendidos["Peso salida"] - vendidos["Peso entrada"]).mean()
    if pd.isna(ganancia):
        ganancia = 0

    return en_finca, len(vendidos), total, ganancia


def agregar_bovino(df, identificacion, sexo, color, peso):
    identificacion = identificacion.strip().upper()

    if identificacion == "" or color.strip() == "" or peso <= 0:
        return False, "Completa todos los campos", df
    elif identificacion in df["Identificacion"].values:
        return False, "Este bovino ya está registrado", df
    else:
        nuevo = pd.DataFrame([{
            "Identificacion": identificacion,
            "Sexo": sexo,
            "Color": color.strip(),
            "Peso entrada": peso,
            "Estado": "En finca",
            "Peso salida": None,
            "Precio venta": None,
        }])
        df = pd.concat([df, nuevo], ignore_index=True)
        guardar_bovinos(df)
        return True, "Bovino " + identificacion + " registrado", df


def vender_bovino(df, identificacion, peso_salida, precio):
    if peso_salida <= 0 or precio <= 0:
        return False, "El peso y el valor deben ser mayores a cero", df

    fila = df[df["Identificacion"] == identificacion].index[0]
    df.loc[fila, "Estado"] = "Vendido"
    df.loc[fila, "Peso salida"] = peso_salida
    df.loc[fila, "Precio venta"] = precio
    guardar_bovinos(df)
    return True, "Venta de " + identificacion + " registrada", df