# Tanda R5-R7 (19/10/2026): velocidad de la IA (tope, paralelo, enfriar 429, imágenes a la vez), aviso «Sin IA» tardío y pie de otro post.
# Tiempos a escala: «el servidor corta a los 30 s» se simula con HANG ms y el tope de 14 s con TOPE ms (se ajusta con la constante).
# Uso: python test-tanda-R5.py            (versión nueva)   |   python test-tanda-R5.py base   (index.antes-R5.html, solo mide S1)
import sys, os, time; sys.path.insert(0, "C:/Users/PC/DeskBox/Apps/CODE/IG Info extractor Code/ig-vault-apk/tools")
import arnes
from arnes import *
CD = BASE + "capturas/tanda-R5/"; os.makedirs(CD, exist_ok=True)
BASEMODE = len(sys.argv) > 1 and sys.argv[1] == "base"
if BASEMODE: arnes.HTML = "file:///" + BASE + "BACKUPS/index.antes-R5.html"
HANG, TOPE = 2000, 1000

MOCK = """()=>{
 window.__esc={nv:'ok',or:'ok'}; window.__calls={nv:0,or:0}; window.__lat={nv:200,or:200}; window.__hang=%d; window.__prim={nv:0,or:0};
 if (typeof TOPE_IA_MS!=='undefined') TOPE_IA_MS=%d;
 http = async (url, opt={}) => {
  const isNv=url.includes('nvidia.com'), isOr=url.includes('openrouter.ai/api/v1/chat');
  if(!isNv&&!isOr) return await window.__py('http',[opt.method||'GET',url,opt.headers||{},opt.body||'']);
  const k=isNv?'nv':'or'; __calls[k]++; const m=__esc[k];
  if(m==='hang'){ await dormir(__hang); return {status:0,body:''}; }
  if(m==='429') return {status:429,body:''};
  if(m==='500uno' && !Array.isArray(JSON.parse(opt.body).messages[0].content) && __prim[k]++===0){ await dormir(100); return {status:500,body:''}; }
  await dormir(__lat[k]);
  const c=JSON.parse(opt.body).messages[0].content;
  if(Array.isArray(c)) return {status:200,body:JSON.stringify({choices:[{message:{content:'Imagen: texto '+k}}]})};
  if(window.__plano) return {status:200,body:JSON.stringify({choices:[{message:{content:'respuesta '+k}}]})};
  return await window.__py('http',[opt.method,'https://integrate.api.nvidia.com/v1/chat/completions',opt.headers||{},opt.body||'']);
 };
 enfria={}; muertos={};
}""" % (HANG, TOPE)

def ms(pg, js, *a):
    t = time.time(); r = pg.evaluate(js, *a) if a else pg.evaluate(js); return r, int((time.time() - t) * 1000)

with sync_playwright() as p:
    for ancho, nom in ((390, "movil"), (1280, "pc")):
        print("== " + nom + (" (BASE antigua)" if BASEMODE else ""))
        IA["modo"] = "ok"; IA["extra"] = {}
        br, pg = pagina(p, ancho)
        pg.evaluate("db.cfg={nvidia:'nvapi-x',openrouter:'sk-or-x'}")
        pg.evaluate(MOCK); pg.evaluate("window.__plano=true")
        # S1: NVIDIA se cuelga, OpenRouter contesta
        pg.evaluate("__esc={nv:'hang',or:'ok'};enfria={};muertos={}")
        r, t = ms(pg, "async()=>await chat('hola')")
        print("  [S1 NV colgada + OR ok] %d ms -> %s" % (t, r)); open(CD + "tiempos-%s.txt" % ("base" if BASEMODE else "nuevo"), "a").write("%s S1 %d ms\n" % (nom, t))
        if BASEMODE: br.close(); continue
        ok("S1 responde la IA que contesta (OpenRouter)", r == "respuesta or", r)
        ok("S1 no espera a la colgada (< 1,5 s con tope de %d ms)" % TOPE, t < 1500, t)
        # S2: OpenRouter da 429, NVIDIA ok; luego una 2ª petición NO vuelve a llamar a la clave enfriada
        pg.evaluate("__esc={nv:'ok',or:'429'};enfria={};muertos={};__calls={nv:0,or:0};__lat.nv=300")
        r1, t1 = ms(pg, "async()=>await chat('hola')"); r2, t2 = ms(pg, "async()=>await chat('otra')")
        c = pg.evaluate("__calls")
        ok("S2 429 en una clave: gana la otra", r1 == "respuesta nv" and r2 == "respuesta nv", (r1, r2))
        ok("S2 la clave con 429 se enfría (1 sola llamada a OpenRouter en 2 fichas)", c["or"] == 1, c)
        ok("S2 queda enfriada en el estado", pg.evaluate("estaFria('OpenRouter')"))
        # S3: ambas lentas: gana la primera; ambas colgadas: acaba acotado y devuelve null
        pg.evaluate("__esc={nv:'ok',or:'ok'};enfria={};__lat={nv:900,or:700}")
        r, t = ms(pg, "async()=>await chat('hola')")
        ok("S3 ambas lentas: gana la primera en llegar (~700 ms)", r == "respuesta or" and t < 1300, (r, t))
        pg.evaluate("__esc={nv:'hang',or:'hang'};enfria={}")
        r, t = ms(pg, "async()=>await chat('hola')")
        print("  [S3 ambas colgadas] %d ms -> %s" % (t, r))
        ok("S3 ambas colgadas: null y acotado (< 4,5 s; antes ~30 s por modelo)", r is None and t < 4500, (r, t))
        # S4: 3 imágenes a la vez
        pg.evaluate("__esc={nv:'ok',or:'ok'};enfria={};__lat={nv:800,or:800}")
        r, t = ms(pg, "async()=>await leerImgs(['u1','u2','u3'])")
        ok("S4 3 imágenes en paralelo (~0,8 s, no 2,4 s)", t < 1600 and r.count("Imagen") == 3, (t, r))
        # S5: lote completo (Instagram) con NVIDIA colgada y un 500 -> sale «Esperando a la IA…»
        pg.evaluate("window.__plano=false")
        CAPS.clear(); CAPS.update({"RB": "foo-cli install with npx. Fast CLI to run jobs and shell chores. https://x.test/foo"})
        pg.evaluate("__esc={nv:'hang',or:'500uno'};enfria={};muertos={};__lat={nv:200,or:300};db.cards=[];db.bn=0;db.cfg={nvidia:'nvapi-x',openrouter:'sk-or-x'}")
        pg.fill("#txt", "https://www.instagram.com/p/RB/"); t0 = time.time(); pg.click("#bOrdenar"); vio = False
        for _ in range(300):
            pg.wait_for_timeout(100)
            if "Esperando a la IA" in pg.inner_text("#progS"): vio = True; pg.screenshot(path=CD + "esperando-%s.png" % nom)
            if pg.evaluate("!corriendo"): break
        t = int((time.time() - t0) * 1000); est = pg.evaluate("db.cards.map(c=>c.estado+'|'+c.resumen.slice(0,40))")
        print("  [S5 lote con NV colgada] %d ms -> %s" % (t, est))
        ok("S5 la ficha acaba bien con una IA colgada", len(est) == 1 and est[0].startswith("ok|foo-cli"), est)
        ok("S5 el progreso dijo «Esperando a la IA…» al reintentar", vio)
        ok("S5 el lote termina en < 5 s (antes 60-110 s)", t < 5000, t)
        pg.screenshot(path=CD + "lote-%s.png" % nom)
        # R6: sin saber las claves no se muestra «Sin IA»
        pg.evaluate("db.cfg={nvidia:'',openrouter:''};clavesListas=false;pintaAvisoIA()")
        ok("R6 mientras se cargan las claves NO aparece «Sin IA»", pg.evaluate("[...document.querySelectorAll('.avIA')].every(e=>getComputedStyle(e).display==='none')"))
        pg.evaluate("clavesListas=true;pintaAvisoIA()")
        ok("R6 ya cargadas y sin clave: sí aparece", pg.evaluate("[...document.querySelectorAll('.avIA')].some(e=>getComputedStyle(e).display!=='none'&&e.textContent.includes('Sin IA'))"))
        # R7: pie de otro post
        pg.evaluate("""()=>{window.__page=(cod)=>'<meta property="og:image" content="https://img.test/a.jpg">'
          +'{"caption":{"text":"Gemini 4 Argon is here \\\\u2014 frontier"},"code":"DepDOriT67X","x":1}{"caption":{"text":"Otro post distinto"},"code":"Deew3nshjRl"}'
          +(cod==='MIO'?'{"caption":{"text":"Ballroom in Focus archive"},"code":"MIO"}':'')}""")
        pg.evaluate("""()=>{const h0=http; http=async(u,o={})=>{ if(u.includes('instagram.com/p/')&&(o.headers||{})['User-Agent']&&/Googlebot/.test(o.headers['User-Agent'])){return {status:200,url:u,body:__page(u.includes('/MIO/')?'MIO':'AJENO')}} return h0(u,o)}}""")
        a = pg.evaluate("async()=>(await gbIG('https://www.instagram.com/p/AJENO/')).cap")
        b = pg.evaluate("async()=>(await gbIG('https://www.instagram.com/p/MIO/')).cap")
        ok("R7 pie de OTRO post en la página: no se usa como pie", a == "", a)
        ok("R7 pie pegado al código del propio post: sí se usa", b == "Ballroom in Focus archive", b)
        # R7: el texto no coincide con la voz -> Para revisar, sin afirmar nada
        r = pg.evaluate("""async()=>{ db.cfg={nvidia:'nvapi-x'}; db.cards=[];
          leerIG=async()=>({texto:'Gemini Argon frontier newest tackle hardest problems helps launch today',imgs:[],video:'https://v.test/v.mp4'});
          leerVoz=async()=>'Introducing Ballroom archive digital history curated community throwbacks culture legends performers mothers houses dancers vogue femme realness category runway';
          leerFrames=async()=>[];
          const k={id:'m1',url:'https://www.instagram.com/p/MM1/',tipo:'Instagram',estado:'pendiente',bloque:1,grupo:'AI',titulo:'',resumen:'',categoria:'',repos:[],tags:[],fuente:'',motivo:''};
          await analizar(k); return k.estado+'|'+k.motivo+'|'+k.categoria}""")
        ok("R7 pie y voz sin nada en común -> Para revisar con motivo claro", r == "revisar|El texto del post y el vídeo no coinciden|Para revisar", r)
        r = pg.evaluate("""async()=>{ leerIG=async()=>({texto:'Introducing Ballroom archive digital history curated community',imgs:[],video:'https://v.test/v.mp4'});
          const k={id:'m2',url:'https://www.instagram.com/p/MM2/',tipo:'Instagram',estado:'pendiente',bloque:1,grupo:'AI',titulo:'',resumen:'',categoria:'',repos:[],tags:[],fuente:'',motivo:''};
          await analizar(k); return k.estado}""")
        ok("R7 pie y voz que coinciden -> la ficha se hace normal", r == "ok", r)
        br.close()
fin()
