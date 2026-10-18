# Tanda G (18/10/2026): cola con Reiniciar / Quitar / añadir mientras trabaja / aviso de atascado. Móvil 390 + PC 1280.
import sys; sys.path.insert(0, "C:/Users/PC/DeskBox/Apps/CODE/IG Info extractor Code/ig-vault-apk/tools")
from arnes import *
with sync_playwright() as p:
    for ancho, nom in ((390, "movil"), (1280, "pc")):
        print("== " + nom)
        CAPS.clear(); CAPS.update({k: "Mira foo-cli herramienta de terminal " + k for k in ["A1", "A2", "B1", "B2", "C1"]})
        br, pg = pagina(p, ancho)
        pg.evaluate("window.__h=http; http=()=>new Promise(()=>{});0")   # el primer link se queda colgado
        pg.fill("#txt", "https://www.instagram.com/p/A1/\nhttps://www.instagram.com/p/A2/"); pg.click("#bOrdenar"); pg.wait_for_timeout(500)
        ok("G1 el bloque que trabaja tiene «Reiniciar»", pg.locator("#bloques [data-rb]").count() == 1)
        ok("G2 el bloque tiene «Quitar»", pg.locator("#bloques [data-bq]").count() == 1)
        pg.fill("#txt", "https://www.instagram.com/p/B1/\nhttps://www.instagram.com/p/B2/"); pg.click("#bOrdenar"); pg.wait_for_timeout(300)
        ok("G3 se puede añadir otra lista mientras trabaja (2 bloques)", pg.locator("#bloques .blq").count() == 2, pg.inner_text("#bOrdenar") + str(pg.locator("#bloques .blq").count()))
        ok("G4 al principio NO avisa de atasco", "Parece atascado" not in pg.inner_text("#bloques"))
        pg.evaluate("ultimoPaso=Date.now()-TIEMPO_ATASCADO_MS-5000"); pg.wait_for_timeout(5600)
        ok("G4 sin avanzar sale «Parece atascado» con Reiniciar y Quitar", "Parece atascado" in pg.inner_text("#bloques") and pg.locator("#bloques [data-rb]").count() == 1 and pg.locator("#bloques [data-bq]").count() >= 1)
        pg.screenshot(path=CAPT + "G4-atascado-" + nom + ".png", full_page=True)
        pg.evaluate("http=window.__h;0")   # la red vuelve
        pg.click("#bloques [data-rb]")
        pg.wait_for_function("db.cards.filter(c=>c.estado==='ok').length>=1", timeout=40000)
        ok("G1 tras Reiniciar el link atascado se procesa", pg.evaluate("db.cards.find(c=>c.url.includes('/A1/')).estado") in ("ok", "revisar"), pg.evaluate("db.cards.map(c=>c.url.slice(-4)+c.estado)"))
        ok("G4 el aviso de atasco desaparece", "Parece atascado" not in pg.inner_text("#bloques"))
        pg.wait_for_function("db.cards.length>=4 && !db.cards.some(c=>c.estado==='pendiente')", timeout=60000)
        ok("la cola sigue y termina los 4 links", pg.evaluate("db.cards.length") == 4)
        # Quitar el bloque activo con lo ya hecho que se queda
        pg.evaluate("http=()=>new Promise(()=>{});0")
        pg.fill("#txt", "https://www.instagram.com/p/C1/"); pg.click("#bOrdenar"); pg.wait_for_timeout(400)
        pg.fill("#txt", "https://www.instagram.com/p/B1/x"); 
        n_antes = pg.evaluate("db.cards.filter(c=>c.estado!=='pendiente').length")
        pg.click("#bloques .blq:last-child [data-bq]"); pg.wait_for_timeout(500)
        ok("G2 «Quitar» en el bloque activo: el pendiente se va y lo hecho se queda", pg.evaluate("db.cards.filter(c=>c.estado==='pendiente').length") == 0 and pg.evaluate("db.cards.filter(c=>c.estado!=='pendiente').length") == n_antes, pg.evaluate("db.cards.length"))
        pg.evaluate("http=window.__h;0"); pg.wait_for_timeout(500)
        ok("tras quitar, la cola queda libre (no se queda colgada)", pg.evaluate("corriendo") is False)
        ok("sin desbordamiento horizontal", pg.evaluate("document.documentElement.scrollWidth<=innerWidth+1"))
        br.close()
fin()
