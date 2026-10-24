# 23/10/2026: añadir imágenes/capturas (botón, pegar, arrastrar, __imagen), aviso, cola, lectura simulada, miniatura local.
import sys; sys.path.insert(0, "C:/Users/PC/DeskBox/Apps/CODE/IG Info extractor Code/ig-vault-apk/tools")
import arnes, json, base64, os
from arnes import *

VIS = {"texto": ""}; VIS_LOG = []
def mi_http(m, url, hd, body):
    if "integrate.api.nvidia.com" in url:
        pr = json.loads(body)["messages"][0]["content"]
        if isinstance(pr, list):
            VIS_LOG.append(pr[1]["image_url"]["url"][:30])
            t = VIS["texto"]() if callable(VIS["texto"]) else VIS["texto"]
            return {"status": 200, "body": json.dumps({"choices": [{"message": {"content": t}}]})}
    return arnes.http_orig(m, url, hd, body)
arnes.http_orig = arnes.http; arnes.http = mi_http

PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")
PIX = os.path.join(os.environ.get("TEMP", "."), "pix23.png")
open(PIX, "wb").write(PNG)
os.makedirs(BASE + "capturas/imagenes-23-10", exist_ok=True)
MKFILE = """(w,h)=>{const c=document.createElement('canvas');c.width=w;c.height=h;const x=c.getContext('2d');x.fillStyle='#456';x.fillRect(0,0,w,h);return new Promise(r=>c.toBlob(b=>r(new File([b],'cap.png',{type:'image/png'})),'image/png'))}"""

def lanza(pg):  # arranca añadirImagenes sin esperar (espera el clic en Enviar)
    pg.evaluate("async()=>{const mk=%s; window.__fin=false; const f=await mk(2000,1000); window.__p=añadirImagenes([f]).then(()=>window.__fin=true)}" % MKFILE)
def envia(pg):
    pg.wait_for_selector("#dlg[open]"); pg.click("#dSi")
def espera(pg):
    pg.wait_for_function("window.__fin===true", timeout=30000)

with sync_playwright() as p:
    br, pg = pagina(p, 390)
    pg.evaluate("db.cfg={nvidia:'k'};correr=()=>{};")
    pg.evaluate("window.__av=[];new MutationObserver(()=>__av.push(document.querySelector('#aviso').textContent)).observe(document.querySelector('#aviso'),{childList:true,characterData:true,subtree:true})")
    ok("botón «Añadir imagen» junto al de pegar, con input de imágenes", pg.evaluate("document.querySelector('#bImagen').textContent==='Añadir imagen'&&document.querySelector('#bPegar').nextElementSibling.id==='bImagen'&&document.querySelector('#fImagen').accept==='image/*'&&document.querySelector('#fImagen').multiple"))

    # 1) captura de WhatsApp con 3 reels -> una ficha por enlace
    VIS["texto"] = "Cuenta: @amigo\nMira esto https://www.instagram.com/reel/AAAAAAAAAAA/?igsh=x y https://www.instagram.com/reel/BBBBBBBBBBB/ también https://www.instagram.com/p/CCCCCCCCCCC/\nImagen: chat de WhatsApp con tres enlaces"
    lanza(pg); envia(pg); espera(pg)
    r = pg.evaluate("db.cards.map(c=>({u:c.url,t:c.tipo,e:c.estado}))")
    ok("3 enlaces del texto leído -> 3 fichas Instagram pendientes (flujo normal)", len(r) == 3 and all(c["t"] == "Instagram" and c["e"] == "pendiente" for c in r), r)
    ok("la imagen se envió reducida (data:image/jpeg) al modelo", len(VIS_LOG) == 1 and VIS_LOG[0].startswith("data:image/jpeg"), VIS_LOG)

    # 2) aviso visible antes de enviar + Cancelar no envía nada
    pg.evaluate("db.cards=[]"); VIS_LOG.clear()
    lanza(pg); pg.wait_for_selector("#dlg[open]")
    txt = pg.inner_text("#dlg")
    ok("aviso «La imagen se envía a un modelo gratis en línea; no subas capturas privadas.» con Cancelar y Enviar", "La imagen se envía a un modelo gratis en línea; no subas capturas privadas." in txt and "Cancelar" in txt and "Enviar" in txt, txt)
    pg.screenshot(path=BASE + "capturas/imagenes-23-10/aviso-movil-390.png")
    pg.click("#dNo"); espera(pg)
    ok("Cancelar: no se llama al modelo ni se crean fichas", len(VIS_LOG) == 0 and pg.evaluate("db.cards.length") == 0 and "Cancelado" in pg.inner_text("#aviso"))

    # 3) captura sin enlaces -> ficha Foto con texto, miniatura <=1200 guardada en local
    VIS["texto"] = "Cuenta: @dev\nfunction hola() { return 42 }  // código de ejemplo para sumar\nImagen: captura de un fragmento de código JavaScript"
    lanza(pg); envia(pg); espera(pg)
    c = pg.evaluate("db.cards[0]")
    ok("sin enlaces: 1 ficha tipo Foto con el texto leído, local", len(pg.evaluate("db.cards")) == 1 and c["tipo"] == "Foto" and "function hola" in c["textoImg"] and c["imgLocal"], c)
    m = pg.evaluate("""async()=>{const v=await MINI.get(db.cards[0].id);if(!v||!v[0])return null;const im=new Image();im.src=v[0].d;await im.decode();return {w:im.naturalWidth,h:im.naturalHeight,jpg:v[0].d.startsWith('data:image/jpeg'),n:db.cards[0].minis}}""")
    ok("miniatura guardada en el aparato: JPEG, lado máx 1200, c.minis=1", m and m["jpg"] and max(m["w"], m["h"]) == 1200 and m["n"] == 1, m)

    # 4) la ficha se procesa con el flujo normal SIN volver a llamar a la visión
    VIS_LOG.clear()
    r = pg.evaluate("""async()=>{const c=db.cards[0];await analizar(c);return {e:c.estado,t:c.titulo,m:c.motivo}}""")
    ok("analizar usa el texto ya leído (no repite la visión)", len(VIS_LOG) == 0 and r["e"] in ("ok", "revisar"), r)

    # 5) cola de varias imágenes con avisos de paso
    pg.evaluate("db.cards=[];window.__av=[]"); VIS_LOG.clear()
    VIS["texto"] = lambda: "Texto largo de una captura de ejemplo sobre una herramienta %d\nImagen: captura" % len(VIS_LOG)
    pg.evaluate("""async()=>{const mk=%s; window.__fin=false; const fs=[await mk(800,600),await mk(800,600),await mk(800,600)]; window.__p=añadirImagenes(fs).then(()=>window.__fin=true)}""" % MKFILE)
    envia(pg); espera(pg)
    av = pg.evaluate("__av")
    ok("cola: avisos «Leyendo imagen 1/3…», «2/3…», «3/3…»", all(any(f"Leyendo imagen {k}/3…" in a for a in av) for k in (1, 2, 3)), av)
    ok("cola: 3 imágenes -> 3 llamadas y 3 fichas Foto", len(VIS_LOG) == 3 and pg.evaluate("db.cards.filter(c=>c.tipo==='Foto').length") == 3)

    # 6) no se entiende nada -> se dice claro, sin fichas
    pg.evaluate("db.cards=[];window.__av=[]"); VIS["texto"] = "Imagen: "
    lanza(pg); envia(pg); espera(pg)
    ok("imagen ilegible: sin fichas inventadas y aviso claro", pg.evaluate("db.cards.length") == 0 and "No entendí 1 imagen" in pg.inner_text("#aviso"), pg.inner_text("#aviso"))

    # 7) sin clave de IA
    pg.evaluate("db.cfg={}"); lanza(pg); espera(pg)
    ok("sin clave de IA: avisa y no abre el envío", "Sin IA" in pg.inner_text("#aviso") and not pg.evaluate("document.querySelector('#dlg').open"))
    pg.evaluate("db.cfg={nvidia:'k'}")

    # 8) entradas: selector de archivos, Ctrl+V, arrastrar y __imagen
    VIS["texto"] = "Texto suficiente de una captura de ejemplo\nImagen: x"; VIS_LOG.clear(); pg.evaluate("db.cards=[]")
    pg.set_input_files("#fImagen", PIX); pg.wait_for_selector("#dlg[open]")
    ok("selector de archivos (galería/foto) abre el aviso", True); pg.click("#dNo")
    pg.evaluate("""()=>{const dt=new DataTransfer();dt.items.add(new File([new Uint8Array([1])],'a.png',{type:'image/png'}));document.dispatchEvent(new ClipboardEvent('paste',{clipboardData:dt,bubbles:true,cancelable:true}))}""")
    ok("Ctrl+V con imagen abre el aviso", pg.evaluate("document.querySelector('#dlg').open") and "imagen" in pg.inner_text("#dT")); pg.click("#dNo")
    pg.evaluate("""()=>{const dt=new DataTransfer();dt.items.add(new File([new Uint8Array([1])],'a.png',{type:'image/png'}));document.dispatchEvent(new DragEvent('drop',{dataTransfer:dt,bubbles:true,cancelable:true}))}""")
    ok("arrastrar y soltar abre el aviso", pg.evaluate("document.querySelector('#dlg').open")); pg.click("#dNo")
    pg.evaluate("void window.__imagen('data:image/png;base64,%s')" % base64.b64encode(PNG).decode())
    ok("window.__imagen (Compartir del móvil) abre el aviso", pg.evaluate("document.querySelector('#dlg').open")); pg.click("#dNo")
    br.close()
fin()
