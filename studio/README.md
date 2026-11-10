# MR Studio — piloto de automatización editorial

Sistema de **preparación de campañas en borrador** para los repositorios de Manu Romera. Este directorio no modifica ni publica software de Foundry, ni sube nada a YouTube, Patreon o redes sociales.

## Funciona así

1. El workflow [MR Studio · Detectar novedades](../../.github/workflows/mr-studio.yml) comprueba las últimas releases de los tres proyectos incluidos en \`catalog.json\`, cada día o manualmente.
2. Detecta una release sin incidencia previa (identificador \`MR_STUDIO:repo@tag\`). Las programadas ignoran releases antiguas.
3. Extrae los cambios declarados en la release. No inventa funciones, disponibilidad ni compatibilidades.
4. Prepara \`campaign.md\`, \`campaign.json\`, guion, copys y una **previsualización de vídeo sin música** en 9:16 y 16:9, a partir de imágenes de repositorios propios. Si faltan imágenes, se queda en borrador de texto.
5. Publica los archivos **solo como artefactos de la ejecución (visibles a quienes tengan acceso al repositorio)** (no posts) y abre una incidencia de revisión. No hay botones de publicación automática.
6. La persona responsable verifica capturas, derechos, afirmaciones, comportamiento real y decide si usar el material.

## Ejecutarlo desde GitHub

En **Actions → MR Studio · Detectar novedades → Run workflow** selecciona \`mr-direccion\` y activa \`Forzar revisión de una release antigua\` en el primer piloto.

El workflow también corre a diario con un filtro de novedades de las últimas 72 horas. Para evitar incidencias duplicadas utiliza la etiqueta \`mr-studio\`.

## IA opcional

Si añades un secreto del repositorio llamado \`OPENAI_API_KEY\`, el agente reescribe los textos **solo para campañas externas autoeditadas**. Sin el secreto genera borradores útiles con plantillas. El modelo se puede definir con la variable \`MR_STUDIO_AI_MODEL\` (por defecto \`gpt-5-mini\`). El coste de API, si se habilita, corre por cuenta del propietario.

> Nunca introduzcas tokens dentro del código, del README o de las incidencias.

## Barreras de seguridad

- **Estado inicial: solo borradores.** Nada se publica en canales externos y no se procesan pagos.
- Las rutas de imágenes están fijadas en el catálogo y se descargan exclusivamente desde el GitHub del autor. Toda imagen sigue necesitando comprobación humana de derechos/procedencia.
- Los vídeos llevan la marca «BORRADOR · REVISAR» y **no simulan clics de Foundry**: usan capturas de documentación del proyecto; las grabaciones reales se conectarán después, cuando exista una instancia de pruebas accesible y autorizada.
- No usar estos copys ni vídeos generados por IA como marketing para la **lista oficial de paquetes de Foundry**. La política aplicable exige materiales promocionales basados en autoría humana: https://foundryvtt.com/article/ai-policy/
- Una traducción/adaptación de terceros no entra automáticamente en el catálogo aunque sea gratuita; requiere auditoría de derechos.
- No comercializar material CC BY-NC u otro contenido restringido sin autorización adecuada.
- Patreon requiere identidad, cuenta y, si se automatizan membresías, OAuth/API v2 y configuración de prestaciones; esta fase no crea ni cobra suscripciones.

## Siguientes conexiones

1. **Foundry de pruebas**: URL, credenciales dedicadas y mundo de demostración para grabar secuencias reales con Playwright; no guardarlas en GitHub.
2. **Canal de vídeo**: conectar YouTube u otro publicador mediante OAuth con revisión humana previa.
3. **Patreon**: crear perfil, definir recompensas y distribución solo de obras verificadas comercializables.
4. **Analítica**: medir clics y conversiones en enlaces propios y comparar campañas.

## Estructura

- \`catalog.json\`: lista blanca de proyectos y rutas de capturas.
- \`../../scripts/mr_studio.py\`: consulta GitHub, deduplicación, guiones y borradores.
- \`../../scripts/mr_studio_render.py\`: vídeos MP4 básicos desde imágenes y cartas tipográficas.
- \`../../tests/test_mr_studio.py\`: pruebas de extracción y seguridad.

**Criterio de éxito del piloto:** una release de MR · Dirección da lugar a una incidencia revisable y a dos MP4 de prueba, sin intervención para preparar el material y sin publicación externa.
