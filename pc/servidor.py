"""IG Extractor: servidor local (solo libreria estandar). Sirve la web y hace de puente sin CORS."""
import ast, hashlib, json, mimetypes, os, shutil, subprocess, sys, threading, time, uuid
import urllib.error, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

AQUI = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get("IGX_PORT", "8777"))
UA = "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36"
MAX_HTTP = 1_500_000
MAX_VOZ = 12_000_000
ULTIMO_PING = [0.0]
BRAVE = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
WEB = os.path.join(AQUI, "web")
WEB_APK = os.path.abspath(os.path.join(AQUI, "..", "ig-vault-apk", "src", "assets"))


def log(msg):
    try:
        with open(os.path.join(AQUI, "servidor.log"), "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + msg + "\n")
    except OSError:
        pass


def claves():
    r = {"nvidia": os.environ.get("NVIDIA_API_KEY", ""), "openrouter": os.environ.get("OPENROUTER_API_KEY", ""),
         "groq": os.environ.get("GROQ_API_KEY", ""), "gemini": os.environ.get("GEMINI_API_KEY", "")}
    try:
        with open(os.path.join(os.path.expanduser("~"), ".ig-extractor", "claves.json"), encoding="utf-8") as f:
            for k, v in json.load(f).items():
                if k in r and isinstance(v, str) and v:
                    r[k] = v
    except (OSError, ValueError, AttributeError):
        pass
    return r


def http(d):
    url = d.get("url") or ""
    if not url.lower().startswith(("http://", "https://")):
        return {"status": 0, "body": "", "error": "solo http/https"}
    h = {"User-Agent": UA, "Accept-Language": "es,en;q=0.8"}
    h.update({str(k): str(v) for k, v in (d.get("headers") or {}).items()})
    cuerpo = d.get("body")
    req = urllib.request.Request(url, data=cuerpo.encode("utf-8") if cuerpo else None, headers=h,
                                 method=(d.get("method") or "GET").upper())
    try:
        try:
            r = urllib.request.urlopen(req, timeout=30)
        except urllib.error.HTTPError as e:
            r = e  # 4xx/5xx: tambien devolvemos el cuerpo
        with r:
            raw = r.read(MAX_HTTP)
            return {"status": r.getcode(), "url": r.geturl(), "body": raw.decode("utf-8", errors="replace")}
    except Exception as e:
        return {"status": 0, "body": "", "error": str(e)}


def groq_req(video, key, modelo):
    b = "----igx" + uuid.uuid4().hex
    cab = (f'--{b}\r\nContent-Disposition: form-data; name="model"\r\n\r\n{modelo}\r\n'
           f'--{b}\r\nContent-Disposition: form-data; name="response_format"\r\n\r\njson\r\n'
           f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="v.mp4"\r\n'
           f'Content-Type: video/mp4\r\n\r\n').encode()
    data = cab + video + f"\r\n--{b}--\r\n".encode()
    req = urllib.request.Request("https://api.groq.com/openai/v1/audio/transcriptions", data=data, method="POST",
                                 headers={"Authorization": "Bearer " + key,
                                          "Content-Type": "multipart/form-data; boundary=" + b,
                                          "User-Agent": "ig-extractor/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return (json.loads(r.read().decode("utf-8", errors="replace")).get("text") or "").strip()


def voz(d):
    key = d.get("groq") or claves()["groq"]
    if not key:
        return {"status": 0, "body": "error: sin claves de voz"}
    url = d.get("url") or ""
    if not url.lower().startswith(("http://", "https://")):
        return {"status": 0, "body": "error descarga: url no valida"}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Range": f"bytes=0-{MAX_VOZ - 1}"})
        with urllib.request.urlopen(req, timeout=30) as r:
            v = r.read(MAX_VOZ)
    except Exception as e:
        return {"status": 0, "body": "error descarga: " + str(e)}
    if len(v) < 2000:
        return {"status": 0, "body": "error descarga: vacio"}
    err, g400 = [], 0
    for modelo in ("whisper-large-v3-turbo", "whisper-large-v3"):
        try:
            t = groq_req(v, key, modelo)
            if t:
                return {"status": 200, "body": t}
            err.append(modelo + ":vacio")
        except urllib.error.HTTPError as e:
            if e.code == 400:
                g400 += 1
                if g400 == 2:
                    return {"status": 0, "body": "sin audio (Groq 400)"}
            err.append(f"{modelo}:HTTP {e.code}")
            if e.code in (401, 403):
                break  # clave mala: no probar el otro modelo
        except Exception as e:
            err.append(f"{modelo}:{e}")
    return {"status": 0, "body": "error: " + " ".join(err)}


def ffmpeg_exe():
    import shutil
    return shutil.which("ffmpeg") or os.path.expanduser(r"~\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe")


def frames(d):
    """Fotogramas del video (ffmpeg) como data URLs JPEG, repartidos por toda la duracion."""
    import base64, tempfile, re, shutil
    url = d.get("url") or ""
    n = max(1, min(int(d.get("n") or 4), 6))
    if not url.lower().startswith(("http://", "https://")):
        return {"status": 0, "frames": [], "error": "url no valida"}
    exe = ffmpeg_exe()
    if not os.path.exists(exe):
        return {"status": 0, "frames": [], "error": "ffmpeg no esta instalado"}
    tmp = tempfile.mkdtemp(prefix="igx-")
    try:
        v = os.path.join(tmp, "v.mp4")
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Range": f"bytes=0-{MAX_VOZ - 1}"})
        with urllib.request.urlopen(req, timeout=30) as r, open(v, "wb") as fh:
            fh.write(r.read(MAX_VOZ))
        info = subprocess.run([exe, "-hide_banner", "-i", v], capture_output=True, text=True, creationflags=0x08000000).stderr
        m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", info)
        dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) if m else 20.0
        out = []
        for i in range(n):
            t = max(0.2, dur * (i + 0.5) / n)
            f = os.path.join(tmp, f"f{i}.jpg")
            subprocess.run([exe, "-hide_banner", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", v, "-frames:v", "1",
                            "-vf", "scale='min(720,iw)':-2", "-q:v", "5", f], capture_output=True, creationflags=0x08000000, timeout=40)
            if os.path.exists(f) and os.path.getsize(f) > 1500:
                with open(f, "rb") as fh:
                    out.append("data:image/jpeg;base64," + base64.b64encode(fh.read()).decode())
        return {"status": 200 if out else 0, "frames": out, "error": "" if out else "ffmpeg no saco fotogramas", "dur": dur}
    except Exception as e:
        return {"status": 0, "frames": [], "error": str(e)}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


OBSIDIAN = r"C:\Users\PC\DeskBox\Apps\CODE\Claudes Things\IG Extractor Obsidian"



RESP = os.path.join(os.path.expanduser("~"), ".ig-extractor")

def respaldo_guardar(d):
    # copia de las fichas fuera del navegador; nunca pisa una copia llena con una vacía (salvo "vaciar")
    os.makedirs(RESP, exist_ok=True)
    lleno = os.path.join(RESP, "respaldo.json")
    if d.get("vaciar"):
        if os.path.exists(lleno):
            os.replace(lleno, os.path.join(RESP, "respaldo-borrado.json"))
        return {"ok": True}
    if not d.get("cards"):
        return {"ok": True, "ignorado": True}
    with open(lleno + ".tmp", "w", encoding="utf-8") as f:
        json.dump({"cards": d["cards"], "sel": d.get("sel", [])}, f, ensure_ascii=False)
    os.replace(lleno + ".tmp", lleno)
    return {"ok": True}

def respaldo_leer():
    try:
        with open(os.path.join(RESP, "respaldo.json"), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"cards": []}

def pegar():
    """Texto del portapapeles de Windows (el navegador a veces no deja leerlo). Sin ventana."""
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", "[Console]::OutputEncoding=[Text.Encoding]::UTF8; Get-Clipboard -Raw"],
                           capture_output=True, timeout=8, creationflags=0x08000000)
        return {"texto": r.stdout.decode("utf-8", "replace").strip()[:60000]}
    except Exception:
        return {"texto": ""}


def abrir(d):
    url = d.get("url") or ""
    if not url.lower().startswith(("http://", "https://")):
        return {"ok": False, "error": "solo http/https"}
    exe = BRAVE if os.path.exists(BRAVE) else CHROME
    if not os.path.exists(exe):
        return {"ok": False, "error": "sin Brave ni Chrome"}
    subprocess.Popen([exe, url], creationflags=0x08000000)  # CREATE_NO_WINDOW
    return {"ok": True}


def buscar_estatico(p):
    """Ruta de fichero para p: primero pc/web, luego la web del APK. None si no existe."""
    rel = "index.html" if p in ("/", "") else p.lstrip("/")
    for base in (WEB, WEB_APK):
        f = os.path.abspath(os.path.join(base, rel))
        if f.startswith(base + os.sep) and os.path.isfile(f):
            return f
    return None


# ---- Autoactualizacion desde Pages (version.json). Silenciosa: sin red o con error sigue con lo que hay ----
PAGES = os.environ.get("IGX_PAGES", "https://jorgeacostalizza-prog.github.io/ig-vault/").rstrip("/") + "/"
ESTADO_VER = os.path.join(AQUI, "estado-version.json")
CADA_HORAS = 4
MIN_HTML, MAX_HTML = 5_000, 5_000_000
MIN_PY, MAX_PY = 2_000, 1_000_000


def _leer_estado():
    try:
        with open(ESTADO_VER, encoding="utf-8") as f:
            d = json.load(f)
            return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _guardar_estado(d):
    try:
        with open(ESTADO_VER + ".tmp", "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False)
        os.replace(ESTADO_VER + ".tmp", ESTADO_VER)
    except OSError:
        pass


def _bajar(rel, tope):
    with urllib.request.urlopen(urllib.request.Request(PAGES + rel.lstrip("/"), headers={"User-Agent": "ig-extractor-pc"}), timeout=8) as r:
        return r.read(tope + 1)


def _sha(b):
    return hashlib.sha256(b).hexdigest()


def _copia_fechada(ruta, carpeta):
    if os.path.isfile(ruta):
        os.makedirs(carpeta, exist_ok=True)
        base, ext = os.path.splitext(os.path.basename(ruta))
        shutil.copy2(ruta, os.path.join(carpeta, f"{base}.antes-{time.strftime('%Y%m%d-%H%M%S')}{ext}"))


def _reemplazar(ruta, datos):
    with open(ruta + ".nuevo", "wb") as f:
        f.write(datos)
    os.replace(ruta + ".nuevo", ruta)


def comprobar_actualizacion():
    """Una pasada. Devuelve texto de lo hecho (para log/tests); nunca lanza."""
    try:
        meta = json.loads(_bajar("version.json", 100_000).decode("utf-8"))
        if not isinstance(meta, dict) or not meta.get("version"):
            return "version.json invalido"
        est = _leer_estado()
        hecho = []
        # interfaz
        rel = meta.get("index_url") or "src/assets/index.html"
        destino = os.path.join(WEB, "index.html")
        local = b""
        if os.path.isfile(destino):
            with open(destino, "rb") as f:
                local = f.read()
        h_rem = str(meta.get("index_sha256") or "")
        if h_rem and _sha(local) != h_rem:
            nuevo = _bajar(rel, MAX_HTML)
            if not (MIN_HTML <= len(nuevo) <= MAX_HTML) or b"</html>" not in nuevo.lower() or _sha(nuevo) != h_rem:
                log("index.html publicado no valido: se ignora")
                return "index invalido"
            os.makedirs(WEB, exist_ok=True)
            _copia_fechada(destino, os.path.join(WEB, "BACKUPS"))
            _reemplazar(destino, nuevo)
            hecho.append("index")
        # el propio servidor (se usa en el proximo arranque)
        h_srv = str(meta.get("servidor_sha256") or "")
        mio = os.path.join(AQUI, "servidor.py")
        if h_srv and meta.get("servidor_url"):
            with open(mio, "rb") as f:
                sha_mio = _sha(f.read())
            if True:
                if sha_mio != h_srv:
                    nuevo = _bajar(meta["servidor_url"], MAX_PY)
                    ok = MIN_PY <= len(nuevo) <= MAX_PY and _sha(nuevo) == h_srv
                    if ok:
                        try:
                            ast.parse(nuevo.decode("utf-8"))
                        except (SyntaxError, ValueError):
                            ok = False
                    if ok:
                        _copia_fechada(mio, os.path.join(WEB, "BACKUPS"))
                        _reemplazar(mio, nuevo)
                        hecho.append("servidor")
                    else:
                        log("servidor.py publicado no valido: se ignora")
        est["version"] = str(meta["version"])
        est["comprobado"] = time.strftime("%Y-%m-%d %H:%M:%S")
        if hecho:
            est["actualizado"] = time.strftime("%Y-%m-%d %H:%M:%S")
            log("actualizado: " + ", ".join(hecho) + " -> " + est["version"])
        _guardar_estado(est)
        return "actualizado " + "+".join(hecho) if hecho else "al dia"
    except Exception as e:
        log("autoupdate sin efecto: " + type(e).__name__ + " " + str(e)[:120])
        return "sin red o error"


def hilo_actualizar():
    time.sleep(2)
    while True:
        comprobar_actualizacion()
        time.sleep(CADA_HORAS * 3600)


def info_version():
    est = _leer_estado()
    if not est.get("actualizado"):
        try:
            est["actualizado"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(os.path.join(WEB, "index.html"))))
        except OSError:
            est["actualizado"] = ""
    return {"version": est.get("version") or "local", "actualizado": est["actualizado"], "origen": PAGES}


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _enviar(self, b, tipo, code=200):
        self.send_response(code)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(b)

    def _json(self, obj, code=200):
        self._enviar(json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8", code)

    def do_GET(self):
        p = self.path.split("?")[0]
        if p == "/api/ping":
            ULTIMO_PING[0] = time.time()
            return self._json({"ok": True, "app": "ig-extractor"})
        if p == "/api/version":
            return self._json(info_version())
        if p == "/api/pegar":
            return self._json(pegar())
        if p == "/api/claves":
            return self._json(claves())
        if p == "/api/respaldo":
            return self._json(respaldo_leer())
        if p == "/api/semilla":  # fichas precargadas una vez por versión (la app las suma sin repetir)
            try:
                with open(os.path.join(RESP, "semilla.json"), "rb") as f:
                    return self._enviar(f.read(), "application/json; charset=utf-8")
            except OSError:
                return self._json({"cards": []})
        f = buscar_estatico(p)
        if not f:
            return self._json({"error": "no existe"}, 404)
        tipo = mimetypes.guess_type(f)[0] or "application/octet-stream"
        if tipo.startswith("text/") or tipo in ("application/javascript", "application/json"):
            tipo += "; charset=utf-8"
        with open(f, "rb") as fh:
            self._enviar(fh.read(), tipo)

    def do_POST(self):
        try:
            n = int(self.headers.get("Content-Length") or 0)
            d = json.loads(self.rfile.read(n).decode("utf-8") or "{}")
        except Exception:
            return self._json({"status": 0, "body": "", "error": "json invalido"}, 400)
        f = {"/api/http": http, "/api/voz": voz, "/api/abrir": abrir, "/api/frames": frames, "/api/respaldo": respaldo_guardar}.get(self.path.split("?")[0])
        if not f:
            return self._json({"error": "no existe"}, 404)
        self._json(f(d))


def ping_ajeno():
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/ping", timeout=3) as r:
            return json.loads(r.read()).get("app") == "ig-extractor"
    except Exception:
        return False


def vigilar():
    while True:
        time.sleep(5)
        if ULTIMO_PING[0] and time.time() - ULTIMO_PING[0] > 120:
            log("sin pings 120 s: apagado")
            os._exit(0)


if __name__ == "__main__":
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", PORT), H)
    except OSError:
        if ping_ajeno():
            sys.exit(0)  # ya hay uno corriendo
        log(f"puerto {PORT} ocupado por otro programa")
        sys.exit(1)
    log(f"servidor en 127.0.0.1:{PORT}")
    threading.Thread(target=vigilar, daemon=True).start()
    threading.Thread(target=hilo_actualizar, daemon=True).start()
    srv.serve_forever()
