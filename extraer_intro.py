"""
extraer_intro.py
Extrae entre 1500 y 2000 palabras desde el inicio de la Introducción,
terminando siempre el párrafo en curso,
de artículos académicos en PDF, manejando diseños de 1 y 2 columnas.

Uso:
    python extraer_intro.py articulo.pdf
    python extraer_intro.py carpeta_con_pdfs/ -o salida/ --min 1500 --max 2000
    python extraer_intro.py carpeta/ --solo-intro     # corta al llegar a la siguiente sección

Requisitos:
    pip install pymupdf
"""

import argparse
import csv
import re
import sys
from collections import Counter
from pathlib import Path

import pymupdf  # PyMuPDF

# ---------------------------------------------------------------------------
# Patrones
# ---------------------------------------------------------------------------

# Encabezado de introducción: "Introducción", "1. Introduction", "I. INTRODUCCIÓN", "1 Introdução"...
PATRON_INTRO = re.compile(
    r"^\s*(?:(?:\d{1,2}|[IVX]{1,4})\s*[.)\-–]?\s*)?"
    r"(introducci[oó]n|introduction|introdu[cç][aã]o|introduzione)\b\s*[:.]?\s*",
    re.IGNORECASE,
)

# Encabezados de la sección siguiente (para --solo-intro)
PATRON_SIGUIENTE = re.compile(
    r"^\s*(?:(?:\d{1,2}|[IVX]{1,4})\s*[.)\-–]?\s*)?"
    r"(marco te[oó]rico|antecedentes|estado del arte|revisi[oó]n de (la )?literatura|"
    r"metodolog[ií]a|materiales? y m[eé]todos|m[eé]todos?|"
    r"methodology|methods?|materials and methods|related work|background|literature review|"
    r"theoretical framework|resultados|results)\b",
    re.IGNORECASE,
)

# Respaldo si no hay encabezado "Introducción": arrancar después de palabras clave
PATRON_KEYWORDS = re.compile(r"^\s*(palabras[\s-]clave|keywords?|key\s*words|palavras[\s-]chave)\b", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Lectura con orden correcto para 1 y 2 columnas
# ---------------------------------------------------------------------------

def bloques_de_pagina(pagina):
    """Devuelve los bloques de texto de la página en orden de lectura.

    Lógica: los bloques angostos (< 60 % del ancho útil) se asignan a la columna
    izquierda o derecha según su centro. Los bloques anchos (título, abstract,
    figuras a todo el ancho) cortan el flujo: todo lo angosto que está arriba de
    ellos se lee primero (izq. completa, luego der.), después el bloque ancho.
    Así funciona igual para páginas de 1 columna, de 2, o mixtas.
    """
    bloques = []
    for x0, y0, x1, y1, texto, _num, tipo in pagina.get_text("blocks", sort=False):
        if tipo != 0 or not texto.strip():
            continue  # ignora imágenes y bloques vacíos
        bloques.append((x0, y0, x1, y1, texto))

    if not bloques:
        return [], 1

    margen_izq = min(b[0] for b in bloques)
    margen_der = max(b[2] for b in bloques)
    ancho_util = max(margen_der - margen_izq, 1)
    medio = margen_izq + ancho_util / 2

    angostos = [b for b in bloques if (b[2] - b[0]) < 0.6 * ancho_util]
    # La página es de 2 columnas si hay texto angosto a ambos lados del centro
    hay_izq = any((b[0] + b[2]) / 2 < medio for b in angostos)
    hay_der = any((b[0] + b[2]) / 2 >= medio for b in angostos)
    dos_columnas = hay_izq and hay_der and len(angostos) >= 0.4 * len(bloques)

    if not dos_columnas:
        return [b[4] for b in sorted(bloques, key=lambda b: (round(b[1]), b[0]))], 1

    ordenados = sorted(bloques, key=lambda b: (b[1], b[0]))
    salida, izq, der = [], [], []

    def vaciar():
        salida.extend(t for *_, t in sorted(izq, key=lambda b: b[1]))
        salida.extend(t for *_, t in sorted(der, key=lambda b: b[1]))
        izq.clear()
        der.clear()

    for b in ordenados:
        es_ancho = (b[2] - b[0]) >= 0.6 * ancho_util
        if es_ancho:
            vaciar()
            salida.append(b[4])
        elif (b[0] + b[2]) / 2 < medio:
            izq.append(b)
        else:
            der.append(b)
    vaciar()
    return salida, 2


def lineas_repetidas(paginas_margenes, umbral=0.5):
    """Detecta encabezados/pies de página: líneas en la franja superior o inferior
    de la página que se repiten en muchas páginas (nombre de la revista, DOI, etc.)."""
    if len(paginas_margenes) < 3:
        return set()
    conteo = Counter()
    for textos in paginas_margenes:
        vistas = {re.sub(r"\d+", "#", l.strip().lower())
                  for t in textos for l in t.splitlines() if 0 < len(l.strip()) < 150}
        conteo.update(vistas)
    minimo = max(2, int(len(paginas_margenes) * umbral))
    return {l for l, c in conteo.items() if c >= minimo}


def textos_en_margenes(pagina, franja=0.08):
    """Bloques ubicados en el 8 % superior o inferior de la página."""
    alto = pagina.rect.height
    return [b[4] for b in pagina.get_text("blocks")
            if b[6] == 0 and (b[3] < alto * franja or b[1] > alto * (1 - franja))]


def extraer_lineas(ruta_pdf):
    """Devuelve (lista de líneas en orden de lectura, info de columnas por página)."""
    doc = pymupdf.open(ruta_pdf)
    paginas, columnas, margenes = [], [], []
    for pagina in doc:
        bloques, ncol = bloques_de_pagina(pagina)
        paginas.append(bloques)
        columnas.append(ncol)
        margenes.append(textos_en_margenes(pagina))
    doc.close()

    repetidas = lineas_repetidas(margenes)
    lineas = []
    for bloques in paginas:
        for t in bloques:
            for linea in t.splitlines():
                l = linea.strip()
                if not l:
                    continue
                if re.fullmatch(r"\d{1,4}", l):  # número de página suelto
                    continue
                if re.sub(r"\d+", "#", l.lower()) in repetidas:
                    continue
                lineas.append(l)
            lineas.append("")  # separador de bloque (párrafo)
    return lineas, columnas


# ---------------------------------------------------------------------------
# Limpieza y recorte
# ---------------------------------------------------------------------------

def unir_lineas(lineas):
    """Une líneas en párrafos y repara palabras cortadas con guion al final de línea."""
    parrafos, actual = [], ""
    for l in lineas:
        if not l:
            if actual:
                parrafos.append(actual)
                actual = ""
            continue
        if actual.endswith("-") and l[:1].islower():
            actual = actual[:-1] + l          # "investi-" + "gación" -> "investigación"
        elif actual:
            actual += " " + l
        else:
            actual = l
    if actual:
        parrafos.append(actual)
    texto = "\n\n".join(parrafos)
    texto = texto.replace("­", "")       # guion suave
    texto = re.sub(r"[ \t]+", " ", texto)
    return texto


def es_encabezado(linea, patron):
    """Una línea cuenta como encabezado si coincide con el patrón y es corta."""
    return bool(patron.match(linea)) and len(linea.split()) <= 8


def localizar_inicio(lineas):
    """Índice de la primera línea de contenido de la introducción y el método usado."""
    for i, l in enumerate(lineas):
        m = PATRON_INTRO.match(l)
        if m and len(l.split()) <= 8:
            resto = l[m.end():].strip()
            if resto:  # "1. Introducción El presente..." en la misma línea
                lineas[i] = resto
                return i, "encabezado"
            return i + 1, "encabezado"
        # Encabezado pegado al primer párrafo, p. ej. "INTRODUCCIÓN. En las últimas décadas..."
        if m and l[: m.end()].strip().isupper() and len(l.split()) > 8:
            lineas[i] = l[m.end():].strip()
            return i, "encabezado"

    for i, l in enumerate(lineas):  # respaldo: después del bloque de palabras clave
        if PATRON_KEYWORDS.match(l):
            j = i + 1
            while j < len(lineas) and lineas[j]:  # salta el resto del bloque de keywords
                j += 1
            return j, "respaldo_keywords"
    return None, "no_encontrado"


def recortar(lineas, inicio, minimo, maximo, solo_intro):
    seleccion = []
    for l in lineas[inicio:]:
        if solo_intro and l and es_encabezado(l, PATRON_SIGUIENTE):
            break
        seleccion.append(l)
    texto = unir_lineas(seleccion)
    return cortar_en_parrafo(texto, minimo, maximo)


FIN_ORACION = re.compile(r"[.!?…:;][\"'”»)\]]*$")


def cortar_en_parrafo(texto, minimo, maximo):
    """Toma párrafos completos hasta llegar al mínimo de palabras.

    - Se detiene al final del párrafo en que se alcanza `minimo`.
    - Un bloque que no termina en signo de puntuación se considera un párrafo
      partido por un salto de columna o de página, así que sigue leyendo.
    - Si terminar el párrafo obligaría a pasar de `maximo`, corta en el último
      final de oración que quepa; si no hay ninguno, corta exacto en `maximo`.
    """
    parrafos = [p for p in texto.split("\n\n") if p.strip()]
    salida, cuenta = [], 0

    for p in parrafos:
        palabras_p = p.split()
        if cuenta + len(palabras_p) <= maximo:
            salida.append(p)
            cuenta += len(palabras_p)
            if cuenta >= minimo and FIN_ORACION.search(p.strip()):
                return "\n\n".join(salida), cuenta
            continue

        # El párrafo se pasa del máximo: cortar en el último final de oración posible
        cupo = maximo - cuenta
        fragmento = palabras_p[:cupo]
        ultimo_fin = max((i for i, w in enumerate(fragmento) if FIN_ORACION.search(w)), default=None)
        if ultimo_fin is not None and cuenta + ultimo_fin + 1 >= minimo:
            fragmento = fragmento[: ultimo_fin + 1]
        salida.append(" ".join(fragmento))
        cuenta += len(fragmento)
        return "\n\n".join(salida), cuenta

    return "\n\n".join(salida), cuenta  # el texto se acabó antes del mínimo


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------

def procesar(ruta_pdf, carpeta_salida, minimo, maximo, solo_intro):
    try:
        lineas, columnas = extraer_lineas(ruta_pdf)
    except Exception as e:
        return {"archivo": ruta_pdf.name, "estado": f"error: {e}", "metodo": "", "columnas": "",
                "palabras": 0, "salida": ""}

    if sum(len(l) for l in lineas) < 200:
        return {"archivo": ruta_pdf.name, "estado": "sin_texto (¿PDF escaneado? requiere OCR)",
                "metodo": "", "columnas": "", "palabras": 0, "salida": ""}

    paginas_2col = sum(1 for c in columnas if c == 2)
    diseno = "2 columnas" if paginas_2col > len(columnas) / 2 else "1 columna"

    inicio, metodo = localizar_inicio(lineas)
    if inicio is None:
        return {"archivo": ruta_pdf.name, "estado": "no se encontró la introducción",
                "metodo": metodo, "columnas": diseno, "palabras": 0, "salida": ""}

    texto, cuenta = recortar(lineas, inicio, minimo, maximo, solo_intro)
    destino = carpeta_salida / f"{ruta_pdf.stem}_intro.txt"
    destino.write_text(texto, encoding="utf-8")

    estado = "ok" if cuenta >= minimo else f"ok (solo {cuenta} palabras disponibles)"
    return {"archivo": ruta_pdf.name, "estado": estado, "metodo": metodo, "columnas": diseno,
            "palabras": cuenta, "salida": destino.name}


def main():
    ap = argparse.ArgumentParser(description="Extrae N palabras desde la introducción de PDFs académicos.")
    ap.add_argument("entrada", help="Un PDF o una carpeta con PDFs")
    ap.add_argument("-o", "--salida", default="extracciones", help="Carpeta de salida (por defecto: extracciones)")
    ap.add_argument("--min", dest="minimo", type=int, default=1500,
                    help="Mínimo de palabras; termina el párrafo en curso (por defecto: 1500)")
    ap.add_argument("--max", dest="maximo", type=int, default=2000,
                    help="Tope de palabras si el párrafo es muy largo (por defecto: 2000)")
    ap.add_argument("--solo-intro", action="store_true",
                    help="Detenerse al llegar a la siguiente sección (Metodología, Marco teórico...)")
    args = ap.parse_args()
    if args.maximo < args.minimo:
        sys.exit("--max debe ser mayor o igual que --min")

    entrada = Path(args.entrada)
    pdfs = sorted(entrada.glob("*.pdf")) if entrada.is_dir() else [entrada]
    if not pdfs:
        sys.exit("No se encontraron PDFs.")

    salida = Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)

    resultados = []
    for pdf in pdfs:
        r = procesar(pdf, salida, args.minimo, args.maximo, args.solo_intro)
        resultados.append(r)
        print(f"[{r['estado']}] {r['archivo']}  ({r['columnas']}, {r['palabras']} palabras, {r['metodo']})")

    with open(salida / "resumen.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["archivo", "estado", "metodo", "columnas", "palabras", "salida"])
        w.writeheader()
        w.writerows(resultados)
    print(f"\nResumen guardado en {salida / 'resumen.csv'}")


if __name__ == "__main__":
    main()