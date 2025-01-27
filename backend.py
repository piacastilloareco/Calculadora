import pandas as pd

def calcular_precio_minimo_con_tercera_fuente(archivo_excel, cantidad_proveedores, nivel, distribuccion_por_pais, margen_opcional=None):
    """
    Función para calcular el precio mínimo considerando:
    - Coste de operaciones: Depende del nivel y la cantidad total de proveedores.
    - Coste de tercera fuente: Aplica solo si el modelo incluye enriquecimiento y depende del país y la cantidad de proveedores.
    
    Parámetros:
    - archivo_excel: Ruta del archivo Excel con los servicios contratados.
    - cantidad_proveedores: Cantidad total de proveedores.
    - nivel: Nivel del cliente (360, 180, basic, Elementary, Digital).
    - distribuccion_por_pais: Diccionario con la distribución de cantidad de proveedores por país (ej. {'ESP': 50, 'PRT': 30}).
    - margen_opcional: Margen deseado opcional (ej. 0.2 para 20%).
    
    Retorna:
    - Un diccionario con el coste total, el precio mínimo sugerido y el precio mínimo por proveedor.
    """
    # Reglas de negocio: Coste por proveedor según el nivel
    coste_por_proveedor_nivel = {
        '360': 25.97,
        '180': 11.41,
        'basic': 2.32,
        'Elementary': 0.54,
        'Digital': 0.27
    }

    # Leer el archivo Excel para identificar el modelo
    servicios_df = pd.read_excel(archivo_excel)
    modelos_enriquecidos = ['Modelo Reducido Enriquecido (Con documento)', 'Modelo Reducido Enriquecido (Con Documento)']
    modelo_enriquecido = servicios_df['Check Name'].isin(modelos_enriquecidos).any()

    # Cargar el coste de tercera fuente desde un DataFrame o archivo CSV externo
    coste_tercera_fuente_df = pd.read_excel(r"C:\Users\Pia\OneDrive - GoSupply Advanced Applications SL\Escritorio\Automatización de procesos\Calculadora\COSTE_3_fuente.xlsx")
    
    # Calcular el número restante de proveedores y asignarlo a "RoW" si no se alcanza la cantidad total
    total_asignado = sum(distribuccion_por_pais.values())
    proveedores_por_pais = distribuccion_por_pais.copy()
    if total_asignado < cantidad_proveedores:
        proveedores_por_pais['RoW'] = cantidad_proveedores - total_asignado

    # Calcular el coste de tercera fuente solo si el modelo es enriquecido
    coste_tercera_fuente = 0
    if modelo_enriquecido:
        for pais, cantidad in proveedores_por_pais.items():
            coste_por_proveedor = coste_tercera_fuente_df.loc[coste_tercera_fuente_df['Country'] == pais, 'Coste por Proveedor (€)'].values
            if len(coste_por_proveedor) > 0:
                coste_tercera_fuente += coste_por_proveedor[0] * cantidad
    
    # Calcular el coste de operaciones
    coste_operaciones = coste_por_proveedor_nivel.get(str(nivel), 0) * cantidad_proveedores

    # Calcular el coste total
    coste_total = coste_operaciones + coste_tercera_fuente
    
    # Si se proporciona un margen, calcular el precio mínimo con margen
    if margen_opcional is not None:
        precio_minimo = coste_total * (1 + margen_opcional)
    else:
        precio_minimo = coste_total

    # Calcular el precio mínimo por proveedor
    precio_minimo_por_proveedor = precio_minimo / cantidad_proveedores if cantidad_proveedores > 0 else 0
    
    # Retornar el resultado
    return {
        'Coste de Operaciones': round(coste_operaciones, 2),
        'Coste de Tercera Fuente': round(coste_tercera_fuente, 2),
        'Coste total': round(coste_total, 2),
        'Precio mínimo sugerido por proyecto': round(precio_minimo, 2),
        'Precio mínimo por proveedor': round(precio_minimo_por_proveedor, 2)
    }

# Chatbot interactivo
if __name__ == "__main__":
    print("Bienvenido al chatbot de cálculo de precio mínimo")
    archivo_excel = input("Por favor, ingrese la ruta del archivo Excel con los servicios contratados: ")
    cantidad_proveedores = int(input("Ingrese la cantidad total de proveedores: "))
    nivel = input("Ingrese el nivel del cliente (360, 180, basic, Elementary, Digital): ")
    num_paises = int(input("¿Cuántos países quiere ingresar para la distribución de proveedores?: "))
    distribuccion_por_pais = {}
    for _ in range(num_paises):
        pais = input("Ingrese el código del país (ej. ESP, PRT): ")
        while True:
            cantidad = input(f"Ingrese la cantidad de proveedores para {pais}: ")
            if cantidad.isdigit():
                cantidad = int(cantidad)
                break
            else:
                print("Por favor, ingrese un número válido.")
        distribuccion_por_pais[pais] = cantidad

    total_asignado = sum(distribuccion_por_pais.values())
    if total_asignado < cantidad_proveedores:
        distribuccion_por_pais['RoW'] = cantidad_proveedores - total_asignado

    margen_opcional = input("Ingrese el margen deseado (opcional, presione Enter para omitir): ")
    margen_opcional = float(margen_opcional) if margen_opcional else None

    resultado = calcular_precio_minimo_con_tercera_fuente(
        archivo_excel=archivo_excel,
        cantidad_proveedores=cantidad_proveedores,
        nivel=nivel,
        distribuccion_por_pais=distribuccion_por_pais,
        margen_opcional=margen_opcional
    )

    print("\nResultado del cálculo:")
    for clave, valor in resultado.items():
        print(f"{clave}: {valor}")