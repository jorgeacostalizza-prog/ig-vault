# Tanda F1 (18/10/2026): 1 sola peticion a /embed/captioned/ por post; fichas identicas a index.antes-F1.html. Movil 390 + PC 1280.
import sys, os, json; sys.path.insert(0, "C:/Users/PC/DeskBox/Apps/CODE/IG Info extractor Code/ig-vault-apk/tools")
import arnes
from arnes import *
VIEJO = "file:///" + BASE + "BACKUPS/index.antes-F1.html"; NUEVO = HTML
CAPS.clear(); CAPS.update({"F1": "Mira foo-cli, una herramienta de terminal para automatizar tareas repetitivas de la linea de comandos uno", "F2": "Otro post de bar-tool para gestionar proyectos desde la terminal con comandos sencillos y rapidos"})
EMB = {"F1": '<img class="EmbeddedMediaImage" src="https://img.test/e1.jpg?a=1&amp;b=2"><img class="EmbeddedMediaImage" src="https://img.test/e2.jpg">{"video_url":"https:\\/\\/v.test\\/a.mp4?x=1\\u0026y=2"}',
       "F2": '<div class="Caption"></div>'}  # F2: embed sin imagenes -> cae a og del post
orig = arnes.http
def http2(m, url, hd, body):
    if "/embed/captioned/" in url:
        LOG.append(url); c = url.split("/p/")[1].split("/")[0]
        return {"status": 200, "url": url, "body": EMB[c]} if c in EMB else {"status": 404, "url": url, "body": ""}
    return orig(m, url, hd, body)
arnes.http = http2
def corre(pg, cod):
    del LOG[:]
    r = pg.evaluate("""async(c)=>{const k={id:'z'+c,url:'https://www.instagram.com/p/'+c+'/',tipo:'Instagram',estado:'pendiente',bloque:1,grupo:'AI',titulo:'',resumen:'',categoria:'',repos:[],tags:[],fuente:'',motivo:''};
      db.cards.push(k);await analizar(k);return {k:{t:k.titulo,r:k.resumen,e:k.estado,i:k.imgs,v:(k.vio||{}).video,f:k.fuente}}}""", cod)
    return r, sum("/embed/captioned/" in u for u in LOG)
with sync_playwright() as p:
    for ancho, nom in ((390, "movil"), (1280, "pc")):
        print("== " + nom); sal = {}
        for et, h in (("viejo", VIEJO), ("nuevo", NUEVO)):
            arnes.HTML = h; globals()["HTML"] = h
            br, pg = arnes.pagina(p, ancho); pg.on("pageerror", lambda e: None)
            IA["modo"] = "ok"; pg.evaluate('db.cfg={nvidia:"nvapi-x"}')
            sal[et] = {c: corre(pg, c) for c in ("F1", "F2", "F3")}; br.close()
        for c in ("F1", "F2", "F3"):
            ok("%s: nuevo pide embed 1 vez (viejo %d)" % (c, sal["viejo"][c][1]), sal["nuevo"][c][1] <= 1 and (c != "F1" or sal["nuevo"][c][1] == 1), sal["nuevo"][c][1])
            ok("%s: ficha y lectura identicas" % c, sal["viejo"][c][0] == sal["nuevo"][c][0], (sal["viejo"][c][0], sal["nuevo"][c][0]))
        ok("F1 trae imagenes y video", len(sal["nuevo"]["F1"][0]["k"]["i"] or []) == 2 and sal["nuevo"]["F1"][0]["k"]["v"] is True, sal["nuevo"]["F1"][0]["k"])
fin()
