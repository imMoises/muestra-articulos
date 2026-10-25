"""
Genera en la consola el prompt.xml con un archivo de texto insertado.

Uso:
    python generar_prompt.py salida/articulo-1_intro.txt
    python generar_prompt.py salida/articulo-1_intro.txt --plantilla otro-prompt.xml
"""

import argparse
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape


ETIQUETA_REFERENCIA = re.compile(
    r"(<texto_referencia\b[^>]*>).*?(</texto_referencia\s*>)",
    re.DOTALL,
)


def leer_texto(ruta: Path) -> str:
    """Lee un archivo de texto intentando primero UTF-8 y luego Latin-1."""
    try:
        return ruta.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return ruta.read_text(encoding="latin-1")


def generar_prompt(plantilla: str, referencia: str) -> str:
    """Reemplaza el contenido de texto_referencia en la plantilla."""
    referencia_xml = escape(referencia, entities={'"': "&quot;", "'": "&apos;"})
    resultado, reemplazos = ETIQUETA_REFERENCIA.subn(
        lambda coincidencia: (
            coincidencia.group(1) + referencia_xml + coincidencia.group(2)
        ),
        plantilla,
        count=1,
    )
    if reemplazos == 0:
        raise ValueError(
            "La plantilla no contiene una etiqueta "
            "<texto_referencia>...</texto_referencia>."
        )
    return resultado


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inserta un archivo de texto en la plantilla prompt.xml."
    )
    parser.add_argument(
        "archivo",
        type=Path,
        help="Archivo .txt que se insertará dentro de <texto_referencia>.",
    )
    parser.add_argument(
        "-p",
        "--plantilla",
        type=Path,
        default=Path(__file__).with_name("prompt.xml"),
        help="Plantilla XML (por defecto: prompt.xml).",
    )
    args = parser.parse_args()

    for ruta, descripcion in (
        (args.archivo, "archivo de referencia"),
        (args.plantilla, "archivo de plantilla"),
    ):
        if not ruta.is_file():
            parser.error(f"No existe el {descripcion}: {ruta}")

    referencia = leer_texto(args.archivo)
    if not referencia.strip():
        parser.error(f"El archivo de referencia está vacío: {args.archivo}")

    try:
        plantilla = leer_texto(args.plantilla)
        prompt = generar_prompt(plantilla, referencia)
    except (OSError, ValueError) as error:
        parser.error(str(error))

    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        sys.stdout.write(prompt)
    except UnicodeEncodeError as error:
        parser.error(
            "La consola no admite algún carácter del archivo. "
            "Usa una terminal configurada en UTF-8."
        )


if __name__ == "__main__":
    main()
