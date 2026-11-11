# MR Studio · Grabaciones reales de Foundry

El grabador ya tiene dos modos: **Wicked Ones (mundo existente, sólo demostración visual)** y **mundo demo independiente**. Ambos requieren una ejecución manual y generan borradores; **nunca publican vídeos ni cambian contraseñas**.

## La opción sencilla: aprovechar Wicked Ones en Foundry v13

**Instancia correcta: Foundry VTT v13, no v12.** Introduce la dirección de tu instancia **v13** como valor del secreto `FOUNDRY_DEMO_URL`; no uses la dirección antigua. Por seguridad, la dirección no se guarda en los archivos públicos del repositorio. El grabador verifica la versión real de Foundry y **rechaza v12 automáticamente**, incluso si se ha configurado una URL equivocada.



El modo existente usa el mundo ya autorizado y comprueba su título exacto antes de grabar; no instala contenidos ni activa escenas. El usuario se configura internamente o mediante Actions Secrets.

### 1. Un secreto privado de GitHub (NO es una publicación)

Abre [Settings → Secrets and variables → Actions](https://github.com/ManuRomera/ManuRomera/settings/secrets/actions), y pulsa **New repository secret**:

| Campo de GitHub | Qué introducir |
|---|---|
| **Name** | `FOUNDRY_DEMO_URL` |
| **Secret** | La URL HTTPS de la **instancia Foundry v13** (no la antigua v12). Si `FOUNDRY_DEMO_URL` ya existe, usa **Update** para sustituir el valor |

Pulsa **Add secret**. El valor queda almacenado de forma cifrada para Actions y no se publica en el README ni en el código. GitHub no lo permite volver a visualizar en claro desde la web.

**Para este modo no es necesario buscar el ID interno del mundo**. La cuenta se configura en el workflow; si tiene contraseña, guárdala como segundo secreto `FOUNDRY_DEMO_GM_PASSWORD` y no la compartas por chat.

> ⚠️ **Protege la cuenta Gamemaster.** Foundry advierte que las cuentas GM deben protegerse con contraseña, especialmente en servidores accesibles por Internet. La documentación oficial recomienda establecer contraseñas: https://foundryvtt.com/article/users/

### 2. Botón para grabar

Abre [Actions → MR Studio · Captura real de Foundry](https://github.com/ManuRomera/ManuRomera/actions/workflows/mr-studio-capture.yml) y pulsa **Run workflow**.

- **Autorizo grabación de la interfaz existente de Wicked Ones** → marca esta casilla.
- **Instalar/actualizar ejemplo** → **déjala desmarcada**: en Wicked Ones está deshabilitado para proteger los datos.
- **Adjuntar vídeos** → inicialmente **déjala desmarcada**. El repositorio es público; si la marcas, otras personas con acceso a los artefactos de Actions podrían ver el vídeo. Sólo marca la casilla una vez revisado que el mundo no muestre usuarios, mensajes o datos privados.

La automatización abrirá la sesión, comprobará título del mundo y rol GM, navegará por los menús de MR · Dirección, generará una grabación real y montará dos previsualizaciones MP4 con marca **BORRADOR · NO PUBLICAR**.

**Limitación:** si no adjuntas artefactos, el vídeo queda en el ejecutor temporal de Actions y no podrás descargarlo después. Para guardar de manera privada las tomas, usa un repositorio privado o el modo local.

### 3. ¿Y si prefieres que los vídeos se guarden en privado?

Puedes ejecutar el mismo capturador en tu ordenador, con Node 22 y Playwright, y usar la salida local (incluye la grabación WebM original). No se suben contraseñas ni vídeos a GitHub. Desde la raíz del proyecto:

```bash
cd studio/capture
npm install
npx playwright install chromium
# Define FOUNDRY_DEMO_URL y FOUNDRY_DEMO_APPROVED de forma privada.
export FOUNDRY_DEMO_APPROVED=YES_WICKED_ONES_VIEW_ONLY
node capture.mjs --product mr-direccion --out output
```

El workflow usa los valores del escenario autorizado. Configura contraseñas mediante secretos si corresponde; nunca las añadas a archivos del repositorio.

## Cómo se evita grabar otra partida o cambiar Wicked Ones

El capturador valida **después de entrar y antes de realizar ninguna acción grabada**:

- `game.version` debe indicar la **versión mayor 13**; si es v12 se aborta antes de grabar.
- `game.world.title` debe coincidir exactamente con el mundo autorizado.
- `game.user.isGM` debe ser verdadero.
- MR · Dirección debe estar activo.
- Sólo permite clics/hover en controles de MR · Dirección definidos en el escenario, no macros externas.
- La opción `--prepare-example` **está prohibida** en el modo Wicked Ones.

La sesión de autenticación se realiza en un contexto de navegador que no se graba. El vídeo se genera desde un contexto posterior. El script nunca guarda los secretos en los archivos de salida. Los vídeos sí podrían mostrar contenido privado de la escena actualmente activa, por lo que es imprescindible revisarlos antes de difundirlos.

## Configuración avanzada: un mundo demo separado

El modo original también está disponible para un mundo de demostración independiente. En ese caso configura los secretos `FOUNDRY_DEMO_URL`, `FOUNDRY_DEMO_WORLD_ID` (o `FOUNDRY_DEMO_WORLD_TITLE`), `FOUNDRY_DEMO_GM_USER`, `FOUNDRY_DEMO_GM_PASSWORD` y `FOUNDRY_DEMO_APPROVED` con valor `YES_DEDICATED_DEMO_WORLD`.

Sólo en ese modo se permite marcar **Instalar/actualizar ejemplo**, que usa la API original del módulo para crear la Posada del Cuervo. El flujo de revisión sigue sin publicar nada por sí solo.

## Estado real

- El código y las pruebas de montaje están integrados.
- La primera grabación en la instancia Oracle está **pendiente de configurar FOUNDRY_DEMO_URL y ejecutar Actions**.
- Las pruebas técnicas utilizan vídeo sintético para verificar FFmpeg; no se hacen pasar por una grabación de Foundry.
- Para promociones en listados oficiales de Foundry hay que cumplir [su política de IA](https://foundryvtt.com/article/ai-policy/). Las piezas automatizadas están destinadas a revisión y posibles campañas externas, no a publicación oficial automática.
