import streamlit as st
import pandas as pd
from backend import calcular_precio_minimo_con_tercera_fuente  # Asegúrate de que el backend esté correctamente importado
import io

st.title("Cálculo de Precio Mínimo con Tercera Fuente")

# Permitir subir hasta 5 archivos
archivos_excel = st.file_uploader("Sube hasta 5 archivos Excel con los servicios contratados", type=["xlsx"], accept_multiple_files=True)

if archivos_excel:
    niveles_detectados = {}
    check_names_por_nivel = {}  # Diccionario para almacenar los Check Names por nivel
    archivos_invalidos = []

    for archivo in archivos_excel:
        try:
            servicios_df = pd.read_excel(archivo, sheet_name=None, header=None)
            hoja_info_general = servicios_df.get("Información General")
            hoja_lista_servicios = servicios_df.get("Lista de Servicios")

            # Detectar niveles desde "Información General"
            if hoja_info_general is not None and len(hoja_info_general) > 4 and hoja_info_general.shape[1] > 1:
                nivel = str(hoja_info_general.iloc[4, 1]).strip()  # Leer nivel desde la celda B5
                if nivel in niveles_detectados:
                    niveles_detectados[nivel] += 1
                else:
                    niveles_detectados[nivel] = 1

            # Detectar Check Names desde "Lista de Servicios"
            if hoja_lista_servicios is not None:
                columna_check_name = hoja_lista_servicios.iloc[:, 0]  # Asumir que la primera columna contiene los Check Names
                check_names_por_nivel.setdefault(nivel, []).extend(columna_check_name.dropna().unique())
        except Exception as e:
            archivos_invalidos.append(archivo.name)

    # Mostrar los niveles detectados
    st.subheader("Niveles Detectados")
    if niveles_detectados:
        st.write(f"Se detectaron los siguientes niveles: {', '.join(niveles_detectados.keys())}")
    else:
        st.error("No se detectaron niveles válidos en los archivos cargados.")

    if archivos_invalidos:
        st.warning(f"Los siguientes archivos no pudieron procesarse: {', '.join(archivos_invalidos)}")

    # Solicitar la cantidad de proveedores para cada nivel detectado
    distribuccion_por_nivel = {}
    for nivel in niveles_detectados.keys():
        cantidad = st.number_input(f"Cantidad de proveedores para el nivel {nivel}", min_value=0, step=1, key=f"nivel_{nivel}")
        distribuccion_por_nivel[nivel] = cantidad

    # Determinar si se requiere distribución por región
    modelo_enriquecido = any([nivel in ["360", "180", "Digital"] for nivel in niveles_detectados.keys()])

    if modelo_enriquecido:
        st.subheader("Distribución por Región para Niveles Enriquecidos")
        distribuccion_por_region = {}
        regiones = ["Europa", "Africa", "LATAM", "Asia", "Oceania", "Norte America", "Centro America", "Oriente Medio", "ROW", "Tarifa Plana"]
        for region in regiones:
            porcentaje = st.number_input(f"Porcentaje de proveedores para {region} (en %)", min_value=0.0, max_value=100.0, step=0.1, key=f"region_{region}")
            distribuccion_por_region[region] = porcentaje
    else:
        distribuccion_por_region = None

        # Agregar un separador visual
    st.markdown("---")  # Este es el separador  

    # Ingresar el margen opcional
    margen_opcional = st.number_input("Margen deseado (opcional, en porcentaje)", min_value=0.0, step=0.1) / 100

    # Agregar un separador visual
    st.markdown("---")  # Este es el separador
    try:
        resultado = calcular_precio_minimo_con_tercera_fuente(
            cantidad_proveedores=sum(distribuccion_por_nivel.values()),
            distribuccion_por_nivel=distribuccion_por_nivel,
            distribuccion_por_region=distribuccion_por_region,
            margen_opcional=margen_opcional,
            check_names_por_nivel=check_names_por_nivel
        )
        st.session_state.resultado = resultado
    except ValueError as e:
        st.error(str(e))


    # Mostrar resultados si existen
    if 'resultado' in st.session_state:
        resultado = st.session_state.resultado

        st.subheader("Resultado del cálculo")

        # Mostrar resultados por nivel
        if 'Resultados por Nivel' in resultado:
            st.markdown("### Detalle por Nivel")
            df_resultados_nivel = pd.DataFrame.from_dict(resultado['Resultados por Nivel'], orient='index')
            st.table(df_resultados_nivel)

        # Mostrar precio mínimo por nivel
        if 'Precio mínimo por nivel' in resultado:
            st.markdown("### Precio mínimo por proveedor por nivel")
            df_precio_nivel = pd.DataFrame.from_dict(resultado['Precio mínimo por nivel'], orient='index', columns=['Precio mínimo por proveedor (€)'])
            st.table(df_precio_nivel)

        # Mostrar resumen general
        st.markdown("### Resumen General")
        for clave in [
            'Coste de Operaciones Total',
            'Coste de Tercera Fuente Financiera Total',
            'Coste de Compliance Total',
            'Coste Total',
            'Precio mínimo sugerido por proyecto',
            'Precio mínimo por proveedor'
        ]:
            if clave in resultado:
                st.write(f"**{clave}:** {resultado[clave]:,.2f} €")

        # Botón de descarga
        if st.button("📥 Descargar resultados en Excel", key="descargar_excel"):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_resultados_nivel.to_excel(writer, sheet_name='Resultados por Nivel')
                df_precio_nivel.to_excel(writer, sheet_name='Precio Mínimo por Nivel')
            output.seek(0)

            st.download_button(
                label="Haz clic para descargar el archivo Excel",
                data=output,
                file_name="resultado_precio_minimo.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )


