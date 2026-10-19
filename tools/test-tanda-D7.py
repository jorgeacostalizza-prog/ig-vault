# Tanda D7 (19/10/2026): lista limpia (fila con 1 control, deslizar, filtros en 1 fila, barra sin solapes, pendiente colgada). Movil 390 y PC 1280, claro y oscuro.
import sys, os; sys.path.insert(0, "C:/Users/PC/DeskBox/Apps/CODE/IG Info extractor Code/ig-vault-apk/tools")
from arnes import *
CD = BASE + "capturas/tanda-D7/"; os.makedirs(CD, exist_ok=True)
def fichas(n=14):
    return [{"id": "v%d" % i, "url": "https://www.instagram.com/reel/V%d/" % i, "tipo": "Instagram", "estado": "ok", "grupo": "AI",
             "titulo": "Herramienta número %d para automatizar un montón de cosas distintas en el PC" % i,
             "resumen": "El proyecto es un repositorio que automatiza tareas. Segunda frase." if i % 2 else "Es una herramienta de terminal para tareas.",
             "sirve": "Automatizar tareas repetitivas desde la terminal" if i % 3 == 0 else "",
             "accion": "Instalar" if i % 3 == 0 else "Solo guardar", "categoria": "Repositorios" if i < 7 else "Programas y apps",
             "repos": [{"full": "a/b%d" % i, "url": "https://github.com/a/b%d" % i, "stars": "5"}] if i % 4 == 0 else [], "tags": [], "fuente": "", "motivo": "", "estadoUso": "nuevo"} for i in range(n)]
with sync_playwright() as p:
    for esquema in ("dark", "light"):
        for ancho, alto, nom in ((390, 844, "movil"), (1280, 900, "pc")):
            tag = "%s-%s" % (nom, esquema); print("== " + tag)
            br = p.chromium.launch(); ctx = br.new_context(viewport={"width": ancho, "height": alto}, color_scheme=esquema, has_touch=False); pg = ctx.new_page()
            pg.on("pageerror", lambda e: ERR.append(str(e)))
            pg.on("console", lambda m: ERR.append(m.text) if m.type == "error" and "Failed to load resource" not in m.text and "api/ping" not in m.text else None)
            pg.expose_function("__py", lambda n, a: http(*a)); pg.add_init_script(INIT)
            pg.route("https://img.test/**", lambda r: r.abort()); pg.goto(HTML); pg.wait_for_timeout(500)
            import json as J
            pg.evaluate("c=>{db.cards=c;db.bn=0;db.cfg={};filtro='todo';guardar();cambiaTab('fichas')}", fichas())
            pg.wait_for_timeout(200)
            # (1) primera ficha sin scroll por debajo de ~300px (movil)
            y = pg.evaluate("document.querySelector('#lista .rw').getBoundingClientRect().top")
            if nom == "movil": ok("primera ficha por encima de 300px (top=%d)" % y, y < 300, y)
            # (2) ninguna fila con >1 control visible a la derecha
            mx = pg.evaluate("""Math.max(...[...document.querySelectorAll('#lista .rw')].map(r=>{const b=r.querySelector('.rb').getBoundingClientRect();
              return [...r.querySelectorAll('button,a')].filter(e=>!e.closest('.racc')&&!e.classList.contains('sel')&&!e.classList.contains('rb')&&e.getBoundingClientRect().left>=b.right-1&&e.offsetWidth>0).length}))""")
            ok("ninguna fila con más de 1 control a la derecha (max=%s)" % mx, mx <= 1, mx)
            ok("sin botón «Nuevo» repetido en las filas", pg.evaluate("[...document.querySelectorAll('#lista .rw button')].filter(b=>b.textContent.trim()==='Nuevo').length") == 0)
            t = pg.evaluate("document.querySelector('#lista .rw[data-id=v3] .rs').textContent")
            ok("«Sirve para: …» si hay sirve", "Sirve para: Automatizar" in t, t)
            t = pg.evaluate("document.querySelector('#lista .rw[data-id=v1] .rs').textContent")
            ok("sin sirve: primera frase sin «El proyecto es»", "Un repositorio que automatiza tareas" in t and "El proyecto es" not in t, t)
            ok("título hasta 2 líneas", pg.evaluate("(()=>{const e=document.querySelector('#lista .rw[data-id=v1] .rt');const lh=parseFloat(getComputedStyle(e).lineHeight);return e.clientHeight<=lh*2+2})()"))
            ok("1 solo icono de fuente por fila", pg.evaluate("[...document.querySelectorAll('#lista .rw')].every(r=>r.querySelectorAll('a.li').length<=1)"))
            # (3) filtros en una fila con scroll
            f = pg.evaluate("(()=>{const b=[...document.querySelectorAll('#filtros button')].map(x=>x.getBoundingClientRect().top);const e=document.querySelector('#filtros');return {una:Math.max(...b)-Math.min(...b)<2,n:b.length,sc:e.scrollWidth>e.clientWidth,txt:[...document.querySelectorAll('#filtros button')].map(x=>x.textContent)}})()")
            ok("filtros en 1 fila: " + str(f["txt"]), f["una"] and f["n"] == 5 and f["txt"][-1].startswith("Más"), f)
            if nom == "movil": ok("la fila de filtros se desliza (scroll horizontal) y «Más» queda visible", f["sc"] and pg.evaluate("(()=>{const b=document.querySelector('#filtros [data-mas]').getBoundingClientRect();return b.right<=innerWidth&&b.left>=0})()"), f)
            pg.click("#filtros [data-mas]"); pg.wait_for_timeout(200)
            ok("hoja «Más» con Para revisar, Con GitHub, Descartadas, categoría y Plegar", pg.evaluate("(()=>{const t=document.querySelector('#hojaF').innerText;return document.querySelector('#hojaF').open&&['Para revisar','Con GitHub','Descartadas','Ir a categoría','Plegar todo'].every(x=>t.includes(x))})()"))
            if nom == "movil": pg.screenshot(path=CD + "hoja-%s.png" % tag)
            pg.click("#hojaF [data-f=repo]"); pg.wait_for_timeout(200)
            ok("filtro «Con GitHub» desde la hoja", pg.evaluate("filtro")=="repo" and pg.locator("#lista .rw").count()==4 and pg.locator("#filtros button.on").inner_text().startswith("Con GitHub"))
            pg.click("#filtros [data-f=todo]"); pg.wait_for_timeout(150)
            # (4) deslizar
            def desliza(sel, dx):
                pg.locator(sel + " .rb").scroll_into_view_if_needed(); pg.wait_for_timeout(100); b = pg.locator(sel + " .rb").bounding_box(); x0 = b["x"] + b["width"] / 2; y0 = b["y"] + b["height"] / 2
                pg.mouse.move(x0, y0); pg.mouse.down(); pg.mouse.move(x0 + dx / 2, y0 + 1, steps=4); pg.mouse.move(x0 + dx, y0 + 1, steps=4)
                if "cap" in desliza.__dict__ and desliza.cap: pg.screenshot(path=desliza.cap)
                pg.mouse.up(); pg.wait_for_timeout(200)
            desliza.cap = CD + "deslizando-%s.png" % tag if nom == "movil" else None
            desliza('.rw[data-id="v2"]', 150)
            ok("deslizar a la derecha = Lo quiero", pg.evaluate("db.cards[2].estadoUso") == "quiero", pg.evaluate("db.cards[2].estadoUso"))
            ok("aviso con «Deshacer»", pg.locator("#avDeshacer").count() == 1 and pg.locator("#avDeshacer").is_visible())
            ok("fila muestra etiqueta «Lo quiero» discreta", "Lo quiero" in pg.evaluate("document.querySelector('.rw[data-id=v2] .rs').textContent"))
            pg.click("#avDeshacer"); pg.wait_for_timeout(200)
            ok("Deshacer revierte a Nuevo", pg.evaluate("db.cards[2].estadoUso") == "nuevo")
            desliza.cap = None
            desliza('.rw[data-id="v5"]', -150)
            ok("deslizar a la izquierda = Descartar", pg.evaluate("db.cards[5].estadoUso") == "descartada")
            pg.click("#avDeshacer"); pg.wait_for_timeout(200)
            ok("Deshacer revierte el descarte", pg.evaluate("db.cards[5].estadoUso") == "nuevo")
            desliza('.rw[data-id="v6"]', 40)
            ok("deslizar poco no cambia nada y no abre la ficha", pg.evaluate("db.cards[6].estadoUso") == "nuevo" and not pg.evaluate("document.querySelector('#det').classList.contains('on')") or nom == "pc")
            # accesible por teclado y desde la ficha
            pg.locator('.rw[data-id="v7"] .rb').scroll_into_view_if_needed(); pg.focus('.rw[data-id="v7"] .rb'); pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(150)
            ok("teclado: flecha derecha = Lo quiero", pg.evaluate("db.cards[7].estadoUso") == "quiero")
            pg.locator('.rw[data-id="v8"] .rb').scroll_into_view_if_needed(); pg.click('.rw[data-id="v8"] .rb'); pg.wait_for_timeout(300)
            pg.click('#det [data-a=uso][data-u=hecho]'); pg.wait_for_timeout(150)
            ok("desde la ficha abierta sigue funcionando (Hecho)", pg.evaluate("db.cards[8].estadoUso") == "hecho")
            pg.evaluate("cerrarDet()"); pg.wait_for_timeout(200)
            # selección múltiple intacta
            pg.locator('.rw[data-id="v9"] .sel').scroll_into_view_if_needed(); pg.locator('.rw[data-id="v9"] .sel').click(); pg.locator('.rw[data-id="v10"] .sel').click(); pg.wait_for_timeout(100)
            ok("selección múltiple: 2 seleccionadas", "2 seleccionadas" in pg.inner_text("#selN"))
            pg.evaluate("db.sel={};marca()")
            # (5) barra inferior no tapa la última fila
            if nom == "movil":
                pg.evaluate("document.querySelector('main').scrollTop=1e6"); pg.wait_for_timeout(200)
                r = pg.evaluate("(()=>{const f=[...document.querySelectorAll('#lista .rw')].pop().getBoundingClientRect();const n=document.querySelector('nav').getBoundingClientRect();return {fb:f.bottom,nt:n.top}})()")
                ok("la última fila queda por encima de la barra (fila %d <= barra %d)" % (r["fb"], r["nt"]), r["fb"] <= r["nt"] + 1, r)
                z = pg.evaluate("(()=>{const n=document.querySelector('nav');const q=n.getBoundingClientRect();const e=document.elementFromPoint(q.left+q.width/2,q.top+q.height/2);return n.contains(e)})()")
                ok("nada se cuela por encima de la barra (summary sticky)", z)
                pg.screenshot(path=CD + "final-lista-%s.png" % tag)
            pg.evaluate("document.querySelector('main').scrollTop=0")
            pg.screenshot(path=CD + "lista-%s.png" % tag)
            # (6) pendiente colgada
            pg.evaluate("""()=>{db.cards.push({id:'pp',url:'https://www.instagram.com/reel/Demo6mdgilA/',tipo:'Instagram',estado:'pendiente',bloque:1,grupo:'AI',titulo:'https://www.instagram.com/reel/Demo6mdgilA/',resumen:'',categoria:'Pendiente',repos:[],tags:[],fuente:'',motivo:''});
              db.cards.push({id:'pq',url:'https://github.com/a/zzz',tipo:'GitHub',estado:'pendiente',bloque:1,grupo:'AI',titulo:'https://github.com/a/zzz',resumen:'',categoria:'Pendiente',repos:[],tags:[],fuente:'',motivo:''});
              reconciliar=true; corriendo=false; pintar()}""")
            pg.wait_for_timeout(200)
            e = pg.evaluate("db.cards.filter(c=>c.id==='pp'||c.id==='pq').map(c=>c.estado)")
            ok("pendiente sin cola -> Para revisar", e == ["revisar", "revisar"], e)
            tx = pg.evaluate("document.querySelector('#lista .rw[data-id=pp]').innerText")
            ok("motivo en palabras, título «Reel de Instagram», sin URL cruda", "Reel de Instagram" in tx and "Se quedó a medias" in tx and "http" not in tx, tx)
            tx2 = pg.evaluate("document.querySelector('#lista .rw[data-id=pq]').innerText")
            ok("repo directo: «Repo de GitHub»", "Repo de GitHub" in tx2 and "http" not in tx2, tx2)
            pg.evaluate("db.cards.push({id:'pr',url:'https://x.test/a',tipo:'Web',estado:'pendiente',cola:Date.now(),titulo:'https://x.test/a',resumen:'',categoria:'Pendiente',repos:[],tags:[],fuente:'',motivo:''});pintar()")
            ok("pendiente con trabajo reciente no se toca; título = dominio", pg.evaluate("db.cards.find(c=>c.id==='pr').estado")=="pendiente" and "x.test" in pg.evaluate("document.querySelector('#lista .rw[data-id=pr] .rt').textContent"))
            pg.screenshot(path=CD + "pendiente-%s.png" % tag)
            br.close()
fin()
