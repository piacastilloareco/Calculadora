import pandas as pd

def calcular_precio_minimo_con_tercera_fuente(cantidad_proveedores, distribuccion_por_nivel, distribuccion_por_region=None, margen_opcional=None, check_names_por_nivel=None, tipo_cliente=None, incluye_integraciones=False):
    
    costes_fijos_clientes = {
        "VIP High Spend": {"Setup": 9500, "Licencia": 29000, "Integraciones": 15000},
        "High Growth Potential": {"Setup": 9500, "Licencia": 25000, "Integraciones": 15000},
        "Medium Spend Medium Growth": {"Setup": 9500, "Licencia": 22000, "Integraciones": 12000},
        "Medium Spend Low Growth": {"Setup": 9500, "Licencia": 19000, "Integraciones": 12000},
        "Low Spend Low Growth": {"Setup": 9500, "Licencia": 15000, "Integraciones": 10000},
    }

    coste_fijo_detalle = {"Setup": 0, "Licencia": 0, "Integraciones": 0}
    if tipo_cliente in costes_fijos_clientes:
        detalle = costes_fijos_clientes[tipo_cliente]
        coste_fijo_detalle["Setup"] = detalle["Setup"]
        coste_fijo_detalle["Licencia"] = detalle["Licencia"]
        coste_fijo_detalle["Integraciones"] = detalle["Integraciones"] if incluye_integraciones else 0
    coste_fijo = sum(coste_fijo_detalle.values())

    coste_por_proveedor_nivel = {"360": 25.97, "180": 11.41, "Basic": 2.32, "Elementary": 0.54, "Digital": 0.27}
    coste_por_region = {"Europa": 35.26, "Africa": 46.9, "LATAM": 51.64, "Asia": 69.99, "Oceania": 46, "Norte America": 30, "Centro America": 60.75, "Oriente Medio": 59.95, "ROW": 32.43, "Tarifa Plana": 0}
    check_names_fuente_compliance = {"Onlycompany", "Onlycompany + Politicas", "Stakeholders", "Stakeholders + Politicas", "Stakeholders + Peps y Sips", "Stakeholders + Politicas + Peps y Sips"}
    check_names_enriquecimiento = {"Modelo Completo Enriquecido (Con Documento)", "Modelo Reducido Enriquecido (Con Documento)"}

    resultados_por_nivel = {}
    coste_operaciones = 0
    coste_tercera_fuente = 0

    # Primer loop: operaciones y tercera fuente
    for nivel, cantidad in distribuccion_por_nivel.items():
        if cantidad > 0:
            coste_op = coste_por_proveedor_nivel.get(nivel, 0) * cantidad
            coste_operaciones += coste_op

            tiene_enriquecimiento = check_names_por_nivel and nivel in check_names_por_nivel and any(chk in check_names_enriquecimiento for chk in check_names_por_nivel[nivel])
            coste_tf = 0
            if distribuccion_por_region and tiene_enriquecimiento:
                if sum(distribuccion_por_region.values()) > 100:
                    raise ValueError("La suma de porcentajes por región excede 100%")
                for region, proporcion in distribuccion_por_region.items():
                    coste_por_prov = coste_por_region.get(region, 0)
                    coste_tf += coste_por_prov * (cantidad * (proporcion / 100))
            coste_tercera_fuente += coste_tf

            resultados_por_nivel[nivel] = {
                "Coste de Operaciones": round(coste_op, 2),
                "Coste de Tercera Fuente": round(coste_tf, 2),
                "Coste de Compliance": 0,  # se completa después
                "Coste Total": 0
            }

    # Segundo loop: compliance total y distribución proporcional
    compliance_por_nivel = {}
    total_proveedores_compliance = 0

    for nivel, cantidad in distribuccion_por_nivel.items():
        if cantidad > 0 and check_names_por_nivel and nivel in check_names_por_nivel and any(chk in check_names_fuente_compliance for chk in check_names_por_nivel[nivel]):
            compliance_por_nivel[nivel] = cantidad * 5
            total_proveedores_compliance += cantidad
        else:
            compliance_por_nivel[nivel] = 0

    coste_compliance = sum(compliance_por_nivel.values())
    if coste_compliance < 5000 and total_proveedores_compliance > 0:
        for nivel in compliance_por_nivel:
            if compliance_por_nivel[nivel] > 0:
                compliance_por_nivel[nivel] = round(5000 * (distribuccion_por_nivel[nivel] / total_proveedores_compliance), 2)
        coste_compliance = 5000

    # Actualización de resultados finales
    for nivel in resultados_por_nivel:
        compliance_nivel = compliance_por_nivel.get(nivel, 0)
        total_nivel = (
            resultados_por_nivel[nivel]["Coste de Operaciones"] +
            resultados_por_nivel[nivel]["Coste de Tercera Fuente"] +
            compliance_nivel
        )
        resultados_por_nivel[nivel]["Coste de Compliance"] = round(compliance_nivel, 2)
        resultados_por_nivel[nivel]["Coste Total"] = round(total_nivel, 2)

    coste_total = coste_operaciones + coste_tercera_fuente + coste_compliance + coste_fijo
    precio_minimo = coste_total * (1 + margen_opcional) if margen_opcional is not None else coste_total

    coste_total_sin_fijo = coste_operaciones + coste_tercera_fuente + coste_compliance
    precio_minimo_por_proveedor = (coste_total_sin_fijo * (1 + margen_opcional) if margen_opcional is not None else coste_total_sin_fijo) / cantidad_proveedores if cantidad_proveedores > 0 else 0

    precio_minimo_por_nivel = {}
    for nivel, resultado in resultados_por_nivel.items():
        cantidad_nivel = distribuccion_por_nivel.get(nivel, 0)
        if cantidad_nivel > 0:
            precio_nivel = resultado["Coste Total"] * (1 + margen_opcional) if margen_opcional is not None else resultado["Coste Total"]
            precio_minimo_por_nivel[nivel] = round(precio_nivel / cantidad_nivel, 2)

    df_coste_fijo = pd.DataFrame.from_dict(coste_fijo_detalle, orient="index", columns=["Coste (€)"])

    return {
        "Resultados por Nivel": resultados_por_nivel,
        "Coste de Operaciones Total": round(coste_operaciones, 2),
        "Coste de Tercera Fuente Financiera Total": round(coste_tercera_fuente, 2),
        "Coste de Compliance Total": round(coste_compliance, 2),
        "Coste Fijo Total": round(coste_fijo, 2),
        "Detalle Coste Fijo": coste_fijo_detalle,
        "Coste Total": round(coste_total, 2),
        "Precio mínimo sugerido por proyecto": round(precio_minimo, 2),
        "Precio mínimo por proveedor (solo variable)": round(precio_minimo_por_proveedor, 2),
        "Precio mínimo por nivel": precio_minimo_por_nivel,
        "DataFrame Coste Fijo": df_coste_fijo
    }





 
