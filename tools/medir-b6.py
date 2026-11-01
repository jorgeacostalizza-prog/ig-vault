# B6 (1/11): mide tiempos reales por funcion (window.TLOG) con 3 posts publicos. Servidor propio 8807, datos temporales vacios, navegador headless sin sesion de Finn.
import os, sys, subprocess, tempfile, time, json, urllib.request
from playwright.sync_api import sync_playwright
RAIZ = "C:/Users/PC/DeskBox/Apps/CODE/IG Info extractor Code/"
OUT = sys.argv[1]
URLS = ["https://www.instagram.com/p/" + x + "/" for x in sys.argv[2].split(",")]
def w(t):
    with open(OUT, "a", encoding="utf-8") as f: f.write(t + "\n")
tmp = tempfile.mkdtemp(prefix="igx-b6-")
env = dict(os.environ, IGX_PORT="8807", IGX_DATOS=tmp, IGX_PAGES="http://127.0.0.1:9/", IGX_INACTIVIDAD="1800")
pr = subprocess.Popen([sys.executable, "-X", "utf8", "-I", RAIZ + "pc/servidor.py"], env=env, cwd=tmp, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=0x08000000)
try:
    for _ in range(60):
        try: urllib.request.urlopen("http://127.0.0.1:8807/api/ping", timeout=1).read(); break
        except Exception: time.sleep(0.5)
    with sync_playwright() as p:
        br = p.chromium.launch(); pg = br.new_page(viewport={"width": 1280, "height": 900})
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto("http://127.0.0.1:8807/"); pg.wait_for_timeout(1500)
        pg.evaluate("db.cards=[];db.bn=0;guardar();pintar();cambiaTab('pegar')")
        res = []
        for u in URLS:
            pg.evaluate("window.TLOG=[]"); t0 = time.time()
            pg.fill("#txt", u); pg.click("#bOrdenar")
            while time.time() - t0 < 240:
                st = pg.evaluate("(u)=>{const c=db.cards.find(x=>x.url===u);return c?c.estado:'-'}", u)
                if st not in ("pendiente", "-"): break
                time.sleep(1)
            dt = time.time() - t0
            c = pg.evaluate("(u)=>{const c=db.cards.find(x=>x.url===u);return c?{estado:c.estado,voz:c.voz,imgs:(c.imgs||[]).length,links:(c.links||[]).length,inf:!!(c.explicacion||c.puntos),tit:c.titulo}:null}", u)
            tl = pg.evaluate("window.TLOG")
            w(json.dumps({"url": u[-12:], "total_s": round(dt, 1), "tiempos_ms": tl, "ficha": c}, ensure_ascii=False))
            pg.wait_for_timeout(2500)
        fotos = len(os.listdir(os.path.join(tmp, "fotos"))) if os.path.isdir(os.path.join(tmp, "fotos")) else 0
        w("fotos_guardadas_en_disco=%d errores_js=%s" % (fotos, errs[:3])); br.close()
finally:
    pr.kill(); w("FIN")
