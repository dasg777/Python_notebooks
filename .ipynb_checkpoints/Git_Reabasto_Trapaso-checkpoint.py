import requests
import os

def download_and_run_github_script():
      # URL del archivo en GitHub
    github_url = "https://raw.githubusercontent.com/dasg777/Python_notebooks/main/analizar_traspasos.py"
    
    # Ruta local donde se guardará el archivo descargado
    local_path = r"C:\Temp\archivo.py"
    
    try:
        # Descargar el archivo de GitHub
        response = requests.get(github_url)
        if response.status_code == 200:
            with open(local_path, 'wb') as file:
                file.write(response.content)
            print("Archivo descargado exitosamente.")
            
            # Ejecutar el archivo descargado
            os.system(f'python {local_path}')
        else:
            print(f"Error al descargar el archivo: {response.status_code}")
    finally:
        # Eliminar el archivo descargado
        if os.path.exists(local_path):
            os.remove(local_path)
            print("Archivo eliminado después de la ejecución.")

if __name__ == "__main__":
    download_and_run_github_script()

# import requests
# import os
# import logging


# def download_and_run_github_script():
    
#     # Configurar logging
#     logging.basicConfig(filename='logfile.log', level=logging.DEBUG, 
#     format='%(asctime)s:%(levelname)s:%(message)s')

#     # URL del archivo en GitHub
#     github_url = "https://raw.githubusercontent.com/dasg777/Python_notebooks/main/analizar_traspasos.py"
#     logging.debug(f"URL del archivo en GitHub: {github_url}")

#     # Obtener el nombre del usuario de Windows
#     user_name = os.getlogin()
#     logging.debug(f"Nombre del usuario de Windows: {user_name}")

#     # Ruta local donde se guardará el archivo temporal descargado
#     local_path = f'C:\\Users\\{user_name}\\OneDrive - RODAMIENTOS Y ACCESORIOS SA DE CV\\Documents\\Analisis_Traspasos\\archivo.py'
#     logging.debug(f"Ruta local para guardar el archivo: {local_path}")

#     try:
#         # Descargar el archivo de GitHub
#         response = requests.get(github_url)
#         if response.status_code == 200:
#             with open(local_path, 'wb') as file:
#                 file.write(response.content)
#             logging.info("Archivo descargado exitosamente.")
            
#             # Ejecutar el archivo descargado
#             os.system(f'python {local_path}')
#             logging.info(f"Archivo ejecutado: {local_path}")
#         else:
#             logging.error(f"Error al descargar el archivo: {response.status_code}")
#     except Exception as e:
#         logging.error(f"Exception occurred: {e}")
#     finally:
#         # Eliminar el archivo descargado
#         if os.path.exists(local_path):
#             os.remove(local_path)
#             logging.info("Archivo eliminado después de la ejecución.")

# if __name__ == "__main__":
#     download_and_run_github_script()
