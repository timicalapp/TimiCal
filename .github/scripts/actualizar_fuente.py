"""Mantiene fuente.json al día con las Releases de GitHub.

Lo ejecuta el workflow "Actualizar fuente" cada vez que se publica, edita o
borra una Release. En cada ejecución mira TODAS las Releases del
repositorio (no solo la del aviso), así la fuente siempre coincide con lo
que hay publicado aunque se borren o creen varias seguidas.

Entra en la fuente cada Release que:
- no es borrador ni pre-release (las betas nunca llegan a SideStore),
- tiene un archivo .ipa adjunto,
- y la versión de dentro del .ipa coincide con la etiqueta (v1.5.3 -> 1.5.3).

Si una Release nueva no cumple lo último, no se añade y el workflow sale en
rojo con el motivo. Las versiones se ordenan de la más nueva a la más
antigua (SideStore toma la primera como la más reciente).
"""
import io
import json
import os
import plistlib
import time
import urllib.request
import zipfile

REPO = os.environ.get("GITHUB_REPOSITORY", "timicalapp/TimiCal")
TOKEN = os.environ.get("GH_TOKEN", "")
errores = []


def numero(v):
    """'1.5.2' -> (1, 5, 2) para ordenar bien (1.10 va después de 1.9)."""
    partes = []
    for trozo in str(v).split("."):
        cifras = "".join(c for c in trozo if c.isdigit())
        partes.append(int(cifras) if cifras else 0)
    return tuple(partes)


def pedir(url, binario=False):
    cabeceras = {"User-Agent": "actualizar-fuente"}
    if not binario:
        cabeceras["Accept"] = "application/vnd.github+json"
        if TOKEN:
            cabeceras["Authorization"] = f"Bearer {TOKEN}"
    ultimo_error = None
    for intento in range(5):
        try:
            peticion = urllib.request.Request(url, headers=cabeceras)
            with urllib.request.urlopen(peticion, timeout=120) as respuesta:
                return respuesta.read()
        except Exception as error:  # recién subido a veces tarda un poco
            ultimo_error = error
            time.sleep(10 * (intento + 1))
    raise RuntimeError(f"No se ha podido descargar {url}: {ultimo_error}")


def todas_las_releases():
    releases, pagina = [], 1
    while True:
        datos = json.loads(pedir(
            f"https://api.github.com/repos/{REPO}/releases?per_page=100&page={pagina}"
        ))
        releases += datos
        if len(datos) < 100:
            return releases
        pagina += 1


def version_dentro_del_ipa(url):
    """Descarga el .ipa y devuelve (Version, Build) de su Info.plist."""
    with zipfile.ZipFile(io.BytesIO(pedir(url, binario=True))) as ipa:
        rutas = [
            n for n in ipa.namelist()
            if n.startswith("Payload/") and n.endswith(".app/Info.plist")
            and n.count("/") == 2
        ]
        if not rutas:
            raise RuntimeError("El .ipa no tiene Payload/…app/Info.plist.")
        info = plistlib.loads(ipa.read(rutas[0]))
    return (
        str(info.get("CFBundleShortVersionString", "")),
        str(info.get("CFBundleVersion", "")),
    )


with open("fuente.json", encoding="utf-8") as f:
    fuente = json.load(f)

app = fuente["apps"][0]
# Lo que ya estaba comprobado: no hace falta volver a descargar su .ipa.
comprobadas = {
    (v.get("downloadURL"), v.get("size")): v for v in app.get("versions", [])
}

versiones = []
for release in todas_las_releases():
    version = release["tag_name"].lstrip("vV").strip()
    if release.get("draft") or release.get("prerelease"):
        print(f"{release['tag_name']}: borrador o pre-release, no va a la fuente.")
        continue
    ipas = [a for a in release.get("assets", []) if a["name"].lower().endswith(".ipa")]
    if not ipas:
        print(f"{release['tag_name']}: sin .ipa, no va a la fuente.")
        continue
    ipa = ipas[0]
    url, tamano = ipa["browser_download_url"], ipa["size"]

    if (url, tamano) not in comprobadas:
        try:
            version_ipa, build_ipa = version_dentro_del_ipa(url)
        except Exception as error:
            errores.append(f"No se ha podido comprobar el .ipa de {release['tag_name']}: {error}")
            continue
        if version_ipa != version:
            errores.append(
                f"El .ipa de la Release {release['tag_name']} es la versión "
                f"{version_ipa} (build {build_ipa}). La etiqueta tiene que ser "
                f"v{version_ipa}, o vuelve a compilar con la versión {version}."
            )
            continue
        print(f"{release['tag_name']}: comprobado (build {build_ipa}).")

    notas = (release.get("body") or "").strip() or f"Versión {version}."
    fecha = (release.get("published_at") or release.get("created_at") or "")[:10]
    versiones.append({
        "version": version,
        "date": fecha,
        "localizedDescription": notas,
        "downloadURL": url,
        "size": tamano,
        "minOSVersion": "17.0",
    })

# SideStore y AltStore toman la PRIMERA de la lista como la más reciente.
versiones.sort(key=lambda v: numero(v.get("version", "0")), reverse=True)
app["versions"] = versiones
print("En la fuente:", ", ".join(v["version"] for v in versiones) or "nada")

with open("fuente.json", "w", encoding="utf-8") as f:
    json.dump(fuente, f, ensure_ascii=False, indent=2)
    f.write("\n")

if errores:
    texto = "\n".join(errores)
    print("ERROR: " + texto)
    resumen = os.environ.get("GITHUB_STEP_SUMMARY")
    if resumen:
        with open(resumen, "a", encoding="utf-8") as f:
            f.write("### ❌ No se ha añadido a la fuente\n\n" + texto + "\n")
    salida = os.environ.get("GITHUB_OUTPUT")
    if salida:
        with open(salida, "a", encoding="utf-8") as f:
            f.write("error=si\n")
