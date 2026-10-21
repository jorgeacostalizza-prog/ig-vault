# Tanda H2-H4 (18/10/2026): estado de uso Nuevo/Lo quiero/Hecho/Descartar. Movil 390 + PC 1280.
import sys, os; sys.path.insert(0, "C:/Users/PC/DeskBox/Apps/CODE/IG Info extractor Code/ig-vault-apk/tools")
from arnes import *
CD = BASE + "capturas/tanda-H2/"; os.makedirs(CD, exist_ok=True)
def ficha(i, t, **k):
    d = dict(id=i, url="https://a.test/" + i, tipo="Web", estado="ok", bloque=1, grupo="AI", titulo=t, resumen="Resumen de " + t, categoria="Webs", repos=[], tags=[]); d.update(k); return d
# D7: el estado y descartar de la fila ahora se cambian DESLIZANDO (ya no hay botones en la fila)
def desliza(pg, sel, dx):
    pg.locator(sel).scroll_into_view_if_needed(); b = pg.locator(sel).bounding_box(); x0 = b["x"] + b["width"] / 2; y0 = b["y"] + b["height"] / 2
    pg.mouse.move(x0, y0); pg.mouse.down(); pg.mouse.move(x0 + dx / 2, y0 + 1, steps=4); pg.mouse.move(x0 + dx, y0 + 1, steps=4); pg.mouse.up(); pg.wait_for_timeout(250)
with sync_playwright() as p:
    for ancho, nom in ((390, "movil"), (1280, "pc")):
        print("== " + nom)
        br, pg = pagina(p, ancho)
        # H4 migracion: fichas viejas sin estadoUso
        pg.evaluate("localStorage.removeItem('igv-antes-H2');db.cards=%s;pintar()" % json.dumps([ficha("v%d" % i, "Vieja %d" % i) for i in range(5)]))
        ok("migracion: todas Nuevo", pg.evaluate("db.cards.every(c=>c.estadoUso==='nuevo')"))
        ok("migracion: copia previa guardada", pg.evaluate("JSON.parse(localStorage.getItem('igv-antes-H2')).cards.length")==5)
        pg.evaluate("pintar();pintar()"); ok("idempotente: 5 fichas", pg.evaluate("db.cards.length")==5)
        # H3 al abrir: filtro Nuevo con contador, filtros visibles
        pg.evaluate("cambiaTab('fichas')")
        ok("abre en Nuevo con contador", pg.evaluate("document.querySelector('#filtros button.on').textContent")=="Nuevo (5)", pg.evaluate("document.querySelector('#filtros').innerText"))
        t = pg.evaluate("document.querySelector('#filtros').innerText+document.querySelector('#hojaF').textContent")
        ok("filtros visibles", all(x in t for x in ["Lo quiero","Hecho","Para revisar","Papelera"]))
        ok("filtros no cortados", pg.evaluate("[...document.querySelectorAll('#filtros button[data-mas]')].every(b=>b.getBoundingClientRect().right<=innerWidth+1)"))
        # cambiar desde la fila
        desliza(pg, '.rw[data-id="v0"] .rb', 150); ok("fila: Nuevo->Lo quiero", pg.evaluate("db.cards[0].estadoUso")=="quiero")
        ok("sale de la lista Nuevo", pg.evaluate("!document.querySelector('.rw[data-id=\"v0\"]')"))
        alto = pg.evaluate("Math.min(...[...document.querySelectorAll('.rw .rb')].map(b=>b.getBoundingClientRect().height))")
        ok("objetivo tactil >=44", alto>=44, alto)
        # desde la ficha
        pg.click('.rw[data-id="v1"] [data-a=det]'); pg.click('#det [data-a=uso][data-u=hecho]')
        ok("ficha: Hecho", pg.evaluate("db.cards[1].estadoUso")=="hecho")
        pg.screenshot(path=CD+"ficha-%s.png"%nom); pg.evaluate("cerrarDet()")
        # descartar y recuperar
        desliza(pg, '.rw[data-id="v2"] .rb', -150)
        ok("descartar no borra", pg.evaluate("db.cards.length")==5 and pg.evaluate("db.cards[2].estadoUso")=="descartada")
        ok("descartada oculta en Todo", pg.evaluate("filtro='todo';pintar();!document.querySelector('.rw[data-id=\"v2\"]')"))
        pg.evaluate("filtro='descartada';pintar()"); pg.wait_for_timeout(200); pg.screenshot(path=CD+"descartadas-%s.png"%nom)
        ok("filtro Descartadas la muestra", pg.evaluate("!!document.querySelector('.rw[data-id=\"v2\"]')"))
        desliza(pg, '.rw[data-id="v2"] .rb', 150); ok("recuperar -> Nuevo", pg.evaluate("db.cards[2].estadoUso")=="nuevo")
        # busqueda
        pg.evaluate("db.cards[3].estadoUso='descartada';filtro='nuevo';pintar()")
        pg.fill("#buscar", "Vieja 1"); pg.wait_for_timeout(100); pg.evaluate("pintar()")
        ok("busqueda halla Hecho aunque filtro Nuevo", pg.evaluate("!!document.querySelector('.rw[data-id=\"v1\"]')"))
        pg.fill("#buscar", "Vieja 3"); pg.evaluate("pintar()")
        ok("busqueda no halla Descartada", pg.evaluate("!document.querySelector('.rw[data-id=\"v3\"]')"))
        pg.evaluate("filtro='descartada';pintar()"); ok("con filtro Descartadas si", pg.evaluate("!!document.querySelector('.rw[data-id=\"v3\"]')"))
        pg.fill("#buscar", ""); pg.evaluate("filtro='nuevo';pintar()")
        # fusion
        pg.evaluate("""db.cards=[{id:'m1',url:'https://a.test/1',tipo:'Web',estado:'ok',grupo:'AI',titulo:'Igual',resumen:'x'.repeat(200),categoria:'Webs',estadoUso:'nuevo'},
          {id:'m2',url:'https://a.test/1?utm_source=b',tipo:'Web',estado:'ok',grupo:'AI',titulo:'Igual',resumen:'y',categoria:'Webs',estadoUso:'hecho'},
          {id:'m3',url:'https://a.test/3',tipo:'Web',estado:'ok',grupo:'AI',titulo:'Otra',resumen:'x',categoria:'Webs',estadoUso:'descartada'},
          {id:'m4',url:'https://a.test/3?utm_source=b',tipo:'Web',estado:'ok',grupo:'AI',titulo:'Otra',resumen:'y',categoria:'Webs',estadoUso:'descartada'},
          {id:'m5',url:'https://a.test/5',tipo:'Web',estado:'ok',grupo:'AI',titulo:'Tercera',resumen:'x',categoria:'Webs',estadoUso:'quiero'},
          {id:'m6',url:'https://a.test/5?utm_source=b',tipo:'Web',estado:'ok',grupo:'AI',titulo:'Tercera',resumen:'y',categoria:'Webs',estadoUso:'nuevo'}];unirRepetidas()""")
        m = pg.evaluate("db.cards.map(c=>c.titulo+':'+c.estadoUso).sort().join('|')")
        ok("fusion: hecho>nuevo, descartada+descartada, quiero>nuevo", m=="Igual:hecho|Otra:descartada|Tercera:quiero", m)
        # exportar: Lo quiero por defecto
        pg.evaluate("db.sel={};filtro='todo';pintar()")
        txt = pg.evaluate("(()=>{const cs=db.cards.filter(c=>c.estado!=='pendiente'&&(selIds()[c.id]||uso(c)==='quiero'));return exportTxt(cs)})()")
        ok("export por defecto: solo Lo quiero", "Tercera" in txt and "Igual" not in txt)
        pg.evaluate("exportar()"); pg.wait_for_timeout(300)
        ok("exportar() abre con Lo quiero", "Tercera" in pg.evaluate("$('#ccTxt').value") and "Igual" not in pg.evaluate("$('#ccTxt').value"))
        pg.evaluate("$('#dcc').close();filtro='nuevo';pintar()"); pg.wait_for_timeout(200); pg.screenshot(path=CD+"lista-%s.png"%nom)
        br.close()
fin()
