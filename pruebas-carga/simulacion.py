"""
Simulación de Pruebas de Carga para Academic Agents as a Service
==============================================================

Este script genera gráficas simuladas para el análisis de capacidad del sistema,
basadas en los SLOs (Service Level Objectives) definidos en el plan de pruebas.

Genera tres gráficas principales:
1. Throughput vs Usuarios: Muestra la capacidad de procesamiento del sistema
2. Tiempo de Respuesta vs Carga: Analiza la latencia bajo diferentes cargas
3. Tiempo de Ingesta vs Tamaño: Evalúa el procesamiento de documentos

Los datos simulados están basados en los siguientes SLOs del plan:
- Chat: p95 ≤ 8s, promedio ≤ 5s
- Ingesta: documentos de 20MB procesados en ≤ 3min
- Throughput objetivo: ≥ 1000 chunks/min
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import seaborn as sns  

sns.set_palette("husl")

out = Path("pruebas-carga/resultados")
out.mkdir(parents=True, exist_ok=True)

# Datos simulados basados en los SLOs del plan de pruebas
usuarios = np.array([10, 50, 100, 300, 500])  # Usuarios concurrentes
throughput = np.array([20, 100, 180, 520, 800])  # msgs/min (objetivo: escalar hasta 1000)
lat_avg = np.array([1.2, 2.1, 2.8, 4.6, 5.0])   # segundos (SLO: promedio ≤ 5s)
lat_p95 = np.array([2.2, 4.0, 5.3, 7.8, 8.0])   # segundos (SLO: p95 ≤ 8s)

# Datos para pruebas de ingesta
tam_mb = np.array([2, 8, 20])  # Tamaños de documentos según plan
ingesta_min = np.array([0.5, 1.3, 2.7])  # minutos (SLO: ≤ 3min para 20MB)

# Gráfica de throughput vs usuarios concurrentes
def crear_grafica_throughput():
    plt.figure(figsize=(10, 6))
    plt.plot(usuarios, throughput, marker="o", linewidth=2)
    plt.title("Throughput vs Usuarios Concurrentes", pad=20, fontsize=14)
    plt.xlabel("Usuarios concurrentes", fontsize=12)
    plt.ylabel("Throughput (mensajes/minuto)", fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.fill_between(usuarios, throughput*0.9, throughput*1.1, alpha=0.2)
    plt.savefig(out/"throughput_vs_usuarios.png", dpi=300, bbox_inches='tight')
    plt.close()

# Gráfica de tiempos de respuesta promedio y p95
def crear_grafica_latencia():
    plt.figure(figsize=(10, 6))
    plt.plot(usuarios, lat_avg, marker="o", label="Promedio", linewidth=2)
    plt.plot(usuarios, lat_p95, marker="s", label="p95", linewidth=2)
    plt.axhline(y=5, color='r', linestyle='--', alpha=0.5, label='SLO promedio (5s)')
    plt.axhline(y=8, color='r', linestyle=':', alpha=0.5, label='SLO p95 (8s)')
    plt.title("Tiempo de Respuesta vs Carga", pad=20, fontsize=14)
    plt.xlabel("Usuarios concurrentes", fontsize=12)
    plt.ylabel("Latencia (segundos)", fontsize=12)
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.savefig(out/"tiempo_vs_carga.png", dpi=300, bbox_inches='tight')
    plt.close()

# Gráfica de tiempos de ingesta vs tamaño de documento
def crear_grafica_ingesta():
    plt.figure(figsize=(10, 6))
    plt.plot(tam_mb, ingesta_min, marker="o", linewidth=2)
    plt.axhline(y=3, color='r', linestyle='--', alpha=0.5, label='SLO (3 min)')
    plt.title("Tiempo de Ingesta vs Tamaño de Documento", pad=20, fontsize=14)
    plt.xlabel("Tamaño del documento (MB)", fontsize=12)
    plt.ylabel("Tiempo de procesamiento (minutos)", fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=10)
    plt.savefig(out/"ingesta_vs_tamano.png", dpi=300, bbox_inches='tight')
    plt.close()

# Función principal para generar todas las gráficas
def main():
    print("Generando gráficas de simulación...")
    crear_grafica_throughput()
    crear_grafica_latencia()
    crear_grafica_ingesta()
    print(f"Gráficas generadas exitosamente en: {out.resolve()}")

if __name__ == "__main__":
    main()