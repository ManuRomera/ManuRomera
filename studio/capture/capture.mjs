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
      socketConnected: Boolean(globalThis.game?.socket?.connected),
      webgl2: (()=>{try{return Boolean(document.createElement("canvas").getContext("webgl2"));}catch{return false;}})(),
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
      " socketConnected="+status.socketConnected+" webgl2="+status.webgl2+
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
  const view=await page.evaluate(()=>String(globalThis.game?.view || ""));
  if(view==="auth") throw Error(
    "El servidor muestra autenticación de administración (auth). "+
    "Inicia Wicked Ones desde la configuración de Foundry antes de grabar."
  );
  if(view==="game") {await ready(page);return;}
  // Foundry v13 renders its user picker inside an ApplicationV2 container,
  // which is not necessarily a <form>. Query the controls themselves.
  const selector=page.locator(
    'select[name="userid"], select[name="userId"], select[name="user"]'
  ).first();
  try {
    await selector.waitFor({state:"visible",timeout:15000});
  } catch {
    throw Error("No se encuentra el selector de usuarios visible de Foundry v13.");
  }
  const choices=await selector.locator("option").allTextContents();
  if(!choices.some(name=>name.trim()===config.user)) {
    throw Error("El usuario GM configurado no figura en la pantalla de entrada.");
  }
  await selector.selectOption({label:config.user,timeout:8000});
  const password=page.locator(
    'input[name="password"], input[type="password"]'
  ).first();
  if(await password.count()) await password.fill(config.pass);
  else expect(!config.pass, "No se encuentra el campo de contraseña.");

  // Prefer the precise join action, never the separate 'Return to Setup'
  // submit button which can be a sibling in Foundry V13.
  let joinButton=page.getByRole("button",{
    name:/join game session|join session|unirse a la partida|entrar en la partida|iniciar sesión/i
  }).first();
  if(!await joinButton.isVisible().catch(()=>false)) {
    const joinForm=selector.locator("xpath=ancestor::form[1]");
    joinButton=joinForm.locator('button[type="submit"], input[type="submit"]').first();
  }
  if(!await joinButton.isVisible().catch(()=>false)) {
    joinButton=page.locator(
      '#join-game button[name="join"], button[data-action="join"], button#join-game, button#join'
    ).first();
  }
  if(!await joinButton.isVisible().catch(()=>false)) {
    throw Error("No se encuentra el botón de entrada al mundo; no se intenta otro botón.");
  }
  const post=page.waitForResponse(r=>{
    try{return r.request().method()==="POST" && new URL(r.url()).pathname.endsWith("/join");}
    catch{return false;}
  },{timeout:12000}).catch(()=>null);
  await joinButton.click({timeout:8000});
  const result=await post;
  const answer=result ? await result.json().catch(()=>null) : null;
  const rawMessage=String(answer?.message || answer?.error || "").toLowerCase();
  const reason=/already|online|connected|in use|utilizad|conectad|sesión abierta/.test(rawMessage)
    ? "ACCOUNT_OCCUPIED"
    : /password|contraseña|access key|clave/.test(rawMessage)
      ? "ACCESS_KEY_REJECTED"
      : /denied|forbidden|unauthorized|autoriz/.test(rawMessage)
        ? "ACCESS_DENIED" : "UNCLASSIFIED";
  const hasRedirect=typeof answer?.redirect==="string" && answer.redirect.length>0;
  const statusTag=(typeof answer?.status==="string" ? answer.status : String(answer?.status ?? "none"))
    .replace(/[^A-Za-z0-9_-]/g,"").slice(0,30);
  console.log("Foundry entrada: "+(result ? ("HTTP "+result.status()) : "sin respuesta POST observada")+
    " redirect="+hasRedirect+" category="+reason+" statusTag="+statusTag+
    " responseFields="+(answer && typeof answer==="object" ? Object.keys(answer).filter(k=>["redirect","message","error","status","success"].includes(k)).join(",") : "none"));
  if(hasRedirect) {
    const destination=new URL(answer.redirect,config.url);
    const home=new URL(config.url);
    if(destination.origin!==home.origin || !destination.pathname.endsWith("/game")) {
      throw Error("El servidor ofrece una redirección fuera del destino Foundry esperado.");
    }
    // Foundry joins by asynchronously updating localStorage and navigating
    // from its form handler. Give it time to finish before manual fallback.
    const navigated=await page.waitForURL(url=>{
      try {return new URL(url).pathname.endsWith("/game");}catch{return false;}
    },{timeout:12000}).then(()=>true).catch(()=>false);
    const storedUser=await page.evaluate(()=>Boolean(localStorage.getItem("fvtt-current-user"))).catch(()=>false);
    const cookieCount=(await page.context().cookies()).length;
    console.log("Foundry sesión: redirectObserved="+navigated+
      " storedUser="+storedUser+" cookieCount="+cookieCount+
      " page="+(new URL(page.url()).pathname.endsWith("/game")?"game":"not-game"));
    if(!navigated && !page.url().endsWith("/game")) {
      await page.goto(destination.href,{waitUntil:"domcontentloaded",timeout:45000});
    }
  } else if(result) {
    const occupied=await page.evaluate(name=>
      Boolean(globalThis.game?.users?.contents?.find?.(u=>u.name===name)?.active)
    ,config.user).catch(()=>false);
    throw Error("Foundry no ha autorizado la entrada. Motivo="+reason+
      " userAlreadyActive="+occupied+"; comprueba usuario y sesión actual.");
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
    // Report only coarse navigation and connection states, never network URLs,
    // cookies, page text, world content or credentials.
    authPage.on("framenavigated",frame=>{
      if(frame!==authPage.mainFrame())return;
      const path=new URL(frame.url()).pathname;
      console.log("Foundry navegación: "+(path.endsWith("/game")?"game":
        path.endsWith("/join")?"join":path.endsWith("/setup")?"setup":"other"));
    });
    authPage.on("websocket",ws=>{
      console.log("Foundry conexión WebSocket: creada");
      ws.on("close",()=>console.log("Foundry conexión WebSocket: cerrada"));
    });
    authPage.on("pageerror",e=>{
      const msg=String(e?.message||"");
      const category=/webgl|canvas|renderer/i.test(msg)?"GRAPHICS":
        /websocket|socket|network|connect/i.test(msg)?"NETWORK":"OTHER";
      console.log("Foundry error del navegador: "+category);
    });
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
