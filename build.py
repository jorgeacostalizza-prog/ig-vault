"""Construye IG Extractor.apk sin Gradle (aapt2 -> javac -> d8 -> zipalign -> apksigner). Mismo metodo que Coucou.
Uso: python build.py   (deja la APK en 'Mis Android Apps\IG Extractor.apk')"""
import os, shutil, subprocess, zipfile, secrets, json

AQUI = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
SRC, BUILD = AQUI + "/src", AQUI + "/build"
SDK = os.path.join(os.environ["LOCALAPPDATA"], "Android", "Sdk").replace("\\", "/")
BT, JAR = SDK + "/build-tools/36.1.0", SDK + "/platforms/android-36.1/android.jar"
VERSION_CODE, VERSION_NAME = 2, "1.1"
DESTINO = r"C:\Users\PC\DeskBox\Apps\Mis Android Apps\IG Extractor.apk"
KSDIR = os.path.expanduser("~/.igvault-movil")


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(r.stdout + r.stderr)
        raise SystemExit("FALLO: " + " ".join(map(str, cmd))[:160])
    return r.stdout


CLAVES = SRC + "/assets/claves.json"  # solo dentro de la APK; esta en .gitignore y se borra al acabar


def main():
    shutil.rmtree(BUILD, ignore_errors=True)
    json.dump({"nvidia": os.environ.get("NVIDIA_API_KEY", ""), "openrouter": os.environ.get("OPENROUTER_API_KEY", ""), "groq": os.environ.get("GROQ_API_KEY", ""), "gemini": os.environ.get("GEMINI_API_KEY", "")}, open(CLAVES, "w"))
    for d in ("flat", "gen", "classes"):
        os.makedirs(BUILD + "/" + d)
    for base, _, fs in os.walk(SRC + "/res"):
        for f in fs:
            run([BT + "/aapt2.exe", "compile", "-o", BUILD + "/flat", os.path.join(base, f)])
    flats = [BUILD + "/flat/" + f for f in os.listdir(BUILD + "/flat") if f.endswith(".flat")]
    base_apk = BUILD + "/app-unsigned.apk"
    run([BT + "/aapt2.exe", "link", "-o", base_apk, "-I", JAR, "--manifest", SRC + "/AndroidManifest.xml", "-A", SRC + "/assets",
         "--java", BUILD + "/gen", "--min-sdk-version", "26", "--target-sdk-version", "36", "--version-code", str(VERSION_CODE),
         "--version-name", VERSION_NAME, "--no-version-vectors"] + flats)
    fuentes = [os.path.join(b, f) for root in (SRC + "/app", BUILD + "/gen") for b, _, fs in os.walk(root) for f in fs if f.endswith(".java")]
    run(["javac", "-encoding", "UTF-8", "-nowarn", "--release", "8", "-classpath", JAR, "-d", BUILD + "/classes"] + fuentes)
    cls = [os.path.join(b, f) for b, _, fs in os.walk(BUILD + "/classes") for f in fs if f.endswith(".class")]
    run([BT + "/d8.bat", "--lib", JAR, "--min-api", "26", "--output", BUILD] + cls)
    with zipfile.ZipFile(base_apk, "a", zipfile.ZIP_DEFLATED) as z:
        z.write(BUILD + "/classes.dex", "classes.dex")
    al = BUILD + "/app-aligned.apk"
    run([BT + "/zipalign.exe", "-p", "-f", "4", base_apk, al])
    os.makedirs(KSDIR, exist_ok=True)
    ks, pw = KSDIR + "/igvault.keystore", KSDIR + "/ks.pass"
    if not os.path.exists(pw):
        open(pw, "w").write(secrets.token_urlsafe(18))
    p = open(pw).read()
    if not os.path.exists(ks):
        run(["keytool", "-genkeypair", "-keystore", ks, "-storepass", p, "-keypass", p, "-alias", "igvault", "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000", "-dname", "CN=IG Extractor,O=Privado,C=CH"])
    final = AQUI + "/IG Extractor.apk"
    run([BT + "/apksigner.bat", "sign", "--ks", ks, "--ks-pass", "pass:" + p, "--key-pass", "pass:" + p, "--ks-key-alias", "igvault", "--out", final, al])
    print(run([BT + "/apksigner.bat", "verify", "--verbose", final]).strip())
    os.makedirs(os.path.dirname(DESTINO), exist_ok=True)
    shutil.copy(final, DESTINO)
    os.remove(CLAVES)
    print("LISTO:", DESTINO, os.path.getsize(final) // 1024, "KB")


main()
