# Arnés común para las pruebas de la tanda A/B/G (18/10/2026): red e IA simuladas, navegador oculto.
import json, time, sys
from playwright.sync_api import sync_playwright
BASE = "C:/Users/PC/DeskBox/Apps/CODE/IG Info extractor Code/ig-vault-apk/"
HTML = "file:///" + BASE + "src/assets/index.html"
CAPT = BASE + "capturas/tanda-A/"
ERR, res = [], []
LOG = []          # peticiones simuladas
CAPS = {}         # código del post -> texto del pie
IA = {"modo": "ok", "resumen": "x"}   # ok | 429 | largo
DEMORA = {"s": 0.0}

def http(m, url, hd, body):
    LOG.append(url)
    time.sleep(DEMORA["s"])
    if "instagram.com/p/" in url and "embed" not in url:
        code = url.split("/p/")[1].split("/")[0]
        if code not in CAPS: return {"status": 404, "url": url, "body": ""}
        return {"status": 200, "url": url, "body": '<meta property="og:image" content="https://img.test/a.jpg">{"caption":{"text":' + json.dumps(CAPS[code]) + '},"code":"' + code + '"}'}
    if "youtube.com/oembed" in url or "youtu" in url and "oembed" in url:
        return {"status": 500, "body": ""}
    if "integrate.api.nvidia.com" in url:
        if IA["modo"] == "429": return {"status": 429, "body": ""}
        if IA["modo"] == "401": return {"status": 401, "body": ""}
        pr = json.loads(body)["messages"][0]["content"]
        if isinstance(pr, list): return {"status": 200, "body": json.dumps({"choices": [{"message": {"content": ""}}]})}
        if "Eres un extractor riguroso" in pr:
            r = ("foo-cli es una herramienta de terminal que sirve para automatizar tareas repetitivas desde la línea de comandos. " * 4) if IA["modo"] == "largo" else "foo-cli es una herramienta de terminal que automatiza tareas."
            out = {"titulo": "foo-cli", "resumen": r, "categoria": "Programas y apps", "relevancia": 4, "proyectos": [], "tags": ["cli"], "web": None}
            out.update(IA.get("extra", {}))
        else:
            out = {"explicacion": ("Esto es muy largo. " * 30 if IA["modo"] == "largo" else "") + "foo-cli es una herramienta de terminal que se instala con npx. Sirve para automatizar tareas desde la línea de comandos y el vídeo muestra la instalación paso a paso con el comando exacto.", "puntos": ["Instalar"], "skills": [], "como": [], "limites": ""}
        return {"status": 200, "body": json.dumps({"choices": [{"message": {"content": json.dumps(out)}}]})}
    return {"status": 404, "url": url, "body": ""}

INIT = """(()=>{window.Native={claves:()=>'{}',copiar(t){window.__copiado=t},compartir(){},abrir(){},pegado:()=>window.__pegado||"",
 http:(id,...a)=>window.__py('http',a).then(r=>window.__r(id,JSON.stringify(r))),
 frames:(id)=>window.__r(id,'{"status":0}'),pagina:(id)=>window.__r(id,'{}'),voz:(id)=>window.__r(id,'{"status":0,"body":""}'),foto:(id)=>window.__r(id,'{"status":0}')}})()"""

def ok(t, v, extra=""):
    print(("  OK   " if v else "  FALLA") + " | " + t + (" | " + str(extra)[:300] if (extra and not v) else "")); res.append(bool(v)); return v

def pagina(pw, ancho, alto=900, nativo=True):
    br = pw.chromium.launch(); ctx = br.new_context(viewport={"width": ancho, "height": alto}); pg = ctx.new_page()
    pg.on("pageerror", lambda e: ERR.append(str(e)))
    pg.on("console", lambda m: ERR.append(m.text) if m.type == "error" and "Failed to load resource" not in m.text and "api/ping" not in m.text else None)
    pg.expose_function("__py", lambda n, a: http(*a))
    if nativo: pg.add_init_script(INIT)
    pg.route("https://img.test/**", lambda r: r.abort())
    pg.goto(HTML); pg.wait_for_timeout(600)
    pg.evaluate("db.cards=[];db.bn=0;db.cfg={};guardar();pintar()")
    return br, pg

def fin():
    print("\nERRORES JS:", ERR if ERR else "ninguno"); print("RESULTADO: %d/%d OK" % (sum(res), len(res)))
    sys.exit(0 if all(res) and not ERR else 1)
