import streamlit as st
import unicodedata
import pandas as pd
from backend import calcular_precio_minimo_con_tercera_fuente
import io

# Función para limpiar el texto que pueda causar errores de codificación
def clean_text(text):
    if isinstance(text, str):
        return unicodedata.normalize("NFKD", text).encode("utf-8", "ignore").decode("utf-8")
    return text

# Selector de idioma
idioma = st.radio("Seleccione el idioma / Select language", ["Español", "English"], index=0)

texts = {
    "title": {"Español": "Cálculo de Coste con Tercera Fuente & Coste operacional", "English": "Cost Calculation with Third Party Source & Operational"},
    "upload": {"Español": "Sube hasta 5 archivos Excel con los servicios contratados", "English": "Upload up to 5 Excel files with contracted services"},
    "detected_levels": {"Español": "Niveles Detectados", "English": "Detected Levels"},
    "levels_found": {"Español": "Se detectaron los siguientes niveles", "English": "The following levels were detected"},
    "no_levels": {"Español": "No se detectaron niveles válidos en los archivos cargados.", "English": "No valid levels detected in uploaded files."},
    "invalid_files": {"Español": "Los siguientes archivos no pudieron procesarse", "English": "The following files could not be processed"},
    "num_suppliers": {"Español": "Cantidad de proveedores para el nivel", "English": "Number of suppliers for level"},
    "region_dist": {"Español": "Distribución por Región para Niveles Enriquecidos", "English": "Regional Distribution for Enriched Levels"},
    "percent_suppliers": {"Español": "Porcentaje de proveedores para", "English": "Percentage of suppliers for"},
    "margin": {"Español": "Margen deseado (opcional, en porcentaje). Se sugiere un 70 %", "English": "Desired profit margin (optional, %).70% is suggested."},
    "results": {"Español": "Resultado del cálculo", "English": "Calculation Results"},
    "detail_level": {"Español": "Detalle por Nivel", "English": "Level Details"},
    "min_price_level": {"Español": "Precio mínimo por proveedor por nivel", "English": "Minimum Price per Supplier by Level"},
    "summary": {"Español": "Resumen General", "English": "General Summary"},
    "download_btn": {"Español": "\ud83d\udcc5 Descargar resultados en Excel", "English": "\ud83d\udcc5 Download results in Excel"},
    "download_file": {"Español": "Haz clic para descargar el archivo Excel", "English": "Click to download the Excel file"},
    "cost_operations": {"Español": "Coste de Operaciones Total", "English": "Total Operations Cost"},
    "cost_third_party": {"Español": "Coste de Tercera Fuente Financiera Total", "English": "Total Third Party Financial Cost"},
    "cost_compliance": {"Español": "Coste de Compliance Total", "English": "Total Compliance Cost"},
    "cost_fixed": {"Español": "Coste Fijo Total", "English": "Total Fixed Cost"},
    "fixed_detail": {"Español": "Detalle de Coste Fijo", "English": "Fixed Cost Detail"},
    "setup": {"Español": "Setup", "English": "Setup"},
    "license": {"Español": "Licencia", "English": "License"},
    "integrations": {"Español": "Integraciones", "English": "Integrations"},
    "total_cost": {"Español": "Coste Total", "English": "Total Cost"},
    "min_price_project": {"Español": "Precio mínimo sugerido por proyecto", "English": "Suggested Minimum Price per Project"},
    "min_price_variable": {"Español": "Precio mínimo por proveedor (solo variable)", "English": "Minimum Price per Supplier (variable part only)"},
    "hub_selector": {"Español": "Seleccione el HUB", "English": "Select HUB"},
    "region_sum_error": {"Español": "La suma de porcentajes por región debe ser exactamente 100%", "English": "The sum of region percentages must be exactly 100%"},
    "client_selector": {"Español": "Seleccione el tipo de cliente", "English": "Select client type"},
    "include_integrations": {"Español": "Incluir Integraciones (SAP, etc)", "English": "Include Integrations (SAP, etc)"}
}

st.title(texts["title"][idioma])

selected_hub = st.selectbox(texts["hub_selector"][idioma], ["UKI & MEA", "SEU", "USCAN", "NEU", "LATAM", "APAC"])
selected_client = st.selectbox(texts["client_selector"][idioma], ["VIP High Spend", "High Growth Potential", "Medium Spend Medium Growth", "Medium Spend Low Growth", "Low Spend Low Growth"])
include_integrations = st.checkbox(texts["include_integrations"][idioma])

uploaded_files = st.file_uploader(texts["upload"][idioma], type=["xlsx"], accept_multiple_files=True)

if uploaded_files:
    detected_levels = {}
    check_names_by_level = {}
    invalid_files = []

    for file in uploaded_files:
        try:
            services_df = pd.read_excel(file, sheet_name=None, header=None)
            general_info = services_df.get("Información General")
            services_list = services_df.get("Lista de Servicios")

            if general_info is not None and len(general_info) > 4 and general_info.shape[1] > 1:
                level = str(general_info.iloc[4, 1]).strip()
                detected_levels[level] = detected_levels.get(level, 0) + 1

            if services_list is not None:
                check_column = services_list.iloc[:, 0]
                check_names_by_level.setdefault(level, []).extend(check_column.dropna().unique())
        except Exception as e:
            invalid_files.append(file.name)

    st.subheader(texts["detected_levels"][idioma])
    if detected_levels:
        st.write(f"{texts['levels_found'][idioma]}: {', '.join(detected_levels.keys())}")
    else:
        st.error(texts["no_levels"][idioma])

    if invalid_files:
        st.warning(f"{texts['invalid_files'][idioma]}: {', '.join(invalid_files)}")

    supplier_distribution = {}
    for level in detected_levels.keys():
        count = st.number_input(f"{texts['num_suppliers'][idioma]} {level}", min_value=0, step=1, key=f"level_{level}")
        supplier_distribution[level] = count

    enriched_model = any(level in ["360", "180", "Digital"] for level in detected_levels.keys())
    region_distribution = {}

    if enriched_model:
        st.subheader(texts["region_dist"][idioma])
        regions = [ "Tarifa Plana (ESP - PRT)","Europa (All Countries less ESP and PRT)", "Africa", "LATAM", "Asia", "Oceania", "Norte America", "Centro America", "Oriente Medio", "ROW"]
        for region in regions:
            percent = st.number_input(f"{texts['percent_suppliers'][idioma]} {region} (%)", min_value=0.0, max_value=100.0, step=0.1, key=f"region_{region}")
            region_distribution[region] = percent

        total_percent = sum(region_distribution.values())
        if abs(total_percent - 100) > 0.01:
            st.error(texts["region_sum_error"][idioma])
            region_distribution = None

    st.markdown("---")
    optional_margin = st.number_input(texts["margin"][idioma], min_value=0.0, step=0.1) / 100
    st.markdown("---")

    if sum(supplier_distribution.values()) > 0 and (region_distribution is not None or not enriched_model):
        try:
            result = calcular_precio_minimo_con_tercera_fuente(
                cantidad_proveedores=sum(supplier_distribution.values()),
                distribuccion_por_nivel=supplier_distribution,
                distribuccion_por_region=region_distribution,
                margen_opcional=optional_margin,
                check_names_por_nivel=check_names_by_level,
                tipo_cliente=selected_client,
                incluye_integraciones=include_integrations
            )
            st.session_state.result = result
        except ValueError as e:
            st.error(str(e))

    if 'result' in st.session_state:
        result = st.session_state.result
        st.subheader(texts["results"][idioma])

        if 'Resultados por Nivel' in result:
            df_level = pd.DataFrame.from_dict(result['Resultados por Nivel'], orient='index')
            if not df_level.empty:
                st.markdown(f"### {texts['detail_level'][idioma]}")
                st.table(df_level)

        compliance_data = {
            nivel: datos.get("Coste de Compliance", 0)
            for nivel, datos in result["Resultados por Nivel"].items()
            if datos.get("Coste de Compliance", 0) > 0
        }

        if compliance_data:
            df_compliance = pd.DataFrame.from_dict(compliance_data, orient='index', columns=["Coste de Compliance (€)"])
            st.markdown("#### Niveles con coste de Compliance aplicado")
            st.table(df_compliance)

        if 'Precio mínimo por nivel' in result:
            df_price = pd.DataFrame.from_dict(result['Precio mínimo por nivel'], orient='index', columns=[texts['min_price_level'][idioma] + " (€)"])
            if not df_price.empty:
                st.markdown(f"### {texts['min_price_level'][idioma]}")
                st.table(df_price)

        st.markdown(f"### {texts['summary'][idioma]}")

        st.write(f"**{texts['cost_operations'][idioma]}:** {result.get('Coste de Operaciones Total', 0):,.2f} €")
        st.write(f"**{texts['cost_third_party'][idioma]}:** {result.get('Coste de Tercera Fuente Financiera Total', 0):,.2f} €")
        st.write(f"**{texts['cost_compliance'][idioma]}:** {result.get('Coste de Compliance Total', 0):,.2f} €")
        st.write(f"**{texts['cost_fixed'][idioma]}:** {result.get('Coste Fijo Total', 0):,.2f} €")
        st.write(f"**{texts['total_cost'][idioma]}:** {result.get('Coste Total', 0):,.2f} €")
        st.write(f"**{texts['min_price_project'][idioma]}:** {result.get('Precio mínimo sugerido por proyecto', 0):,.2f} €")
        st.write(f"**{texts['min_price_variable'][idioma]}:** {result.get('Precio mínimo por proveedor (solo variable)', 0):,.2f} €")

        st.markdown(f"### {texts['fixed_detail'][idioma]}")
        detalle = result.get('Detalle Coste Fijo', {})
        st.write(f"**{texts['setup'][idioma]}:** {detalle.get('Setup', 0):,.2f} €")
        st.write(f"**{texts['license'][idioma]}:** {detalle.get('Licencia', 0):,.2f} €")
        st.write(f"**{texts['integrations'][idioma]}:** {detalle.get('Integraciones', 0):,.2f} €")

    download_text = clean_text(texts["download_btn"][idioma])
    if st.button(download_text, key="download_excel"):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            if not df_level.empty:
                df_level.to_excel(writer, sheet_name='Level Details')
            if not df_price.empty:
                df_price.to_excel(writer, sheet_name='Minimum Price by Level')
            if 'DataFrame Coste Fijo' in result:
                result['DataFrame Coste Fijo'].to_excel(writer, sheet_name='Coste Fijo')
        output.seek(0)

        st.download_button(
            label=clean_text(texts["download_file"][idioma]),
            data=output,
            file_name="minimum_price_result.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )




