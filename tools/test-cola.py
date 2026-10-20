import sys, os; sys.path.insert(0, "C:/Users/PC/DeskBox/Apps/CODE/IG Info extractor Code/ig-vault-apk/tools")
from arnes import *
CD = BASE + "capturas/cola/"; os.makedirs(CD, exist_ok=True)
with sync_playwright() as p:
    for ancho, nom in ((390, "movil"), (1280, "pc")):
        br, pg = pagina(p, ancho)
        pg.evaluate("""()=>{sesionDesde=1;db.bn=1;db.cards=[1,2,3].map(i=>({id:'k'+i,url:'https://github.com/a/r'+i,tipo:'GitHub',estado:'pendiente',bloque:1,grupo:'AI',titulo:'https://github.com/a/r'+i,resumen:'',categoria:'Pendiente',repos:[],tags:[]}));guardar();corriendo=true;pausado=true;$('#prog').style.display='flex';$('#progS').textContent='Leyendo la página · github.com/a/r1';actual=db.cards[0];pintaBloques();}""")
        pg.wait_for_timeout(300)
        ok("barra de paso en una línea, sin tarjeta propia", pg.evaluate("getComputedStyle($('#prog')).borderTopWidth")=="0px" and pg.locator("#prog").is_visible())
        ok("sigue habiendo botón Pausar y tarjeta de bloque", pg.locator("#bParar").is_visible() and pg.locator("#bloques .blq").count()==1)
        pg.screenshot(path=CD + "cola-%s.png" % nom); br.close()
fin()
