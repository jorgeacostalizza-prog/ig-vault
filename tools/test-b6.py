# B6 (1/11): foto caducada (403/abortada) -> respaldo bonito (portada de color con inicial) en tarjeta y ficha, sin hueco; guardaFotosLocal pide /api/foto
import sys
sys.path.insert(0, "C:/Users/PC/DeskBox/Apps/CODE/IG Info extractor Code/ig-vault-apk/tools")
from arnes import *
with sync_playwright() as p:
    br, pg = pagina(p, 1280)
    pg.evaluate("""()=>{const b={estado:'ok',categoria:'Programas y apps',resumen:'Resumen de prueba',tags:[],repos:[],proyectos:[],tipo:'Instagram',fuente:'',añadida:Date.now()};
     db.cards=[{...b,id:'f1',titulo:'Foto caducada',url:'https://www.instagram.com/p/Degb7RRgUeV/',imgs:['https://img.test/p/a1.jpg','https://img.test/p/a2.jpg']},
               {...b,id:'f2',titulo:'Sin fotos',url:'https://example.com/z',tipo:'Web'}];guardar();pintar();cambiaTab('inicio');}""")
    pg.wait_for_timeout(1500)
    pg.evaluate("cambiaTab('explorar')"); pg.wait_for_timeout(1200)
    ok("tarjeta: la portada de respaldo esta y se ve", pg.evaluate("(()=>{const g=document.querySelector('.gl[data-gid=f1]');const p=g&&g.querySelector('.port');return !!p&&p.getBoundingClientRect().height>20&&g.getBoundingClientRect().height>20})()"))
    ok("tarjeta: las fotos rotas se quitan (0 img)", pg.evaluate("document.querySelectorAll('.gl[data-gid=f1] img').length") == 0)
    ok("ficha: galeriaHtml con fotos lleva portada", pg.evaluate("galeriaHtml(db.cards[0],'det-gl')").count('class="port"') == 1)
    ok("ficha sin fotos: sigue oculta (sin hueco)", 'display:none' in pg.evaluate("galeriaHtml(db.cards[1],'det-gl')"))
    pg.evaluate("abrirFicha ? abrirFicha('f1') : 0") if pg.evaluate("typeof abrirFicha") == "function" else None
    pg.wait_for_timeout(800)
    g = pg.evaluate("(()=>{const g=document.querySelector('.det-gl[data-gid=f1]');if(!g)return null;const r=g.getBoundingClientRect();return {h:r.height,port:!!g.querySelector('.port')}})()")
    if g is not None: ok("ficha abierta: portada visible con altura", g["port"] and g["h"] > 100, g)
    pg.screenshot(path=BASE + "capturas/b6-foto-respaldo.png")
    # guardaFotosLocal pide /api/foto por cada foto (servidor simulado: SRV a mano)
    pg.evaluate("window.__pf=[];SRV=true;window.fetch=(u)=>{__pf.push(String(u));return Promise.resolve(new Response(new ArrayBuffer(4)))}")
    pg.evaluate("guardaFotosLocal(db.cards[0])"); pg.wait_for_timeout(500)
    pf = [x for x in pg.evaluate("__pf") if x.startswith("/api/foto")]; ok("al crear la ficha se pide /api/foto de cada foto", len(pf) == 2 and all(x.startswith("/api/foto?u=") for x in pf), pf)
    fin()
