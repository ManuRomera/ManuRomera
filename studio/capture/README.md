# MR Studio · Grabaciones reales de Foundry

El grabador ya tiene dos modos: **Wicked Ones (mundo existente, sólo demostración visual)** y **mundo demo independiente**. Ambos requieren una ejecución manual y generan borradores; **nunca publican vídeos ni cambian contraseñas**.

## La opción sencilla: aprovechar Wicked Ones

Ya existe el mundo **Wicked Ones** con **MR · Dirección** instalado y el usuario **Gamemaster**. No necesitas crear otro mundo ni buscar el ID interno. Este modo comprueba el título exacto del mundo antes de grabar y no instala contenidos ni activa escenas.

### 1. Un secreto privado de GitHub (NO es una publicación)

Abre [Settings → Secrets and variables → Actions](https://github.com/ManuRomera/ManuRomera/settings/secrets/actions), y pulsa **New repository secret**:

| Campo de GitHub | Qué introducir |
|---|---|
| **Name** | `FOUNDRY_DEMO_URL` |
| **Secret** | La URL HTTPS de tu servidor Foundry, la que utilizas para entrar en Oracle Cloud |

Pulsa **Add secret**. El valor queda almacenado de forma cifrada para Actions y no se publica en el README ni en el código. GitHub no lo permite volver a visualizar en claro desde la web.

**Para este modo no es necesario configurar los otros cuatro secretos antiguos**: el flujo ya sabe que el mundo se llama Wicked Ones y que el usuario es Gamemaster. Si no tiene contraseña, el campo puede estar vacío. Si después le pones una contraseña (recomendado), guárdala como segundo secreto `FOUNDRY_DEMO_GM_PASSWORD` y no la compartas por chat.

> ⚠️ **Protege la cuenta Gamemaster.** Foundry advierte que las cuentas GM sin contraseña permiten acceder a la configuración del mundo a cualquiera que llegue a la pantalla de acceso. La documentación oficial recomienda establecer contraseñas: https://foundryvtt.com/article/users/

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

El script utiliza por defecto `Wicked Ones` y `Gamemaster` en ese modo. Si la contraseña sigue vacía, no hay que definirla.

## Cómo se evita grabar otra partida o cambiar Wicked Ones

El capturador valida **después de entrar y antes de realizar ninguna acción grabada**:

- `game.world.title` debe ser exactamente **Wicked Ones**.
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
