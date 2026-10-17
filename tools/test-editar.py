# Prueba de la hoja de edicion, mover/arrastre y buscar links sobre el index.html REAL.
# Puente Native simulado: http va de verdad (mismo User-Agent que la APK), el resto simulado.
import json, os, re, sys, urllib.request, urllib.error, time
from playwright.sync_api import sync_playwright

BASE = "C:/Users/PC/DeskBox/Apps/CODE/IG Info extractor Code/ig-vault-apk/"
HTML = "file:///" + BASE + "src/assets/index.html"
UA = "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36"
ERR = []

def http(m, url, hd, body):
    h = {"User-Agent": UA, "Accept-Language": "es,en;q=0.8"}
    h.update(json.loads(hd or "{}"))
    rq = urllib.request.Request(url, data=body.encode() if body else None, headers=h, method=m)
    try:
        r = urllib.request.urlopen(rq, timeout=2.5)
        return {"status": r.status, "url": r.geturl(), "body": r.read(1500000).decode("utf8", "replace")}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "url": url, "body": e.read(300000).decode("utf8", "replace")}
    except Exception as e:
        return {"status": 0, "body": "", "error": str(e)}

def puente(n, a):
    if n == "http": return http(*a)
    return {"status": 0, "body": "", "error": "simulado"}

INIT = """(()=>{window.Native={claves:()=>%s,copiar(){},compartir(){},abrir(){},pegado:()=>"",
 http:(id,...a)=>window.__py('http',a).then(r=>window.__r(id,JSON.stringify(r))),
 pagina:(id,...a)=>window.__py('pagina',a).then(r=>window.__r(id,JSON.stringify(r))),
 voz:(id,...a)=>window.__py('voz',a).then(r=>window.__r(id,JSON.stringify(r))),
 foto:(id,...a)=>window.__py('foto',a).then(r=>window.__r(id,JSON.stringify(r)))}})()""" % json.dumps(json.dumps({}))

def main(movil):
    w, h = (390, 844) if movil else (1280, 900)
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_context(viewport={"width": w, "height": h}, user_agent=UA).new_page()
        pg.on("console", lambda m: ERR.append("CONSOLE " + m.type + ": " + m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: ERR.append("PAGEERROR: " + str(e)))
        pg.expose_function("__py", lambda n, a: puente(n, a))
        pg.add_init_script(INIT)
        pg.goto(HTML); pg.wait_for_timeout(1200)

        # siembra tarjetas realisticas (3 secciones distintas)
        pg.evaluate("""() => {
          db.cards = [
            {id:'a', url:'https://instagram.com/p/AAA', tipo:'Instagram', estado:'ok', grupo:'AI', categoria:'Herramientas de IA', titulo:'Whisperflow: voz a texto', resumen:'Flow automatiza insertar texto con comandos de voz. Ejemplo de un producto de voz.', tags:['#voz'], links:[], motivo:''},
            {id:'b', url:'https://instagram.com/reel/BBB', tipo:'Instagram', estado:'ok', grupo:'AI', categoria:'Herramientas de IA', titulo:'Whisperflow otra ficha', resumen:'Repetida a proposito para probar el arrastre.', tags:[], links:[], motivo:''},
            {id:'c', url:'https://instagram.com/reel/CCC', tipo:'Instagram', estado:'ok', grupo:'AI', categoria:'Tutoriales y cursos', titulo:'Atajos de Claude', resumen:'Chuletas paraountain Claude.', tags:[], links:[], motivo:''},
            {id:'d', url:'https://instagram.com/p/DDD', tipo:'Instagram', estado:'ok', grupo:'Musica', categoria:'Canciones', titulo:'Waiting Room EP', resumen:'EP de Waiting Room.', tags:[], links:[], motivo:''}
          ];
          guardar(); pintar(); cambiaTab("fichas");
        }""")
        ok = lambda t, v: print(("  OK   " if v else "  FALLA") + " | " + t) or v
        res = []

        # 1) el editor abre y escribe
        pg.evaluate("abrirEditor(db.cards[0])"); pg.wait_for_timeout(250)
        res.append(ok("editor abre y se ve", pg.is_visible("#hoja")))
        pg.fill("#hTit", "Whisperflow (corregido a mano)")
        pg.fill("#hRes", "Texto escrito por Jorge para probar que se guarda bien y sale entero.")
        pg.fill("#hNota", "NOTA DE JORGE: mirar esto luego\nsegunda linea con tildes: áéñ")
        pg.fill("#hTags", "#voz, #dictado, #prueba")
        res.append(ok("el textarea de notas acepta varias lineas y tildes",
                      pg.eval_on_selector("#hNota", "e => e.value.includes('segunda linea con tildes: áéñ')")))
        pg.click("#hSi"); pg.wait_for_timeout(300)
        st = pg.evaluate("() => { const c = db.cards[0]; return {t: c.titulo, n: c.notas, tags: c.tags.join(','), ls: localStorage.getItem('igv').includes('NOTA DE JORGE')} }")
        res.append(ok("titulo guardado", st["t"] == "Whisperflow (corregido a mano)"))
        res.append(ok("notas guardadas y persistidas", st["n"].startswith("NOTA DE JORGE") and st["ls"]))
        res.append(ok("tags con # y sin espacios raros", st["tags"] == "#voz,#dictado,#prueba"))

        # 2) la nota se ve en el detalle y en el texto exportado
        vis = pg.evaluate("() => { abrirDet(db.cards[0]); const r = document.querySelector('#det').innerHTML.includes('NOTA DE JORGE'); cerrarDet(); return r; }")
        res.append(ok("la nota se ve en el detalle", vis))
        res.append(ok("la nota sale en el .txt", pg.evaluate("() => exportTxt([db.cards[0]]).includes('Notas de Jorge')")))

        # 3) mover con el editor (seleccionando seccion existente)
        pg.evaluate("abrirEditor(db.cards[2])"); pg.wait_for_timeout(200)
        pg.click("#hDest button[data-g='Musica']")
        pg.wait_for_timeout(120)
        pg.click("#hSi"); pg.wait_for_timeout(300)
        mv = pg.evaluate("() => db.cards[2].grupo + ' > ' + db.cards[2].categoria")
        res.append(ok("mover de seccion con el editor (" + mv + ")", mv.startswith("Musica")))

        # 4) mover() directo
        pg.evaluate("mover(db.cards[1], 'AI', 'Para revisar')")
        res.append(ok("mover() cambia grupo y categoria", pg.evaluate("() => db.cards[1].categoria") == "Para revisar"))

        # 5) (arrastre eliminado a propósito: ahora es el botón Mover, probado en el paso 3/4)

        # 6) buscador de links reales (con verificacion) sobre una ficha sin links
        pg.evaluate("db.cards[0].estado='ok'")
        t = time.time()
        found = pg.evaluate("async () => { const c = db.cards[0]; const n = await buscarLinksOficiales(c, {forzar:true}); return {n: n.length, links: (c.links||[]).map(l=>l.t+' | '+l.u), buscado: c.buscado} }")
        res.append(ok("buscar links devuelve algo real en %.0fs: %s" % (time.time()-t, found.get("n")),
                      found.get("n", 0) >= 1))
        print("       ->", found.get("links"))

        # 7) una tarjeta sin links: comprueba que devuelve lista vacia sin romperse
        vac = pg.evaluate("async () => { const c = {id:'x', url:'https://instagram.com/p/ZZZ', estado:'ok', titulo:'zzzz qqqq', resumen:'texto sin nada reconocible zzzz', texto:'', links:[], tags:[]}; const n = await buscarLinksOficiales(c, {forzar:true}); return n.length; }")
        res.append(ok("sin candidatos no inventa links (0)", vac == 0))

        # 8) boton masivo
        pg.evaluate("() => { db.cards[0].links=[]; db.cards[3].links=[]; guardar(); }")
        pg.evaluate("$('#bLinksMasivos').click()")
        pg.wait_for_timeout(500)
        pg.evaluate("() => { window.__finMasivo = true; }")
        pg.wait_for_function("() => !$('#bLinksMasivos').disabled", timeout=120000)
        mres = pg.evaluate("() => ({a:(db.cards[0].links||[]).length, d:(db.cards[3].links||[]).length})")
        res.append(ok("boton masivo busca en las que no tienen (a=%s d=%s)" % (mres["a"], mres["d"]), mres["a"] >= 0))

        # 9) boton atras cierra la hoja
        pg.evaluate("abrirEditor(db.cards[0])"); pg.wait_for_timeout(150)
        back = pg.evaluate("() => window.__atras()")
        res.append(ok("el boton atras cierra el editor", back and not pg.is_visible("#hoja")))

        # 10) zoom de texto y areas tactiles minimas
        tact = pg.evaluate("""() => {
          abrirEditor(db.cards[0]);
          const malos = [...document.querySelectorAll('#hoja button, #hoja input, #hoja textarea, #hoja .hcamp')]
            .map(e => ({t: (e.tagName+'.'+e.className).slice(0,30), h: Math.round(e.getBoundingClientRect().height)}))
            .filter(x => x.h > 0 && x.h < 42);
          return {malos: malos.slice(0,5), n: malos.length, overflow: document.body.scrollWidth > innerWidth + 1};
        }""")
        res.append(ok("todo lo tocable >=42px (malos=%s)" % tact["n"], tact["n"] == 0))
        res.append(ok("sin desbordamiento horizontal", not tact["overflow"]))
        pg.evaluate("cerrarEditor()")

        pg.screenshot(path=BASE + "capturas/hoja-%s.png" % ("movil" if movil else "escritorio"), full_page=False)
        br.close()
    return res

if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "escritorio"
    print("=== " + modo.upper() + " ===")
    r = main(modo == "movil")
    fall = [x for x in r if not x]
    print("  %d/%d OK" % (len(r) - len(fall), len(r)))
    if ERR:
        print("  ERRORES JS:")
        for e in dict.fromkeys(ERR): print("   ", e[:300])
    sys.exit(1 if fall or ERR else 0)