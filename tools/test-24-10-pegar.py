# 24/10/2026: pegar enlaces en cualquier pantalla (fuera de campos) -> a la cola; dentro de un campo se pega normal.
import sys; sys.path.insert(0, "C:/Users/PC/DeskBox/Apps/CODE/IG Info extractor Code/ig-vault-apk/tools")
import arnes
from arnes import *

PEGA = """([t,sel])=>{const el=sel?document.querySelector(sel):document.body;const dt=new DataTransfer();dt.setData('text/plain',t);const ev=new ClipboardEvent('paste',{clipboardData:dt,bubbles:true,cancelable:true});el.dispatchEvent(ev);return ev.defaultPrevented}"""
with sync_playwright() as p:
    br, pg = pagina(p, 390)
    pg.evaluate("correr=()=>{};")
    for tab in ["pegar", "inicio"]:
        pg.evaluate("db.cards=[]; $('#txt').value=''")
        try: pg.evaluate("t=>cambiaTab(t)", tab)
        except Exception: pass
        prev = pg.evaluate(PEGA, ["mira https://www.instagram.com/reel/AAAAAAAAAAA/ y https://www.instagram.com/reel/BBBBBBBBBBB/", None])
        r = pg.evaluate("db.cards.map(c=>c.url)")
        ok(f"pegar 2 enlaces desde la pantalla «{tab}» -> 2 fichas en cola", prev and len(r) == 2, r)
    pg.evaluate("db.cards=[]; $('#txt').value=''")
    prev = pg.evaluate(PEGA, ["texto sin enlaces", None])
    ok("texto sin enlaces: no se toca nada", not prev and pg.evaluate("db.cards.length") == 0)
    prev = pg.evaluate(PEGA, ["https://www.instagram.com/reel/CCCCCCCCCCC/", "#txt"])
    ok("pegar dentro del cuadro de texto: pegado normal (no se crea ficha por su cuenta)", not prev and pg.evaluate("db.cards.length") == 0)
    pg.evaluate("db.cards=[]; $('#txt').value=''")
    prev = pg.evaluate(PEGA, ["https://www.instagram.com/reel/AAAAAAAAAAA/", None])
    n1 = pg.evaluate("db.cards.length")
    prev = pg.evaluate(PEGA, ["https://www.instagram.com/reel/AAAAAAAAAAA/", None])
    ok("el mismo enlace dos veces: no se duplica", n1 == 1 and pg.evaluate("db.cards.length") == 1)
    br.close()
fin()
