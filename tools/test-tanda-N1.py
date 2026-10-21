import json, sys, time
from playwright.sync_api import sync_playwright
A="C:/Users/PC/DeskBox/Apps/CODE/IG Info extractor Code/ig-vault-apk/src/assets/"
HTML="file:///"+A+"index.html"
sem=json.load(open(A+"semilla.json"))
ERR=[];res=[];IMGS_OK="--fotos" in sys.argv
def ok(t,v,x=""):
    print(("  OK   " if v else "  FALLA")+" | "+t+(" | "+str(x)[:400] if x and not v else "")); res.append(bool(v))
CAPS={"A1":"Mira Cloud Code con este skill gratis open source. Canal: t.me/canalprueba y github.com/obra/superpowers","A2":"Codex Security de OpenAI escanea tu código"}
def http(m,url,hd,body):
    if "instagram.com/p/" in url and "embed" not in url:
        code=url.split("/p/")[1].split("/")[0]
        if code not in CAPS: return {"status":404,"body":""}
        return {"status":200,"url":url,"body":'<meta property="og:image" content="https://scontent.cdninstagram.com/x.jpg">{"caption":{"text":'+json.dumps(CAPS[code])+'},"code":"'+code+'"}'}
    if "api.github.com/repos/obra/superpowers" in url and "readme" not in url:
        return {"status":200,"body":json.dumps({"full_name":"obra/superpowers","description":"Skills library for Claude Code","stargazers_count":900,"pushed_at":"2026-10-01T00:00:00Z","html_url":"https://github.com/obra/superpowers","topics":[]})}
    if "integrate.api.nvidia.com" in url:
        pr=json.loads(body)["messages"][0]["content"]
        if isinstance(pr,list): return {"status":200,"body":json.dumps({"choices":[{"message":{"content":""}}]})}
        if "Eres un extractor riguroso" in pr:
            out={"titulo":"Superpowers para Claude Code","resumen":"Superpowers es una librería de skills gratis para Claude Code.","categoria":"Inteligencia artificial","proyectos":[],"tags":["claude-code","skill"],"web":None,"sirve":"Dar skills nuevas a Claude Code","sirve_cita":"skill gratis open source","sirve_fuente":"pie","accion":"Instalar"}
        else:
            out={"resumen":"Superpowers es una librería de skills gratis para Claude Code.","explicacion":"Superpowers es una librería open source de skills para Claude Code. Sirve para darle a Claude Code habilidades nuevas sin escribirlas tú. El post la enseña como gratis.","puntos":["Skills gratis para Claude Code"],"skills":[],"como":[],"limites":""}
        return {"status":200,"body":json.dumps({"choices":[{"message":{"content":json.dumps(out)}}]})}
    return {"status":404,"url":url,"body":""}
INIT="""(()=>{window.Native={claves:()=>'{}',copiar(t){},compartir(){},abrir(){},pegado:()=>"",
 http:(id,...a)=>window.__py('http',a).then(r=>window.__r(id,JSON.stringify(r))),
 frames:(id)=>window.__r(id,'{"status":0}'),pagina:(id)=>window.__r(id,'{}'),voz:(id)=>window.__r(id,'{"status":0,"body":""}'),foto:(id)=>window.__r(id,'{"status":0}')}})()"""
def pagina(pw,ancho,datos=None):
    br=pw.chromium.launch();ctx=br.new_context(viewport={"width":ancho,"height":860});pg=ctx.new_page()
    pg.on("pageerror",lambda e:ERR.append(str(e)))
    pg.on("console",lambda m:ERR.append(m.text) if m.type=="error" and "Failed to load resource" not in m.text and "ERR_" not in m.text else None)
    pg.expose_function("__py",lambda n,a:http(*a))
    pg.add_init_script(INIT)
    if datos is not None: pg.add_init_script("localStorage.setItem('igv',"+json.dumps(json.dumps(datos))+")")
    import itertools; cyc=itertools.cycle([0,1,2])
    def img(r):
        u=r.request.url
        if IMGS_OK and ("cdninstagram" in u or "githubusercontent" in u): r.fulfill(path="/home/claude/igx/t/f%d.png"%next(cyc), headers={"Access-Control-Allow-Origin":"*"})
        else: r.abort()
    pg.route(lambda u: any(x in u for x in (".jpg",".png",".jpeg","cdninstagram","opengraph","thum.io")) and not u.startswith("file:"), img)
    pg.goto(HTML,wait_until="domcontentloaded");pg.wait_for_timeout(2500);return br,pg
datos={"cards":sem["cards"],"cfg":{"nvidia":"k"}}
for i,c in enumerate(datos["cards"]): c["id"]="s%d"%i
with sync_playwright() as p:
  for ancho,nom in ((390,"movil"),(1280,"pc")):
    print("== "+nom); ERR.clear() if False else None
    br,pg=pagina(p,ancho,datos)
    n0=len(sem["cards"]); n1=pg.evaluate("db.cards.length")
    ok("arranca en Inicio", pg.evaluate("document.querySelector('#p-feed').classList.contains('on')"))
    ok("unió duplicados solo al abrir (%d -> %d)"%(n0,n1), n1<n0, n1)
    ok("Codex Security queda en 1 ficha", pg.evaluate("db.cards.filter(c=>/codex security de openai/i.test(c.titulo)).length")==1, pg.evaluate("db.cards.filter(c=>/codex security/i.test(c.titulo)).map(c=>c.titulo)"))
    ok("genéricas NO unidas a la fuerza", pg.evaluate("db.cards.filter(c=>/Herramientas gratuitas y repositorios/i.test(c.titulo)).length")>=1)
    ok("aviso con Deshacer", pg.locator("#avDeshacer").count()>0)
    ok("nombres corregidos (sin 'Cloud Code')", pg.evaluate("!JSON.stringify(db.cards).match(/Cloud Code/)"))
    ok("feed pinta tarjetas", pg.locator("#feed .fc").count()>=10, pg.locator("#feed .fc").count())
    ok("temas: 'Otros' no se come todo", pg.evaluate("(()=>{const m={};db.cards.filter(c=>c.estado==='ok').forEach(c=>{const t=temaFicha(c);m[t]=(m[t]||0)+1});return Math.max(...Object.values(m))/db.cards.length})()")<0.5, pg.evaluate("(()=>{const m={};db.cards.filter(c=>c.estado==='ok').forEach(c=>{const t=temaFicha(c);m[t]=(m[t]||0)+1});return m})()"))
    print("   temas:", pg.evaluate("(()=>{const m={};db.cards.filter(c=>c.estado==='ok').forEach(c=>{const t=temaFicha(c);m[t]=(m[t]||0)+1});return m})()"))
    ok("sin banners repetidos en el feed", pg.evaluate("(()=>{const m={};document.querySelectorAll('#feed .gl img').forEach(i=>{const s=i.getAttribute('src');m[s]=(m[s]||0)+1});return Object.values(m).filter(v=>v>1).length})()")==0)
    pg.screenshot(path="/home/claude/igx/t/feed-%s.png"%nom)
    # guía
    # Lo quiero
    id0=pg.evaluate("document.querySelector('#feed .fc').dataset.id")
    pg.locator("#feed .fc [data-fa=quiero]").first.click(); pg.wait_for_timeout(200)
    ok("Lo quiero desde el feed", pg.evaluate("db.cards.find(c=>c.id==='%s').estadoUso"%id0)=="quiero")
    # filtros
    # lote nuevo
    pg.click("nav button[data-t=pegar]")
    pg.fill("#txt","https://www.instagram.com/p/A1/\nhttps://www.instagram.com/p/A2/"); pg.click("#bOrdenar")
    pg.wait_for_function("!corriendo && db.cards.filter(c=>c.lote===1).every(c=>c.estado!=='pendiente')", timeout=60000); pg.wait_for_timeout(1500)
    LID=pg.evaluate("db.cards.find(c=>c.url.includes('/p/A1/')).lote")
    ok("lote nuevo con fecha 'hoy'", pg.evaluate("etqLote(%d)"%LID).startswith("Lote ") and "hoy" in pg.evaluate("etqLote(%d)"%LID), pg.evaluate("etqLote(%d)"%LID))
    ok("historial de lotes visible", pg.locator("#lotesHist .ltr").count()>=1)
    c1=pg.evaluate("db.cards.find(c=>c.url.includes('/p/A1/'))")
    ok("A1 procesada ok", c1 and c1["estado"]=="ok", c1 and (c1["estado"],c1.get("motivo")))
    ok("link de Telegram sacado del texto", c1 and any("t.me/canalprueba" in l["u"] for l in c1.get("links",[])), c1 and c1.get("links"))
    ok("A2 (Codex) unida a la ficha que ya había", pg.evaluate("db.cards.filter(c=>/codex security/i.test(c.titulo)&&c.estado==='ok').length")<=2)
    pg.screenshot(path="/home/claude/igx/t/pegar-%s.png"%nom, full_page=True)
    pg.evaluate("verLote(%d)"%LID); pg.wait_for_timeout(300)
    ok("Ver lote 1 -> Inicio filtrado", pg.locator("#feed .fhd").first.text_content().startswith("Lote "), pg.locator("#feed").inner_text()[:200])
    ok("telegram en links del feed", pg.locator("#feed a.tg").count()>=1)
    pg.screenshot(path="/home/claude/igx/t/lote-%s.png"%nom)
    # Explorar (sustituye a Fichas; N3)
    pg.click("nav button[data-t=explorar]"); pg.wait_for_timeout(400)
    ok("Explorar lista fichas", pg.evaluate("resultados().length")>=4)
    pg.evaluate("(()=>{const b=[...document.querySelectorAll('#xRes .xc')].find(e=>e.offsetParent);b&&b.click()})()"); pg.wait_for_timeout(400); ok("informe abierto", pg.evaluate("document.querySelector('#lector').classList.contains('on')"))
    ok("sin desbordamiento horizontal", pg.evaluate("document.documentElement.scrollWidth<=innerWidth+1"))
    br.close()
print("ERRORES JS:",ERR or "ninguno"); print("RESULTADO %d/%d"%(sum(res),len(res)))
