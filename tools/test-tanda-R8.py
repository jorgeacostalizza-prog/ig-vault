# Tanda R8 (19/10/2026): «Sirve para…» con cita textual (fuente en otro idioma). Movil 390 + PC 1280.
import sys, os; sys.path.insert(0, "C:/Users/PC/DeskBox/Apps/CODE/IG Info extractor Code/ig-vault-apk/tools")
from arnes import *
CD = BASE + "capturas/tanda-R8/"; os.makedirs(CD, exist_ok=True)
CAPS.clear()
VOZ_EN = "Today I show you foo-cli, a terminal tool that automates repetitive tasks. Ballroom culture was a refuge and a place of civil rights organizing for many people."
VOZ_ES = "Hoy te enseño foo-cli, una herramienta de terminal para automatizar tareas repetitivas desde la linea de comandos, muy util para programadores"
def reel(pg, cod, extra, voz):
    IA["modo"] = "ok"; IA["extra"] = extra
    pg.evaluate("db.cfg={nvidia:'nvapi-x'}")
    return pg.evaluate("""async([c,voz])=>{
      leerIG=async()=>({texto:'Increible, guardalo para luego',video:'https://v.test/a.mp4',imgs:[]});
      leerVoz=async()=>voz; leerFrames=async()=>[]; leerImgs=async()=>'';
      const k={id:'z'+c,url:'https://www.instagram.com/reel/'+c+'/',tipo:'Instagram',estado:'pendiente',bloque:1,grupo:'AI',titulo:'',resumen:'',categoria:'',repos:[],tags:[],fuente:'',motivo:''};
      db.cards.push(k);await analizar(k);return {s:k.sirve,a:k.accion,d:k.sirveDe,e:k.estado}}""", [cod, voz])
ES = "Automatizar tareas repetitivas desde la terminal"
with sync_playwright() as p:
    for ancho, nom in ((390, "movil"), (1280, "pc")):
        print("== " + nom)
        br, pg = pagina(p, ancho)
        r = reel(pg, "A", {"sirve": ES, "accion": "Instalar", "sirve_cita": "a terminal tool that automates repetitive tasks", "sirve_fuente": "voz"}, VOZ_EN)
        ok("(a) voz EN + linea ES + cita real -> aceptada, origen voz", r["s"] == ES and r["a"] == "Instalar" and r["d"] == "voz", r)
        h = pg.evaluate("detalleHtml(db.cards.find(c=>c.id==='zA'))")
        ok("(a) etiqueta «según la voz del vídeo»", "según la voz del vídeo" in h, h[-300:])
        pg.screenshot(path=CD + "a-%s.png" % nom)
        r = reel(pg, "B", {"sirve": ES, "accion": "Instalar", "sirve_cita": "this tool installs with one command", "sirve_fuente": "voz"}, VOZ_EN)
        ok("(b) cita inventada -> vacio y Solo guardar", r["s"] == "" and r["a"] == "Solo guardar", r)
        r = reel(pg, "B2", {"sirve": ES, "accion": "Instalar", "sirve_cita": "a terminal tool that automates repetitive tasks", "sirve_fuente": "pie"}, VOZ_EN)
        ok("(b2) cita real pero fuente equivocada -> vacio", r["s"] == "" and r["a"] == "Solo guardar", r)
        r = reel(pg, "C", {"sirve": "Ahorrar horas programando guiones del sistema", "accion": "Instalar"}, VOZ_EN)
        ok("(c) sin cita, otro idioma -> vacio y Solo guardar", r["s"] == "" and r["a"] == "Solo guardar", r)
        r = reel(pg, "D", {"sirve": ES, "accion": "Instalar"}, VOZ_ES)
        ok("(d) fuente ES sin cita -> camino por palabras", r["s"] == ES and r["a"] == "Instalar" and r["d"] == "voz", r)
        pg.screenshot(path=CD + "d-%s.png" % nom)
        br.close()
fin()
