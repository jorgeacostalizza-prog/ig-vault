# Prueba de IG Extractor (reforma 2026-10-15) sobre el index.html REAL en Chromium oculto.
# Red 100% simulada (sin internet): Instagram, GitHub y la IA responden con datos de prueba.
import json, re, sys
from playwright.sync_api import sync_playwright

BASE = "C:/Users/PC/DeskBox/Apps/CODE/IG Info extractor Code/ig-vault-apk/"
HTML = "file:///" + BASE + "src/assets/index.html"
ERR = []
ALUCINA = {"on": False}
LLAMADAS = {"ia": 0}

CAP = "Mira este repo obra/superpowers: skills para Claude Code. 1) brainstorming 2) planes 3) tests. Instálalo con /plugin install superpowers. Comenta SKILLS y te lo mando. github.com/obra/superpowers"
IG_HTML = ('<html><head><meta property="og:image" content="https://img.test/portada.jpg"></head><body>'
           '{"caption":{"text":' + json.dumps(CAP) + '},"edge_media_to_comment":{"count":7},'
           '"carousel_media":[' + ",".join('{"image_versions2":{"candidates":[{"url":"https://img.test/s%d.jpg"}]}}' % i for i in range(1, 6)) + ']}</body></html>')
README = "# superpowers\nSkills para agentes de código. Brainstorming, planes y tests. Install: /plugin install superpowers@claude-plugins-official"

def http(m, url, hd, body):
    if "instagram.com/p/AAA111" in url and "embed" not in url:
        return {"status": 200, "url": url, "body": IG_HTML}
    if "api.github.com/repos/obra/superpowers/readme" in url:
        return {"status": 200, "url": url, "body": README}
    if "api.github.com/repos/obra/superpowers" in url:
        return {"status": 200, "url": url, "body": json.dumps({"full_name": "obra/superpowers", "description": "Skills library for coding agents", "stargazers_count": 21000, "topics": ["claude", "skills"], "html_url": "https://github.com/obra/superpowers", "homepage": ""})}
    if "raw.githubusercontent.com/obra/superpowers" in url and "README.md" in url:
        return {"status": 200, "url": url, "body": README}
    if "integrate.api.nvidia.com" in url:
        LLAMADAS["ia"] += 1
        pr = json.loads(body)["messages"][0]["content"]
        if isinstance(pr, list):
            return {"status": 200, "body": json.dumps({"choices": [{"message": {"content": "Imagen: captura de un repo de skills"}}]})}
        if "Eres un extractor riguroso" in pr:
            if ALUCINA["on"]:
                out = {"titulo": "Videojuego de aventuras", "resumen": "Un videojuego de aventuras gratuito con dragones y mazmorras para consola.", "categoria": "Programas y apps", "relevancia": 3, "proyectos": [], "tags": ["juego"], "web": None}
            else:
                out = {"titulo": "Superpowers: skills para Claude Code", "resumen": "Superpowers es una librería de skills para Claude Code: brainstorming, planes y tests para agentes de código.", "categoria": "Inteligencia artificial", "relevancia": 5, "proyectos": [{"nombre": "superpowers", "repo": "obra/superpowers"}], "tags": ["claude", "skills"], "web": None}
        else:
            out = {"explicacion": "Superpowers es una librería de skills para Claude Code. Añade tres habilidades al agente: brainstorming antes de programar, planes por pasos y pruebas automáticas. Sirve para que el agente trabaje de forma ordenada en proyectos de código y se instala como plugin desde el marketplace oficial.",
                   "puntos": ["Brainstorming: aclara la idea antes de programar", "Planes: divide el trabajo en pasos", "Tests: comprueba cada cambio"], "skills": ["brainstorming — explora requisitos", "writing-plans — plan por pasos"],
                   "como": ["Ejecuta /plugin install superpowers@claude-plugins-official"], "limites": ""}
        return {"status": 200, "body": json.dumps({"choices": [{"message": {"content": json.dumps(out)}}]})}
    return {"status": 404, "url": url, "body": ""}

INIT = """(()=>{window.Native={claves:()=>%s,copiar(t){window.__copiado=t},compartir(){},abrir(u){window.__abierto=u},pegado:()=>"",
 http:(id,...a)=>window.__py('http',a).then(r=>window.__r(id,JSON.stringify(r))),
 pagina:(id,...a)=>window.__r(id,'{}'),voz:(id,...a)=>window.__r(id,'{"status":0,"body":""}'),foto:(id,...a)=>window.__r(id,'{"status":0}')}})()""" % json.dumps(json.dumps({"nvidia": "nvapi-test"}))

res = []
def ok(t, v, extra=""):
    print(("  OK   " if v else "  FALLA") + " | " + t + (" | " + str(extra) if (extra and not v) else ""))
    res.append(bool(v)); return v

def main(movil):
    w, h = (390, 844) if movil else (1280, 900)
    print("== " + ("MÓVIL 390px" if movil else "ESCRITORIO 1280px"))
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_context(viewport={"width": w, "height": h}).new_page()
        pg.on("console", lambda m: ERR.append("CONSOLE: " + m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: ERR.append("PAGEERROR: " + str(e)))
        pg.expose_function("__py", lambda n, a: http(*a))
        PNG = bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d4944415478da63fcffff3f0300050001a5f645400000000049454e44ae426082")
        pg.route("https://img.test/**", lambda r: r.fulfill(status=200, content_type="image/png", body=PNG))
        pg.add_init_script(INIT)
        pg.goto(HTML); pg.wait_for_timeout(900)
        ok("título de la pestaña = IG Extractor", pg.title() == "IG Extractor", pg.title())
        ok("ya no aparece «IG Vault» en la pantalla", "IG Vault" not in pg.inner_text("body"))
        pg.evaluate("db.cards=[]; guardar(); pintar()")

        # ---- pipeline completo: pegar un link de Instagram y ordenar ----
        pg.fill("#txt", "mira esto https://www.instagram.com/p/AAA111/?igsh=zzz y otra vez instagram.com/reel/AAA111 \nhttps://github.com/obra/superpowers")
        pg.click("#bOrdenar"); pg.wait_for_function("db.cards.length>0 && !db.cards.some(c=>c.estado==='pendiente')", timeout=60000)
        c = pg.evaluate("db.cards.map(c=>({t:c.titulo,e:c.estado,cat:c.categoria,tipo:c.tipo,imgs:(c.imgs||[]).length,links:(c.links||[]).map(l=>l.u),repos:(c.repos||[]).map(r=>r.full),n:(c.puntos||[]).length,sk:(c.skills||[]).length,como:(c.como||[]).length,extra:c.extra||[],res:c.resumen,url:c.url}))")
        print("   fichas:", json.dumps(c, ensure_ascii=False)[:700])
        ok("3 links pegados (post IG + reel repetido + repo) → fusionados en 1 ficha", len(c) == 1, len(c))
        f = c[0] if c else {}
        ok("ficha ok y categoría fija", f.get("e") == "ok" and f.get("cat") in ["Repositorios", "Inteligencia artificial", "Programas y apps", "Webs", "Recursos", "Tutoriales", "Cursos", "Otros"], f.get("cat"))
        ok("muestra TODAS las imágenes (≥5)", f.get("imgs", 0) >= 5, f.get("imgs"))
        ok("tiene repo verificado obra/superpowers", "obra/superpowers" in f.get("repos", []))
        ok("explicación con puntos, skills y pasos", f.get("n") == 3 and f.get("sk") == 2 and f.get("como") == 1, (f.get("n"), f.get("sk"), f.get("como")))
        ok("guarda el link original de Instagram", "instagram.com/p/AAA111" in f.get("url", ""))

        pg.evaluate("cambiaTab('fichas')"); pg.wait_for_timeout(300)
        hrefs = pg.eval_on_selector_all(".card a.lk", "els=>els.map(e=>e.href)")
        ok("se ven a la vez el link de Instagram y el de GitHub (como <a> reales)", any("instagram.com/p/AAA111" in x for x in hrefs) and any("github.com/obra/superpowers" in x for x in hrefs), hrefs)
        ok("las imágenes se pintan todas", pg.locator(".card .gal img").count() >= 5, pg.locator(".card .gal img").count())
        ok("etiqueta de relevancia visible", pg.locator(".card .rel").count() == 1, pg.inner_text(".card .rel") if pg.locator(".card .rel").count() else "")

        # clic en enlace: la página NO se queda en negro / sigue usable
        pg.click(".card a.lk.ig"); pg.wait_for_timeout(200)
        ok("el clic en Instagram abre el link correcto (puente nativo)", "instagram.com/p/AAA111" in (pg.evaluate("window.__abierto||''")))
        vis = pg.evaluate("(()=>{const e=document.elementFromPoint(innerWidth/2,innerHeight/2);return !!e && e.tagName!=='HTML'})()")
        ok("tras pulsar un enlace la app sigue visible y usable", vis and pg.is_visible(".card") and pg.evaluate("getComputedStyle(document.body).backgroundColor")!="rgb(0, 0, 0)")

        # Claude Code
        pg.click(".card [data-a=claude]"); pg.wait_for_timeout(250)
        t = pg.input_value("#ccTxt")
        ok("texto para Claude Code incluye post original + GitHub + pasos", "instagram.com/p/AAA111" in t and "github.com/obra/superpowers" in t and "plugin install" in t and "Qué quiero que hagas" in t)
        pg.click("#ccT button[data-k=instalar]"); ok("cambiar la tarea cambia el texto", "Instálalo" in pg.input_value("#ccTxt"))
        pg.click("#ccCopia"); pg.wait_for_timeout(200)
        ok("botón Copiar entrega el texto (puente nativo)", "Tarea para Claude Code" in (pg.evaluate("window.__copiado||''")))

        # ---- anti-invención: la IA habla de un videojuego sin relación ----
        ALUCINA["on"] = True
        pg.evaluate("db.cards=[]; guardar(); cambiaTab('pegar')")
        pg.fill("#txt", "https://www.instagram.com/p/AAA111/"); pg.click("#bOrdenar")
        pg.wait_for_function("db.cards.length>0 && !db.cards.some(c=>c.estado==='pendiente')", timeout=60000)
        r = pg.evaluate("({t:db.cards[0].titulo,r:db.cards[0].resumen,m:db.cards[0].motivo})")
        ok("resumen inventado (videojuego) descartado", "videojuego" not in (r["r"] + r["t"]).lower(), r)
        ALUCINA["on"] = False

        # ---- duplicados ----
        pg.evaluate("""()=>{db.cards=[
          {id:'a',url:'https://www.instagram.com/reel/XYZ1/',tipo:'Instagram',estado:'ok',grupo:'AI',categoria:'Repositorios',titulo:'Superpowers para Claude',resumen:'corto',links:[{t:'Web',u:'https://a.com'}],repos:[{full:'obra/superpowers',url:'https://github.com/obra/superpowers',stars:21000}],tags:[]},
          {id:'b',url:'https://instagram.com/p/XYZ1/?igsh=1',tipo:'Instagram',estado:'ok',grupo:'AI',categoria:'Repositorios',titulo:'Otro titulo',resumen:'un resumen bastante más largo y completo de la misma publicación',links:[{t:'Docs',u:'https://b.com'}],repos:[],tags:[]},
          {id:'c',url:'https://github.com/obra/superpowers',tipo:'GitHub',estado:'ok',grupo:'AI',categoria:'Repositorios',titulo:'obra/superpowers',resumen:'x',links:[],repos:[{full:'obra/superpowers',url:'https://github.com/obra/superpowers',stars:21000}],tags:[]},
          {id:'d',url:'https://example.com/herramienta-uno',tipo:'Web',estado:'ok',grupo:'AI',categoria:'Webs',titulo:'Una herramienta distinta de verdad',resumen:'r',links:[],repos:[],tags:[]},
          {id:'e',url:'https://example.org/otra-url-distinta',tipo:'Web',estado:'ok',grupo:'AI',categoria:'Webs',titulo:'Una herramienta distinta de verdad',resumen:'r2',links:[],repos:[],tags:[]}
        ]; guardar(); pintar();}""")
        pg.click("#bDup"); pg.wait_for_timeout(250)
        ok("el aviso de duplicados aparece", pg.is_visible("#dlg"))
        pg.click("#dSi"); pg.wait_for_timeout(250)
        pg.evaluate("cambiaTab('fichas')"); n = pg.evaluate("db.cards.length"); ex = pg.evaluate("db.cards[0].links.length")
        ok("5 fichas → 2 (IG+IG+repo juntas; mismo título juntas)", n == 2, n)
        ok("la fusión conserva los links de las repetidas", ex >= 2, ex)
        pg.click("#bDup"); pg.wait_for_timeout(200)
        ok("sin duplicados avisa y no abre nada", not pg.is_visible("#dlg"))

        # ---- clasificación + relevancia ----
        r = pg.evaluate("""()=>({
          a: clasificar({titulo:'Curso gratis de Python en Udemy',resumen:'',url:'https://udemy.com/x',tipo:'Web'}),
          b: clasificar({titulo:'obra/superpowers',resumen:'repo',url:'https://github.com/o/r',tipo:'GitHub',repos:[{full:'o/r'}]}),
          c: clasificar({titulo:'Agentes de IA con MCP',resumen:'un agente con LLM y prompts',url:'https://instagram.com/p/x',tipo:'Instagram'}),
          d: clasificar({titulo:'Cómo configurar tu terminal paso a paso',resumen:'tutorial',url:'https://instagram.com/p/y',tipo:'Instagram'}),
          e: clasificar({titulo:'Nada',resumen:'',url:'https://instagram.com/p/z',tipo:'Instagram'}),
          rel1: relevancia({estado:'ok',titulo:'Claude Code agentes MCP gratis',resumen:'open source github skill',repos:[{full:'a/b',stars:15000}],links:[1,2],fuente:'investigado'}).n,
          rel2: relevancia({estado:'ok',titulo:'Receta de tarta',resumen:'harina',repos:[],links:[]}).n })""")
        print("   clasificación:", r)
        ok("Udemy → Cursos", r["a"] == "Cursos"); ok("repo GitHub → Repositorios", r["b"] == "Repositorios")
        ok("agentes/MCP/LLM → Inteligencia artificial", r["c"] == "Inteligencia artificial"); ok("cómo/paso a paso → Tutoriales", r["d"] == "Tutoriales")
        ok("sin pistas → Otros", r["e"] == "Otros"); ok("tema de Jorge ≥4 y receta ≤2", r["rel1"] >= 4 and r["rel2"] <= 2, (r["rel1"], r["rel2"]))

        # ---- mover sin arrastrar ----
        pg.evaluate("cambiaTab('fichas')"); pg.wait_for_timeout(300)
        pg.click(".card [data-a=mover]"); pg.wait_for_timeout(200)
        ok("el diálogo Mover abre", pg.is_visible("#dmv"))
        pg.fill("#mvN", "Música › Canciones"); pg.click("#mvSi"); pg.wait_for_timeout(250)
        g = pg.evaluate("db.cards.map(c=>c.grupo+'>'+c.categoria)")
        ok("la ficha se movió a Música › Canciones", "Música>Canciones" in g, g)
        ok("ya no existe el agarre de arrastrar", pg.locator(".agarre").count() == 0)

        # ---- filtros y diseño ----
        pg.click("#filtros button[data-f=rel]"); pg.wait_for_timeout(200)
        ok("filtro «Más relevantes» funciona sin error", pg.locator("#filtros button.on").inner_text().startswith("★"))
        if not movil:
            ok("PC: barra lateral a la izquierda", pg.evaluate("document.querySelector('nav').getBoundingClientRect().left")<5 and pg.evaluate("document.querySelector('nav').getBoundingClientRect().width")>150)
        else:
            ok("móvil: barra abajo", pg.evaluate("document.querySelector('nav').getBoundingClientRect().bottom") >= h - 2)
            ok("móvil: sin scroll horizontal", pg.evaluate("document.documentElement.scrollWidth<=innerWidth+1"))
        pg.evaluate("filtro='todo'; cambiaTab('fichas'); pintar()")
        pg.screenshot(path=BASE + "capturas/nuevo-" + ("movil" if movil else "pc") + ".png")
        br.close()

main(False); main(True)
print("\nERRORES JS:", ERR if ERR else "ninguno")
print("RESULTADO: %d/%d OK" % (sum(res), len(res)))
sys.exit(0 if all(res) and not ERR else 1)
