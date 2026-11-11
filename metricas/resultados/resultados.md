# Resultados del cálculo de métricas

- Fecha de ejecución: 2026-11-10 20:59
- Datos: `metricas/datos/matriz_veredictos.csv` (SHA-256 `bf98cd32bdf112cc5f0ee5911ea83f2293caad5495419e38cf691eb6eca3a829`)
- Commit del código: `148d4ab`

## Métricas globales de precisión

| Detector | TP | TN | FP | FN | FPR (Falsos Pos.) | Sensibilidad (Recall) | Precisión | F1-Score |
|---|---|---|---|---|---|---|---|---|
| GPTZERO | 37 | 30 | 0 | 53 | 0.0000 | 0.4111 | 1.0000 | 0.5827 |
| ZeroGPT | 24 | 18 | 12 | 66 | 0.4000 | 0.2667 | 0.6667 | 0.3810 |
| Grammarly | 33 | 30 | 0 | 57 | 0.0000 | 0.3667 | 1.0000 | 0.5366 |

## Confiabilidad e inter-acuerdo

| Indicador | Valor |
|---|---|
| Kappa de Fleiss | 0.2780 |
| Textos con consenso absoluto | 66 de 120 |
| PAU (%) | 55.0000 |
| Q de Cochran | 0.4815 |
| p (Q de Cochran) | 0.7860 |
