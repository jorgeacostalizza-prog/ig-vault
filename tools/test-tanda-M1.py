# Tanda M1-M2 (19/10/2026): «Sirve para…» con voz/fotogramas + unión de repetidas por identidad real con Deshacer. Movil 390 + PC 1280.
import sys, os; sys.path.insert(0, "C:/Users/PC/DeskBox/Apps/CODE/IG Info extractor Code/ig-vault-apk/tools")
from arnes import *
CD = BASE + "capturas/tanda-M1/"; os.makedirs(CD, exist_ok=True)
CAPS.clear(); CAPS.update({k: "Increible, guardalo para luego " + k for k in ["M1", "M2", "M3", "M4"]})
VOZ = "Hoy te enseño foo-cli, una herramienta de terminal para automatizar tareas repetitivas desde la linea de comandos, muy util para programadores"
def reel(pg, cod, extra, voz="", frames=""):
    IA["modo"] = "ok"; IA["extra"] = extra
    pg.evaluate("db.cfg={nvidia:'nvapi-x'}")
    return pg.evaluate("""async([c,voz,fr])=>{
      leerIG=async()=>({texto:'Increible, guardalo para luego',video:'https://v.test/a.mp4',imgs:[]});
      leerVoz=async()=>voz; leerFrames=async()=>fr?['https://img.test/f.jpg']:[]; leerImgs=async()=>fr;
      const k={id:'z'+c,url:'https://www.instagram.com/reel/'+c+'/',tipo:'Instagram',estado:'pendiente',bloque:1,grupo:'AI',titulo:'',resumen:'',categoria:'',repos:[],tags:[],fuente:'',motivo:''};
      db.cards.push(k);await analizar(k);return {s:k.sirve,a:k.accion,d:k.sirveDe,e:k.estado,f:k.fuente}}""", [cod, voz, frames])
G = lambda i, t, u: "{id:'%s',url:'%s',tipo:'GitHub',estado:'ok',grupo:'AI',titulo:'%s',resumen:'Una herramienta',categoria:'Repositorios',repos:[],tags:[]}" % (i, u, t)
with sync_playwright() as p:
    for ancho, nom in ((390, "movil"), (1280, "pc")):
        print("== " + nom)
        br, pg = pagina(p, ancho)
        S = {"sirve": "Automatizar tareas repetitivas desde la terminal", "accion": "Instalar"}
        r = reel(pg, "M1", S, voz=VOZ)
        ok("voz respalda -> se muestra, origen voz", r["s"] == S["sirve"] and r["a"] == "Instalar" and r["d"] == "voz", r)
        r = reel(pg, "M2", S, voz="", frames="Terminal con foo-cli: herramienta para automatizar tareas repetitivas desde la linea de comandos")
        ok("fotogramas respaldan -> se muestra, origen imagenes", r["s"] == S["sirve"] and r["d"] == "imagenes", r)
        r = reel(pg, "M3", {"sirve": "Ganar dinero invirtiendo en criptomonedas rapidamente", "accion": "Instalar"}, voz=VOZ)
        ok("inventada sin respaldo -> vacia y Solo guardar", r["s"] == "" and r["a"] == "Solo guardar", r)
        h = pg.evaluate("detalleHtml(db.cards.find(c=>c.id==='zM1'))")
        ok("ficha muestra etiqueta «según la voz del vídeo»", "según la voz del vídeo" in h, h[-300:])
        pr = pg.evaluate("""async()=>{let p='';const o=http;window.__p='';return 1}""")
        # M2: mismo titulo, distinto repo -> NO se unen
        pg.evaluate("db.cards=[%s,%s];unirRepetidas()" % (G("a1", "Mismo nombre", "https://github.com/uno/app"), G("a2", "Mismo nombre", "https://github.com/dos/app")))
        ok("mismo titulo, distinto repo: NO se unen", pg.evaluate("db.cards.length") == 2)
        # mismo repo con otra forma de link -> se unen, Deshacer separa
        pg.evaluate("localStorage.removeItem('igv-deshacer-union');_undo=null;db.cards=[%s,%s];unirRepetidas()" % (G("b1", "Foo", "https://github.com/uno/app"), G("b2", "Otro titulo", "https://www.github.com/Uno/app/?utm_source=x")))
        ok("mismo repo: se unen", pg.evaluate("db.cards.length") == 1)
        t = pg.evaluate("document.getElementById('aviso').innerText"); vis = pg.evaluate("getComputedStyle(document.getElementById('aviso')).display")
        ok("aviso con Deshacer visible", "Unidas 1 repetidas" in t and "Deshacer" in t and vis == "block", t)
        pg.screenshot(path=CD + "aviso-%s.png" % nom)
        pg.wait_for_timeout(5500)
        ok("el aviso no desaparece solo a los 5 s", pg.evaluate("getComputedStyle(document.getElementById('aviso')).display") == "block")
        pg.evaluate("localStorage.getItem('igv-deshacer-union')") 
        ok("copia en localStorage", pg.evaluate("!!localStorage.getItem('igv-deshacer-union')"))
        # recarga: sigue disponible
        pg.reload(); pg.wait_for_timeout(700)
        t = pg.evaluate("document.getElementById('aviso').innerText")
        ok("tras recargar sigue el Deshacer", "Deshacer" in t, t)
        pg.click("#avDeshacer"); pg.wait_for_timeout(200)
        ids = pg.evaluate("db.cards.map(c=>c.id).sort().join(',')")
        ok("Deshacer separa las dos fichas originales", ids == "b1,b2", ids)
        ok("tras deshacer ya no hay copia", pg.evaluate("localStorage.getItem('igv-deshacer-union')") is None)
        # caducidad 10 min
        pg.evaluate("db.cards=[%s,%s];unirRepetidas();var s=JSON.parse(localStorage.getItem('igv-deshacer-union'));s.t-=700000;localStorage.setItem('igv-deshacer-union',JSON.stringify(s));_undo=null" % (G("c1", "X", "https://github.com/q/w"), G("c2", "X", "https://github.com/q/w")))
        ok("caducada (10 min): ya no hay deshacer", pg.evaluate("deshacerVivo()") is None)
        pg.screenshot(path=CD + "final-%s.png" % nom)
        br.close()
fin()
