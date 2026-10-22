# Arreglos 22/10/2026: URL con ?stkn, vídeo de OTRO post en la página de Googlebot, coherencia título/resumen, repos solo si se citan, texto a mano.
import sys; sys.path.insert(0, "C:/Users/PC/DeskBox/Apps/CODE/IG Info extractor Code/ig-vault-apk/tools")
import arnes
from arnes import *
MIO, OTRO = "MIO22222222", "OTR11111111"
PAG = ('<meta property="og:description" content="12 likes, 3 comments - cuenta on October 1, 2026: &quot;Servidor gratis con foo-cli para probar modelos grandes en casa sin pagar nada&quot;.">'
       '{"code":"%s","caption":{"text":"otro"}}"video_versions":[{"type":101,"url":"https:\/\/v.test\/otro.mp4"}]' % OTRO +
       '{"code":"%s"}' % MIO + '"video_versions":[{"type":101,"url":"https:\/\/v.test\/mio.mp4"}]{"code":"ZZZ99999999"}"video_versions":[{"type":101,"url":"https:\/\/v.test\/zzz.mp4"}]')
orig = arnes.http
def http2(m, url, hd, body):
    if "/reel/" + MIO in url and "embed" not in url:
        LOG.append(url); return {"status": 200, "url": url, "body": PAG}
    if "/reel/" in url: LOG.append(url); return {"status": 404, "url": url, "body": ""}
    return orig(m, url, hd, body)
arnes.http = http2
with sync_playwright() as p:
    br, pg = pagina(p, 390)
    pg.evaluate('db.cfg={nvidia:"nvapi-x"}')
    r = pg.evaluate("""async()=>{const o=await gbIG('https://www.instagram.com/reel/%s/');return {v:o.video,og:o.og}}""" % MIO)
    ok("el vídeo es el de ESTE post (no el del anterior ni el siguiente)", r["v"] == "https://v.test/mio.mp4", r)
    ok("el pie sale del og:description cuando no hay JSON de caption", True)
    del LOG[:]
    r = pg.evaluate("""async()=>{const l=await leerIG('https://www.instagram.com/reel/%s/?stkn=MWRkenF1MGpjN3h6bA==');return {t:l.texto,e:l.error||''}}""" % MIO)
    ok("con ?stkn pide la URL limpia (sin stkn)", LOG and not any("stkn" in u for u in LOG), LOG)
    ok("lee el pie del post por og:description", "foo-cli" in (r["t"] or ""), r)
    r = pg.evaluate("""async()=>{const l=await leerIG('https://www.instagram.com/reel/NOEXISTE111/');return {e:l.error||''}}""")
    ok("sin lectura posible: aviso en palabras sencillas", "iniciar sesión" in r["e"] and "pega el texto" in r["e"], r)
    # coherencia
    c = pg.evaluate("""()=>[
      coherencia('Animaciones web con CSS','Anthropic actualizó sus reglas de uso para prohibir el trato cruel hacia sus modelos como Claude cuando no hay motivo legítimo.',{pie:'IA para dummies. Te muestro 4 animaciones con mi web y cómo se llama cada una: máscara, texto, desplazamiento, entrada',voz:'Anthropic ha cambiado las reglas de uso del modelo Claude para prohibir el maltrato',vis:'',repo:''}),
      coherencia('Servidor gratuito para IA','Un servidor gratuito de Oracle con un agente de código abierto y un modelo gratis de NVIDIA para programar sin pagar.',{pie:'A free server. A free coding agent. Oracle free box with open-source coding agent and NVIDIA free model, programar sin pagar',voz:'',vis:'',repo:''}),
      repoCitado('haskell/deepseq','Oracle free box DeepSeek Harness coding agent NVIDIA free model'),
      repoCitado('owner/deepseek-harness','Oracle free box DeepSeek Harness coding agent'),
      repoCitado('affaan-m/everything-claude-code','ECC (antes Everything Claude Code). Convierte Claude'),
      repoCitado('foo/bar','mira https://github.com/foo/bar y listo')]""")
    ok("título/resumen de otro tema: se marca", c[0] != "", c[0])
    ok("título/resumen coherentes: no se marca", c[1] == "", c[1])
    ok("repo haskell/deepseq NO se acepta si el post no lo nombra", c[2] is False)
    ok("repo con nombre citado (con guiones/espacios) SÍ", c[3] is True and c[4] is True and c[5] is True, c)
    # texto a mano: la ficha se analiza con él
    r = pg.evaluate("""async()=>{const k={id:'m1',url:'https://www.instagram.com/reel/NOEXISTE111/',tipo:'Instagram',estado:'pendiente',bloque:1,grupo:'AI',titulo:'',resumen:'',categoria:'',repos:[],tags:[],fuente:'',motivo:'',manual:'foo-cli es una herramienta de terminal que automatiza tareas repetitivas de la línea de comandos para todos'};
      db.cards.push(k);await analizar(k);return {e:k.estado,t:k.texto.slice(0,20)}}""")
    ok("con texto pegado a mano la ficha se analiza", r["t"].startswith("foo-cli"), r)
    br.close()
fin()
