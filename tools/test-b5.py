# B5 (1/11): fecha de publicacion (campo publicada o shortcode de Instagram) en tarjeta, ficha y orden; «Sin fecha» solo sin publicada ni añadida
import sys
sys.path.insert(0, "C:/Users/PC/DeskBox/Apps/CODE/IG Info extractor Code/ig-vault-apk/tools")
from arnes import *
with sync_playwright() as p:
    br, pg = pagina(p, 1280)
    pg.evaluate("""()=>{const b={estado:'ok',categoria:'Programas y apps',resumen:'r',tags:[],repos:[],proyectos:[],tipo:'Instagram',fuente:''};
     db.cards=[{...b,id:'a1',titulo:'Con campo',url:'https://www.instagram.com/p/Degb7RRgUeV/',publicada:Date.UTC(2026,5,1,12),añadida:Date.now()},
               {...b,id:'a2',titulo:'Solo shortcode',url:'https://www.instagram.com/p/DehNrb5xHQf/',añadida:Date.now()-1000},
               {...b,id:'a3',titulo:'Web con alta',url:'https://example.com/x',tipo:'Web',añadida:Date.now()},
               {...b,id:'a4',titulo:'Web sin nada',url:'https://example.com/y',tipo:'Web'}];guardar();pintar();}""")
    e = pg.evaluate("db.cards.map(etqAñadida)")
    ok("publicada del campo", e[0].startswith("Publicado") and "jun" in e[0].lower(), e)
    ok("publicada del shortcode", e[1].startswith("Publicado") and "oct" in e[1].lower(), e)
    ok("web con alta: Añadido", e[2].startswith("Añadido"), e)
    ok("sin nada: Sin fecha", e[3] == "Sin fecha", e)
    ok("filtro Sin fecha solo la ultima", pg.evaluate("db.cards.filter(c=>FECHAS.find(f=>f[0]==='sin')[2](añadida(c)||publicada(c))).map(c=>c.id)") == ["a4"])
    ok("pubIG rango y no-IG", pg.evaluate("pubIG('https://example.com/p/abc')") == 0 and 1.7e12 < pg.evaluate("pubIG('https://www.instagram.com/p/DehNrb5xHQf/')") < 1.8e12)
    ok("orden recientes por publicada", pg.evaluate("[...db.cards].filter(c=>publicada(c)).sort((a,b)=>fechaVer(b)-fechaVer(a)).map(c=>c.id)") == ["a2", "a1"])
    pg.evaluate("cambiaTab('explorar')"); pg.wait_for_timeout(800)
    t = pg.inner_text("body"); ok("Explorar muestra Publicado", "Publicado" in t)
    pg.screenshot(path=BASE + "capturas/b5-publicada.png")
    fin()
