import argparse
import datetime
import hashlib
import subprocess
from pathlib import Path

import pandas as pd
from statsmodels.stats.inter_rater import fleiss_kappa, aggregate_raters
from statsmodels.stats.contingency_tables import cochrans_q

# ==========================================
# 1. DATOS
# ==========================================
BASE = Path(__file__).resolve().parent
ARCHIVO_DATOS = BASE / "datos" / "matriz_veredictos.csv"
DIR_RESULTADOS = BASE / "resultados"

SPREADSHEET_ID = "1bAFP0fVRmFp-bMqlQBkM0gBer209eyG9XT54E9gSpNA"
SHEET_NAME = "Matriz_de_veredictos"
URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

detectores = ["GPTZERO", "ZeroGPT", "Grammarly"]


def d4(valor):
    """Todos los resultados se expresan con 4 decimales."""
    return f"{valor:.4f}"


parser = argparse.ArgumentParser()
parser.add_argument("--actualizar", action="store_true",
                    help="Descargar la matriz desde Google Sheets y reemplazar la copia local.")
args = parser.parse_args()

if args.actualizar:
    print("Descargando datos desde Google Sheets...")
    columnas = ["ID_Texto", "Origen_Real", "Modelo"] \
        + [f"Probabilidad_{d}" for d in detectores] + [f"Veredicto_{d}" for d in detectores]
    ARCHIVO_DATOS.parent.mkdir(parents=True, exist_ok=True)
    pd.read_csv(URL)[columnas].to_csv(ARCHIVO_DATOS, index=False, lineterminator="\n")

df = pd.read_csv(ARCHIVO_DATOS)
print(f"Datos cargados correctamente. Total de registros: {len(df)}\n")

# Los veredictos con valor 2 (texto mixto) se consideran equivalentes a 1 (IA).
for detector in detectores:
    col_veredicto = f"Veredicto_{detector}"
    df[col_veredicto] = df[col_veredicto].replace(2, 1)

# ==========================================
# 2. MÉTRICAS DE PRECISIÓN
# ==========================================
resultados = []
for det in detectores:
    col_veredicto = f"Veredicto_{det}"

    tp = int(((df["Origen_Real"] == 1) & (df[col_veredicto] == 1)).sum())
    tn = int(((df["Origen_Real"] == 0) & (df[col_veredicto] == 0)).sum())
    fp = int(((df["Origen_Real"] == 0) & (df[col_veredicto] == 1)).sum())
    fn = int(((df["Origen_Real"] == 1) & (df[col_veredicto] == 0)).sum())

    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    resultados.append({
        "Detector": det,
        "TP": tp, "TN": tn, "FP": fp, "FN": fn,
        "FPR (Falsos Pos.)": d4(fpr),
        "Sensibilidad (Recall)": d4(recall),
        "Precisión": d4(precision),
        "F1-Score": d4(f1),
    })

df_global = pd.DataFrame(resultados)
print("=== METRICAS GLOBALES DE PRECISIÓN ===")
print(df_global.to_string(index=False))

# ==========================================
# 3. MÉTRICAS DE CONFIABILIDAD Y SESGO
# ==========================================
matriz_evaluadores = df[[f"Veredicto_{d}" for d in detectores]]
k_detectores = len(detectores)

# A. Kappa de Fleiss
agg_table, _ = aggregate_raters(matriz_evaluadores)
kappa = fleiss_kappa(agg_table)

# B. Proporción de Acuerdo Unánime (PAU)
suma_por_texto = matriz_evaluadores.sum(axis=1)
textos_unanimes = int(suma_por_texto.isin([0, k_detectores]).sum())
pau = textos_unanimes / len(df) * 100

# C. Prueba Q de Cochran
resultado_q = cochrans_q(matriz_evaluadores)

df_confiabilidad = pd.DataFrame([
    ("Kappa de Fleiss", d4(kappa)),
    ("Textos con consenso absoluto", f"{textos_unanimes} de {len(df)}"),
    ("PAU (%)", d4(pau)),
    ("Q de Cochran", d4(resultado_q.statistic)),
    ("p (Q de Cochran)", d4(resultado_q.pvalue)),
], columns=["Indicador", "Valor"])

print("\n=== CONFIABILIDAD E INTER-ACUERDO ===")
print(f"Coeficiente Kappa de Fleiss: {d4(kappa)}")
print(f"Textos con Consenso Absoluto: {textos_unanimes} de {len(df)}")
print(f"PAU (Acuerdo Unánime): {d4(pau)}%")
print("\n=== SESGO SISTEMÁTICO (PRUEBA Q DE COCHRAN) ===")
print(f"Estadístico Q: {d4(resultado_q.statistic)}")
print(f"Valor p (p-value): {d4(resultado_q.pvalue)}")

# ==========================================
# 4. RESULTADOS VERSIONADOS
# ==========================================
huella = hashlib.sha256(ARCHIVO_DATOS.read_bytes()).hexdigest()
try:
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=BASE,
                            capture_output=True, text=True, check=True).stdout.strip()
except (OSError, subprocess.CalledProcessError):
    commit = "sin git"

DIR_RESULTADOS.mkdir(parents=True, exist_ok=True)
df_global.to_csv(DIR_RESULTADOS / "metricas_globales.csv", index=False, lineterminator="\n")
df_confiabilidad.to_csv(DIR_RESULTADOS / "confiabilidad.csv", index=False, lineterminator="\n")


def tabla_md(tabla):
    filas = ["| " + " | ".join(tabla.columns) + " |", "|" + "---|" * len(tabla.columns)]
    filas += ["| " + " | ".join(str(x) for x in fila) + " |" for fila in tabla.itertuples(index=False)]
    return "\n".join(filas)


(DIR_RESULTADOS / "resultados.md").write_text("\n".join([
    "# Resultados del cálculo de métricas", "",
    f"- Fecha de ejecución: {datetime.datetime.now():%Y-%m-%d %H:%M}",
    f"- Datos: `metricas/datos/matriz_veredictos.csv` (SHA-256 `{huella}`)",
    f"- Commit del código: `{commit}`", "",
    "## Métricas globales de precisión", "", tabla_md(df_global), "",
    "## Confiabilidad e inter-acuerdo", "", tabla_md(df_confiabilidad), "",
]), encoding="utf-8")
