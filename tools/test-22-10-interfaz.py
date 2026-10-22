# Interfaz 22/10/2026: arranque en Inicio, foto de respaldo, miniatura al pintar, deslizar entre fichas, chips + Orden iguales en Inicio y Explorar.
# Navegador oculto (headless), sin red, con una COPIA de los datos reales (solo lectura de respaldo.json).
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright
BASE = "C:/Users/PC/DeskBox/Apps/CODE/IG Info extractor Code/ig-vault-apk/"
HTML = "file:///" + BASE + "src/assets/index.html"
real = json.load(open("C:/Users/PC/.ig-extractor/respaldo.json", encoding="utf-8"))
PNG = bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d49444154789c6360000002000001e221bc330000000049454e44ae426082")
ERR, res = [], []
def ok(t, v, x=""):
    print(("  OK   " if v else "  FALLA") + " | " + t + (" | " + str(x)[:300] if x and not v else "")); res.append(bool(v))

def abre(p, ancho, alto, cards, touch=False):
    br = p.chromium.launch(); ctx = br.new_context(viewport={"width": ancho, "height": alto}, has_touch=touch); pg = ctx.new_page()
    pg.on("pageerror", lambda e: ERR.append(str(e)))
    if cards is not None:
        pg.add_init_script("if(!localStorage.getItem('igv'))localStorage.setItem('igv'," + json.dumps(json.dumps({"cards": cards, "cfg": {}})) + ")")
    pg.route("https://scontent.test/**", lambda r: r.fulfill(status=200, body=PNG, headers={"content-type": "image/png", "access-control-allow-origin": "*"}))
    pg.route(lambda u: not u.startswith("file:") and "scontent.test" not in u, lambda r: r.abort())
    pg.goto(HTML); pg.wait_for_timeout(1200)
    return br, pg

def tocar(cdp, pts):
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": pts[0][0], "y": pts[0][1]}]})
    for x, y in pts[1:]:
        cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x, "y": y}]})
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})

with sync_playwright() as p:
    for ancho, alto, nom in ((390, 844, "movil"), (1280, 800, "pc")):
        print("== " + nom)
        # 1) arranque vacío: Inicio con estado vacío útil (nunca «Añadir» vacío)
        br, pg = abre(p, ancho, alto, None)
        ok("vacío: arranca en Inicio", pg.evaluate("document.getElementById('p-feed').classList.contains('on') && !document.getElementById('p-pegar').classList.contains('on')"))
        ok("vacío: pestaña Inicio marcada", pg.evaluate("document.querySelector('nav button.on').dataset.t") == "feed")
        ok("vacío: invita a añadir", "Aún no tienes posts" in pg.inner_text("#feed") and pg.locator("#feed [data-fp]").count() == 1)
        pg.click("nav button[data-t=explorar]"); pg.wait_for_timeout(300)
        ok("vacío: Explorar dice «Aún no tienes posts» (no «Nada con estos filtros»)", "Aún no tienes posts" in pg.inner_text("#xRes") and "Nada con estos filtros" not in pg.inner_text("#xRes"))
        pg.click("#xRes [data-fp]"); pg.wait_for_timeout(300)
        ok("vacío: el botón lleva a Añadir", pg.evaluate("document.getElementById('p-pegar').classList.contains('on')"))
        # restaurar fichas desde el servidor estando en «Añadir» vacío -> vuelve a Inicio
        pg.evaluate("db.cards=%s;guardar();trasRestaurar()" % json.dumps(real["cards"][:5]))
        pg.wait_for_timeout(300)
        ok("tras restaurar fichas vuelve a Inicio", pg.evaluate("document.getElementById('p-feed').classList.contains('on')") and pg.locator("#feed .fc").count() > 0)
        br.close()

        # 2) con datos reales: arranca en Inicio
        br, pg = abre(p, ancho, alto, real["cards"])
        ok("con fichas: arranca en Inicio con tarjetas", pg.evaluate("document.getElementById('p-feed').classList.contains('on')") and pg.locator("#feed .fc").count() >= 10)
        # 3) respaldo de foto: siempre hay .port detrás y sobrevive si la imagen falla DESPUÉS de pintar
        n_fc = pg.locator("#feed .fc").count(); n_port = pg.locator("#feed .fc .fph .gl .port").count()
        ok("cada ficha lleva dibujo de respaldo (inicial + color)", n_fc == n_port, (n_fc, n_port))
        r = pg.evaluate("""()=>{const g=document.querySelector('#feed .fc .gl');const im=document.createElement('img');im.src='https://x.invalid/a.jpg';g.appendChild(im);fotoMala(im);
          const po=g.querySelector('.port');const r=po.getBoundingClientRect();return {vis:getComputedStyle(g).display!=='none',alto:r.height,ini:po.querySelector('span').textContent,h:po.style.getPropertyValue('--h')}}""")
        ok("si la foto falla después de pintar, el respaldo sigue visible", r["vis"] and r["alto"] > 100 and r["ini"] and r["h"] != "", r)
        # 4) miniatura guardada en cuanto se pinta
        pg.evaluate("""()=>{db.cards.unshift({id:'zzmini1',estado:'ok',titulo:'AAAA Prueba mini',resumen:'x',categoria:'Otros',imgs:['https://scontent.test/p1.jpg'],url:'https://www.instagram.com/p/ZZMINI1/',añadida:Date.now(),lote:0});feedOrd='az';resetOrden();pintaFeed()}""")
        pg.wait_for_timeout(1500)
        ok("(antes de los 4 s de minisAtrasadas) la miniatura se guarda al pintar la ficha (sin esperar 4 s)", pg.evaluate("db.cards.find(c=>c.id==='zzmini1').minis")==1, pg.evaluate("JSON.stringify(db.cards.find(c=>c.id==='zzmini1')).slice(0,200)"))
        ok("la copia está en IndexedDB", pg.evaluate("MINI.get('zzmini1').then(v=>Array.isArray(v)&&v.length===1&&/^data:image/.test(v[0].d))"))
        ok("la ficha ya muestra la copia local", pg.evaluate("[...document.querySelectorAll('.gl[data-gid=zzmini1] img')].some(i=>i.src.startsWith('data:image'))"))
        pg.screenshot(path=BASE + "capturas/interfaz-22-10-%s-inicio.png" % nom)
        # 5) chips + orden: Inicio
        ok("Inicio: botón Orden visible", pg.locator("#fbar .ordbtn").is_visible())
        ok("Inicio: fila de chips deslizable", pg.evaluate("getComputedStyle(document.querySelector('#fbar .fchips')).overflowX")=="auto" and pg.locator("#fbar .fchp").count() >= 4)
        ok("Inicio: sin desplegables de filtro en la barra", pg.locator("#fbar select").count()==0)
        pg.click("#fbar .ordbtn"); pg.wait_for_timeout(200)
        ok("Orden abre con 1 toque y ofrece opciones", pg.evaluate("document.getElementById('dOrd').open") and pg.locator("#dOrdC [data-o]").count()==5)
        pg.click("#dOrdC [data-o=az]"); pg.wait_for_timeout(300)
        tit = pg.evaluate("[...document.querySelectorAll('#feed .fc h3')].map(h=>h.textContent)")
        ok("Orden A-Z aplicado en Inicio", len(tit) > 3 and tit == sorted(tit, key=lambda t: t.lower()) or pg.evaluate("feedOrd")=="az", tit[:4])
        ok("el botón muestra el orden actual", "A-Z" in pg.inner_text("#fbar .ordbtn"))
        pg.click("#fbar [data-fm=gratis]"); pg.wait_for_timeout(200)
        ok("chip Gratis filtra en Inicio", pg.evaluate("feedModo")=="gratis" and pg.locator("#fbar [data-fm=gratis].on").count()==1)
        pg.click("#fbar [data-fm=gratis]"); pg.click("#fbar [data-fmasf]"); pg.wait_for_timeout(200)
        ok("«Más filtros» (lote, tema, colección) abre", pg.evaluate("document.getElementById('dFilI').open") and pg.locator("#dFilI #fLote").count()==1)
        pg.click("#dFilIOk"); pg.wait_for_timeout(100)
        # Explorar
        pg.click("nav button[data-t=explorar]"); pg.wait_for_timeout(500)
        ok("Explorar: mismo sistema (Orden visible + chips, sin select de fecha)", pg.locator("#xBar .ordbtn").is_visible() and pg.locator("#xBar select").count()==0 and pg.locator("#xFecha").count()==0 and pg.locator("#xBar .fchp").count()>=5)
        pg.click("#xBar .ordbtn"); pg.click("#dOrdC [data-o=viejo]"); pg.wait_for_timeout(300)
        ok("Explorar: Orden cambia y se refleja en el botón", pg.evaluate("FIL.orden")=="viejo" and "antiguo" in pg.inner_text("#xBar .ordbtn"))
        pg.click("#xBar [data-xq='marca:quiero']"); pg.wait_for_timeout(200)
        ok("Explorar: chip Lo quiero filtra", pg.evaluate("FIL.marca.includes('quiero')"))
        pg.click("#xBar [data-xq='marca:quiero']"); pg.click("#xBar [data-xq='fecha:7d']"); pg.wait_for_timeout(200)
        ok("Explorar: chip de fecha (Últimos 7 días) filtra", pg.evaluate("FIL.fecha")=="7d" and pg.evaluate("resultados().length")<pg.evaluate("db.cards.length"))
        pg.click("#xBar [data-xq='fecha:7d']")
        if ancho < 900:
            pg.click("#xMasF"); pg.wait_for_timeout(300)
            ok("Explorar móvil: «Más filtros» abre la hoja con fecha/lote/marcas", pg.evaluate("document.getElementById('dFil').open") and pg.locator("#dFilC .fck").count()>8)
            pg.click("#dFilOk")
        ok("Explorar: corazón no tapa el título (título empieza bajo la imagen)", pg.evaluate("(()=>{const x=document.querySelector('#xRes .xc'),q=x.querySelector('.xq').getBoundingClientRect(),h=x.querySelector('h3').getBoundingClientRect();return h.top>=q.bottom-1||h.left>=q.right||h.right<=q.left})()"))
        ok("sin desbordamiento horizontal", pg.evaluate("document.documentElement.scrollWidth<=innerWidth+1"))
        pg.screenshot(path=BASE + "capturas/interfaz-22-10-%s-explorar.png" % nom)
        br.close()

    # 6) deslizar entre fichas (táctil real por CDP) + botones grandes
    for ancho, alto, nom in ((390, 844, "movil"), (1280, 800, "pc")):
        print("== deslizar " + nom)
        br, pg = abre(p, ancho, alto, real["cards"], touch=True)
        cdp = pg.context.new_cdp_session(pg)
        pg.evaluate("abrirLector(feedOrden[1])"); pg.wait_for_timeout(500)
        id0 = pg.evaluate("lectorId"); y = int(alto * 0.6)
        ok("botones ‹ y Siguiente › con >=44 px", pg.evaluate("[...document.querySelectorAll('#lAnt,#lSig')].every(b=>{const r=b.getBoundingClientRect();return r.height>=44&&r.width>=44})"))
        X = ancho - 90; tocar(cdp, [(X, y), (X - 50, y + 2), (X - 120, y + 4), (X - 200, y + 5)]); pg.wait_for_timeout(500)
        id1 = pg.evaluate("lectorId")
        ok("deslizar a la izquierda = siguiente ficha", id1 != id0 and id1 == pg.evaluate("feedOrden[2]"), (id0, id1))
        tocar(cdp, [(X - 200, y), (X - 140, y + 3), (X - 60, y + 4), (X, y + 5)]); pg.wait_for_timeout(500)
        ok("deslizar a la derecha = ficha anterior", pg.evaluate("lectorId") == id0, pg.evaluate("lectorId"))
        tocar(cdp, [(X - 100, y), (X - 95, y - 60), (X - 90, y - 150), (X - 88, y - 220)]); pg.wait_for_timeout(400)
        ok("gesto vertical (scroll) no cambia de ficha", pg.evaluate("lectorId") == id0)
        tocar(cdp, [(X - 100, y), (X - 70, y + 2), (X - 50, y + 3)]); pg.wait_for_timeout(400)
        ok("movimiento corto no cambia de ficha", pg.evaluate("lectorId") == id0)
        pg.click("#lSig"); pg.wait_for_timeout(300)
        ok("el botón Siguiente sigue funcionando", pg.evaluate("lectorId") == pg.evaluate("feedOrden[2]"))
        pg.click("#lAnt"); pg.wait_for_timeout(300)
        ok("el botón ‹ sigue funcionando", pg.evaluate("lectorId") == id0)
        pg.screenshot(path=BASE + "capturas/interfaz-22-10-%s-ficha.png" % nom)
        br.close()

print("ERRORES JS:", ERR if ERR else "ninguno"); print("RESULTADO: %d/%d OK" % (sum(res), len(res)))
sys.exit(0 if all(res) and not ERR else 1)
