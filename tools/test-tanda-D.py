# Tanda D1-D3 (18/10/2026): categoria gorda subdividida y plegada, filtros sin corte, contraste. Movil 390 + PC 1280, claro y oscuro.
import sys, os; sys.path.insert(0, "C:/Users/PC/DeskBox/Apps/CODE/IG Info extractor Code/ig-vault-apk/tools")
from arnes import *
CD = BASE + "capturas/tanda-D/"; os.makedirs(CD, exist_ok=True)
TAGS = [["agentes"], ["skill"], ["llm"], ["prompt"], ["herramienta"], []]
with sync_playwright() as p:
    for ancho, nom in ((390, "movil"), (1280, "pc")):
        for esq in ("light", "dark"):
            print("== %s %s" % (nom, esq))
            br, pg = pagina(p, ancho); pg.emulate_media(color_scheme=esq)
            pg.evaluate("""(T)=>{db.cards=[];for(let i=0;i<30;i++)db.cards.push({id:'x'+i,url:'https://www.instagram.com/p/X'+i+'/',tipo:'Instagram',estado:'ok',grupo:'AI',titulo:'Ficha '+i,resumen:'r',categoria:'Inteligencia artificial',repos:[],tags:T[i%6],fuente:'deducido',motivo:''});
              db.cards[0].subtipo='Modelos';
              for(let i=0;i<3;i++)db.cards.push({id:'o'+i,url:'https://x.test/'+i,tipo:'Web',estado:'ok',grupo:'AI',titulo:'Web '+i,resumen:'r',categoria:'Webs',repos:[],tags:[],fuente:'deducido',motivo:''});
              db.cards.push({id:'r1',url:'https://www.instagram.com/p/R/',tipo:'Instagram',estado:'revisar',grupo:'AI',titulo:'https://www.instagram.com/p/R/',resumen:'',categoria:'Para revisar',repos:[],tags:[],fuente:'',motivo:'Instagram no dejo leer'});
              cambiaTab('fichas');pintar()}""", TAGS)
            pg.wait_for_timeout(300)
            ok("D1 la categoria gorda sale plegada", pg.evaluate("!document.querySelector('#lista details[data-k$=\"Inteligencia artificial\"]').open"))
            ok("D1 lista inicial corta", pg.evaluate("document.querySelector('#lista').scrollHeight") < 1200, pg.evaluate("document.querySelector('#lista').scrollHeight"))
            pg.evaluate("document.querySelector('#lista details[data-k$=\"Inteligencia artificial\"]').open=true")
            subs = pg.evaluate("[...document.querySelectorAll('#lista details.sub')].map(d=>d.dataset.k.split('/').pop()+':'+d.querySelector('b').textContent)")
            ok("D1 subgrupos por tipo con contador", len(subs) >= 4 and any(s.startswith("Agentes") for s in subs) and any(s.startswith("General") for s in subs), subs)
            ok("D1 subgrupos plegados por defecto", pg.evaluate("[...document.querySelectorAll('#lista details.sub')].every(d=>!d.open)"))
            ok("D1 la suma de subgrupos = 30 (nada se pierde)", sum(int(s.split(':')[1]) for s in subs) == 30, subs)
            ok("D1 subtipo de la IA manda sobre etiquetas", pg.evaluate("subDe(db.cards[0])") == "Modelos")
            pg.evaluate("document.querySelector('#lista details[data-k$=\"Inteligencia artificial\"]').open=false")
            pg.fill("#buscar", "Ficha 3"); pg.dispatch_event("#buscar", "input"); pg.wait_for_timeout(300)
            ok("D1 buscar abre los grupos con resultados", pg.evaluate("[...document.querySelectorAll('#lista details')].every(d=>d.open)"))
            pg.fill("#buscar", ""); pg.dispatch_event("#buscar", "input"); pg.wait_for_timeout(200)
            fl = pg.evaluate("[...document.querySelectorAll('#filtros button')].map(b=>b.textContent)")
            ok("D2 Para revisar va justo tras Todo (H3: tras los filtros de estado)", [x for x in fl if x != "Plegar todo"][[x.split(" (")[0] for x in fl].index("Todo")+1].startswith("Para revisar"), fl)
            ok("D2 ningun filtro cortado", pg.evaluate("[...document.querySelectorAll('#filtros>*')].every(b=>{const r=b.getBoundingClientRect();return r.left>=0&&r.right<=innerWidth+1})"))
            ok("D2 sin desbordamiento horizontal", pg.evaluate("document.documentElement.scrollWidth<=innerWidth+1"))
            if esq == "light":
                c = pg.evaluate("[getComputedStyle(document.documentElement).getPropertyValue('--acx').trim(),getComputedStyle(document.documentElement).getPropertyValue('--bad').trim()]")
                ok("D3 texto oscuro sobre el naranja", c[0].lower() == "#14171c", c)
            pg.screenshot(path=CD + "D-%s-%s.png" % (nom, "claro" if esq == "light" else "oscuro"), full_page=True)
            br.close()
fin()
