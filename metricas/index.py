import numpy as np
import pandas as pd
from statsmodels.stats.inter_rater import fleiss_kappa, aggregate_raters
from statsmodels.stats.contingency_tables import cochrans_q

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

# Lista de los detectores evaluados (Asegúrate de incluir los 5 de tu tesis si ya los tienes)
detectores = ["GPTZERO", "ZeroGPT", "Grammarly"]

# ==========================================
# 2. CÁLCULO DE MÉTRICAS DE PRECISIÓN GLOBAL
# ==========================================
def calcular_metricas_globales(df_datos, lista_detectores):
    resultados = []

    for det in lista_detectores:
        col_veredicto = f"Veredicto_{det}"

        if col_veredicto not in df_datos.columns:
            print(f"⚠️ Advertencia: La columna {col_veredicto} no existe en la matriz.")
            continue

        # Matriz de Confusión
        tp = ((df_datos["Origen_Real"] == 1) & (df_datos[col_veredicto] == 1)).sum()
        tn = ((df_datos["Origen_Real"] == 0) & (df_datos[col_veredicto] == 0)).sum()
        fp = ((df_datos["Origen_Real"] == 0) & (df_datos[col_veredicto] == 1)).sum()
        fn = ((df_datos["Origen_Real"] == 1) & (df_datos[col_veredicto] == 0)).sum()

        # Métricas principales
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        
        # F1-Score (Corregido el error de sintaxis del multiplicador)
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
print("\n" + "=" * 50 + "\n") # Corregido el multiplicador de string


# ==========================================
# 3. MÉTRICAS DE CONFIABILIDAD Y SESGO
# ==========================================

# Identificar columnas válidas
cols_veredictos = [f"Veredicto_{d}" for d in detectores if f"Veredicto_{d}" in df.columns]
matriz_evaluadores = df[cols_veredictos]

if len(cols_veredictos) >= 2:
    
    # --- A. KAPPA DE FLEISS ---
    # aggregate_raters agrupa las respuestas en categorías para que statsmodels lo entienda
    agg_table, categories = aggregate_raters(matriz_evaluadores)
    kappa = fleiss_kappa(agg_table)
    
    print("=== CONFIABILIDAD E INTER-ACUERDO ===")
    print(f"Coeficiente Kappa de Fleiss: {kappa:.4f}")
    
    # --- B. PROPORCIÓN DE ACUERDO UNÁNIME (PAU) ---
    suma_por_texto = matriz_evaluadores.sum(axis=1)
    k_detectores = len(cols_veredictos)
    
    # Es unánime si la suma de todos los detectores da 0 (todos dicen humano) o K (todos dicen IA)
    textos_unanimes = suma_por_texto.isin([0, k_detectores]).sum()
    total_textos = len(df)
    pau = (textos_unanimes / total_textos) * 100
    
    print(f"Textos con Consenso Absoluto: {textos_unanimes} de {total_textos}")
    print(f"PAU (Acuerdo Unánime): {pau:.2f}%")
    
    # --- C. PRUEBA Q DE COCHRAN (Sesgo Sistemático) ---
    # La prueba Q requiere que la matriz no tenga valores nulos (solo 0 y 1)
    resultado_q = cochrans_q(matriz_evaluadores.dropna())
    
    print("\n=== SESGO SISTEMÁTICO (PRUEBA Q DE COCHRAN) ===")
    print(f"Estadístico Q: {resultado_q.statistic:.4f}")
    print(f"Valor p (p-value): {resultado_q.pvalue:.4e}")
    
    if resultado_q.pvalue < 0.05:
        print("-> CONCLUSIÓN: p < 0.05. EXISTE un sesgo sistemático significativo entre los detectores.")
    else:
        print("-> CONCLUSIÓN: p >= 0.05. NO EXISTE evidencia de sesgo sistemático.")
        
else:
    print("⚠️ No hay suficientes detectores configurados en la base de datos para calcular métricas de confiabilidad.")