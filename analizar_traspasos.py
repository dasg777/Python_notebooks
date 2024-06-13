import xlwings as xw
import pandas as pd
import numpy as np
import os

def analizar_traspasos():

    # Construir la ruta completa al archivo de Excel
    file_path = r'C:\Users\diego.salinas\OneDrive - RODAMIENTOS Y ACCESORIOS SA DE CV\Documents\TI\Proyectos_BI\Almacen e inventarios\Traspasos\escenarios_traspasos.xlsm'
                 
    # Lee el libro de Excel
    bk = xw.Book(file_path)
    # Selecciona la hoja de trabajo
    sht = bk.sheets['tablas']

    # restablecer status
    sht.range("status").value = 'Procesando...'

    # Convierte los rangos de las tablas de Excel a DataFrames de pandas
    def table_to_df(table):
        table_range = table.data_body_range
        headers = table.header_row_range.value
        data = table_range.value
        return pd.DataFrame(data, columns=headers)

    # Necesidades de producto de las sucursales
    deficit_df = table_to_df(sht.tables['requerimientos'])
    # Inventario disponible de productos en otras sucursales distintas a la sucursal con deficit
    inventario_df = table_to_df(sht.tables['inventario'])
    # Matriz de traspasos, prioridad de la ruta entre sucursales, y elegibilidad de la sucursal
    prioridades_df = table_to_df(sht.tables['distancias'])
    # Valor para decidir a quien se la da prioridad como sucursal (ordenada segun ventas totales, de mayor a menor; revisar orden)
    orden_prioridad_df = table_to_df(sht.tables['prioridad_sucursal'])

    # Ordenar los déficits por prioridad de sucursal
    deficit_df = deficit_df.merge(orden_prioridad_df, on='sucursal')
    deficit_df = deficit_df.sort_values(by='orden')

    # /////////////////////////////////////////// Variables ////////////////////////////////////////////////////
    kms_maximos_distancia = sht.range("kmsMaximosDistancia").value # Establecer el valor máximo de kms de distancia entre sucursales
    max_exced_permitido_AB = float(sht.range("max_exced_permitido_AB").value) # Establecer el porcentaje máximo permitido que una sucursal puede tomar del excedente de un producto clas A o B
    max_inv_disp_C = float(sht.range("max_inv_disp_C").value) # Establecer el porcentaje máximo permitido que una sucursal puede tomar del inv disp de un producto clasificación C

    # el inventario disponible que una sucursal puede tomar de otra, de un produco clasificación L es 100%.

    # Filtrar matriz de traspasos, según kms máximos y elegibilidad
    prioridades_df = prioridades_df[(prioridades_df['prioridad'] <= kms_maximos_distancia) & (prioridades_df['elegible'] == 1)]

    # Ajustar los valores de inventario disponible y excedente según los porcentajes permitidos
    def ajustar_inventario(row):
        clasificacion = row['clasificacion']
        if clasificacion in ['A', 'B']:
            row['excedente_ajustado'] = row['excedente'] * max_exced_permitido_AB
            row['inventario_ajustado'] = 0
        elif clasificacion == 'C':
            row['inventario_ajustado'] = (row['inventario_disponible'] - row['excedente']) * max_inv_disp_C + row['excedente']
        return row

    inventario_df['excedente_ajustado'] = inventario_df['excedente']
    inventario_df['inventario_ajustado'] = inventario_df['inventario_disponible']

    inventario_df = inventario_df.apply(ajustar_inventario, axis=1)

    # Normalización de valores
    prioridad_max = prioridades_df['prioridad'].max()  
    clasificacion_dict = {'A': 1, 'B': 2, 'C': 3, 'L': 4}
    inventario_max = inventario_df['inventario_ajustado'].max()
    excedente_max = inventario_df['excedente_ajustado'].max()
    clas_max = max(clasificacion_dict.values())

    # Asignar los pesos específicos
    w_P = float(sht.range("w_P").value) # Prioridad geográfica
    w_C = float(sht.range("w_C").value) # Prioridad de clasificación ABC
    w_I = float(sht.range("w_I").value) # Prioridad por inventario disponible
    w_E = float(sht.range("w_E").value) # Prioridad por excedente
    # /////////////////////////////////////////// Variables ////////////////////////////////////////////////////

    def calcular_puntuacion(s_origen, s_destino, producto):
        # Obtener datos relevantes
        prioridad = prioridades_df[(prioridades_df['sucursal_origen'] == s_origen) & (prioridades_df['sucursal_destino'] == s_destino)]['prioridad'].values[0]
        clasificacion = inventario_df[(inventario_df['sucursal'] == s_origen) & (inventario_df['producto'] == producto)]['clasificacion'].values[0]
        inventario_ajustado = inventario_df[(inventario_df['sucursal'] == s_origen) & (inventario_df['producto'] == producto)]['inventario_ajustado'].values[0]
        excedente = inventario_df[(inventario_df['sucursal'] == s_origen) & (inventario_df['producto'] == producto)]['excedente_ajustado'].values[0]
        costo_unitario = inventario_df[(inventario_df['sucursal'] == s_origen) & (inventario_df['producto'] == producto)]['costo_unitario'].values[0]

        # Convertir clasificación a un valor numérico
        clasificacion_val = clasificacion_dict[clasificacion]

        # Normalización
        P_norm = (prioridad_max - prioridad + 1) / prioridad_max  # Prioridad geográfica menor es mejor (menos kms de distancia)
        C_norm = clasificacion_val / clas_max  # Máximo valor de clasificación ABC
        I_norm = inventario_ajustado / inventario_max
        E_norm = excedente / excedente_max

        # Calcular puntuación
        puntuacion = (w_P * P_norm) + (w_C * C_norm) + (w_I * I_norm) + (w_E * E_norm)
        return puntuacion, costo_unitario, clasificacion

    def satisfacer_deficit(deficit_row):
   
        sucursal_destino = deficit_row['sucursal']
        producto = deficit_row['producto']
        unidades_necesarias = deficit_row['unidades_necesarias']

        # Filtrar sucursales elegibles y calcular puntuaciones
        sucursales_origen = prioridades_df[(prioridades_df['sucursal_destino'] == sucursal_destino) & (prioridades_df['elegible'] == 1)]['sucursal_origen'].unique()

        puntuaciones = []

        for s_origen in sucursales_origen:
            if not inventario_df[(inventario_df['sucursal'] == s_origen) & (inventario_df['producto'] == producto)].empty:
                puntuacion, costo_unitario, clasificacion = calcular_puntuacion(s_origen, sucursal_destino, producto)
                puntuaciones.append((s_origen, puntuacion, costo_unitario, clasificacion))

        # Ordenar sucursales por puntuación descendente
        puntuaciones.sort(key=lambda x: x[1], reverse=True)

        # Realizar traspasos hasta satisfacer el déficit
        traspasos = []
        unidades_totales_traspasadas = 0

        for s_origen, _, costo_unitario, clasificacion in puntuaciones:
            if unidades_necesarias <= 0:
                break

            while unidades_necesarias > 0:
                excedente = inventario_df.loc[(inventario_df['sucursal'] == s_origen) & (inventario_df['producto'] == producto), 'excedente_ajustado'].values[0]
                inventario_ajustado = inventario_df.loc[(inventario_df['sucursal'] == s_origen) & (inventario_df['producto'] == producto), 'inventario_ajustado'].values[0]

                if excedente > 0:
                    unidades_traspaso = min(excedente, unidades_necesarias)
                    traspasos.append((s_origen, sucursal_destino, producto, unidades_traspaso, costo_unitario))
                    inventario_df.loc[(inventario_df['sucursal'] == s_origen) & (inventario_df['producto'] == producto), 'excedente_ajustado'] -= unidades_traspaso
                    inventario_df.loc[(inventario_df['sucursal'] == s_origen) & (inventario_df['producto'] == producto), 'inventario_ajustado'] -= unidades_traspaso
                    unidades_necesarias -= unidades_traspaso
                    unidades_totales_traspasadas += unidades_traspaso
                elif inventario_ajustado > 0:
                    unidades_traspaso = min(inventario_ajustado, unidades_necesarias)
                    traspasos.append((s_origen, sucursal_destino, producto, unidades_traspaso, costo_unitario))
                    inventario_df.loc[(inventario_df['sucursal'] == s_origen) & (inventario_df['producto'] == producto), 'inventario_ajustado'] -= unidades_traspaso
                    unidades_necesarias -= unidades_traspaso
                    unidades_totales_traspasadas += unidades_traspaso
                else:
                    break

                if unidades_traspaso == 0:
                    break

        deficit_residual = deficit_row['unidades_necesarias'] - unidades_totales_traspasadas
        return traspasos, deficit_residual

    # Aplicar el proceso para cada déficit
    todos_traspasos = []
    deficits_residuales = []

    total_deficits = len(deficit_df)

    for idx in range(total_deficits):
        row = deficit_df.iloc[idx]
        # Actualizar el progreso en Excel
        progress = f'{idx + 1} de {total_deficits}'
        sht.range("status").value = progress

        traspasos, deficit_residual = satisfacer_deficit(row)
        todos_traspasos.extend(traspasos)
        if deficit_residual > 0:
            deficits_residuales.append((row['sucursal'], row['producto'], deficit_residual))
    
    # Crear el DataFrame con los traspasos realizados
    traspasos_df = pd.DataFrame(todos_traspasos, columns=['sucursal_origen', 'sucursal_destino', 'producto', 'unidades_traspaso', 'costo_unitario'])
    traspasos_df = traspasos_df[traspasos_df['unidades_traspaso'] != 0]

    # Crear el DataFrame con los déficits residuales
    deficits_residuales_df = pd.DataFrame(deficits_residuales, columns=['sucursal_destino', 'producto', 'unidades_no_cubiertas'])

    # Agrupar por sucursal_origen, sucursal_destino y producto
    deficits_residuales_df = deficits_residuales_df.groupby(['sucursal_destino', 'producto']).agg({
        'unidades_no_cubiertas': 'sum'
    }).reset_index()

    # Agrupar por sucursal_origen, sucursal_destino y producto
    traspasos_df = traspasos_df.groupby(['sucursal_origen', 'sucursal_destino', 'producto']).agg({
        'unidades_traspaso': 'sum',
        'costo_unitario': 'mean'
    }).reset_index()

    deficits_residuales_df = deficits_residuales_df.sort_values(by=['sucursal_destino', 'producto'], ascending=[True, True])
    traspasos_df = traspasos_df.sort_values(by=['producto', 'sucursal_destino', 'sucursal_origen'], ascending=[True, True, True])

    # Función para escribir DataFrame en una tabla existente
    def df_to_table(sheet, table_name, df):
        table = sheet.tables[table_name]
        table_range = table.range
        header_range = table.header_row_range

        # Eliminar filas de la tabla
        data_body_range = table.data_body_range
        if data_body_range:
            data_body_range.delete()

        # Escribe los encabezados
        header_range[0, 0].expand('right').value = df.columns.tolist()

        # Escribe los datos
        if not df.empty:
            start_cell = header_range.offset(1, 0)
            start_cell.resize(df.shape[0], df.shape[1]).value = df.values.tolist()

    # Escribe deficit_head_df en la tabla 'recomendaciones'
    df_to_table(sht, 'recomendaciones', traspasos_df)
    df_to_table(sht, 'no_procesados', deficits_residuales_df)

    sht.range("status").value = 'Proceso terminado'

if __name__ == "__main__":
    xw.Book("escenarios_traspasos.xlsm").set_mock_caller()
    analizar_traspasos()