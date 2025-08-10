import pandas as pd

def calcular_precio_minimo_con_tercera_fuente(cantidad_proveedores, distribuccion_por_nivel,
                                              distribuccion_por_region=None, margen_opcional=None,
                                              check_names_por_nivel=None, tipo_cliente=None,
                                              incluye_integraciones=False):

    # Validación margen (margen sobre venta, no markup)
    if margen_opcional is not None:
        if not (0 <= margen_opcional < 1):
            raise ValueError("margen_opcional debe estar entre 0 y 1 (ej. 0.4 = 40%).")

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
    coste_por_region = {"Europa (All Countries less ESP and PRT)": 35.26, "Africa": 46.9, "LATAM": 51.64,
                        "Asia": 69.99, "Oceania": 46, "Norte America": 30, "Centro America": 60.75,
                        "Oriente Medio": 59.95, "ROW": 32.43, "Tarifa Plana (ESP - PRT)": 0}
    check_names_enriquecimiento = {
        "Modelo Completo Enriquecido (Con Documento)",
        "Modelo Reducido Enriquecido (Con Documento)"
    }

    resultados_por_nivel = {}
    coste_operaciones = 0
    coste_tercera_fuente = 0

    for nivel, cantidad in distribuccion_por_nivel.items():
        if cantidad > 0:
            coste_op = coste_por_proveedor_nivel.get(nivel, 0) * cantidad
            coste_operaciones += coste_op

            tiene_enriquecimiento = (
                check_names_por_nivel and nivel in check_names_por_nivel
                and any(chk in check_names_enriquecimiento for chk in check_names_por_nivel[nivel])
            )
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
                "Coste de Compliance": 0,
                "Coste Total": 0
            }

    # --- Compliance (lógica Excel) ---
    avg_llamadas_por_tipo = {
        "Onlycompany": 1,
        "Onlycompany + Politicas": 1,
        "Stakeholders": 1,
        "Stakeholders + Politicas": 1,
        "Stakeholders + Peps y Sips": 6,
        "Stakeholders + Politicas + Peps y Sips": 6,
    }

    factor_precio_por_tipo = {
        "Onlycompany": 1,
        "Onlycompany + Politicas": 1,
        "Stakeholders": 3,
        "Stakeholders + Politicas": 3,
        "Stakeholders + Peps y Sips": 6,
        "Stakeholders + Politicas + Peps y Sips": 6,
    }

    proveedores_por_tipo = {}
    tipo_elegido_por_nivel = {}

    for nivel, cantidad in distribuccion_por_nivel.items():
        if cantidad <= 0:
            continue
        feats = (check_names_por_nivel or {}).get(nivel, [])
        feats_validas = [f for f in feats if f in avg_llamadas_por_tipo]
        tipo = max(feats_validas, key=lambda f: factor_precio_por_tipo[f]) if feats_validas else None
        tipo_elegido_por_nivel[nivel] = tipo
        if tipo:
            proveedores_por_tipo[tipo] = proveedores_por_tipo.get(tipo, 0) + cantidad

    llamadas_totales = sum(cant * avg_llamadas_por_tipo[t] for t, cant in proveedores_por_tipo.items())
    coste_por_llamada = round(1661.9 * (llamadas_totales ** -0.738), 8) if llamadas_totales > 0 else 0.0
    precio_unitario_por_tipo = {t: round(factor_precio_por_tipo[t] * coste_por_llamada, 2) for t in proveedores_por_tipo}
    coste_por_tipo = {t: round(precio_unitario_por_tipo[t] * proveedores_por_tipo[t], 2) for t in proveedores_por_tipo}
    coste_compliance = round(sum(coste_por_tipo.values()), 2)

    for nivel in resultados_por_nivel:
        cantidad_nivel = distribuccion_por_nivel.get(nivel, 0)
        tipo = tipo_elegido_por_nivel.get(nivel)
        compliance_nivel = round((precio_unitario_por_tipo.get(tipo, 0) * cantidad_nivel), 2) if cantidad_nivel > 0 else 0

        total_nivel = (
            resultados_por_nivel[nivel]["Coste de Operaciones"]
            + resultados_por_nivel[nivel]["Coste de Tercera Fuente"]
            + compliance_nivel
        )
        resultados_por_nivel[nivel]["Coste de Compliance"] = compliance_nivel
        resultados_por_nivel[nivel]["Coste Total"] = round(total_nivel, 2)

    coste_total_sin_fijo = coste_operaciones + coste_tercera_fuente + coste_compliance
    coste_total = coste_total_sin_fijo + coste_fijo

    if margen_opcional is not None:
        precio_minimo = coste_total / (1 - margen_opcional)
    else:
        precio_minimo = coste_total

    if margen_opcional is not None:
        precio_minimo_por_proveedor = coste_total_sin_fijo / (1 - margen_opcional)
    else:
        precio_minimo_por_proveedor = coste_total_sin_fijo
    precio_minimo_por_proveedor = (precio_minimo_por_proveedor / cantidad_proveedores) if cantidad_proveedores > 0 else 0

    precio_minimo_por_nivel = {}
    for nivel, resultado in resultados_por_nivel.items():
        cantidad_nivel = distribuccion_por_nivel.get(nivel, 0)
        if cantidad_nivel > 0:
            precio_nivel = (resultado["Coste Total"] / (1 - margen_opcional)) if margen_opcional is not None else resultado["Coste Total"]
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



 



