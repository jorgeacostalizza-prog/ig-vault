# 23/10/2026: unirRepetidas no borra la ficha ?stkn= de Obsidian; claveUrl sin tracking; coherencia rechaza títulos «[…»; fecha de id.
import sys; sys.path.insert(0, "C:/Users/PC/DeskBox/Apps/CODE/IG Info extractor Code/ig-vault-apk/tools")
import arnes
from arnes import *
with sync_playwright() as p:
    br, pg = pagina(p, 390)
    r = pg.evaluate("""()=>{const mk=(id,u,t)=>({id,url:u,tipo:'Instagram',estado:'ok',grupo:'AI',titulo:t,resumen:'x',categoria:'a',tags:[],repos:[{full:'deividcomsono/Obsidian',url:'',stars:1}]});
      db.cards=[mk('mvbw7zm6bpl','https://www.instagram.com/p/Dd_mImzG6jg/','Claude Code y Obsidian'),mk('mviei6d9fenyd','https://www.instagram.com/reel/DeAP6xxRU0H/?stkn=MWVhYmE2dXVscmNnMw==','Obsidian con Claude: Corrección')];
      const n=unirRepetidas();return {n,len:db.cards.length,k:[claveUrl('https://x.com/a/b?stkn=1&xtok=2&exln=3&igsh=4&utm_source=z'),claveUrl('https://x.com/a/b'),claveUrl('https://x.com/a/c?id=1'),claveUrl('https://x.com/a/c?id=2')]}}""")
    ok("no se une/borra la ficha de Obsidian con ?stkn=", r["n"] == 0 and r["len"] == 2, r)
    ok("claveUrl quita stkn/xtok/exln/igsh/utm y mantiene parámetros reales", r["k"][0] == r["k"][1] and r["k"][2] != r["k"][3], r)
    c = pg.evaluate("""()=>['[VOZ DEL VÍDEO, transcrita]','[LO QUE SE VE EN EL VÍDEO (fotogramas)]','Hypervibe app'].map(t=>coherencia(t,'Hypervibe es una app para programar con ayuda de IA',{pie:'Hypervibe app',voz:'',vis:'',repo:''}))""")
    ok("coherencia rechaza títulos que empiezan por «[»", c[0] and c[1] and c[2] == "", c)
    t = pg.evaluate("""()=>({a:añadida({id:'mviei6d9fenyd'}),b:etqAñadida({id:'zz'})})""")
    ok("sin fecha guardada usa la del id; sin nada sigue 'Sin fecha'", t["a"] > 0 and t["b"] == "Sin fecha", t)
    br.close()
fin()
