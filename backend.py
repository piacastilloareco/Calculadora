import pandas as pd

def calcular_precio_minimo_con_tercera_fuente(cantidad_proveedores, distribuccion_por_nivel, distribuccion_por_region=None, margen_opcional=None, check_names_por_nivel=None):
    """
    Función para calcular el precio mínimo considerando:
    - Coste de operaciones: Depende del nivel y la cantidad total de proveedores.
    - Coste de tercera fuente: Aplica solo si el modelo incluye enriquecimiento y depende de la región y la cantidad de proveedores.
    - Coste de Compliance: Aplica si los Check Names relevantes están presentes por nivel.

    Parámetros:
    - cantidad_proveedores: Cantidad total de proveedores.
    - distribuccion_por_nivel: Diccionario con la distribución de cantidad de proveedores por nivel.
    - distribuccion_por_region: Diccionario con la distribución de cantidad de proveedores por región.
    - margen_opcional: Margen deseado opcional.
    - check_names_por_nivel: Diccionario con los Check Names detectados para cada nivel.

    Retorna:
    - Un diccionario con el coste total y desgloses por nivel.
    """
    # Reglas de negocio: Coste por proveedor según el nivel
    coste_por_proveedor_nivel = {
        '360': 25.97,
        '180': 11.41,
        'Basic': 2.32,
        'Elementary': 0.54,
        'Digital': 0.27,
    }

    # Costes por región
    coste_por_region = {
        'Europa': 35.26,
        'Africa': 46.9,
        'LATAM': 51.64,
        'Asia': 69.99,
        'Oceania': 46,
        'Norte America': 30,
        'Centro America': 60.75,
        'Oriente Medio': 59.95,
        'ROW': 32.43,
        'Tarifa Plana': 0  # Tarifa plana siempre tiene coste 0
    }

    # Check Names que habilitan la Fuente Compliance
    check_names_fuente_compliance = {
        "Onlycompany",
        "Onlycompany + Politicas",
        "Stakeholders",
        "Stakeholders + Politicas",
        "Stakeholders + Peps y Sips",
        "Stakeholders + Politicas + Peps y Sips"
    }

    # Check Names que habilitan el enriquecimiento
    check_names_enriquecimiento = {
        "Modelo Completo Enriquecido (Con Documento)",
        "Modelo Reducido Enriquecido (Con Documento)"
    }

    # Inicializar resultados desagregados
    resultados_por_nivel = {}

    # Calcular los costes por nivel
    coste_operaciones = 0
    coste_tercera_fuente = 0
    coste_compliance = 0

    for nivel, cantidad in distribuccion_por_nivel.items():
        if cantidad > 0:  # Solo procesar niveles con proveedores
            # Coste de operaciones para el nivel actual
            coste_nivel_operaciones = coste_por_proveedor_nivel.get(nivel, 0) * cantidad
            coste_operaciones += coste_nivel_operaciones

            # Determinar si el nivel tiene enriquecimiento
            tiene_enriquecimiento = (
                check_names_por_nivel 
                and nivel in check_names_por_nivel 
                and any(check_name in check_names_enriquecimiento for check_name in check_names_por_nivel[nivel])
            )

            # Coste de tercera fuente para el nivel actual
            coste_nivel_tercera_fuente = 0
            if distribuccion_por_region and tiene_enriquecimiento:
                for region, proporcion in distribuccion_por_region.items():
                    coste_por_proveedor = coste_por_region.get(region, 0)
                    coste_nivel_tercera_fuente += coste_por_proveedor * (cantidad * (proporcion / 100))
            coste_tercera_fuente += coste_nivel_tercera_fuente

            # Coste de Compliance para el nivel actual
            coste_nivel_compliance = 0
            if check_names_por_nivel and nivel in check_names_por_nivel:
                if any(check_name in check_names_fuente_compliance for check_name in check_names_por_nivel[nivel]):
                    coste_nivel_compliance = cantidad * 5  # Coste fijo de 5 euros por proveedor
            coste_compliance += coste_nivel_compliance

            # Guardar resultados desagregados por nivel
            resultados_por_nivel[nivel] = {
                'Coste de Operaciones': round(coste_nivel_operaciones, 2),
                'Coste de Tercera Fuente': round(coste_nivel_tercera_fuente, 2),
                'Coste de Compliance': round(coste_nivel_compliance, 2),
                'Coste Total': round(coste_nivel_operaciones + coste_nivel_tercera_fuente + coste_nivel_compliance, 2)
            }

    # Calcular el coste total
    coste_total = coste_operaciones + coste_tercera_fuente + coste_compliance

    # Si se proporciona un margen, calcular el precio mínimo con margen
    if margen_opcional is not None:
        precio_minimo = coste_total * (1 + margen_opcional)
    else:
        precio_minimo = coste_total

    # Calcular el precio mínimo por proveedor
    precio_minimo_por_proveedor = precio_minimo / cantidad_proveedores if cantidad_proveedores > 0 else 0

    # Depuración
    print("Check Names por nivel:", check_names_por_nivel)
    print("Depuración de resultados por nivel:", resultados_por_nivel)

    # Retornar el resultado
    return {
        'Resultados por Nivel': resultados_por_nivel,
        'Coste de Operaciones Total': round(coste_operaciones, 2),
        'Coste de Tercera Fuente Financiera Total': round(coste_tercera_fuente, 2),
        'Coste de Compliance Total': round(coste_compliance, 2),
        'Coste Total': round(coste_total, 2),
        'Precio mínimo sugerido por proyecto': round(precio_minimo, 2),
        'Precio mínimo por proveedor': round(precio_minimo_por_proveedor, 2)
    }


 
