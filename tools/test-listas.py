# Aviso final por listas (20/10/2026): 2 bloques, el último arriba, tocar una lista filtra, ✕ lo quita.
import sys, os; sys.path.insert(0, "C:/Users/PC/DeskBox/Apps/CODE/IG Info extractor Code/ig-vault-apk/tools")
from arnes import *
CD = BASE + "capturas/listas/"; os.makedirs(CD, exist_ok=True)
with sync_playwright() as p:
    for ancho, nom in ((390, "movil"), (1280, "pc")):
        print("== " + nom)
        br, pg = pagina(p, ancho)
        pg.evaluate("""()=>{const mk=(i,b,e)=>({id:'k'+i,url:'https://github.com/a/r'+i,tipo:'GitHub',estado:e,bloque:b,grupo:'AI',titulo:'T'+i,resumen:'r',categoria:'Otros',repos:[],tags:[]});
          sesionDesde=1; db.cards=[mk(1,1,'ok'),mk(2,1,'ok'),mk(3,2,'ok'),mk(4,2,'revisar'),mk(5,2,'ok')]; db.bn=2; guardar();}""")
        pg.evaluate("correr()"); pg.wait_for_timeout(800)
        bs = pg.eval_on_selector_all("#aviso [data-lista]", "e=>e.map(x=>x.textContent)")
        ok("2 listas, la última primero con 🆕", len(bs) == 2 and bs[0].startswith("🆕 Bloque 2") and "Bloque 1" in bs[1], bs)
        pg.screenshot(path=CD + "aviso-%s.png" % nom)
        pg.click("#aviso [data-lista='2']"); pg.wait_for_timeout(300)
        n = pg.evaluate("visibles().length")
        ok("tocar bloque 2 -> solo sus 3 fichas", n == 3 and pg.evaluate("bloqueSel") == 2, n)
        ok("chip «Bloque 2 ✕» visible", pg.locator("#filtros [data-qb]").count() == 1)
        pg.screenshot(path=CD + "filtrado-%s.png" % nom)
        pg.click("#filtros [data-qb]"); pg.wait_for_timeout(200)
        ok("✕ quita el filtro", pg.evaluate("bloqueSel") is None and pg.evaluate("visibles().length") == 5)
        br.close()
fin()
