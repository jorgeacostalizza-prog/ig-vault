# Tanda C5-C6-D6 (18/10/2026): fichas fallidas legibles con botones, fusión de repetidas, "Sin resultados" con salida.
import sys; sys.path.insert(0, "C:/Users/PC/DeskBox/Apps/CODE/IG Info extractor Code/ig-vault-apk/tools")
from arnes import *
CC = BASE + "capturas/tanda-C2/"
CARDS = """db.cards=[
{id:'f1',url:'https://www.instagram.com/p/FAKE123xyz/',tipo:'Instagram',titulo:'https://www.instagram.com/p/FAKE123xyz/',grupo:'AI',categoria:'Para revisar',estado:'revisar',motivo:'Instagram no deja leer este post sin iniciar sesión. Pega el texto del post a mano o prueba más tarde con otra conexión.',resumen:'',links:[]},
{id:'r1',url:'https://x.test/1',tipo:'Web',titulo:'Codex Security de OpenAI',grupo:'AI',categoria:'Programas',estado:'ok',resumen:'uno',imgs:['https://img.test/1.jpg'],links:[{t:'A',u:'https://a.test/'}],notas:'nota uno',fav:false},
{id:'r2',url:'https://x.test/1?utm_source=b',tipo:'Web',titulo:'Codex Security de OpenAI',grupo:'AI',categoria:'Programas',estado:'ok',resumen:'uno largo',imgs:['https://img.test/2.jpg'],links:[{t:'B',u:'https://b.test/'}],notas:'nota dos',fav:true},
{id:'r3',url:'https://x.test/3',tipo:'Web',titulo:'Otra cosa',grupo:'AI',categoria:'Programas',estado:'ok',resumen:'z',links:[]}];db.sel={};guardar();cambiaTab('fichas');pintar()"""
with sync_playwright() as p:
    for ancho, nom in ((390, "movil"), (1280, "pc")):
        print("== " + nom)
        br, pg = pagina(p, ancho)
        pg.evaluate(CARDS); pg.wait_for_timeout(300)
        fila = pg.locator(".rw[data-id=f1]")
        tit = fila.locator(".rt").inner_text()
        ok("C5 título legible, no URL cruda", "http" not in tit and tit.startswith(("Post de Instagram", "Reel de Instagram")), tit)
        ok("C5 botones Reintentar y Abrir en Instagram en la fila", fila.locator("[data-a=reint]").count() == 1 and "Abrir en Instagram" in fila.inner_text(), fila.inner_text())
        h = pg.evaluate("(()=>{const e=document.querySelector('.rw[data-id=f1] .rs');return [e.scrollHeight,e.clientHeight,parseFloat(getComputedStyle(e).lineHeight)]})()")
        ok("C5 motivo en 2 líneas (no 1 ni 3)", 1.5 * h[2] < h[1] <= 2.2 * h[2], h)
        ok("C5 filas no revisadas sin botones", pg.locator(".rw[data-id=r3] .racc").count() == 0)
        pg.screenshot(path=CC + "C5-fallidas-" + nom + ".png", full_page=True)
        # D6
        pg.fill("#buscar", "zzzxx"); pg.wait_for_timeout(300)
        ok("D6 sin resultados cita lo buscado + botón", "zzzxx" in pg.inner_text("#lista") and pg.locator("[data-q]").count() == 1, pg.inner_text("#lista"))
        pg.screenshot(path=CC + "D6-sinresultados-" + nom + ".png", full_page=True)
        pg.click("[data-q]"); pg.wait_for_timeout(300)
        ok("D6 el botón vacía búsqueda, filtro Todo y lista completa", pg.input_value("#buscar") == "" and pg.locator(".rw").count() == 4 and pg.evaluate("filtro") == "todo", pg.locator(".rw").count())
        # C6
        n = pg.evaluate("unirRepetidas()")
        ok("C6 fusiona 1 repetida", n == 1 and pg.evaluate("db.cards.length") == 3, n)
        k = pg.evaluate("db.cards.find(c=>c.titulo.startsWith('Codex'))")
        ok("C6 conserva imágenes, links, notas y favorita de ambas", len(k["imgs"]) == 2 and len(k["links"]) == 2 and "nota uno" in k["notas"] and "nota dos" in k["notas"] and k["fav"] is True, k)
        ok("C6 (M2) misma publicación: no duplica su link en extra", not k.get("extra"), k.get("extra"))
        ok("C6 aviso «Unidas 1 repetidas»", "Unidas 1 repetidas" in pg.inner_text("#aviso"), pg.inner_text("#aviso"))
        ok("C6 sin más repetidas (idempotente)", pg.evaluate("unirRepetidas()") == 0)
        # Reintentar
        pg.evaluate("window.correr=async()=>{}") 
        pg.click(".rw[data-id=f1] [data-a=reint]"); pg.wait_for_timeout(300)
        ok("C5 Reintentar la pone en cola", pg.evaluate("db.cards.find(c=>c.id=='f1').estado") in ("pendiente", "revisar", "ok") and pg.evaluate("db.bn") >= 1)
        # importar semilla con repetidas
        pg.evaluate("""db.cards=[{id:'s1',url:'u1',titulo:'Dup',grupo:'AI',categoria:'Otros',estado:'ok',resumen:'a',links:[]}];guardar()""")
        pg.evaluate("""db.cards.push({id:'s2',url:'u1?utm_source=b',titulo:'dup ',grupo:'AI',categoria:'Otros',estado:'ok',resumen:'a',links:[]});unirRepetidas()""")
        ok("C6 al importar también une (acentos/mayúsculas)", pg.evaluate("db.cards.length") == 1)
        ok("sin desbordamiento horizontal", pg.evaluate("document.documentElement.scrollWidth<=innerWidth+1"))
        br.close()
fin()
