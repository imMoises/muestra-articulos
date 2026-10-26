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
