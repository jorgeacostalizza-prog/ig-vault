# Tanda B (18/10/2026): B1 sin Grupo principal, B2 sin ★, B3 mantenimiento en Ajustes, B4 sin semilla, B5 pegar en PC, B6 botón al acabar, B7 pasos. Móvil 390 + PC 1280.
import sys; sys.path.insert(0, "C:/Users/PC/DeskBox/Apps/CODE/IG Info extractor Code/ig-vault-apk/tools")
from arnes import *
import arnes, json as _j

SEM = _j.dumps({"ver": "9", "cards": [{"id": "sm1", "url": "https://semilla.test/1", "tipo": "Web", "estado": "ok", "grupo": "AI", "categoria": "Webs", "titulo": "Ficha de ejemplo", "resumen": "r", "repos": [], "tags": []}]})

with sync_playwright() as p:
    for ancho, nom in ((390, "movil"), (1280, "pc")):
        print("== " + nom); IA["modo"] = "ok"; DEMORA["s"] = 0
        CAPS.clear(); CAPS.update({"B1": "Mira foo-cli en github.com/acme/foo-cli, herramienta de terminal para automatizar tareas"})
        br, pg = pagina(p, ancho)
        # B1
        ok("B1 Pegar ya no tiene «Grupo principal»", pg.locator("#grupo").count() == 0 and "Grupo principal" not in pg.inner_text("#p-pegar"))
        t = pg.inner_text("#pasos")
        ok("B1 pantalla vacía con 3 pasos (copia, pega, ordena)", pg.is_visible("#pasos") and "1." in t and "2." in t and "3." in t and "Copia" in t and "Pégalos" in t and "Ordenar" in t, t)
        pg.screenshot(path=CAPT + "B1-pegar-vacio-" + nom + ".png")
        # B3
        pg.evaluate("cambiaTab('ajustes')"); pg.wait_for_timeout(150)
        tx = pg.inner_text("#p-ajustes")
        ok("B3 Ajustes › Mantenimiento tiene los 3 botones", "Mantenimiento" in tx and all(pg.is_visible(i) for i in ("#bDup", "#bComprobar", "#bLinksMasivos")))
        ok("B2 Ajustes sin «intereses» ni ★", "intereses" not in tx.lower() and "★" not in tx)
        pg.screenshot(path=CAPT + "B3-ajustes-mantenimiento-" + nom + ".png", full_page=True)
        pg.evaluate("cambiaTab('fichas')"); pg.click("#bMas"); pg.wait_for_timeout(100)
        n = pg.locator("#menuMas button:visible").count()
        ok("B3 menú «⋯ Más» con ≤2 entradas (tiene %d)" % n, 1 <= n <= 2 and not pg.locator("#menuMas #bComprobar").count())
        pg.screenshot(path=CAPT + "B3-menu-mas-" + nom + ".png"); pg.mouse.click(5, 5)
        # B7 + B6 con IA
        pg.evaluate("db.cfg.nvidia='nvapi-test';guardar()"); pg.evaluate("cambiaTab('pegar')"); DEMORA["s"] = 0.25
        pg.evaluate("window.__pasos=[];new MutationObserver(()=>window.__pasos.push($('#progS').textContent)).observe($('#progS'),{childList:true,characterData:true,subtree:true})")
        pg.fill("#txt", "https://www.instagram.com/p/B1/"); pg.click("#bOrdenar")
        pg.wait_for_function("db.cards.length>=1 && !db.cards.some(c=>c.estado==='pendiente')", timeout=60000)
        pasos = pg.evaluate("[...new Set(window.__pasos.map(x=>x.split(' · ')[0]))]")
        ok("B7 el progreso cambió de paso ≥3 veces (%s)" % pasos, len(pasos) >= 3 and any("Leyendo" in x for x in pasos) and any("resumen" in x for x in pasos), pasos)
        pg.wait_for_timeout(300)
        ok("B6 el bloque acabado trae el botón «Ver mis 1 fichas»", pg.is_visible("#bloques [data-ver]") and "Ver mis 1 fichas" in pg.inner_text("#bloques"), pg.inner_text("#bloques"))
        pg.wait_for_timeout(5500)
        ok("B6 el mensaje final NO desaparece solo", pg.is_visible("#aviso") and "Todo listo" in pg.inner_text("#aviso"))
        pg.screenshot(path=CAPT + "B6-lote-acabado-" + nom + ".png")
        pg.click("#bloques [data-ver]"); pg.wait_for_timeout(200)
        ok("B6 el botón lleva a Fichas", pg.evaluate("document.querySelector('#p-fichas').classList.contains('on')"))
        # B2 en lista
        ok("B2 sin filtro «Más relevantes» ni ★ en la lista", pg.locator("#filtros button[data-f=rel]").count() == 0 and pg.locator("#lista .rst").count() == 0 and "Más relevantes" not in pg.inner_text("#p-fichas"))
        g = pg.evaluate("db.cards[0].grupo")
        ok("B1 la ficha nueva va al grupo «AI» por defecto", g == "AI", g)
        pg.screenshot(path=CAPT + "B2-fichas-sin-estrellas-" + nom + ".png")
        ok("sin desbordamiento horizontal", pg.evaluate("document.documentElement.scrollWidth<=innerWidth+1"))
        br.close()
        # B4: con semilla disponible, abrir NO la carga
        br = p.chromium.launch(); pg = br.new_context(viewport={"width": ancho, "height": 900}).new_page()
        pg.on("pageerror", lambda e: ERR.append(str(e))); pg.expose_function("__py", lambda n, a: http(*a))
        pg.add_init_script(INIT.replace("copiar(t)", "semilla:()=>" + _j.dumps(SEM) + ",copiar(t)"))
        pg.goto(HTML); pg.wait_for_timeout(1500)
        pg.evaluate("cambiaTab('fichas')"); pg.wait_for_timeout(200)
        ok("B4 instalación limpia: «Todavía no hay fichas» (sin semilla)", "Todavía no hay fichas" in pg.inner_text("#lista") and pg.evaluate("db.cards.length") == 0, pg.inner_text("#lista")[:100])
        pg.screenshot(path=CAPT + "B4-sin-semilla-" + nom + ".png")
        br.close()
    # B5: Pegar del portapapeles en PC (navegador sin puente nativo)
    br, pg = pagina(p, 1280, nativo=False)
    pg.context.grant_permissions(["clipboard-read", "clipboard-write"])
    pg.evaluate("t=>navigator.clipboard.writeText(t)", "https://github.com/acme/uno" + chr(10) + "https://youtu.be/abcdefghijk")
    pg.click("#bPegar"); pg.wait_for_timeout(300)
    ok("B5 el botón rellena la caja con lo copiado (portapapeles del navegador)", "github.com/acme/uno" in pg.input_value("#txt"), pg.input_value("#txt"))
    br.close()
    br, pg = pagina(p, 1280, nativo=False)   # sin permiso del navegador -> lo lee el servidor local
    pg.evaluate("window.fetch=u=>Promise.resolve({json:()=>Promise.resolve({texto:'https://github.com/acme/dos'})})")  # el servidor local simulado
    pg.evaluate("SRV=true"); pg.click("#bPegar"); pg.wait_for_timeout(500)
    ok("B5 si el navegador no deja, lo lee el servidor (/api/pegar)", "github.com/acme/dos" in pg.input_value("#txt"), pg.input_value("#txt"))
    pg.fill("#txt", ""); pg.evaluate("SRV=false"); pg.click("#bPegar"); pg.wait_for_timeout(300)
    ok("B5 con el portapapeles vacío avisa en palabras normales", "nada copiado" in pg.inner_text("#aviso") or pg.input_value("#txt") != "")
    br.close()
fin()
