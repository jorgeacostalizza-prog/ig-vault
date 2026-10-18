# Tanda H1 (18/10/2026): «Sirve para…» + accion sugerida. IA simulada buena / inventada / sin IA. Movil 390 + PC 1280.
import sys, os; sys.path.insert(0, "C:/Users/PC/DeskBox/Apps/CODE/IG Info extractor Code/ig-vault-apk/tools")
from arnes import *
CD = BASE + "capturas/tanda-H1/"; os.makedirs(CD, exist_ok=True)
CAPS.clear(); CAPS.update({k: "Mira foo-cli, una herramienta de terminal para automatizar tareas repetitivas de la linea de comandos " + k for k in ["H1", "H2", "H3", "H4"]})
def corre(pg, cod, extra, ia=True):
    IA["modo"] = "ok"; IA["extra"] = extra
    pg.evaluate("db.cfg=%s" % ('{nvidia:"nvapi-x"}' if ia else "{}"))
    return pg.evaluate("""async(c)=>{const k={id:'z'+c,url:'https://www.instagram.com/p/'+c+'/',tipo:'Instagram',estado:'pendiente',bloque:1,grupo:'AI',titulo:'',resumen:'',categoria:'',repos:[],tags:[],fuente:'',motivo:''};
      db.cards.push(k);await analizar(k);return {s:k.sirve,a:k.accion,e:k.estado}}""", cod)
with sync_playwright() as p:
    for ancho, nom in ((390, "movil"), (1280, "pc")):
        print("== " + nom)
        br, pg = pagina(p, ancho)
        r = corre(pg, "H1", {"sirve": "Automatizar tareas repetitivas desde la terminal", "accion": "Instalar"})
        ok("buena: se guarda", r["s"] == "Automatizar tareas repetitivas desde la terminal" and r["a"] == "Instalar", r)
        r = corre(pg, "H2", {"sirve": "Ganar dinero invirtiendo en criptomonedas rapidamente", "accion": "Instalar"})
        ok("inventada: se descarta", r["s"] == "" and r["a"] == "Solo guardar", r)
        r = corre(pg, "H3", {"sirve": "Automatizar tareas repetitivas desde la terminal", "accion": "Comprar"})
        ok("accion rara -> Solo guardar", r["a"] == "Solo guardar", r)
        r = corre(pg, "H4", {"sirve": "Automatizar tareas repetitivas desde la terminal", "accion": "Probar"}, ia=False)
        ok("sin IA: Solo guardar y sin linea", r["s"] == "" and r["a"] == "Solo guardar", r)
        # ficha vieja sin campos: no falla
        pg.evaluate("db.cards.push({id:'old',url:'https://x.test/1',tipo:'Web',estado:'ok',bloque:1,grupo:'AI',titulo:'Vieja',resumen:'Algo viejo',categoria:'Webs',repos:[],tags:[]});pintar()")
        pg.evaluate("cambiaTab('fichas')"); t = pg.evaluate('document.body.innerText')
        ok("fila muestra etiqueta Instalar y la linea", "Instalar" in t and "Automatizar tareas repetitivas" in t, t[:200])
        ok("ficha vieja sin etiqueta", pg.evaluate("filaHtml(db.cards.find(c=>c.id==='old'))").count('class="chip') == 0)
        pg.evaluate("tab_ficha=0;abrirDet&&0")  if False else None
        h = pg.evaluate("detalleHtml(db.cards.find(c=>c.id==='zH1'))")
        ok("ficha abierta con Sirve para + etiqueta", "Sirve para…" in h and ">Instalar<" in h)
        ok("ficha vieja abre sin fallar", "Vieja" in pg.evaluate("detalleHtml(db.cards.find(c=>c.id==='old'))"))
        # fusion conserva campos nuevos
        pg.evaluate("""db.cards=[{id:'m1',url:'https://a.test/1',tipo:'Web',estado:'ok',grupo:'AI',titulo:'Igual',resumen:'x'.repeat(200),categoria:'Webs'},
          {id:'m2',url:'https://a.test/2',tipo:'Web',estado:'ok',grupo:'AI',titulo:'Igual',resumen:'y',categoria:'Webs',sirve:'Probar cosas',accion:'Probar'}];unirRepetidas()""")
        m = pg.evaluate("db.cards.length+'|'+db.cards[0].sirve+'|'+db.cards[0].accion")
        ok("fusion conserva sirve/accion", m == "1|Probar cosas|Probar", m)
        pg.evaluate("db.cards=[];IA.x=0") if False else None
        corre(pg, "H1", {"sirve": "Automatizar tareas repetitivas desde la terminal", "accion": "Instalar"})
        pg.evaluate("cambiaTab('fichas')") if pg.evaluate("typeof cambiaTab")=="function" else None
        pg.wait_for_timeout(300); pg.screenshot(path=CD + "lista-%s.png" % nom)
        br.close()
fin()
