# Tanda Z1 (18/10/2026): arreglos del repaso final. Movil 390 + PC 1280.
import sys; sys.path.insert(0, "C:/Users/PC/DeskBox/Apps/CODE/IG Info extractor Code/ig-vault-apk/tools")
from arnes import *
import os
CAP = BASE + "capturas/tanda-Z1/"; os.makedirs(CAP, exist_ok=True)
FALL = """db.cards=[
 {id:'f1',url:'https://www.instagram.com/reel/CxYzAbQ/',tipo:'Instagram',estado:'revisar',categoria:'Para revisar',titulo:'https://www.instagram.com/reel/CxYzAbQ/',resumen:'',motivo:'No se pudo leer el texto de este post. Prueba Reintentar o pega el texto.',repos:[],tags:[]},
 {id:'o1',url:'https://github.com/a/b',tipo:'GitHub',estado:'ok',categoria:'Programas y apps',titulo:'Herramienta 0 de ejemplo muy larga',resumen:'Sirve para algo util en terminal.',repos:[],tags:[]}];guardar();pintar()"""
with sync_playwright() as p:
    for ancho, nom in ((390, "movil"), (1280, "pc")):
        print("== " + nom)
        br, pg = pagina(p, ancho)
        # 6 Pegar vacio
        pg.click("[data-p='pegar'], nav button:has-text('Pegar')") if pg.locator("nav button:has-text('Pegar')").count() else None
        ok("6 Pegar vacio: sin 'Aun no hay links' ni nota de lote", not pg.locator("#detect").is_visible() and not pg.locator("#notaLote").is_visible())
        ok("5 aviso sin IA visible en Pegar", pg.locator("#p-pegar .avIA").is_visible())
        pg.screenshot(path=CAP + "pegar-" + nom + ".png")
        # 8 + 6 cola trabajando
        pg.evaluate("window.__h=http; http=()=>new Promise(()=>{});0")
        CAPS.update({"A1": "Mira foo-cli herramienta", "A2": "otro"})
        pg.fill("#txt", "https://www.instagram.com/p/A1/\nhttps://www.instagram.com/p/A2/"); pg.click("#bOrdenar"); pg.wait_for_timeout(500)
        vis = lambda s: pg.locator(s).first.is_visible()
        ok("8 Reiniciar y Quitar visibles en bloque activo", vis("#bloques [data-rb]") and vis("#bloques [data-bq]"))
        ok("6 con cola aparece la nota de lote", pg.locator("#notaLote").is_visible())
        pg.screenshot(path=CAP + "cola-" + nom + ".png")
        pg.evaluate("window.__tc=1;http=window.__h;0")
        pg.evaluate("db.cards=[];db.bn=0;guardar()")
        pg.evaluate(FALL); pg.evaluate("tab&&0") if False else None
        pg.click("nav button:has-text('Fichas')") if pg.locator("nav button:has-text('Fichas')").count() else pg.evaluate("document.querySelector('[data-t=fichas],[data-tab=fichas]').click()")
        pg.evaluate("document.querySelectorAll('details.cat,details').forEach(d=>d.open=true)")
        pg.evaluate("db.filtro='revisar'") if False else None
        pg.wait_for_timeout(300)
        ok("5 aviso sin IA en Fichas discreto (12px)", pg.evaluate("(()=>{const e=document.querySelector('#p-fichas .avIA');return getComputedStyle(e).display!=='none'&&parseFloat(getComputedStyle(e).fontSize)<=12.5})()"))
        if ancho == 1280:
            ok("7 PC: panel vacio sin tarjeta", pg.evaluate("getComputedStyle(document.querySelector('#det')).backgroundColor")=="rgba(0, 0, 0, 0)", pg.evaluate("getComputedStyle(document.querySelector('#det')).backgroundColor"))
        pg.screenshot(path=CAP + "fichas-vacio-" + nom + ".png")
        # 1/3/4 fila fallida
        r = pg.evaluate("""(()=>{const w=document.querySelector('.rw[data-id=f1]');if(!w)return null;const q=s=>w.querySelector(s),b=x=>x?x.getBoundingClientRect():null;
          const rt=b(q('.rt')),rs=b(q('.rs')),re=b(q('[data-a=reint]')),ab=b(q('.racc a')),W=innerWidth;
          return {rt:rt.width,rs:rs.width,reintR:re.right,abR:ab.right,W,hre:re.height,hab:ab.height,txt:q('.rs').textContent,tit:q('.rt').textContent,top:re.top>rt.bottom}})()""")
        ok("1 fila fallida: titulo y motivo visibles (ancho>60)", r and r["rt"] > 60 and r["rs"] > 60, r)
        ok("1 Reintentar y Abrir dentro de pantalla y en 2a linea", r and r["reintR"] <= r["W"] and r["abR"] <= r["W"] and r["top"], r)
        ok("4 Reintentar/Abrir en Instagram >=44px", r and r["hre"] >= 43.9 and r["hab"] >= 43.9, r)
        pg.screenshot(path=CAP + "fila-fallida-" + nom + ".png", full_page=True)
        pg.evaluate("document.querySelector('.rw[data-id=f1] .rb').click()"); pg.wait_for_timeout(400)
        d = pg.evaluate("""(()=>{const c=document.querySelector('#detC');const h=c.querySelector('h2').textContent;const r=c.querySelector('[data-a=reint]');const lk=[...c.querySelectorAll('.lk')].map(e=>e.getBoundingClientRect().height);
          return {h,nota:c.querySelector('.nota').textContent,reint:r?r.getBoundingClientRect().height:0,lk,reintTop:r.getBoundingClientRect().top,h2b:c.querySelector('h2').getBoundingClientRect().bottom}})()""")
        ok("2 ficha fallida: titulo 'No se pudo leer' + motivo + Reintentar arriba", d["h"] == "No se pudo leer" and "Prueba" in d["nota"] and d["reint"] >= 44, d)
        ok("4 enlaces de la ficha fallida >=44", all(x >= 43.9 for x in d["lk"]) and d["lk"], d)
        pg.screenshot(path=CAP + "ficha-fallida-" + nom + ".png")
        pg.click("#detC [data-a=reint]"); pg.wait_for_timeout(300)
        ok("2 Reintentar de la ficha reencola", pg.evaluate("db.bn")>0)
        # 3 titulo de lista no cortado
        if ancho == 390:
            pg.evaluate("document.querySelector('.rw[data-id=o1]')&&0")
            t = pg.evaluate("(()=>{const e=document.querySelector('.rw[data-id=o1] .rt');return e?{w:e.getBoundingClientRect().height,lh:parseFloat(getComputedStyle(e).lineHeight),cortado:e.scrollHeight>e.clientHeight+1}:null})()")
            ok("3 (D7) titulo de lista hasta 2 lineas y sin cortar en movil", t and t["w"] <= t["lh"] * 2 + 1 and not t["cortado"], t)
        ok("sin desbordamiento horizontal", pg.evaluate("document.documentElement.scrollWidth<=innerWidth+1"))
        br.close()
fin()
