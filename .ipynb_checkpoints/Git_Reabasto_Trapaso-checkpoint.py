import requests
import os

def download_and_run_github_script_analizar_traspasos():
      # URL del archivo en GitHub
    github_url = "https://raw.githubusercontent.com/dasg777/Python_notebooks/main/traspasos_reabasto.py"
    
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
    download_and_run_github_script_analizar_traspasos()
