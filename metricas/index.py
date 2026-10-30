import numpy as np
import pandas as pd
from statsmodels.stats.inter_rater import fleiss_kappa

# ==========================================
# 1. CONEXIÓN A GOOGLE SHEETS
# ==========================================
SPREADSHEET_ID = "1bAFP0fVRmFp-bMqlQBkM0gBer209eyG9XT54E9gSpNA"
SHEET_NAME = "Matriz_de_veredictos"  # Nombre exacto de tu pestaña en Google Sheets

# URL formateada para exportar directamente a CSV
url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

print("Cargando datos desde Google Sheets...")
df = pd.read_csv(url)
print(f"✅ Datos cargados correctamente. Total de registros: {len(df)}\n")

# Lista de los 5 detectores evaluados
detectores = ["GPTZERO", "ZeroGPT", "Grammarly"]

# ==========================================
# 2. CÁLCULO DE MÉTRICAS DE PRECISIÓN GLOBAL
# ==========================================
def calcular_metricas_globales(df_datos, lista_detectores):
    resultados = []

    for det in lista_detectores:
        col_veredicto = f"Veredicto_{det}"

        if col_veredicto not in df_datos.columns:
            continue

        # Matriz de Confusión
        tp = (
            (df_datos["Origen_Real"] == 1) & (df_datos[col_veredicto] == 1)
        ).sum()
        tn = (
            (df_datos["Origen_Real"] == 0) & (df_datos[col_veredicto] == 0)
        ).sum()
        fp = (
            (df_datos["Origen_Real"] == 0) & (df_datos[col_veredicto] == 1)
        ).sum()
        fn = (
            (df_datos["Origen_Real"] == 1) & (df_datos[col_veredicto] == 0)
        ).sum()

        # Métricas principales
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        f1 = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )

        resultados.append({
            "Detector": det,
            "TP": tp,
            "TN": tn,
            "FP": fp,
            "FN": fn,
            "FPR (Falsos Pos.)": round(fpr, 4),
            "Sensibilidad (Recall)": round(recall, 4),
            "Precisión": round(precision, 4),
            "F1-Score": round(f1, 4),
        })

    return pd.DataFrame(resultados)


df_global = calcular_metricas_globales(df, detectores)
print("=== METRICAS GLOBALES DE PRECISIÓN ===")
print(df_global.to_string(index=False))
print("\n" + "=" * 50 + "\n")

