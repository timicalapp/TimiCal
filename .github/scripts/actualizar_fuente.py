"""Mantiene fuente.json al día con las Releases de GitHub.

Lo ejecuta el workflow "Actualizar fuente" cada vez que se publica, edita o
borra una Release. Lee del evento:
- la etiqueta (v1.5.2 -> versión 1.5.2),
- la descripción de la Release (novedades),
- el archivo .ipa adjunto (dirección y tamaño).

Comprobaciones para que SideStore nunca falle al actualizar:
- Abre el .ipa y mira que la versión de dentro (Version en Xcode) sea la
  misma que la etiqueta. Si no coincide, esa versión NO se añade a la
  fuente y el workflow sale en rojo con el motivo.
- Si la Release no tiene .ipa o se ha borrado, se quita de la fuente.
- Las versiones se ordenan de la más nueva a la más antigua por número
  (SideStore toma la primera como la más reciente), aunque edites una
  Release antigua.
"""
import io
import json
import os
import plistlib
import time
import urllib.request
import zipfile

with open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8") as f:
    evento = json.load(f)

accion = evento.get("action", "")
release = evento["release"]
version = release["tag_name"].lstrip("vV").strip()
errores = []


def numero(v):
    """'1.5.2' -> (1, 5, 2) para ordenar bien (1.10 va después de 1.9)."""
    partes = []
    for trozo in str(v).split("."):
        cifras = "".join(c for c in trozo if c.isdigit())
        partes.append(int(cifras) if cifras else 0)
    return tuple(partes)


def version_dentro_del_ipa(url):
    """Descarga el .ipa y devuelve (Version, Build) de su Info.plist."""
    ultimo_error = None
    for intento in range(5):
        try:
            with urllib.request.urlopen(url, timeout=120) as respuesta:
                datos = respuesta.read()
            break
        except Exception as error:  # recién subido a veces tarda un poco
            ultimo_error = error
            time.sleep(10 * (intento + 1))
    else:
        raise RuntimeError(f"No se ha podido descargar el .ipa: {ultimo_error}")

    with zipfile.ZipFile(io.BytesIO(datos)) as ipa:
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
versiones = [
    v for v in app.get("versions", [])
    if v.get("version") != version and "PENDIENTE" not in json.dumps(v)
]

ipas = [a for a in release.get("assets", []) if a["name"].lower().endswith(".ipa")]

if accion == "deleted":
    print(f"Release {version} borrada: se quita de la fuente.")
elif release.get("draft") or release.get("prerelease"):
    print(f"Release {version} en borrador o prerelease: se quita de la fuente.")
elif not ipas:
    print(f"La Release {version} no tiene .ipa: se quita de la fuente.")
else:
    ipa = ipas[0]
    try:
        version_ipa, build_ipa = version_dentro_del_ipa(ipa["browser_download_url"])
    except Exception as error:
        version_ipa, build_ipa = None, None
        errores.append(f"No se ha podido comprobar el .ipa de la {version}: {error}")

    if version_ipa is not None and version_ipa != version:
        errores.append(
            f"El .ipa de la Release v{version} es la versión {version_ipa} "
            f"(build {build_ipa}). En Xcode, Target > General > Version tiene "
            f"que ser {version}. Vuelve a compilar y sustituye TimiCal.ipa en "
            f"la Release (Edit > quitar el .ipa > subir el nuevo > Update)."
        )
    elif version_ipa is not None:
        notas = (release.get("body") or "").strip() or f"Versión {version}."
        fecha = (release.get("published_at") or release.get("created_at") or "")[:10]
        versiones.append({
            "version": version,
            "date": fecha,
            "localizedDescription": notas,
            "downloadURL": ipa["browser_download_url"],
            "size": ipa["size"],
            "minOSVersion": "17.0",
        })
        print(f"Fuente actualizada: {version} (build {build_ipa}, {ipa['size']} bytes)")

# SideStore y AltStore toman la PRIMERA de la lista como la más reciente.
versiones.sort(key=lambda v: numero(v.get("version", "0")), reverse=True)
app["versions"] = versiones

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
