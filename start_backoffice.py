#!/usr/bin/env python3
"""
Lanzador universal para IS-BACKOFFICE
Ejecutar cada manana con: python start_backoffice.py
"""

import os
import sys
import subprocess
import webbrowser
import socket
import time
from pathlib import Path

# Configuracion
PORT = 8508
HOST = "localhost"
PROJECT_DIR = Path(__file__).parent.absolute()


def print_colored(text, color="green"):
    """Imprime texto con color si es posible"""
    colors = {
        "green": "\033[92m",
        "red": "\033[91m",
        "yellow": "\033[93m",
        "cyan": "\033[96m",
        "reset": "\033[0m",
    }
    if sys.platform == "win32":
        print(text)
    else:
        print(f"{colors.get(color, '')}{text}{colors['reset']}")


def find_python():
    """Encuentra el ejecutable de Python"""
    # Buscar en entorno virtual
    venv_python = PROJECT_DIR / ".venv" / "Scripts" / "python.exe"
    if sys.platform != "win32":
        venv_python = PROJECT_DIR / ".venv" / "bin" / "python"

    if venv_python.exists():
        print_colored(f"[OK] Entorno virtual: {venv_python}", "green")
        return str(venv_python)

    # Buscar en sistema
    for cmd in ["python", "python3"]:
        try:
            subprocess.run([cmd, "--version"], capture_output=True, check=True)
            print_colored(f"[OK] Python encontrado: {cmd}", "green")
            return cmd
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue

    print_colored("[ERROR] No se encuentra Python", "red")
    return None


def is_port_available(port):
    """Verifica si un puerto esta disponible"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((HOST, port))
            return True
        except socket.error:
            return False


def kill_process_on_port(port):
    """Mata el proceso que usa un puerto (Windows)"""
    if sys.platform == "win32":
        try:
            result = subprocess.run(
                f'netstat -ano | findstr ":{port} " | findstr "LISTENING"',
                shell=True,
                capture_output=True,
                text=True,
            )
            for line in result.stdout.split("\n"):
                if line.strip():
                    parts = line.split()
                    pid = parts[-1]
                    subprocess.run(f"taskkill /F /PID {pid}", shell=True)
                    print_colored(f"[INFO] Proceso {pid} terminado", "yellow")
                    time.sleep(1)
        except Exception as e:
            print_colored(f"[WARN] No se pudo liberar puerto: {e}", "yellow")


def main():
    """Funcion principal"""
    os.chdir(PROJECT_DIR)
    current_port = PORT

    print_colored("=" * 50, "cyan")
    print_colored("   IS-BACKOFFICE - Lanzador Rapido", "cyan")
    print_colored(f"   {time.strftime('%Y-%m-%d %H:%M:%S')}", "cyan")
    print_colored("=" * 50, "cyan")
    print()

    # Encontrar Python
    python_cmd = find_python()
    if not python_cmd:
        input("Presiona Enter para salir...")
        return

    # Verificar streamlit
    try:
        subprocess.run([python_cmd, "-c", "import streamlit"], check=True, capture_output=True)
        print_colored("[OK] Streamlit instalado", "green")
    except subprocess.CalledProcessError:
        print_colored("[INFO] Instalando streamlit...", "yellow")
        subprocess.run([python_cmd, "-m", "pip", "install", "streamlit"])

    # Verificar puerto
    if not is_port_available(current_port):
        print_colored(f"[WARN] Puerto {current_port} ocupado", "yellow")
        respuesta = input(f"Liberar puerto {current_port}? (S/N): ").upper()
        if respuesta == "S":
            kill_process_on_port(current_port)
        else:
            nuevo_port = input(f"Ingresa nuevo puerto (default {current_port}): ")
            current_port = int(nuevo_port) if nuevo_port else current_port

    # Abrir navegador
    url = f"http://{HOST}:{current_port}"
    print_colored(f"[INFO] Abriendo navegador en: {url}", "green")
    webbrowser.open(url)

    # Configurar Streamlit
    streamlit_args = [
        python_cmd,
        "-m",
        "streamlit",
        "run",
        "streamlit_app.py",
        "--server.port",
        str(current_port),
        "--server.address",
        HOST,
        "--server.headless",
        "true",
        "--browser.gatherUsageStats",
        "false",
    ]

    print_colored("\n" + "=" * 50, "cyan")
    print_colored("   Streamlit iniciando...", "cyan")
    print_colored("   Presiona Ctrl+C para detener", "cyan")
    print_colored("=" * 50 + "\n", "cyan")

    # Ejecutar Streamlit
    try:
        subprocess.run(streamlit_args)
    except KeyboardInterrupt:
        print_colored("\n[INFO] Servidor detenido", "yellow")
    except Exception as e:
        print_colored(f"[ERROR] {e}", "red")

    input("\nPresiona Enter para salir...")


if __name__ == "__main__":
    main()
