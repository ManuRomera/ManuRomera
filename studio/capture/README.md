# Captura real de MR · Dirección en Foundry

El grabador abre **una instancia real de Foundry**, autentica un GM de pruebas **sin grabar el formulario de acceso**, comprueba el mundo de demostración y captura el funcionamiento visible de MR · Dirección. Produce borradores 9:16 y 16:9. **Nunca publica.**

> [!IMPORTANT]
> No conectarlo a tus partidas reales. Sólo a un mundo demo con personajes e imágenes que puedan mostrarse públicamente. Este repositorio de GitHub es público; por defecto el workflow **no adjunta los vídeos**.

## Preparación inicial (una vez)

1. En el Foundry v13 que tienes en Oracle Cloud, crea un **mundo nuevo dedicado** (por ejemplo MR Studio Demo) y activa MR · Dirección. Encontrarás el manifest de instalación en su repositorio. Evita interrumpir las partidas: una instancia de Foundry sólo aloja un mundo activo al mismo tiempo.
2. Crea un **GM exclusivo de demostraciones con una contraseña distinta**. No reutilices la cuenta habitual.
3. Anota el ID interno de ese mundo, que puedes consultar desde su consola como `game.world.id`.
4. En **GitHub → ManuRomera/ManuRomera → Settings → Secrets and variables → Actions**, crea estos secretos:

   | Secreto | Valor |
   |---|---|
   | `FOUNDRY_DEMO_URL` | URL HTTPS de acceso al mundo demo |
   | `FOUNDRY_DEMO_WORLD_ID` | El ID interno exacto del mundo |
   | `FOUNDRY_DEMO_GM_USER` | Nombre visible del GM de pruebas |
   | `FOUNDRY_DEMO_GM_PASSWORD` | Contraseña del GM de pruebas |
   | `FOUNDRY_DEMO_APPROVED` | Literal `YES_DEDICATED_DEMO_WORLD` |

No compartas contraseñas por chat ni las pegues en GitHub Issues.

## Grabar con un botón

En **Actions → MR Studio · Captura real de Foundry → Run workflow**:

- Marca **Instalar/actualizar ejemplo** en la primera ejecución para instalar **La Posada del Cuervo**, a través de la API de tu propio módulo. El programa primero verifica que está dentro del mundo demo.
- Marca **Adjuntar vídeos** sólo si el mundo de demostración no contiene datos privados y quieres descargar los resultados desde el repositorio público.
- Ejecuta el flujo. Preparará el texto factual desde la release y dos teasers con movimiento real y una marca permanente de BORRADOR.

La sesión de acceso se hace fuera de la grabación. Los permisos/cookies se mantienen **en memoria**, sin guardarlos en el repositorio. El capturador verifica el mundo, el rol GM y la activación del módulo, y no actúa en caso de error.

## Qué graba

`scenarios/mr-direccion.json` describe la secuencia: mostrar barra, abrir selector de escenas, previsualizar una escena, mostrar motivos, controles de figuras, mezcla y editor. Son acciones de interfaz auténticas, no pantallas inventadas. No se usan macros ni escrituras de datos durante la grabación. **Instalar el ejemplo** sí crea escenas, actores, diarios y sonidos, exclusivamente en el mundo autorizado y mediante una casilla opcional.

## Alternativa local

Si los ejecutores de GitHub no pueden alcanzar el servidor Oracle, puedes utilizarlo desde tu Mac, con Node 22:

~~~bash
cd studio/capture
npm install
npx playwright install chromium
# Carga las cinco variables desde tu gestor de secretos local.
node capture.mjs --product mr-direccion --out output
~~~

Para montar la campaña desde la raíz de este repositorio, con Python 3, Pillow, FFmpeg y ffprobe:

~~~bash
python3 scripts/mr_studio.py --repo mr-direccion --force --out studio/output
python3 scripts/mr_studio_live_render.py \
  --capture studio/capture/output/mr-direccion-demo.webm \
  --campaign studio/output/mr-direccion/v0.5.0/campaign.json
~~~

Sustituye v0.5.0 por la versión de la release vigente cuando corresponda. No confirmes capturas ni claves al repositorio.

## Estado y limitaciones

- **Pendiente de conexión real**: sin los cinco secretos y un mundo demo activo no es posible autenticar ni grabar tu Foundry.
- La prueba de CI utiliza un vídeo sintético exclusivamente para verificar la tecnología de montaje; **no se presenta como vídeo real ni se distribuye**.
- Los teasers son silenciosos y están marcados como BORRADOR; requieren revisión de derechos, contenido y privacidad antes de difundirlos.
- La política de Foundry para sus listados oficiales exige que el material promocional sea de autoría humana. Los borradores automatizados de este sistema se destinan únicamente a campañas externas que cumplan las licencias y requisitos aplicables: https://foundryvtt.com/article/ai-policy/
