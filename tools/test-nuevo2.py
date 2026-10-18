# Prueba 2 (2026-10-15): fotogramas del video, bloques en cola, repos obsoletos, enlaces rotos, selección y exportar .txt.
import json, sys, threading, time
from playwright.sync_api import sync_playwright

BASE = "C:/Users/PC/DeskBox/Apps/CODE/IG Info extractor Code/ig-vault-apk/"
HTML = "file:///" + BASE + "src/assets/index.html"
ERR, res = [], []
PNG = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

def repo(name, pushed, archived=False, stars=500):
    return {"full_name": name, "description": "Herramienta " + name, "stargazers_count": stars, "topics": [], "html_url": "https://github.com/" + name, "homepage": "", "pushed_at": pushed, "archived": archived}

def http(m, url, hd, body):
    time.sleep(0.15)  # que los bloques tarden un poco y se vea la cola
    if "instagram.com/p/" in url and "embed" not in url:
        code = url.split("/p/")[1].split("/")[0]
        cap = "Mira esta herramienta CLI foo-cli " + code + " con github.com/acme/vieja-" + code + " y github.com/acme/nueva-" + code
        return {"status": 200, "url": url, "body": '<meta property="og:image" content="https://img.test/a.jpg">{"caption":{"text":' + json.dumps(cap) + '},"video_versions":[{"width":1,"url":"https://vid.test/' + code + '.mp4"}]}'}
    if "api.github.com/repos/acme/vieja-" in url and "readme" not in url:
        return {"status": 200, "body": json.dumps(repo(url.split("repos/")[1], "2022-01-01T00:00:00Z"))}
    if "api.github.com/repos/acme/nueva-" in url and "readme" not in url:
        return {"status": 200, "body": json.dumps(repo(url.split("repos/")[1], time.strftime("%Y-%m-%dT00:00:00Z")))}
    if "api.github.com/repos/acme/archivada" in url:
        return {"status": 200, "body": json.dumps(repo("acme/archivada", "2024-01-01T00:00:00Z", True))}
    if "api.github.com/repos/acme/borrada" in url:
        return {"status": 404, "body": "{}"}
    if "integrate.api.nvidia.com" in url:
        pr = json.loads(body)["messages"][0]["content"]
        if isinstance(pr, list):
            txt = pr[0]["text"]
            return {"status": 200, "body": json.dumps({"choices": [{"message": {"content": "Terminal: npx foo-cli install --global\nPantalla: instalación de foo-cli" if "fotograma" in txt else "Imagen: portada"}}]})}
        if "asistente de productividad" in pr:
            ids = [x["id"] for x in json.loads(pr.split("FICHAS: ")[1])]
            out = {"plan": [{"id": i, "motivo": "Encaja con tu trabajo", "paso": "Abre el repo y lee el README"} for i in ids[:5]]}
        elif "Eres un extractor riguroso" in pr:
            out = {"titulo": "foo-cli: herramienta de terminal", "resumen": "foo-cli es una herramienta de terminal que se instala con npx foo-cli install para automatizar tareas.", "categoria": "Programas y apps", "relevancia": 4, "proyectos": [], "tags": ["cli"], "web": None}
        else:
            out = {"explicacion": "foo-cli es una herramienta de terminal que se instala con npx. Sirve para automatizar tareas desde la línea de comandos y el vídeo muestra la instalación paso a paso con el comando exacto.", "puntos": ["Instalar con npx", "Usar desde terminal"], "skills": [], "como": ["npx foo-cli install --global"], "limites": ""}
        return {"status": 200, "body": json.dumps({"choices": [{"message": {"content": json.dumps(out)}}]})}
    if url.endswith("/viva"):
        return {"status": 200, "body": "ok"}
    if url.endswith("/muerta"):
        return {"status": 404, "body": ""}
    return {"status": 404, "url": url, "body": ""}

INIT = """(()=>{window.__fr=0;window.Native={claves:()=>%s,copiar(t){window.__copiado=t},compartir(t){window.__compartido=t},abrir(){},pegado:()=>"",
 http:(id,...a)=>window.__py('http',a).then(r=>window.__r(id,JSON.stringify(r))),
 frames:(id,u)=>{window.__fr++;window.__r(id,JSON.stringify({status:200,frames:["%s","%s"]}))},
 pagina:(id)=>window.__r(id,'{}'),voz:(id)=>window.__r(id,'{"status":0,"body":""}'),foto:(id)=>window.__r(id,'{"status":0}')}})()""" % (json.dumps(json.dumps({"nvidia": "nvapi-test"})), PNG, PNG)

def ok(t, v, extra=""):
    print(("  OK   " if v else "  FALLA") + " | " + t + (" | " + str(extra) if (extra and not v) else "")); res.append(bool(v)); return v

with sync_playwright() as p:
    br = p.chromium.launch(); pg = br.new_context(viewport={"width": 1280, "height": 900}).new_page()
    pg.on("pageerror", lambda e: ERR.append(str(e))); pg.on("console", lambda m: ERR.append(m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)  # imágenes externas: no son fallos de la app
    pg.expose_function("__py", lambda n, a: http(*a)); pg.add_init_script(INIT)
    pg.route("https://img.test/**", lambda r: r.abort())
    pg.goto(HTML); pg.wait_for_timeout(800); pg.evaluate("db.cards=[];db.bn=0;guardar();pintar()")

    # ---- bloques: 3 lotes pegados mientras trabaja ----
    pg.fill("#txt", "https://www.instagram.com/p/AAA1/\nhttps://www.instagram.com/p/AAA2/"); pg.click("#bOrdenar"); pg.wait_for_timeout(300)
    ok("el botón cambia a «Añadir bloque 2» mientras trabaja", "bloque 2" in pg.inner_text("#bOrdenar"), pg.inner_text("#bOrdenar"))
    pg.fill("#txt", "https://www.instagram.com/p/BBB1/\nhttps://www.instagram.com/p/BBB2/"); pg.click("#bOrdenar")
    pg.fill("#txt", "https://www.instagram.com/p/CCC1/"); pg.click("#bOrdenar"); pg.wait_for_timeout(300)
    ok("se ven 3 bloques a la vez", pg.locator("#bloques .blq").count() == 3, pg.locator("#bloques .blq").count())
    ok("sigue en la pestaña Pegar (no te saca)", pg.evaluate("document.querySelector('#p-pegar').classList.contains('on')"))
    pg.wait_for_function("db.cards.length==5 && !db.cards.some(c=>c.estado==='pendiente')", timeout=90000)
    ok("5 links de 3 bloques procesados", pg.evaluate("db.cards.filter(c=>c.estado==='ok').length") == 5, pg.evaluate("db.cards.map(c=>c.estado)"))
    ok("bloques marcados ✅ terminado", pg.inner_text("#bloques").count("terminado") == 3, pg.inner_text("#bloques"))

    # ---- fotogramas ----
    c = pg.evaluate("(()=>{const c=db.cards[0];return {frames:c.vio&&c.vio.frames,t:c.texto,n:window.__fr,rep:(c.repos||[]).map(r=>r.full)}})()")
    ok("se pidieron fotogramas del vídeo", c["n"] >= 5, c["n"])
    ok("lo que se ve en el vídeo entra en la ficha", c["frames"] and "npx foo-cli install" in c["t"], c)
    ok("la ficha enseña 🎞 fotogramas del vídeo", "fotogramas del vídeo" in (pg.evaluate("cambiaTab('fichas')") or "") + (pg.click(".rw .rb") or "") + pg.inner_text("#det"))

    # ---- repos obsoletos ----
    pg.evaluate("cambiaTab('fichas')"); pg.wait_for_timeout(200)
    pg.evaluate("cerrarDet()"); txt = pg.inner_text("#lista")
    ok("repo con pushed 2022 sale como Obsoleto", "Obsoleto" in txt or pg.evaluate("estadoRepo({pushed:'2022-01-01T00:00:00Z'}).cls") == "bad")
    r = pg.evaluate("[estadoRepo({pushed:'2022-01-01T00:00:00Z'}).cls, estadoRepo({archived:true,pushed:'2026-10-01T00:00:00Z'}).cls, estadoRepo({pushed:new Date().toISOString()}).cls, estadoRepo({pushed:new Date(Date.now()-8*2.63e9).toISOString()}).cls]")
    ok("estado repo: obsoleto/archivado=bad, reciente=ok, 8 meses=warn", r == ["bad", "bad", "ok", "warn"], r)

    # ---- comprobar enlaces y repos ----
    pg.evaluate("""()=>{db.cards=[{id:'x1',url:'https://www.instagram.com/p/ZZZ/',tipo:'Instagram',estado:'ok',grupo:'AI',categoria:'Repositorios',titulo:'Con enlaces',resumen:'r',
      repos:[{full:'acme/borrada',url:'https://github.com/acme/borrada',stars:1},{full:'acme/archivada',url:'https://github.com/acme/archivada',stars:5,pushed:'2025-01-01T00:00:00Z'}],
      links:[{t:'Viva',u:'https://ok.test/viva'},{t:'Muerta',u:'https://ok.test/muerta'}],tags:[]}];guardar();pintar();}""")
    pg.evaluate("cambiaTab('ajustes')"); pg.click("#bComprobar");  # B3: ahora en Ajustes › Mantenimiento
    pg.wait_for_function("!comprobando", timeout=40000); pg.wait_for_timeout(300)
    d = pg.evaluate("({rotos:db.cards[0].rotos, arch:db.cards[0].repos[1].archived})")
    ok("detecta el enlace roto y el repo borrado", "https://ok.test/muerta" in d["rotos"] and "https://github.com/acme/borrada" in d["rotos"] and "https://ok.test/viva" not in d["rotos"], d)
    ok("detecta repo archivado", d["arch"] is True)
    pg.evaluate("cambiaTab('fichas')"); pg.wait_for_timeout(200); pg.click(".rw .rb"); pg.wait_for_timeout(200)
    ok("el detalle muestra enlaces rotos y archivado", "roto(s)" in pg.inner_text("#det") and "archivado" in pg.inner_text("#det"), pg.inner_text("#det")[:400]); pg.evaluate("cerrarDet()")

    # ---- selección + exportar .txt: solo sale lo marcado ----
    pg.evaluate("""()=>{db.sel={};db.cards=['Alfa','Beta','Gamma'].map((n,i)=>({id:'e'+i,url:'https://ex.test/'+n,tipo:'Web',estado:'ok',grupo:'AI',categoria:'Webs',titulo:'Herramienta '+n,resumen:'Resumen de '+n,
      como:i==0?['npx '+n.toLowerCase()+' install']:[],repos:[],links:[{t:'Docs',u:'https://docs.test/'+n}],notas:i==0?'MI NOTA':'',tags:[]}));guardar();pintar();cambiaTab('fichas')}""")
    pg.wait_for_timeout(200)
    ok("cada ficha tiene casilla de ≥44px", pg.evaluate("[...document.querySelectorAll('.rw .sel')].every(b=>{const r=b.getBoundingClientRect();return r.width>=44&&r.height>=44})") and pg.locator(".rw .sel").count() == 3)
    pg.locator(".rw .sel").nth(0).click(); pg.locator(".rw .sel").nth(2).click(); pg.wait_for_timeout(100)
    ok("barra: «2 seleccionadas»", pg.is_visible("#barSel") and "2 seleccionadas" in pg.inner_text("#selN"), pg.inner_text("#selN"))
    pg.fill("#buscar", "Beta"); pg.wait_for_timeout(150)
    ok("la selección sobrevive al filtrar", "2 seleccionadas" in pg.inner_text("#selN") and pg.evaluate("Object.keys(db.sel).length") == 2)
    pg.fill("#buscar", ""); pg.wait_for_timeout(150)
    pg.click("#bExport"); pg.wait_for_selector("#dcc[open]", timeout=3000)
    t = pg.input_value("#ccTxt")
    ok("el .txt solo contiene lo marcado (Alfa y Gamma, no Beta)", "Herramienta Alfa" in t and "Herramienta Gamma" in t and "Herramienta Beta" not in t, t[:400])
    ok("trae instrucciones, comando real, 'sin comando verificado', links y notas", "Pide confirmación" in t and "npx alfa install" in t and "sin comando verificado" in t and "https://docs.test/Gamma" in t and "https://ex.test/Alfa" in t and "MI NOTA" in t)
    pg.click("#ccNo")
    pg.click("#selNinguna"); pg.wait_for_timeout(100)
    ok("«Ninguna» limpia la selección y oculta la barra", not pg.is_visible("#barSel"))
    pg.click("#bExport"); pg.wait_for_selector("#dlg[open]", timeout=3000)
    ok("sin selección pregunta «¿Exportar todo lo visible?»", "Exportar lo que se ve (3)" in pg.inner_text("#dC"), pg.inner_text("#dC"))
    pg.click("#dSi"); pg.wait_for_selector("#dcc[open]", timeout=3000)
    ok("tras aceptar exporta las 3", pg.input_value("#ccTxt").count("\n## ") == 3)
    pg.click("#ccNo")
    pg.click("#selNinguna") if pg.is_visible("#barSel") else None
    pg.click("#bMas"); pg.wait_for_timeout(100)
    ok("menú «⋯ Más» con ≤2 acciones (B3)", 1 <= pg.locator("#menuMas button:visible").count() <= 2)
    pg.mouse.click(5, 5); pg.wait_for_timeout(100)
    ok("el menú se cierra al tocar fuera", not pg.is_visible("#menuMas"))
    ok("ya no existen los botones eliminados", all(pg.locator(i).count() == 0 for i in ["#bSemana", "#bObs", "#bCopiar", "#bComp", "#bReclas", "#bClaude"]))
    br.close()

print("\nERRORES JS:", ERR if ERR else "ninguno"); print("RESULTADO: %d/%d OK" % (sum(res), len(res)))
sys.exit(0 if all(res) and not ERR else 1)
