# Tanda P1 (21/10/2026): Papelera visible. Descartar -> filtro «Papelera» en la fila, recuperar, vaciar con confirmación y Deshacer. Móvil 390 + PC 1280.
import sys, os; sys.path.insert(0, "C:/Users/PC/DeskBox/Apps/CODE/IG Info extractor Code/ig-vault-apk/tools")
from arnes import *
CD = BASE + "capturas/tanda-P1/"; os.makedirs(CD, exist_ok=True)
FICHAS = """db.cards=[{id:'a1',url:'https://x.test/a1',tipo:'Web',estado:'ok',bloque:1,grupo:'AI',titulo:'Ficha buena',resumen:'Algo util',categoria:'Webs',repos:[],tags:[],estadoUso:'nuevo'},
 {id:'d1',url:'https://x.test/d1',tipo:'Web',estado:'ok',bloque:1,grupo:'AI',titulo:'Ficha descartada uno',resumen:'No me sirve',categoria:'Webs',repos:[],tags:[],estadoUso:'descartada'},
 {id:'d2',url:'https://x.test/d2',tipo:'Web',estado:'ok',bloque:1,grupo:'AI',titulo:'Ficha descartada dos',resumen:'Tampoco',categoria:'Webs',repos:[],tags:[],estadoUso:'descartada'}];filtro='nuevo';cambiaTab('fichas');pintar()"""
with sync_playwright() as p:
    for ancho, nom in ((390, "movil"), (1280, "pc")):
        print("== " + nom)
        br, pg = pagina(p, ancho)
        pg.evaluate(FICHAS); pg.wait_for_timeout(300)
        bt = pg.inner_text("#filtros")
        ok("Papelera sale en la fila de filtros con su número", "Papelera (2)" in bt, bt)
        ok("«Descartadas» ya no está en «Más filtros»", "Descartadas" not in pg.inner_text("#hojaF") and pg.evaluate("document.querySelector('#hojaF').textContent.includes('Descartadas')") is False)
        ok("descartadas no salen en Nuevo", "descartada" not in pg.inner_text("#lista").lower() and "Ficha buena" in pg.inner_text("#lista"))
        pg.click('#filtros button[data-f="descartada"]'); pg.wait_for_timeout(300)
        t = pg.inner_text("#lista")
        ok("Papelera muestra solo las descartadas y el botón Vaciar", "Ficha descartada uno" in t and "Ficha descartada dos" in t and "Ficha buena" not in t and "Vaciar papelera" in t, t[:200])
        pg.screenshot(path=CD + "papelera-%s.png" % nom)
        # descartar desde Nuevo manda la ficha a la papelera
        pg.evaluate(FICHAS.replace("estadoUso:'nuevo'", "estadoUso:'nuevo'", 1)); pg.click('#filtros button[data-f="nuevo"]'); pg.wait_for_timeout(300)
        pg.evaluate("ponUso(db.cards[0],'descartada')") if pg.evaluate("typeof ponUso==='function'") else pg.evaluate("db.cards[0].estadoUso='descartada';guardar();pintar()")
        pg.wait_for_timeout(300)
        ok("al descartar, la ficha desaparece de Nuevo y cuenta en Papelera (3)", "Ficha buena" not in pg.inner_text("#lista") and "Papelera (3)" in pg.inner_text("#filtros"), pg.inner_text("#filtros"))
        # recuperar
        pg.evaluate("db.cards[0].estadoUso='nuevo';guardar();pintar()")
        ok("recuperar la saca de la Papelera (2)", "Papelera (2)" in pg.inner_text("#filtros"))
        # vaciar: cancelar no borra
        pg.click('#filtros button[data-f="descartada"]'); pg.wait_for_timeout(200)
        pg.click('#lista [data-vaciar]'); pg.wait_for_timeout(200)
        ok("vaciar pide confirmación escrita", "VACIAR" in pg.inner_text("#dlg"))
        pg.fill("#dIn", "nada"); pg.click("#dSi"); pg.wait_for_timeout(300)
        ok("confirmación mal escrita no borra", pg.evaluate("db.cards.length") == 3)
        # vaciar de verdad
        pg.click('#lista [data-vaciar]'); pg.wait_for_timeout(200); pg.fill("#dIn", "vaciar"); pg.click("#dSi"); pg.wait_for_timeout(400)
        ok("vaciar deja solo la ficha buena", pg.evaluate("db.cards.map(c=>c.id).join()") == "a1", pg.evaluate("db.cards.map(c=>c.id).join()"))
        ok("la papelera queda en (0) y sin botón Vaciar", "Papelera (0)" in pg.inner_text("#filtros") and "Vaciar papelera" not in pg.inner_text("#lista"))
        # Deshacer: el aviso trae el botón
        pg.screenshot(path=CD + "vaciada-%s.png" % nom)
        h = pg.evaluate("document.body.innerText")
        ok("el aviso ofrece Deshacer", "Papelera vaciada (2)" in h and "Deshacer" in h, h[-200:])
        pg.click("text=Deshacer"); pg.wait_for_timeout(300)
        ok("Deshacer devuelve las 2 fichas", pg.evaluate("db.cards.length") == 3 and "Papelera (2)" in pg.inner_text("#filtros"))
        br.close()
fin()
