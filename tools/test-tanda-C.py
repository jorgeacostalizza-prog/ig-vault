# Tanda C1-C4 (18/10/2026): un camino para mover, hoja con chips, ficha con 2 botones + ⋯, links en un sitio.
import sys; sys.path.insert(0, "C:/Users/PC/DeskBox/Apps/CODE/IG Info extractor Code/ig-vault-apk/tools")
from arnes import *
CC = BASE + "capturas/tanda-C/"
with sync_playwright() as p:
    for ancho, nom in ((390, "movil"), (1280, "pc")):
        print("== " + nom)
        br, pg = pagina(p, ancho)
        pg.evaluate("""db.cards=[{id:'a1',url:'https://x.test/1',titulo:'Ficha uno',grupo:'AI',categoria:'Programas',resumen:'r',estado:'ok',links:[]},{id:'a2',url:'https://x.test/2',titulo:'Ficha dos',grupo:'AI',categoria:'Otros',resumen:'r',estado:'ok',links:[]}];guardar();cambiaTab('fichas');pintar();abrirDet(db.cards[0])""")
        pg.wait_for_timeout(400)
        acs = pg.locator("#det .acs").first
        vis = [b.inner_text() for b in pg.locator("#det .acs .btn").all()]
        ok("C3 al abrir: Editar y Favorita grandes, ⋯ y Borrar", "Editar" in vis and "Favorita" in vis and any("⋯" in v for v in vis) and any("Borrar" in v for v in vis), vis)
        ok("C3 no se ven Mover/Buscar links/Seleccionar/Pegar texto sueltos", not any(k in " ".join(vis) for k in ("Mover", "Buscar links", "Seleccionar", "Pegar texto")), vis)
        ok("C1 no existe el diálogo «Mover»", pg.locator("#dmv").count() == 0)
        pg.screenshot(path=CC + "C3-ficha-" + nom + ".png", full_page=True)
        pg.click("[data-a=mas]"); pg.wait_for_timeout(200)
        vis = [b.inner_text() for b in pg.locator("#det .acs .btn").all()]
        ok("C3 «⋯» enseña Buscar links, Seleccionar, Pegar texto", all(any(k in v for v in vis) for k in ("Buscar links", "Seleccionar", "Pegar texto")), vis)
        ok("C4 «Buscar links» aparece 1 vez en la ficha", sum("Buscar links" in v for v in vis) == 1)
        pg.screenshot(path=CC + "C3-mas-" + nom + ".png", full_page=True)
        col = pg.evaluate("getComputedStyle(document.querySelector('[data-a=borrar]')).color")
        ok("C3 Borrar en rojo", col != pg.evaluate("getComputedStyle(document.querySelector('[data-a=editar]')).color"), col)
        pg.click("[data-a=fav]"); pg.wait_for_timeout(200)
        ok("C3 Favorita funciona", pg.evaluate("db.cards[0].fav") is True)
        # borrar pide confirmación
        pg.click("[data-a=borrar]"); pg.wait_for_timeout(300)
        ok("C3 Borrar pide confirmación", pg.evaluate("document.getElementById('dlg').open") and pg.evaluate("db.cards.length") == 2)
        pg.click("#dNo"); pg.wait_for_timeout(200)
        ok("C3 cancelar no borra", pg.evaluate("db.cards.length") == 2)
        # editar
        pg.click("[data-a=editar]"); pg.wait_for_timeout(300)
        ok("C2 hoja: sin cajas Grupo/Categoría visibles", pg.locator("#hojaC input.hcamp:visible[placeholder*='Grupo'], #hojaC input.hcamp:visible[placeholder*='Categor']").count() == 0)
        ok("C4 hoja: sin «Buscar links» ni «Investigar»", "Buscar links" not in pg.inner_text("#hoja").replace("«⋯ › Buscar links»", "") and "Investigar" not in pg.inner_text("#hoja"))
        ok("C2 hoja: chips de sección + «Nueva…»", pg.locator("#hDest button").count() == 3 and "Nueva" in pg.inner_text("#hDest"))
        pg.screenshot(path=CC + "C2-hoja-" + nom + ".png", full_page=True)
        pg.click("#hDest button[data-c='Otros']")
        ok("C1 elegir chip marca la sección", pg.evaluate("document.querySelector('#hDest .on').dataset.c") == "Otros")
        pg.click("#hSi"); pg.wait_for_timeout(300)
        ok("C1 guardar mueve la ficha", pg.evaluate("db.cards[0].categoria") == "Otros")
        # sección nueva
        pg.evaluate("abrirEditor(db.cards[0])"); pg.wait_for_timeout(200)
        pg.click("#hDest button[data-g='']"); pg.wait_for_timeout(300)
        pg.fill("#dC input, #dC textarea", "Cosas › Nuevas"); pg.click("#dSi"); pg.wait_for_timeout(300)
        ok("C2 «Nueva…» crea chip marcado", "Nuevas" in pg.inner_text("#hDest .on"), pg.inner_text("#hDest"))
        pg.click("#hSi"); pg.wait_for_timeout(300)
        ok("C2 se guarda grupo y categoría nuevos", pg.evaluate("[db.cards[0].grupo,db.cards[0].categoria]") == ["Cosas", "Nuevas"])
        ok("sin desbordamiento horizontal", pg.evaluate("document.documentElement.scrollWidth<=innerWidth+1"))
        br.close()
fin()
