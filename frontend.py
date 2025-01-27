import streamlit as st
from backend import calcular_precio_minimo_con_tercera_fuente  # Importar la función del backend

st.title("Cálculo de Precio Mínimo")

archivo_excel = st.file_uploader("Sube el archivo Excel con los servicios contratados", type=["xlsx"])
cantidad_proveedores = st.number_input("Cantidad total de proveedores", min_value=1, step=1)
nivel = st.selectbox("Selecciona el nivel del cliente", ["360", "180", "basic", "Elementary", "Digital"])

num_paises = st.number_input("¿Cuántos países quieres ingresar para la distribución de proveedores?", min_value=1, step=1)
distribuccion_por_pais = {}
for i in range(int(num_paises)):
    pais = st.text_input(f"Código del país #{i+1} (ej. ESP, PRT)", key=f"pais_{i}")
    cantidad = st.number_input(f"Cantidad de proveedores para {pais}", min_value=0, step=1, key=f"cantidad_{i}")
    if pais:
        distribuccion_por_pais[pais] = cantidad

margen_opcional = st.number_input("Margen deseado (opcional, en porcentaje)", min_value=0.0, step=0.1) / 100

if st.button("Calcular Precio Mínimo"):
    if archivo_excel is not None and cantidad_proveedores > 0:
        resultado = calcular_precio_minimo_con_tercera_fuente(
            archivo_excel=archivo_excel,
            cantidad_proveedores=cantidad_proveedores,
            nivel=nivel,
            distribuccion_por_pais=distribuccion_por_pais,
            margen_opcional=margen_opcional
        )
        st.subheader("Resultado del cálculo:")
        for clave, valor in resultado.items():
            st.write(f"{clave}: {valor}")

