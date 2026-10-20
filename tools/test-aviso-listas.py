# Mensaje final por listas (20/10/2026): 3 bloques, el último arriba con 🆕. Móvil 390 + PC 1280.
import sys, os; sys.path.insert(0, "C:/Users/PC/DeskBox/Apps/CODE/IG Info extractor Code/ig-vault-apk/tools")
from arnes import *
CD = BASE + "capturas/aviso-listas/"; os.makedirs(CD, exist_ok=True)
with sync_playwright() as p:
    for ancho, nom in ((390, "movil"), (1280, "pc")):
        br, pg = pagina(p, ancho)
        t = pg.evaluate("""async()=>{
          sesionDesde=1; db.cards=[];
          const mk=(b,i,e)=>({id:'x'+b+i,url:'https://github.com/a/r'+b+i,tipo:'GitHub',estado:e,bloque:b,grupo:'AI',titulo:'Ficha '+b+i,resumen:'r',categoria:'Otros',repos:[],tags:[],fuente:'',motivo:''});
          [[1,3,0],[2,2,1],[3,4,0]].forEach(([b,n,r])=>{for(let i=0;i<n;i++)db.cards.push(mk(b,i,i<r?'revisar':'ok'))});
          await correr(); return $('#aviso').textContent}""")
        print(nom, repr(t))
        ok("último bloque primero con 🆕", t.index("Bloque 3") < t.index("Bloque 2") < t.index("Bloque 1") and "🆕 Bloque 3 (el último)" in t, t)
        ok("revisar contado en bloque 2", "Bloque 2: 2 fichas, 1 para revisar" in t, t)
        pg.screenshot(path=CD + nom + ".png"); br.close()
fin()
