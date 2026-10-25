"""
contar_palabras.py
Cuenta las palabras de archivos .txt y verifica si están dentro de un rango
(por defecto 1500–2000) y si terminan en una oración completa.

Usa la misma definición de "palabra" que extraer_intro.py:
cualquier secuencia de caracteres separada por espacios o saltos de línea.

Uso:
    python contar_palabras.py salida
    python contar_palabras.py salida/articulo1_intro.txt
    python contar_palabras.py salida --min 1200 --max 1800 --csv conteo.csv

No requiere librerías externas.
"""

import argparse
import csv
import re
import sys
from pathlib import Path

FIN_ORACION = re.compile(r"[.!?…][\"'”»)\]]*$")


def analizar(ruta, minimo, maximo):
    try:
        texto = ruta.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        texto = ruta.read_text(encoding="latin-1")

    palabras = len(texto.split())
    if palabras < minimo:
        rango = "por debajo"
    elif palabras > maximo:
        rango = "por encima"
    else:
        rango = "dentro"

    final = texto.strip()
    termina_bien = bool(final) and bool(FIN_ORACION.search(final))

    return {
        "archivo": ruta.name,
        "palabras": palabras,
        "caracteres": len(texto),
        "parrafos": len([p for p in texto.split("\n\n") if p.strip()]),
        "rango": rango,
        "oracion_completa": "sí" if termina_bien else "no",
    }


def main():
    ap = argparse.ArgumentParser(description="Cuenta palabras en archivos .txt.")
    ap.add_argument("entrada", help="Un archivo .txt o una carpeta con archivos .txt")
    ap.add_argument("--min", dest="minimo", type=int, default=1500, help="Mínimo esperado (por defecto: 1500)")
    ap.add_argument("--max", dest="maximo", type=int, default=2000, help="Máximo esperado (por defecto: 2000)")
    ap.add_argument("--csv", help="Guardar el resultado en este archivo CSV (opcional)")
    args = ap.parse_args()

    entrada = Path(args.entrada)
    if entrada.is_dir():
        archivos = sorted(entrada.glob("*.txt"))
    elif entrada.is_file():
        archivos = [entrada]
    else:
        sys.exit(f"No existe: {entrada}")
    if not archivos:
        sys.exit("No se encontraron archivos .txt.")

    resultados = [analizar(a, args.minimo, args.maximo) for a in archivos]

    # Tabla en la terminal
    ancho = max(len(r["archivo"]) for r in resultados)
    ancho = max(ancho, len("Archivo"))
    print(f"\n{'Archivo':<{ancho}}  {'Palabras':>8}  {'Rango':<11}  Oración completa")
    print("-" * (ancho + 42))
    for r in resultados:
        marca = "" if r["rango"] == "dentro" else "  <--"
        print(f"{r['archivo']:<{ancho}}  {r['palabras']:>8}  {r['rango']:<11}  {r['oracion_completa']}{marca}")

    # Resumen
    total = len(resultados)
    dentro = sum(r["rango"] == "dentro" for r in resultados)
    cortados = sum(r["oracion_completa"] == "no" for r in resultados)
    menor = min(resultados, key=lambda r: r["palabras"])
    mayor = max(resultados, key=lambda r: r["palabras"])
    promedio = sum(r["palabras"] for r in resultados) / total

    print("\nResumen")
    print(f"  Archivos revisados:        {total}")
    print(f"  Dentro de {args.minimo}–{args.maximo}:       {dentro}")
    print(f"  Fuera del rango:           {total - dentro}")
    print(f"  Terminan sin oración completa: {cortados}")
    print(f"  Promedio de palabras:      {promedio:.0f}")
    print(f"  Menos palabras:            {menor['archivo']} ({menor['palabras']})")
    print(f"  Más palabras:              {mayor['archivo']} ({mayor['palabras']})")

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=list(resultados[0].keys()))
            w.writeheader()
            w.writerows(resultados)
        print(f"\nResultado guardado en {args.csv}")


if __name__ == "__main__":
    main()