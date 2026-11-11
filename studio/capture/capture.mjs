#!/usr/bin/env node
/**
 * MR Studio Foundry capture.
 * Credentials are used only in a NON-recorded authentication context.
 * Recording starts only after world / GM / module checks have succeeded.
 * This script never publishes or uploads anything.
 */
import {readFile, mkdir, copyFile, writeFile, rm} from "node:fs/promises";
import {resolve, join} from "node:path";
import process from "node:process";

const SCRIPT_ROOT = new URL(".", import.meta.url);
const PROJECT_ROOT = resolve(new URL("../../", SCRIPT_ROOT).pathname);
const SCENARIO_DIR = resolve(new URL("scenarios/", SCRIPT_ROOT).pathname);
const APPROVALS = new Set(["YES_DEDICATED_DEMO_WORLD", "YES_WICKED_ONES_VIEW_ONLY"]);

function arg(name, fallback = undefined) {
  const index = process.argv.indexOf("--" + name);
  return index >= 0 ? process.argv[index+1] : fallback;
}
function flag(name) {return process.argv.includes("--" + name);}
function expect(condition, message) {
  if (!condition) throw new Error(message);
}
function sanitizeName(value) {
  expect(/^[a-z0-9-]{3,64}$/.test(value), "Nombre de escenario no permitido.");
  return value;
}
async function scenarioFor(product) {
  const content = JSON.parse(await readFile(join(SCENARIO_DIR,product+".json"),"utf8"));
  expect(content.product === product, "El escenario no coincide con el producto.");
  expect(typeof content.requiredSelector === "string" && content.requiredSelector.startsWith("#mr-direccion-bar"),
    "El selector principal no es válido.");
  expect(Array.isArray(content.steps) && content.steps.length > 0 && content.steps.length <= 24,
    "Escenario vacío o demasiado largo.");
  for (const step of content.steps) {
    expect(["wait","click","hover"].includes(step.action), "Acción no permitida en el escenario.");
    expect(Number.isInteger(step.holdMs) && step.holdMs >= 200 && step.holdMs <= 4500,
      "La duración de cada paso debe estar entre 200 y 4500 ms.");
    if (step.action !== "wait") {
      expect(typeof step.selector === "string" && step.selector.startsWith("#mr-direccion-bar "),
        "Las acciones sólo pueden manipular controles de la barra MR · Dirección.");
      expect(!/[;{}]/.test(step.selector), "Selector no permitido.");
    }
  }
  return content;
}
function configFromEnv() {
  const env=process.env;
  expect(APPROVALS.has(env.FOUNDRY_DEMO_APPROVED),
    "El acceso requiere la autorización explícita del mundo seleccionado.");
  const urlString=env.FOUNDRY_DEMO_URL;
  expect(urlString, "Falta FOUNDRY_DEMO_URL.");
  let url;
  try {url=new URL(urlString);} catch {throw new Error("FOUNDRY_DEMO_URL no es una URL válida.");}
  const local=["localhost","127.0.0.1","[::1]"].includes(url.hostname);
  expect(url.protocol==="https:" || (local && url.protocol==="http:"),
    "Sólo se acepta HTTPS o HTTP local; no se envían contraseñas por HTTP remoto.");
  expect(!url.username && !url.password && !url.hash,
    "La URL no puede contener credenciales ni fragmentos.");
  const isExisting = env.FOUNDRY_DEMO_APPROVED === "YES_WICKED_ONES_VIEW_ONLY";
  const worldTitle = (env.FOUNDRY_DEMO_WORLD_TITLE || (isExisting ? "Wicked Ones" : "")).trim();
  const worldId = (env.FOUNDRY_DEMO_WORLD_ID || "").trim();
  expect(worldTitle || worldId, "Configura el título o el ID del mundo autorizado.");
  const user = (env.FOUNDRY_DEMO_GM_USER || (isExisting ? "Gamemaster" : "")).trim();
  expect(user, "Falta el usuario GM.");
  return {
    url:url.href, user,
    pass:env.FOUNDRY_DEMO_GM_PASSWORD || "",
    world:worldId, worldTitle, mode:isExisting ? "existing-read-only" : "dedicated-demo",
  };
}
async function ready(page) {
  try {
    await page.waitForFunction(() => Boolean(globalThis.game?.ready), null, {timeout:30000});
  } catch (err) {
    const status = await page.evaluate(() => ({
      pathname: new URL(window.location.href).pathname.toLowerCase(),
      gamePresent: Boolean(globalThis.game),
      gameView: String(globalThis.game?.view || ""),
      worldPresent: Boolean(globalThis.game?.world),
      loginSelect: Boolean(document.querySelector('select[name="userid"], select[name="user"]')),
      hasPasswordField: Boolean(document.querySelector('input[type="password"]')),
      setupUI: Boolean(document.querySelector('#setup, #setup-app, #setup-menu, #worlds')),
      joinUI: Boolean(document.querySelector('#join-game, #join-game-form, #join-form'))
    })).catch(()=>({pathname:"unknown",gamePresent:false,gameView:"",worldPresent:false,loginSelect:false,hasPasswordField:false,setupUI:false,joinUI:false}));
    const phase = status.gameView==="setup" || status.pathname.endsWith("/setup") ? "SETUP_NOT_LAUNCHED" :
                  status.gameView==="join" || status.pathname.endsWith("/join") ? "JOIN_NOT_COMPLETED" :
                  status.gameView==="game" || status.pathname.endsWith("/game") ? "GAME_NOT_READY" : "OTHER";
    console.log("Foundry diagnóstico seguro: fase="+phase+" gameView="+status.gameView+
      " game="+status.gamePresent+" world="+status.worldPresent+
      " setupUI="+status.setupUI+" joinUI="+status.joinUI+
      " loginSelect="+status.loginSelect+" passwordField="+status.hasPasswordField);
    if (phase==="SETUP_NOT_LAUNCHED")
      throw Error("Foundry muestra /setup: inicia Wicked Ones desde la pantalla de configuración antes de grabar.");
    if (phase==="JOIN_NOT_COMPLETED")
      throw Error("Foundry sigue en /join: revisar controles de acceso del formulario.");
    throw Error("Foundry no ha cargado el mundo en 30 segundos (fase: "+phase+").");
  }
}
async function verify(page, config, product) {
  await ready(page);
  const state=await page.evaluate((product)=>({
    world:globalThis.game?.world?.id,
    worldTitle:globalThis.game?.world?.title,
    foundryVersion:globalThis.game?.version || globalThis.game?.release?.version || "",
    gm:globalThis.game?.user?.isGM,
    moduleActive:globalThis.game?.modules?.get(product)?.active === true,
    moduleVersion:globalThis.game?.modules?.get(product)?.version || ""
  }), product);
  if (config.world) expect(state.world===config.world,
    "El ID del mundo no coincide: se cancela la grabación.");
  if (config.worldTitle) expect(state.worldTitle===config.worldTitle,
    "El título del mundo no coincide: se cancela la grabación.");
  const major = Number.parseInt(String(state.foundryVersion).replace(/^v/i, ""), 10);
  expect(major===13, "Se requiere Foundry VTT v13; se ha detectado otra versión o no se ha podido verificar. Grabación cancelada.");
  expect(state.gm, "La cuenta seleccionada no es un GM del mundo de demostración.");
  expect(state.moduleActive, "El módulo objetivo no está activo en el mundo de demostración.");
  return state;
}
async function login(page, config) {
  await page.goto(config.url, {waitUntil:"domcontentloaded",timeout:45000});
  const form=page.locator(
    "#join-game-form, form#join-form, form:has(select[name=userid]), form:has(select[name=user])"
  ).first();
  // Foundry v13 may mount its join form asynchronously after DOMContentLoaded.
  await form.waitFor({state:"visible",timeout:10000}).catch(()=>{});
  if (await form.isVisible().catch(()=>false)) {
    const selector=form.locator("select[name=userid],select[name=user],select").first();
    expect(await selector.count(), "La pantalla de acceso no tiene selector de usuario.");
    await selector.selectOption({label:config.user});
    const password=form.locator("input[name=password],input[type=password]").first();
    if (await password.count()) await password.fill(config.pass);
    else expect(!config.pass, "No se encuentra el campo de contraseña de Foundry.");
    const submit=form.locator("button[type=submit],input[type=submit]").first();
    expect(await submit.count(), "No se encuentra el botón de acceso a Foundry.");
    await submit.click();
  }
  await ready(page);
}
async function maybeSetupExample(page, product) {
  if (!flag("prepare-example")) return;
  // Existing campaigns may contain real users or scenes: never create example data there.
  expect(process.env.FOUNDRY_DEMO_APPROVED==="YES_DEDICATED_DEMO_WORLD",
    "No se puede instalar el ejemplo ni activar escenas en Wicked Ones.");
  expect(process.env.FOUNDRY_DEMO_ALLOW_SETUP==="YES",
    "Instalar el ejemplo modifica el mundo. Autoriza FOUNDRY_DEMO_ALLOW_SETUP=YES.");
  expect(product==="mr-direccion", "Sólo está preparado el ejemplo de MR · Dirección.");
  await page.evaluate(async ()=>{
    const mr=globalThis.game.modules.get("mr-direccion");
    await mr.api.installExample();
    const scene=globalThis.game.scenes.find(s=>s.getFlag("mr-direccion","example")==="camino");
    if (!scene) throw Error("No se creó la escena de ejemplo.");
    await scene.activate();
    await scene.view();
  });
  await page.waitForTimeout(2500);
}
async function playScenario(page, scenario, minActions=2) {
  await page.locator(scenario.requiredSelector).waitFor({state:"visible",timeout:20000});
  let successes=0;
  for (const step of scenario.steps) {
    if (step.action==="wait") {
      await page.waitForTimeout(step.holdMs);
      continue;
    }
    const target=page.locator(step.selector).first();
    try {
      await target.waitFor({state:"visible",timeout:step.optional?3500:12000});
      if (step.action==="click") await target.click({timeout:5000});
      else await target.hover({timeout:5000});
      successes++;
      await page.waitForTimeout(step.holdMs);
    } catch(error) {
      if (!step.optional) throw new Error("Falló el paso "+step.label+": "+error.message.split("\n")[0]);
      console.log("Paso opcional omitido:",step.label);
    }
  }
  expect(successes>=minActions,"La demostración no contiene suficientes interacciones reales.");
  return successes;
}
async function main() {
  const product=sanitizeName(arg("product","mr-direccion"));
  const scenario=await scenarioFor(product);
  if (flag("validate-only")) {
    console.log("Escenario validado:", product, scenario.steps.length, "pasos.");
    return;
  }
  const config=configFromEnv();
  if (flag("check-config-only")) {
    console.log("Configuración válida: modo",config.mode,
      "(sin conexión a servidor ni lectura de credenciales en los logs).");
    return;
  }
  const output=resolve(arg("out","studio/capture/output"),product+"-demo.webm");
  const outputDir=resolve(arg("out","studio/capture/output"));
  await mkdir(outputDir,{recursive:true});
  const {chromium}=await import("playwright");
  const browser=await chromium.launch({headless:true});
  let videoPath;
  let version="";
  let actions=0;
  let recording;
  try {
    // Login is NEVER included in the marketing video.
    const authContext=await browser.newContext({viewport:{width:1600,height:900}});
    const authPage=await authContext.newPage();
    await login(authPage,config);
    const verified=await verify(authPage,config,product);
    version=verified.moduleVersion;
    await maybeSetupExample(authPage,product);
    const state=await authContext.storageState();
    await authContext.close();

    recording=await browser.newContext({
      viewport:{width:1600,height:900},
      deviceScaleFactor:1,
      storageState:state,
      recordVideo:{dir:outputDir,size:{width:1600,height:900}}
    });
    const page=await recording.newPage();
    await page.goto(config.url,{waitUntil:"domcontentloaded",timeout:45000});
    await verify(page,config,product);
    actions=await playScenario(page,scenario,config.mode==="existing-read-only"?1:2);
    videoPath=await page.video().path();
    await recording.close();
    recording=null;
    await copyFile(videoPath,output);
    await rm(videoPath,{force:true});
    // Do not persist cookies, credentials, server URL or world name.
    await writeFile(resolve(outputDir,product+"-capture.json"),JSON.stringify({
      product,version,actions,recording:"real_foundry",human_review_required:true,
      published:false,source:"read-only browser interactions, approved world"
    },null,2)+"\n");
    console.log("CAPTURA REAL COMPLETADA:",output,"versión",version,"interacciones",actions);
  } catch (error) {
    // Never upload an unsuccessful video, which might include a login screen.
    if (recording) {
      await recording.close().catch(()=>{});
    }
    if (videoPath) await rm(videoPath,{force:true}).catch(()=>{});
    await rm(output,{force:true}).catch(()=>{});
    throw error;
  } finally {
    await browser.close();
  }
}
main().catch(e=>{
  console.error("MR Studio Foundry: "+e.message.split("\n")[0]);
  process.exitCode=1;
});
