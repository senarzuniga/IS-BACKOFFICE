#!/usr/bin/env python3
"""
Script para abrir IS-BACKOFFICE con búsqueda automática de puerto libre
Uso: python abrir_app.py
"""

import subprocess
import socket
import sys
import os
import webbrowser
from pathlib import Path

# Configuración
PUERTO_INICIO = 8511
PUERTO_FIN = 8530
ARCHIVO_APP = "streamlit_app.py"

def es_puerto_libre(puerto):
    """Verifica si un puerto está disponible"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        resultado = sock.connect_ex(('localhost', puerto))
        return resultado != 0

def buscar_puerto_libre():
    """Busca el primer puerto libre en el rango especificado"""
    for puerto in range(PUERTO_INICIO, PUERTO_FIN + 1):
        if es_puerto_libre(puerto):
            return puerto
    return None

def obtener_python_ejecutable():
    """Obtiene la ruta del ejecutable de Python"""
    # Verificar si estamos en entorno virtual
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        # Estamos en un entorno virtual
        if sys.platform == "win32":
            python_path = Path(sys.prefix) / "Scripts" / "python.exe"
        else:
            python_path = Path(sys.prefix) / "bin" / "python"
        
        if python_path.exists():
            return str(python_path)
    
    # Si no, usar el python actual
    return sys.executable

def main():
    """Función principal"""
    print("=" * 50)
    print("   IS-BACKOFFICE - Lanzador Automático")
    print("=" * 50)
    print()
    
    # Verificar que el archivo de la app existe
    if not Path(ARCHIVO_APP).exists():
        print(f"❌ Error: No se encuentra {ARCHIVO_APP}")
        print(f"   Asegúrate de ejecutar este script desde la carpeta del proyecto")
        sys.exit(1)
    
    # Buscar puerto libre
    print(f"🔍 Buscando puerto libre entre {PUERTO_INICIO} y {PUERTO_FIN}...")
    puerto = buscar_puerto_libre()
    
    if puerto is None:
        print(f"❌ No se encontró un puerto libre en el rango especificado")
        print(f"   Puedes modificar PUERTO_INICIO y PUERTO_FIN en el script")
        sys.exit(1)
    
    print(f"✅ Puerto libre encontrado: {puerto}")
    
    # Construir URL
    url = f"http://localhost:{puerto}"
    print(f"🌐 Abriendo navegador en: {url}")
    
    # Abrir navegador
    webbrowser.open(url)
    
    # Obtener Python ejecutable
    python_cmd = obtener_python_ejecutable()
    print(f"🐍 Usando Python: {python_cmd}")
    
    # Comando para ejecutar Streamlit
    cmd = [
        python_cmd, "-m", "streamlit", "run", ARCHIVO_APP,
        "--server.port", str(puerto),
        "--server.address", "localhost",
        "--server.fileWatcherType", "none"
    ]
    
    print("🚀 Iniciando Streamlit...")
    print("-" * 50)
    print()
    
    # Ejecutar Streamlit
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n\n🛑 Servidor detenido por el usuario")
    except Exception as e:
        print(f"\n❌ Error al ejecutar Streamlit: {e}")
        sys.exit(1)
    
    print()
    print("=" * 50)
    print("   Aplicación finalizada")
    print("=" * 50)

if __name__ == "__main__":
    main()