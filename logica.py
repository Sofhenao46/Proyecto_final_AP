import hashlib
import hmac
import os
import re
import pandas as pd
from pathlib import Path
from io import BytesIO
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

carpeta = Path(__file__).resolve().parent.parent
datos = carpeta / "data"
archivo_usuarios = datos / "usuarios.csv"
archivo_excel = datos / "ganaderia_wj.xlsx"
archivo_anterior = datos / "bovinos.csv"

columnas_usuarios = ["Usuario", "Nombre", "Clave"]
columnas_bovinos = ["Identificacion", "Sexo", "Color", "Peso entrada", "Estado", "Peso salida", "Precio venta"]

def convertir_clave(clave):
    sal = os.urandom(16)
    resultado = hashlib.pbkdf2_hmac("sha256", clave.encode("utf-8"), sal, 260000)
    return f"pbkdf2${sal.hex()}${resultado.hex()}"

def comprobar_clave(clave, guardada):
    try:
        if guardada.startswith("pbkdf2$"):
            _, sal, hash_guardado = guardada.split("$")
            calculado = hashlib.pbkdf2_hmac("sha256", clave.encode("utf-8"), bytes.fromhex(sal), 260000)
            return hmac.compare_digest(calculado, bytes.fromhex(hash_guardado))
        anterior = hashlib.sha256(clave.encode("utf-8")).hexdigest()
        return hmac.compare_digest(anterior, guardada)
    except (ValueError, TypeError):
        return False

def cargar_usuarios():
    if not archivo_usuarios.exists():
        return pd.DataFrame(columns=columnas_usuarios)
    try:
        df = pd.read_csv(archivo_usuarios, dtype=str).fillna("")
        for columna in columnas_usuarios:
            if columna not in df.columns:
                df[columna] = ""
        return df[columnas_usuarios]
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=columnas_usuarios)

def guardar_usuarios(df):
    datos.mkdir(parents=True, exist_ok=True)
    df.to_csv(archivo_usuarios, index=False)

def registrar_usuario(nombre, usuario, clave, clave2):
    nombre, usuario = nombre.strip(), usuario.strip().lower()
    if not all([nombre, usuario, clave, clave2]):
        return False, "Completa todos los campos."
    if len(usuario) < 4:
        return False, "El usuario debe tener mínimo 4 caracteres."
    if len(clave) < 6:
        return False, "La contraseña debe tener mínimo 6 caracteres."
    if clave != clave2:
        return False, "Las contraseñas no coinciden."
    usuarios = cargar_usuarios()
    if usuario in usuarios["Usuario"].str.lower().values:
        return False, "Ese usuario ya está registrado."
    nuevo = pd.DataFrame([{"Usuario": usuario, "Nombre": nombre, "Clave": convertir_clave(clave)}])
    guardar_usuarios(pd.concat([usuarios, nuevo], ignore_index=True))
    return True, "Cuenta creada correctamente."

def validar_login(usuario, clave):
    usuarios = cargar_usuarios()
    encontrado = usuarios[usuarios["Usuario"].str.lower() == usuario.strip().lower()]
    if encontrado.empty or not clave:
        return False, "Usuario o contraseña incorrectos."
    fila = encontrado.iloc[0]
    if comprobar_clave(clave, fila["Clave"]):
        return True, fila["Nombre"]
    return False, "Usuario o contraseña incorrectos."

def preparar_bovinos(df):
    df = df.copy()
    for columna in columnas_bovinos:
        if columna not in df.columns:
            df[columna] = None
    df = df[columnas_bovinos]
    for columna in ["Identificacion", "Sexo", "Color", "Estado"]:
        df[columna] = df[columna].fillna("").astype(str)
    for columna in ["Peso entrada", "Peso salida", "Precio venta"]:
        df[columna] = pd.to_numeric(df[columna], errors="coerce")
    return df

def proteger_excel(valor):
    if isinstance(valor, str) and valor.startswith(("=", "+", "-", "@")):
        return "'" + valor
    return valor

def crear_excel(df):
    df = preparar_bovinos(df)
    salida = BytesIO()
    vendidos = df[df["Estado"] == "Vendido"].copy()
    vendidos["Diferencia peso"] = vendidos["Peso salida"] - vendidos["Peso entrada"]
    columnas_ventas = ["Identificacion", "Sexo", "Color", "Peso entrada", "Peso salida", "Diferencia peso", "Precio venta"]

    with pd.ExcelWriter(salida, engine="openpyxl") as writer:
        for nombre, tabla in [("Bovinos", df), ("Ventas", vendidos[columnas_ventas])]:
            tabla = tabla.astype(object).where(pd.notna(tabla), None)
            for columna in ["Identificacion", "Sexo", "Color", "Estado"]:
                if columna in tabla.columns:
                    tabla[columna] = tabla[columna].map(proteger_excel)
            tabla.to_excel(writer, sheet_name=nombre, index=False)
            hoja = writer.sheets[nombre]
            hoja.freeze_panes = "A2"
            hoja.sheet_view.showGridLines = False
            hoja.auto_filter.ref = hoja.dimensions
            for celda in hoja[1]:
                celda.fill = PatternFill("solid", fgColor="1F4D36")
                celda.font = Font(bold=True, color="FFFFFF")
                celda.alignment = Alignment(horizontal="center")
            for indice, columna in enumerate(hoja.columns, 1):
                ancho = max(len(str(c.value)) if c.value is not None else 0 for c in columna)
                hoja.column_dimensions[get_column_letter(indice)].width = min(max(ancho + 3, 16), 30)
            for fila in hoja.iter_rows(min_row=2):
                for celda in fila:
                    if isinstance(celda.value, (int, float)):
                        celda.number_format = '"$" #,##0' if hoja.cell(1, celda.column).value == "Precio venta" else '#,##0.##'
    return salida.getvalue()

def guardar_bovinos(df):
    datos.mkdir(parents=True, exist_ok=True)
    temporal = archivo_excel.with_suffix(".tmp.xlsx")
    temporal.write_bytes(crear_excel(df))
    os.replace(temporal, archivo_excel)

def cargar_bovinos():
    if not archivo_excel.exists():
        if archivo_anterior.exists():
            try:
                df = pd.read_csv(archivo_anterior, dtype={"Identificacion": str})
            except pd.errors.EmptyDataError:
                df = pd.DataFrame(columns=columnas_bovinos)
        else:
            df = pd.DataFrame(columns=columnas_bovinos)
        df = preparar_bovinos(df)
        guardar_bovinos(df)
        return df
    df = pd.read_excel(archivo_excel, sheet_name="Bovinos", dtype={"Identificacion": str})
    return preparar_bovinos(df)

def leer_numero(texto, dinero=False):
    texto = str(texto).strip().replace(" ", "").replace("$", "").upper().replace("COP", "")
    if not texto or not re.fullmatch(r"[0-9.,]+", texto):
        raise ValueError("Escribe un número válido.")
    if dinero:
        if re.fullmatch(r"\d{1,3}([.,]\d{3})+", texto):
            texto = texto.replace(".", "").replace(",", "")
        elif texto.count(".") + texto.count(",") == 1:
            texto = texto.replace(",", ".")
        elif "." in texto or "," in texto:
            raise ValueError("Escribe el precio como 2800000 o 2.800.000.")
    else:
        if "," in texto and "." in texto:
            texto = texto.replace(".", "").replace(",", ".") if texto.rfind(",") > texto.rfind(".") else texto.replace(",", "")
        else:
            texto = texto.replace(",", ".")
    try:
        numero = float(texto)
    except ValueError:
        raise ValueError("El número no es válido.")
    if not 0 < numero < 1e13:
        raise ValueError("Ingresa un valor mayor que cero y dentro del límite.")
    if dinero and not numero.is_integer():
        raise ValueError("El precio debe estar en pesos completos.")
    return numero

def filtrar_sexo(df, sexo):
    return df if sexo == "Todos" else df[df["Sexo"] == sexo]

def calcular_metricas(df):
    en_finca = len(df[df["Estado"] == "En finca"])
    vendidos = df[df["Estado"] == "Vendido"]
    total = vendidos["Precio venta"].sum()
    diferencia = (vendidos["Peso salida"] - vendidos["Peso entrada"]).mean()
    return en_finca, len(vendidos), total, 0 if pd.isna(diferencia) else diferencia

def agregar_bovino(df, identificacion, sexo, color, peso):
    identificacion, color = identificacion.strip().upper(), color.strip()
    if not identificacion or not color:
        return False, "Completa todos los campos.", df
    if sexo not in ["Macho", "Hembra"]:
        return False, "Selecciona un sexo válido.", df
    if not 0 < peso < 100000:
        return False, "Ingresa un peso válido.", df
    if identificacion in df["Identificacion"].astype(str).str.strip().str.upper().values:
        return False, "Este bovino ya está registrado.", df
    nuevo = pd.DataFrame([{
        "Identificacion": identificacion, "Sexo": sexo, "Color": color,
        "Peso entrada": peso, "Estado": "En finca",
        "Peso salida": None, "Precio venta": None
    }])
    actualizado = pd.concat([df, nuevo], ignore_index=True)
    guardar_bovinos(actualizado)
    return True, f"Bovino {identificacion} registrado correctamente.", actualizado

def vender_bovino(df, identificacion, peso_salida, precio):
    if not 0 < peso_salida < 100000 or not 0 < precio < 1e13:
        return False, "Ingresa un peso y precio válidos.", df
    encontrado = df[df["Identificacion"] == identificacion]
    if encontrado.empty:
        return False, "No se encontró el bovino.", df
    indice = encontrado.index[0]
    if df.loc[indice, "Estado"] != "En finca":
        return False, "Este bovino no está disponible.", df
    actualizado = df.copy()
    actualizado.loc[indice, "Estado"] = "Vendido"
    actualizado.loc[indice, "Peso salida"] = peso_salida
    actualizado.loc[indice, "Precio venta"] = precio
    guardar_bovinos(actualizado)
    return True, f"Venta del bovino {identificacion} registrada correctamente.", actualizado