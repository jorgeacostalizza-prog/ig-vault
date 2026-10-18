# Tanda A (18/10/2026): A1 sin IA, A2 resumen corto, A3 solo gancho, A4 errores en palabras normales. Móvil 390 + PC 1280.
import sys; sys.path.insert(0, "C:/Users/PC/DeskBox/Apps/CODE/IG Info extractor Code/ig-vault-apk/tools")
from arnes import *

def pegar_y_esperar(pg, links, n):
    pg.fill("#txt", "\n".join(links)); pg.click("#bOrdenar")
    pg.wait_for_function("db.cards.length>=%d && !db.cards.some(c=>c.estado==='pendiente')" % n, timeout=60000)

with sync_playwright() as p:
    for ancho, nom in ((390, "movil"), (1280, "pc")):
        print("== " + nom); IA["modo"] = "ok"
        br, pg = pagina(p, ancho)
        CAPS.clear(); CAPS.update({"S1": "Mira foo-cli, una herramienta de terminal para automatizar tareas", "G1": "Comenta GUIA y te lo mando por mensaje directo", "L1": "foo-cli herramienta de terminal que automatiza tareas", "R1": "foo-cli herramienta de terminal"})
        # A1: sin claves
        pegar_y_esperar(pg, ["https://www.instagram.com/p/S1/"], 1)
        ok("A1 Pegar muestra el aviso de que no hay IA", pg.is_visible("#p-pegar .avIA") and "Sin IA" in pg.inner_text("#p-pegar .avIA"))
        pg.evaluate("cambiaTab('fichas')"); pg.wait_for_timeout(200)
        ok("A1 Fichas muestra el aviso", pg.is_visible("#p-fichas .avIA") and "añade una clave" in pg.inner_text("#p-fichas .avIA"))
        ok("A1 la ficha dice «Sin IA: añade una clave»", "Sin IA: añade una clave" in pg.inner_text("#lista"), pg.inner_text("#lista")[:200])
        pg.screenshot(path=CAPT + "A1-sin-ia-" + nom + ".png")
        # con clave: el aviso desaparece
        pg.evaluate("db.cfg.nvidia='nvapi-test';guardar();pintar()")
        ok("A1 con clave el aviso se va", not pg.is_visible("#p-fichas .avIA"))
        # A3: solo gancho -> Para revisar
        pg.evaluate("cambiaTab('pegar')"); pegar_y_esperar(pg, ["https://www.instagram.com/p/G1/"], 2)
        g = pg.evaluate("db.cards.find(c=>c.url.includes('/G1/'))")
        ok("A3 post con solo gancho queda «Para revisar», no «ok»", g["estado"] == "revisar" and "no dejó leer" in g["motivo"], g)
        # A2: resumen largo
        IA["modo"] = "largo"; pg.evaluate("cambiaTab('pegar')"); pegar_y_esperar(pg, ["https://www.instagram.com/p/L1/"], 3)
        l = pg.evaluate("db.cards.find(c=>c.url.includes('/L1/'))")
        ok("A2 resumen ≤ 220 caracteres", 0 < len(l["resumen"]) <= 221, len(l["resumen"]))
        ok("A2 el texto largo se guarda aparte", len(l.get("detalle", "")) > 220, len(l.get("detalle", "")))
        pg.evaluate("cambiaTab('fichas')"); pg.wait_for_timeout(200)
        pg.evaluate("abrirDet(db.cards.find(c=>c.url.includes('/L1/')))"); pg.wait_for_timeout(200)
        ok("A2 el detalle tiene «Ver más»", "Ver más" in pg.inner_text("#det"))
        n0 = len(pg.inner_text("#det")); pg.click("#det [data-a=vermas]"); pg.wait_for_timeout(150)
        ok("A2 «Ver más» enseña el texto largo", len(pg.inner_text("#det")) > n0 + 150)
        pg.screenshot(path=CAPT + "A2-ver-mas-" + nom + ".png")
        pg.evaluate("cerrarDet()")
        # A4: IA saturada (429) y YouTube caído -> frases normales
        IA["modo"] = "401"; pg.evaluate("muertos={}"); pg.evaluate("cambiaTab('pegar')")
        pegar_y_esperar(pg, ["https://www.instagram.com/p/R1/", "https://youtu.be/abcdefghijk"], 5)
        pg.evaluate("cambiaTab('fichas')"); pg.wait_for_timeout(300)
        r = pg.evaluate("db.cards.find(c=>c.url.includes('/R1/'))")
        ok("A4 la ficha sin respuesta de la IA lo explica en palabras", "rechazada" in r.get("sinIA", "") and "401" not in r["sinIA"], r.get("sinIA"))
        ok("A4 una IA saturada se explica sin «429»", pg.evaluate("(()=>{muertos={};iaError='NVIDIA: HTTP 429';return iaTexto()})()") == "la IA está saturada ahora mismo")
        ok("A4 el detalle técnico queda guardado aparte", "401" in r.get("detalleTecnico", "") or "rechazada" in r.get("detalleTecnico", ""), r.get("detalleTecnico"))
        pg.evaluate("abrirDet(db.cards.find(c=>c.url.includes('/R1/')))"); pg.wait_for_timeout(150)
        ver = pg.inner_text("body"); pg.evaluate("cerrarDet()")
        ok("A4 nada de «HTTP», «429» ni «TypeError» en pantalla", all(x not in ver and x not in pg.inner_text("#lista") for x in ["HTTP", "429", "TypeError", "Fallo inesperado"]))
        y = pg.evaluate("db.cards.find(c=>c.tipo==='YouTube')")
        ok("A4 YouTube caído: motivo sin códigos", y["estado"] == "revisar" and "HTTP" not in y["motivo"], y["motivo"])
        pg.evaluate("cambiaTab('fichas')"); pg.screenshot(path=CAPT + "A4-errores-" + nom + ".png")
        ok("sin desbordamiento horizontal", pg.evaluate("document.documentElement.scrollWidth<=innerWidth+1"))
        br.close()
fin()
