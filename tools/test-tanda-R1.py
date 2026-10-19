# Tanda R1-R4 (18/10/2026): fallos de la prueba real. R1 link que no termina, R2 «Sirve para» en inglés, R4 recuperar de Descartadas. Móvil 390 + PC 1280.
import sys, os; sys.path.insert(0, "C:/Users/PC/DeskBox/Apps/CODE/IG Info extractor Code/ig-vault-apk/tools")
from arnes import *
CD = BASE + "capturas/tanda-R1/"; os.makedirs(CD, exist_ok=True)
CAPS.clear(); CAPS.update({"RB": "foo-cli install with npx. Fast CLI to run jobs and shell chores. https://x.test/foo",
                           "RC": "foo-cli install with npx. Fast CLI to run jobs and shell chores. Second one"})
def lote(pg, links, espera=40):
    pg.evaluate("db.cfg={nvidia:'nvapi-x'}")
    pg.fill("#txt", "\n".join(links)); pg.click("#bOrdenar")
    for _ in range(espera * 5):
        pg.wait_for_timeout(200)
        if pg.evaluate("!corriendo"): break
    pg.wait_for_timeout(300)
with sync_playwright() as p:
    for ancho, nom in ((390, "movil"), (1280, "pc")):
        print("== " + nom)
        IA["modo"] = "ok"; IA["extra"] = {}
        br, pg = pagina(p, ancho)
        # R1: Instagram que no deja leer (404 simulado) + uno bueno: fin claro, sin «Todo listo» engañoso
        lote(pg, ["https://www.instagram.com/p/MALO1/", "https://www.instagram.com/p/RB/"])
        est = pg.evaluate("db.cards.map(c=>c.estado+'|'+c.motivo)")
        ok("R1 ninguna ficha se queda en cola", not any(e.startswith("pendiente") for e in est), est)
        ok("R1 la mala queda 'Para revisar' con motivo en palabras", any(e.startswith("revisar|Instagram no dejó leer este post") for e in est), est)
        t = pg.evaluate("document.body.innerText")
        ok("R1 el aviso dice «2 procesadas, 1 para revisar»", "2 procesadas, 1 para revisar" in t, t[-300:])
        pg.evaluate("cambiaTab('fichas')"); pg.wait_for_timeout(300)
        t = pg.evaluate("document.body.innerText")
        ok("R1 la lista no dice 'En cola…'", "En cola" not in t and "Instagram no dejó leer este post" in t, t[:300])
        pg.screenshot(path=CD + "R1-lista-%s.png" % nom)
        # R1: si un análisis acaba sin estado final (fallo tragado), correr lo deja en «Para revisar»
        pg.evaluate("""()=>{window.__an=analizar;analizar=async c=>{return c};db.cards=[];db.bn=0;db.cards.push({id:'cola1',url:'https://www.instagram.com/p/X1/',tipo:'Instagram',estado:'pendiente',bloque:1,grupo:'AI',titulo:'https://www.instagram.com/p/X1/',resumen:'',categoria:'Pendiente',repos:[],tags:[],motivo:''});sesionDesde=1;correr()}""")
        for _ in range(50):
            pg.wait_for_timeout(200)
            if pg.evaluate("!corriendo"): break
        pg.evaluate("analizar=window.__an;0")
        r = pg.evaluate("db.cards[0].estado+'|'+db.cards[0].motivo")
        ok("R1 análisis sin estado final -> Para revisar con motivo", r.startswith("revisar|") and len(r) > 12, r)
        ok("R1 aviso no dice 'Todo listo' sin procesadas bien", "1 para revisar" in pg.evaluate("document.body.innerText"))
        # R1: ficha restaurada de la copia con 'pendiente' -> se pinta como para revisar con Reintentar
        pg.evaluate("db.cards=[];db.cards.push({id:'rs',url:'https://www.instagram.com/p/RS/',tipo:'Instagram',estado:'revisar',categoria:'Para revisar',motivo:'Se quedó a medias al cerrar la app. Pulsa «Reintentar»',repos:[],tags:[],estadoUso:'nuevo'});pintar()")
        h = pg.evaluate("filaHtml(db.cards[0])+detalleHtml(db.cards[0])")
        ok("R1 la ficha para revisar ofrece Reintentar y Abrir", "Reintentar" in h and "Abrir en Instagram" in h, h[:200])
        # R2: post en inglés, «Sirve para» en español con buena base: se conserva; inventado: vacío; largo: se acorta
        def corre(cod, extra):
            IA["extra"] = extra; pg.evaluate("db.cfg={nvidia:'nvapi-x'}")
            return pg.evaluate("""async(c)=>{const k={id:'z'+c,url:'https://www.instagram.com/p/'+c+'/',tipo:'Instagram',estado:'pendiente',bloque:1,grupo:'AI',titulo:'',resumen:'',categoria:'',repos:[],tags:[],fuente:'',motivo:''};
              db.cards.push(k);await analizar(k);return {s:k.sirve,a:k.accion}}""", cod)
        r = corre("RB", {"sirve": "Automatizar tareas repetitivas desde la terminal", "accion": "Instalar"})
        ok("R2 sirve en español sobre post en inglés se conserva", r["s"] == "Automatizar tareas repetitivas desde la terminal" and r["a"] == "Instalar", r)
        r = corre("RC", {"sirve": "Ganar dinero invirtiendo en criptomonedas rapidamente", "accion": "Instalar"})
        ok("R2 inventado sigue vacío y Solo guardar", r["s"] == "" and r["a"] == "Solo guardar", r)
        r = corre("RB", {"sirve": "Automatizar tareas repetitivas desde la terminal " + "y también la terminal de tareas " * 5, "accion": "Instalar"})
        ok("R2 línea larga se acorta (<=111) en vez de perderse", 0 < len(r["s"]) <= 111 and r["a"] == "Instalar", r)
        # R4: recuperar una ficha desde «Descartadas»
        pg.evaluate("""db.cards=[{id:'d1',url:'https://x.test/d1',tipo:'Web',estado:'ok',bloque:1,grupo:'AI',titulo:'Ficha descartada',resumen:'Algo que descarté',categoria:'Webs',repos:[],tags:[],estadoUso:'descartada'}];filtro='todo';cambiaTab('fichas');pintar()""")
        pg.click('#filtros [data-mas]'); pg.click('#hojaF [data-f="descartada"]'); pg.wait_for_timeout(300)
        ok("R4 la ficha aparece en Descartadas", "Ficha descartada" in pg.inner_text("#lista"))
        pg.click('#lista .rw[data-id="d1"] .rb'); pg.wait_for_timeout(400)
        pg.screenshot(path=CD + "R4-detalle-%s.png" % nom)
        ok("R4 el detalle se abre y marca Descartada", "Descartada" in pg.inner_text("#det"), pg.inner_text("#det")[:200])
        pg.click('#det button[data-a="uso"][data-u="nuevo"]'); pg.wait_for_timeout(300)
        ok("R4 pasa a «Nuevo»", pg.evaluate("db.cards[0].estadoUso") == "nuevo")
        pg.evaluate("document.querySelector('#det').classList.remove('on')") if ancho < 700 else None
        ok("R4 ya no está en Descartadas", "Ficha descartada" not in pg.inner_text("#lista"))
        pg.click('#filtros button[data-f="nuevo"]'); pg.wait_for_timeout(300)
        ok("R4 está de vuelta en Nuevo", "Ficha descartada" in pg.inner_text("#lista"))
        pg.screenshot(path=CD + "R4-recuperada-%s.png" % nom)
        br.close()
fin()
