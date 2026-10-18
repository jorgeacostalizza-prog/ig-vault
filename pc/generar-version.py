"""Genera version.json para publicar en la raiz de Pages (junto a src/assets/index.html y pc/servidor.py).
Uso: python generar-version.py <carpeta_raiz_de_pages> [version]. No sube nada."""
import hashlib, json, os, sys, time
raiz = os.path.abspath(sys.argv[1])
ver = sys.argv[2] if len(sys.argv) > 2 else time.strftime("%Y.%m.%d.%H%M")
def sha(rel):
    with open(os.path.join(raiz, rel), "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()
meta = {"version": ver, "fecha": time.strftime("%Y-%m-%d"),
        "index_url": "src/assets/index.html", "index_sha256": sha("src/assets/index.html")}
if os.path.isfile(os.path.join(raiz, "pc", "servidor.py")):
    meta.update(servidor_url="pc/servidor.py", servidor_sha256=sha("pc/servidor.py"))
with open(os.path.join(raiz, "version.json"), "w", encoding="utf-8") as f:
    json.dump(meta, f, indent=1)
print("version.json escrito en", raiz, meta)
