import json
from playwright.sync_api import sync_playwright
A="C:/Users/PC/DeskBox/Apps/CODE/IG Info extractor Code/ig-vault-apk/src/assets/"; HTML="file:///"+A+"index.html"
real=json.load(open("C:/Users/PC/.ig-extractor/respaldo.json",encoding="utf-8")); ERR=[]; res=[]
def ok(t,v,x=""):
    print(("  OK   " if v else "  FALLA")+" | "+t+(" | "+str(x)[:300] if x and not v else "")); res.append(bool(v))
with sync_playwright() as p:
  for ancho,nom in ((390,"movil"),(1280,"pc")):
    print("== "+nom)
    br=p.chromium.launch(); pg=br.new_context(viewport={"width":ancho,"height":860}).new_page()
    pg.on("pageerror",lambda e:ERR.append(str(e)))
    pg.add_init_script("if(!localStorage.getItem('igv'))localStorage.setItem('igv',"+json.dumps(json.dumps({"cards":real["cards"],"cfg":{}}))+")")
    pg.route(lambda u: not u.startswith("file:"), lambda r: r.abort())
    pg.goto(HTML); pg.wait_for_timeout(2500)
    ids=pg.evaluate("db.cards.filter(c=>c.estado==='ok').slice(0,3).map(c=>c.id)")
    for i in ids: pg.evaluate("setUso(db.cards.find(c=>c.id==='%s'),'descartada')"%i) if pg.evaluate("typeof setUso")=="function" else pg.evaluate("(()=>{const c=db.cards.find(c=>c.id==='%s');c.estadoUso='descartada';guardar()})()"%i)
    n=pg.evaluate("db.cards.filter(c=>c.estadoUso==='descartada').length")
    ok("3 fichas en la papelera",n>=3,n)
    pg.click("nav button[data-t=explorar]"); pg.wait_for_timeout(400)
    ok("Explorar normal no las muestra", pg.evaluate("resultados().every(c=>c.estadoUso!=='descartada')"))
    pg.evaluate("FIL.marca=['descartada'];pintaExplorar()"); pg.wait_for_timeout(300)
    ok("filtro Papelera las muestra", pg.evaluate("resultados().length")==n, pg.evaluate("resultados().length"))
    ok("botón Vaciar papelera visible", pg.locator("#xRes [data-vaciar]").count()==1)
    pg.click("#xRes [data-vaciar]"); pg.wait_for_timeout(200)
    ok("pide escribir VACIAR", "VACIAR" in pg.inner_text("#dlg"))
    pg.fill("#dIn","nada"); pg.click("#dSi"); pg.wait_for_timeout(300)
    ok("mal escrito no borra", pg.evaluate("db.cards.filter(c=>c.estadoUso==='descartada').length")==n)
    pg.click("#xRes [data-vaciar]"); pg.wait_for_timeout(200); pg.fill("#dIn","vaciar"); pg.click("#dSi"); pg.wait_for_timeout(400)
    ok("vaciar borra", pg.evaluate("db.cards.filter(c=>c.estadoUso==='descartada').length")==0)
    pg.click('#avDeshacer'); pg.wait_for_timeout(400)
    ok("Deshacer las recupera", pg.evaluate("db.cards.filter(c=>c.estadoUso==='descartada').length")==n, pg.evaluate("db.cards.filter(c=>c.estadoUso==='descartada').length"))
    ok("link javascript: se neutraliza", "javascript" not in pg.evaluate("aHtml({u:'javascript:alert(1)',t:'x',ic:'',cls:''},'a',true)"))
    ok("link https se respeta", "https://a.com" in pg.evaluate("aHtml({u:'https://a.com',t:'x',ic:'',cls:''},'a',true)"))
    ok("sin desbordamiento horizontal", pg.evaluate("document.documentElement.scrollWidth<=innerWidth+1"))
    pg.screenshot(path="C:/Users/PC/DeskBox/Apps/CODE/IG Info extractor Code/ig-vault-apk/capturas/n3b-papelera-%s.png"%nom)
    br.close()
print("ERRORES JS:",[e for e in ERR if "api/ping" not in e] or "ninguno"); print("RESULTADO %d/%d"%(sum(res),len(res)))
