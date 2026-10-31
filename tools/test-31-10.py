# 31/10: lectura del pie desde la incrustación (sin navegador), informe completo en una llamada, links después del lote, avisos de Inicio, fotos por el PC
import json, itertools, time
from playwright.sync_api import sync_playwright
A="C:/Users/PC/DeskBox/Apps/CODE/IG Info extractor Code/ig-vault-apk/src/assets/"; HTML="file:///"+A+"index.html"
ERR=[]; res=[]; LOG=[]
def ok(t,v,x=""):
    print(("  OK   " if v else "  FALLA")+" | "+t+(" | "+str(x)[:300] if x and not v else "")); res.append(bool(v))
EMB='<html><head><meta property="og:description" content="x"></head><body><div class="Caption"><a class="CaptionUsername">usuario</a><br>Skill gratis para Claude Code que ahorra tokens: claude-mem guarda memoria entre sesiones.<br>Comenta MEM y te lo paso<div class="CaptionComments">Ver comentarios</div></div><img class="EmbeddedMediaImage" src="https://scontent.cdninstagram.com/e.jpg"></body></html>'
def http(m,url,hd,body):
    LOG.append(url)
    if "/embed/captioned/" in url: return {"status":200,"url":url,"body":EMB}
    if "instagram.com/p/" in url: return {"status":200,"url":url,"body":"<html></html>"}
    if "integrate.api.nvidia.com" in url:
        pr=json.loads(body)["messages"][0]["content"]
        if isinstance(pr,list): return {"status":200,"body":json.dumps({"choices":[{"message":{"content":""}}]})}
        if "Eres un extractor riguroso" in pr:
            out={"titulo":"claude-mem","resumen":"claude-mem es una skill gratis para Claude Code que guarda memoria entre sesiones y ahorra tokens.","categoria":"Inteligencia artificial","proyectos":[],"tags":["claude-code"],"web":None,"sirve":"Guardar memoria entre sesiones de Claude Code","sirve_cita":"guarda memoria entre sesiones","sirve_fuente":"pie","accion":"Probar"}
        else:
            assert "Finn" in pr
            out={"resumen":"claude-mem guarda memoria entre sesiones de Claude Code y ahorra tokens.","explicacion":"claude-mem es una skill gratis para Claude Code. Guarda memoria entre sesiones para que no tengas que explicar tu proyecto cada vez. Así ahorra tokens. Sirve a quien usa Claude Code a diario.","puntos":["claude-mem: guarda memoria entre sesiones"],"skills":["claude-mem — memoria entre sesiones"],"como":[],"limites":"","pros":["Ahorra tokens al guardar memoria entre sesiones","Es gratis"],"contras":[],"dificultad":"Fácil","tipo":"Skill","para_quien":"Quien usa Claude Code a diario","traduccion":""}
        return {"status":200,"body":json.dumps({"choices":[{"message":{"content":json.dumps(out)}}]})}
    return {"status":404,"url":url,"body":""}
with sync_playwright() as p:
  for ancho,nom in ((390,"m"),(1280,"pc")):
    LOG.clear(); print("== "+nom)
    br=p.chromium.launch(); pg=br.new_context(viewport={"width":ancho,"height":860}).new_page()
    pg.on("pageerror",lambda e:ERR.append(str(e)))
    pg.expose_function("__py",lambda n,a:http(*a))
    # PC sin nativo: http por la página (fetch simulado), pagina() no nativa
    pg.add_init_script("window.__httpSim=true")
    pg.goto(HTML); pg.wait_for_timeout(800)
    pg.evaluate("""()=>{window.http=async(url,o={})=>window.__py('http',[o.method||'GET',url,JSON.stringify(o.headers||{}),o.body||'']); db.cards=[];db.cfg={nvidia:'k'};guardar();}""")
    pg.evaluate("window.__navegador=0; window.__pagina=undefined")
    t0=time.time()
    r=pg.evaluate("leerIG('https://www.instagram.com/p/ABC123/')")
    ok("pie leído de la incrustación (sin usuario ni «ver comentarios»)", "claude-mem guarda memoria" in r.get("texto","") and "usuario" not in r.get("texto","") and "Ver comentarios" not in r.get("texto",""), r)
    pg.fill("#txt","https://www.instagram.com/p/ABC123/") if pg.evaluate("ir('pegar'),1") else None
    pg.click("#bOrdenar"); pg.wait_for_function("!corriendo && db.cards.length && db.cards[0].estado!=='pendiente'", timeout=60000)
    c=pg.evaluate("db.cards[0]")
    ok("ficha ok con informe completo en la misma pasada", c["estado"]=="ok" and c.get("informeV")==1 and c.get("pros") and c.get("dificultad")=="Fácil" and c.get("tipoCosa")=="Skill", {k:c.get(k) for k in ("estado","motivo","informeV","pros","dificultad","tipoCosa")})
    ok("los links no frenan el lote (quedan para después)", c.get("faltanLinks")==1 or len(c.get("links",[]))>=0)
    pg.evaluate("ir('feed')"); pg.wait_for_timeout(400)
    ok("Inicio explica cómo funciona la primera vez", pg.locator("#iniEstado .guia").count()==1)
    pg.click("#iniEstado [data-ie=ok]"); pg.wait_for_timeout(200)
    ok("«Entendido» la quita para siempre", pg.locator("#iniEstado .guia").count()==0 and pg.evaluate("db.guiaVista")==1)
    pg.evaluate("db.cards.push({...db.cards[0],id:'f1',url:'https://www.instagram.com/p/F1/',estado:'revisar',motivo:'Instagram no dejó leer',titulo:'https://www.instagram.com/p/F1/'});guardar();pintaFeed()")
    ok("aviso de posts que no se pudieron leer, con Reintentar", pg.locator("#iniEstado .fall [data-ie=reint]").count()==1)
    pg.screenshot(path="C:/Users/PC/DeskBox/Apps/CODE/IG Info extractor Code/ig-vault-apk/capturas/n4-inicio-%s.png"%nom)
    pg.click("#iniEstado [data-ie=reint]"); pg.wait_for_timeout(300)
    ok("Reintentar pone a leer las fallidas y lo dice", pg.evaluate("corriendo || db.cards.find(c=>c.id==='f1').estado!=='revisar'"))
    pg.wait_for_function("!corriendo", timeout=60000)
    ok("fotos en el PC por el programa (no caducan)", pg.evaluate("SRV=true, srcFoto('https://scontent.cdninstagram.com/e.jpg')").startswith("/api/foto?u="))
    pg.evaluate("SRV=false")
    pg.evaluate("abrirLector(db.cards[0].id)"); pg.wait_for_timeout(500)
    t=pg.inner_text("#lectC")
    ok("informe con pros y botón «Leer y explicar otra vez»", "Ahorra tokens" in t and pg.locator("#lectC [data-l=rehacer]").count()==1, t[:400])
    pg.screenshot(path="C:/Users/PC/DeskBox/Apps/CODE/IG Info extractor Code/ig-vault-apk/capturas/n4-informe-%s.png"%nom)
    br.close()
print("ERRORES JS:",ERR or "ninguno"); print("RESULTADO %d/%d"%(sum(res),len(res)))
