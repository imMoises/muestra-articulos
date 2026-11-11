# Extractor de introducciones de artículos académicos

Script en Python que toma artículos académicos en PDF y extrae **entre 1500 y 2000 palabras a partir de la Introducción**, terminando siempre el párrafo en curso para no dejar ideas cortadas.

Funciona con artículos de revista de **1 columna y de 2 columnas**, y puede procesar un solo PDF o una carpeta completa.

---

## ¿Qué hace?

- **Encuentra la introducción** aunque el encabezado tenga distintos formatos: `Introducción`, `INTRODUCCIÓN`, `1. Introduction`, `I. Introducción`, `Introdução`, etc.
- **Lee en el orden correcto** en PDFs de 2 columnas: primero la columna izquierda y luego la derecha. Respeta el título y el resumen cuando ocupan todo el ancho de la página.
- **Extrae entre 1500 y 2000 palabras** desde el inicio de la introducción, sin importar en qué sección termine el texto (marco teórico, metodología, etc.).
- **No corta párrafos**: al llegar a 1500 palabras termina el párrafo que está leyendo. Si ese párrafo es demasiado largo, corta en el último punto antes de las 2000 palabras.
- **Limpia el texto**:
  - quita encabezados y pies de página repetidos (nombre de la revista, DOI, volumen)
  - quita números de página sueltos
  - une las palabras cortadas con guion al final de línea (`investi-` + `gación` → `investigación`)
- **Genera un reporte** (`resumen.csv`) con el resultado de cada artículo para saber cuáles revisar a mano.

---

## Requisitos

- Python 3.9 o superior ([descargar aquí](https://www.python.org/downloads/)). Al instalarlo en Windows, marca la casilla **"Add Python to PATH"**.
- La librería `pymupdf`, que se instala con el archivo `requirements.txt`.

---

## Instalación

1. Organiza los archivos en una carpeta así:

   ```
   proyecto/
   ├── extraer_intro.py
   ├── requirements.txt
   ├── README.md
   └── pdfs/            ← aquí van tus artículos
   ```

2. Abre una terminal dentro de la carpeta `proyecto`.
   - **Windows:** en el Explorador de archivos, entra a la carpeta, escribe `cmd` en la barra de direcciones y presiona Enter.
   - **Mac / Linux:** abre la Terminal y usa `cd ruta/a/proyecto`.

3. Instala la dependencia (solo la primera vez):

   ```bash
   pip install -r requirements.txt
   ```

   > Si aparece el error *"pip no se reconoce"*, usa `python -m pip install -r requirements.txt`.
   > En Mac o Linux usa `pip3` en lugar de `pip`.

---

## Cómo iniciar el script

### Procesar una carpeta completa (lo más común)

```bash
python extraer_intro.py pdfs -o salida
```

### Procesar un solo artículo

```bash
python extraer_intro.py pdfs/mi_articulo.pdf -o salida
```

### Cambiar el rango de palabras

```bash
python extraer_intro.py pdfs -o salida --min 1200 --max 1800
```

### Extraer solo la introducción

Detiene la extracción al llegar a la siguiente sección (Metodología, Marco teórico, etc.):

```bash
python extraer_intro.py pdfs -o salida --solo-intro
```

> En Mac o Linux escribe `python3` en lugar de `python`.

### Opciones disponibles

| Opción         | Qué hace                                                        | Valor por defecto |
|----------------|-----------------------------------------------------------------|-------------------|
| `entrada`      | Un archivo PDF o una carpeta con PDFs (obligatorio)             | —                 |
| `-o`, `--salida` | Carpeta donde se guardan los resultados                       | `extracciones`    |
| `--min`        | Mínimo de palabras; termina el párrafo en curso                 | `1500`            |
| `--max`        | Tope de palabras cuando el párrafo es muy largo                 | `2000`            |
| `--solo-intro` | Se detiene al terminar la introducción                          | desactivado       |

Para ver la ayuda desde la terminal:

```bash
python extraer_intro.py -h
```

---

## Resultados

Mientras corre, la terminal muestra una línea por cada PDF:

```
[ok] articulo1.pdf  (2 columnas, 1534 palabras, encabezado)
[ok] articulo2.pdf  (1 columna, 1612 palabras, respaldo_keywords)
[no se encontró la introducción] articulo3.pdf  (1 columna, 0 palabras, no_encontrado)
```

En la carpeta de salida quedan:

- **`<nombre_del_pdf>_intro.txt`**: el texto extraído de cada artículo.
- **`resumen.csv`**: una tabla (se abre con Excel) con estas columnas:

| Columna    | Significado                                                                 |
|------------|-----------------------------------------------------------------------------|
| `archivo`  | Nombre del PDF                                                              |
| `estado`   | `ok`, o el motivo por el que no se pudo extraer                             |
| `metodo`   | `encabezado` si encontró el título "Introducción"; `respaldo_keywords` si empezó después de las palabras clave |
| `columnas` | Diseño detectado: 1 o 2 columnas                                            |
| `palabras` | Cantidad de palabras extraídas                                              |
| `salida`   | Nombre del archivo `.txt` generado                                          |

---

## Posibles problemas y qué significan

| Estado en `resumen.csv`                     | Causa probable                                                                 | Qué hacer |
|---------------------------------------------|--------------------------------------------------------------------------------|-----------|
| `no se encontró la introducción`            | El artículo no tiene un encabezado "Introducción" ni "Palabras clave"           | Extraer ese artículo a mano o avisar para ajustar los patrones |
| `sin_texto (¿PDF escaneado? requiere OCR)`  | El PDF es una imagen escaneada y no tiene texto seleccionable                  | Pasarlo antes por un OCR (por ejemplo `ocrmypdf`) |
| `ok (solo N palabras disponibles)`          | El artículo tiene menos texto que el mínimo pedido desde la introducción        | Normal en artículos cortos |
| `metodo = respaldo_keywords`                | No encontró el título "Introducción" y empezó después de las palabras clave     | Revisar que el inicio del `.txt` sea correcto |

Se recomienda revisar a mano unos pocos `.txt` de cada revista distinta: tablas a media columna o notas al pie largas pueden colarse en el texto.

## Generar el prompt XML

Para insertar el contenido de un archivo `.txt` dentro de la etiqueta
`<texto_referencia>` y mostrar el prompt completo en la consola:

```bash
python generar_prompt.py salida/articulo-1_intro.txt
```

El resultado se puede copiar y pegar directamente. El script utiliza
`prompt.xml` como plantilla y escapa automáticamente los caracteres
especiales de XML del texto de referencia (`&`, `<` y `>`).

También se puede indicar otra plantilla:

```bash
python generar_prompt.py salida/articulo-1_intro.txt --plantilla otra-plantilla.xml
```

## Cálculo de métricas (versionado)

El script `metricas/index.py` calcula las métricas de precisión (matriz de
confusión, FPR, sensibilidad, precisión, F1, especificidad, exactitud) y de
confiabilidad (Kappa de Fleiss, PAU, Q de Cochran global y por subcorpus,
sensibilidad por modelo generador).

### Dónde están los datos

- `metricas/datos/matriz_veredictos.csv`: copia de la hoja
  `Matriz_de_veredictos` de Google Sheets. **Es la fuente que usa el cálculo** y
  se versiona en Git, de modo que cada resultado queda amarrado a los datos
  exactos que lo produjeron.
- `metricas/resultados/`: salida del cálculo (`metricas_globales.csv`,
  `sensibilidad_por_modelo.csv`, `confiabilidad.csv` y `resultados.md`).
  `resultados.md` registra la fecha, la huella SHA-256 de los datos y el commit
  del código.

### Cómo ejecutarlo

```bash
# Descargar la versión actual de la hoja, validarla y calcular
python metricas/index.py --actualizar

# Calcular con la copia que ya está en el repositorio
python metricas/index.py
```

Regla aplicada: el veredicto 2 («texto mixto» de GPTZero y ZeroGPT) cuenta
como 1 (IA), según la sección «Reclasificación de textos mixtos» de la
metodología. Para Grammarly, una probabilidad mayor a 40 % es IA (1).

### Validación

Antes de calcular, el script revisa la matriz y se detiene si:

- no tiene 120 filas, los ID están vacíos o repetidos, o la división no es
  90 sintéticos / 30 humanos;
- algún veredicto es distinto de 0, 1 o 2;
- algún veredicto de Grammarly no coincide con el umbral del 40 %.

Para el último caso se puede forzar el cálculo con
`--permitir-inconsistencias`, pero los resultados quedan marcados como
**no válidos para reporte**. También se muestran advertencias (probabilidades no
numéricas, código 2 en Grammarly, textos con probabilidades idénticas).

La validación no puede comparar contra las capturas: si un valor se digitó mal
en la hoja pero es coherente consigo mismo, hay que revisarlo contra la
evidencia en `evidencias/`.

### Flujo de trabajo

1. Corregir la hoja en Google Sheets.
2. Ejecutar `python metricas/index.py --actualizar`.
3. Revisar `metricas/resultados/resultados.md`.
4. Guardar datos, código y resultados en el mismo commit:

   ```bash
   git add metricas/datos metricas/resultados metricas/index.py
   git commit -m "Resultados: <qué cambió>"
   ```

5. Cuando las cifras sean las que van al documento, marcar la versión y
   citarla en el anexo:

   ```bash
   git tag -a v1.0-jurado -m "Cifras reportadas en el documento"
   git push --follow-tags
   ```
