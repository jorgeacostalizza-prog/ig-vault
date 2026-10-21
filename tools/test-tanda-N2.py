# N2: tarjeta limpia, doble toque, lector, favoritas, colecciones, lotes únicos, sync con GitHub simulado entre 2 aparatos, duplicados
import json, sys, base64, hashlib, itertools
from playwright.sync_api import sync_playwright
A="C:/Users/PC/DeskBox/Apps/CODE/IG Info extractor Code/ig-vault-apk/src/assets/"; HTML="file:///"+A+"index.html"
sem=json.load(open(A+"semilla.json")); ERR=[]; res=[]
def ok(t,v,x=""):
    print(("  OK   " if v else "  FALLA")+" | "+t+(" | "+str(x)[:300] if x and not v else "")); res.append(bool(v))
GH={"repo":False,"files":{}}  # path -> (sha, bytes)
CAPS={"B1":"Mira esta herramienta Superpowers para Claude Code, skills gratis open source github.com/obra/superpowers"}
def gh(m,url,hd,body):
    h=json.loads(hd or "{}"); raw="raw" in h.get("Accept","")
    path=url.split("api.github.com")[1].split("?")[0]
    if path=="/user": return {"status":200,"body":json.dumps({"login":"jorge"})}
    if path=="/user/repos" and m=="POST": GH["repo"]=True; return {"status":201,"body":"{}"}
    if path=="/repos/jorge/ig-extractor-datos": return {"status":200,"body":json.dumps({"private":True})} if GH["repo"] else {"status":404,"body":""}
    pre="/repos/jorge/ig-extractor-datos/contents/"
    if path.startswith(pre):
        p=path[len(pre):]
        if m=="GET":
            if p in GH["files"]:
                sha,b=GH["files"][p]
                return {"status":200,"body":b.decode()} if raw else {"status":200,"body":json.dumps({"sha":sha,"content":base64.b64encode(b).decode()})}
            kids=[{"name":k[len(p)+1:],"sha":v[0]} for k,v in GH["files"].items() if k.startswith(p+"/")]
            return {"status":200,"body":json.dumps(kids)} if kids else {"status":404,"body":""}
        if m=="PUT":
            d=json.loads(body); cur=GH["files"].get(p)
            if cur and d.get("sha")!=cur[0]: return {"status":409,"body":"{}"}
            if not cur and d.get("sha"): return {"status":409,"body":"{}"}
            b=base64.b64decode(d["content"]); sha=hashlib.sha1(b).hexdigest(); GH["files"][p]=(sha,b)
            return {"status":201,"body":json.dumps({"content":{"sha":sha}})}
    return {"status":404,"body":""}
def http(m,url,hd,body):
    if "api.github.com" in url and ("/user" in url or "ig-extractor-datos" in url): return gh(m,url,hd,body)
    if "instagram.com/p/" in url and "embed" not in url:
        code=url.split("/p/")[1].split("/")[0]
        if code not in CAPS: return {"status":404,"body":""}
        return {"status":200,"url":url,"body":'<meta property="og:image" content="https://scontent.cdninstagram.com/b.jpg">{"caption":{"text":'+json.dumps(CAPS[code])+'},"code":"'+code+'"}'}
    return {"status":404,"url":url,"body":""}
INIT="""(()=>{window.Native={claves:()=>'{}',copiar(t){window.__cp=t},compartir(){},abrir(){},pegado:()=>"",
 http:(id,...a)=>window.__py('http',a).then(r=>window.__r(id,JSON.stringify(r))),
 frames:(id)=>window.__r(id,'{"status":0}'),pagina:(id)=>window.__r(id,'{}'),voz:(id)=>window.__r(id,'{"status":0,"body":""}'),foto:(id)=>window.__r(id,'{"status":0}')}})()"""
cyc=itertools.cycle([0,1,2])
def pagina(pw,ancho,datos,ctx=None):
    br=pw.chromium.launch(); c=br.new_context(viewport={"width":ancho,"height":860}); pg=c.new_page()
    pg.on("pageerror",lambda e:ERR.append(str(e)))
    pg.on("console",lambda m:ERR.append(m.text) if m.type=="error" and "Failed to load resource" not in m.text and "ERR_" not in m.text else None)
    pg.expose_function("__py",lambda n,a:http(*a)); pg.add_init_script(INIT)
    if datos is not None: pg.add_init_script("if(!localStorage.getItem('igv'))localStorage.setItem('igv',"+json.dumps(json.dumps(datos))+")")
    def img(r):
        u=r.request.url
        if "cdninstagram" in u or "githubusercontent" in u: r.fulfill(path="C:/Users/PC/DeskBox/Apps/CODE/IG Info extractor Code/ig-vault-apk/capturas/f%d.png"%next(cyc),headers={"Access-Control-Allow-Origin":"*"})
        else: r.abort()
    pg.route(lambda u: any(x in u for x in (".jpg",".png",".jpeg","cdninstagram","opengraph","thum.io")) and not u.startswith("file:"), img)
    pg.goto(HTML, wait_until="domcontentloaded"); pg.wait_for_timeout(1800); return br,pg
cards=[dict(c,id="s%d"%i) for i,c in enumerate(sem["cards"])]
with sync_playwright() as p:
  for ancho,nom in ((390,"movil"),(1280,"pc")):
    print("== "+nom); GH["repo"]=False; GH["files"]={}
    br,pg=pagina(p,ancho,{"cards":cards,"cfg":{}})
    titulos=pg.evaluate("db.cards.map(c=>c.titulo)")
    print("   quedan", len(titulos), "fichas")
    ok("duplicados: Orchestrator / Codex Security en 1", sum(1 for t in titulos if t.lower().startswith("orchestrator"))<=1 and sum(1 for t in titulos if "codex security de openai" in t.lower())==1, [t for t in titulos if "rchestr" in t or "Codex" in t])
    ok("ids únicos", len(set(pg.evaluate("db.cards.map(c=>c.id)")))==len(titulos))
    ok("tarjeta: 5 botones (quiero, fav, guardar, hecho, descartar) + Leer todo", pg.locator("#feed .fc").first.locator(".fbt .fb").count()==5 and pg.locator("#feed .fc .fleer").count()>0)
    art=pg.locator("#feed .fc").first; cid=art.get_attribute("data-id")
    box=art.locator(".fph").bounding_box(); x=box["x"]+box["width"]/2; y=box["y"]+box["height"]/2
    pg.mouse.click(x,y); pg.wait_for_timeout(90); pg.mouse.click(x,y); pg.wait_for_timeout(700)
    ok("doble toque en la foto = Lo quiero", pg.evaluate("db.cards.find(c=>c.id==='%s').estadoUso"%cid)=="quiero", pg.evaluate("db.cards.find(c=>c.id==='%s').estadoUso"%cid))
    ok("doble toque NO abre el lector", not pg.evaluate("document.querySelector('#lector').classList.contains('on')"))
    ok("corazón marcado en la tarjeta", art.locator(".fb[data-fa=quiero].on").count()==1)
    pg.screenshot(path="/home/claude/igx/t/n2-feed-%s.png"%nom)
    pg.mouse.click(x,y); pg.wait_for_timeout(800)
    ok("un toque en la foto abre «Leer todo»", pg.evaluate("document.querySelector('#lector').classList.contains('on') && lectorId==='%s'"%cid))
    ok("lector con Qué es, Cómo empezar y Links", all(t in pg.inner_text("#lectC") for t in ("QUÉ ES","CÓMO EMPEZAR","LINKS")), pg.inner_text("#lectC")[:300])
    pg.screenshot(path="/home/claude/igx/t/n2-lector-%s.png"%nom)
    pg.click("#lSig"); pg.wait_for_timeout(300)
    ok("Siguiente pasa a otra ficha", pg.evaluate("lectorId")!=cid)
    pg.click("#lector .lbar [data-fa=fav]"); pg.wait_for_timeout(200)
    fid=pg.evaluate("lectorId"); ok("favorita desde el lector", pg.evaluate("db.cards.find(c=>c.id==='%s').fav"%fid)==True)
    pg.click("#lector .lbar [data-fa=col]"); pg.wait_for_timeout(200)
    pg.fill("#colN","Para instalar"); pg.click("#colAdd"); pg.wait_for_timeout(200)
    ok("colección creada y ficha dentro", pg.evaluate("(db.cols||[]).length===1 && db.cards.find(c=>c.id==='%s').cols.length===1"%fid))
    pg.screenshot(path="/home/claude/igx/t/n2-col-%s.png"%nom)
    pg.click("#colOk"); pg.evaluate("window.__atras()"); pg.wait_for_timeout(200)
    ok("atrás cierra el lector", not pg.evaluate("document.querySelector('#lector').classList.contains('on')"))
    pg.click("#fbar [data-fm=fav]"); pg.wait_for_timeout(200)
    ok("filtro Favoritas", pg.locator("#feed .fc").count()==1)
    pg.select_option("#fCol", label="🔖 Para instalar") if pg.locator("#fCol").count() else None; pg.wait_for_timeout(200)
    ok("filtro por colección", pg.locator("#feed .fc").count()==1)
    pg.click("#fbar [data-fm=ti]"); pg.select_option("#fCol", value=""); pg.wait_for_timeout(200)
    # orden estable al marcar
    ids0=pg.evaluate("[...document.querySelectorAll('#feed .fc')].slice(0,6).map(e=>e.dataset.id)")
    pg.locator("#feed .fc").nth(2).locator("[data-fa=quiero]").click(); pg.wait_for_timeout(300)
    ids1=pg.evaluate("[...document.querySelectorAll('#feed .fc')].slice(0,6).map(e=>e.dataset.id)")
    ok("el orden no salta al marcar", ids0==ids1)
    # sincronización: activar en A
    pg.click("nav button[data-t=ajustes]"); pg.fill("#sTok","ghp_prueba123"); pg.click("#sAct")
    pg.wait_for_function("syncUlt>0 || syncError", timeout=30000); pg.wait_for_timeout(500)
    ok("sync activada: repo privado creado y fichas subidas", GH["repo"] and any(k.startswith("fichas/") for k in GH["files"]) and "meta.json" in GH["files"], pg.evaluate("syncError"))
    nA=pg.evaluate("db.cards.length")
    # aparato B vacío
    br2,pb=pagina(p,ancho,{"cards":[],"cfg":{}})
    pb.evaluate("db.cfg.sync={token:'ghp_prueba123',owner:'jorge'};guardar();sincronizar()"); pb.wait_for_function("syncUlt>0 || syncError", timeout=30000); pb.wait_for_timeout(800)
    ok("el otro aparato recibe todas las fichas", pb.evaluate("db.cards.length")==nA, (pb.evaluate("db.cards.length"),nA,pb.evaluate("syncError")))
    ok("recibe favorita, Lo quiero y colección", pb.evaluate("db.cards.find(c=>c.id==='%s').fav && db.cards.find(c=>c.id==='%s').estadoUso==='quiero' && db.cols.length===1"%(fid,cid)))
    # B descarta una y pega un lote; A lo recibe
    pb.evaluate("db.cards.find(c=>c.id==='%s').estadoUso='descartada';guardar()"%cid)
    pb.click("nav button[data-t=pegar]"); pb.fill("#txt","https://www.instagram.com/p/B1/"); pb.click("#bOrdenar")
    pb.wait_for_function("!corriendo && db.cards.some(c=>c.url.includes('/p/B1/') && c.estado!=='pendiente')", timeout=60000); pb.wait_for_timeout(300)
    pb.evaluate("sincronizar()"); pb.wait_for_function("!sincronizando", timeout=30000); pb.wait_for_timeout(300)
    lB=pb.evaluate("loteDe(db.cards.find(c=>c.url.includes('/p/B1/')))")
    pg.evaluate("sincronizar()"); pg.wait_for_function("!sincronizando", timeout=30000); pg.wait_for_timeout(500)
    ok("A recibe el lote pegado en B", pg.evaluate("db.cards.some(c=>c.url.includes('/p/B1/'))"))
    ok("A recibe el «Descartar» de B", pg.evaluate("db.cards.find(c=>c.id==='%s').estadoUso"%cid)=="descartada")
    ok("el lote de B sale con fecha en A", pg.evaluate("etqLote(%d)"%lB).startswith("Lote ") and "hoy" in pg.evaluate("etqLote(%d)"%lB), pg.evaluate("etqLote(%d)"%lB))
    # A borra una; B la pierde
    did=pg.evaluate("db.cards[5].id"); pg.evaluate("db.cards=db.cards.filter(c=>c.id!=='%s');guardar();sincronizar()"%did); pg.wait_for_function("!sincronizando", timeout=30000); pg.wait_for_timeout(300)
    pb.evaluate("sincronizar()"); pb.wait_for_function("!sincronizando", timeout=30000); pb.wait_for_timeout(300)
    ok("borrar en A borra en B", not pb.evaluate("db.cards.some(c=>c.id==='%s')"%did))
    ok("minis subidas a la nube", any(k.startswith("minis/") for k in GH["files"]), list(GH["files"])[:12])
    ok("A y B con el mismo número de fichas", pg.evaluate("db.cards.length")==pb.evaluate("db.cards.length"), (pg.evaluate("db.cards.length"),pb.evaluate("db.cards.length")))
    pg.click("nav button[data-t=ajustes]") if False else None
    pg.screenshot(path="/home/claude/igx/t/n2-ajustes-%s.png"%nom, full_page=True)
    ok("sin desbordamiento horizontal", pg.evaluate("document.documentElement.scrollWidth<=innerWidth+1"))
    br2.close(); br.close()
print("ERRORES JS:",ERR or "ninguno"); print("RESULTADO %d/%d"%(sum(res),len(res)))
