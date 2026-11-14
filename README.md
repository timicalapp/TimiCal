# TimiCal

App para iPhone para fichar entrada y salida, comparar tus horas con las
previstas en tu calendario de Trabajo, controlar días libres y avisos de
descanso, y sacar informes en PDF.

**Privacidad:** todo se guarda solo en tu iPhone. Sin cuentas, sin
servidores, sin publicidad. La política completa está dentro de la app
(Ajustes > Acerca de TimiCal > Política de privacidad).

## Cómo instalarla (gratis)

TimiCal no está en el App Store. Se instala con **SideStore**, que es
gratuito y firma la app con tu propio Apple ID (puedes usar uno secundario).

1. Instala SideStore siguiendo su guía oficial (la primera vez necesitas un
   ordenador, solo una vez).
2. En SideStore: pestaña **Fuentes** > **+** > pega esta dirección:

   `https://raw.githubusercontent.com/timicalapp/TimiCal/main/fuente.json`

3. Abre la fuente TimiCal e instala la app.
4. Ábrela: un asistente te guía para elegir tus calendarios.

### Con otras herramientas (AirSign, Sideloadly…)

Si tu herramienta instala desde una dirección, usa esta. Siempre descarga
la última versión:

`https://github.com/timicalapp/TimiCal/releases/latest/download/TimiCal.ipa`

## Actualizaciones

Cuando haya una versión nueva, SideStore la mostrará en **Mis apps** y la
propia TimiCal te avisará. Pulsa **Actualizar** (con LocalDevVPN conectado).
**No borres la app para actualizar**: actualizar encima conserva tus datos;
borrarla los borra.

Recuerda que con un Apple ID gratuito las apps caducan a los 7 días si
SideStore no las renueva: ábrelo de vez en cuando o activa la renovación
automática.

## Sugerencias y errores

Desde la app: Ajustes > Acerca de TimiCal > Enviar una sugerencia /
Informar de un error. O escribe a timicalapp@gmail.com.

---

## Para publicar una versión nueva (solo el autor)

1. En Xcode, sube la **Version** (1.0 → 1.1…) y saca el `.ipa`.
2. Aquí en GitHub: **Releases** > **Draft a new release**.
3. **Tag**: `v` + la versión, por ejemplo `v1.1` (Create new tag).
4. Título libre y, en la descripción, las novedades (salen en SideStore).
5. Arrastra el archivo, llamado `TimiCal.ipa`, y pulsa **Publish release**.

En un minuto `fuente.json` se actualiza solo (pestaña **Actions**) y
SideStore avisará a todos.
