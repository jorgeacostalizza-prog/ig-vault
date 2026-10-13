package app.igvault.movil;

import android.app.Activity;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.graphics.Color;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.webkit.JavascriptInterface;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;
import org.json.JSONObject;
import org.json.JSONTokener;

import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.net.Uri;
import android.util.Base64;
import org.json.JSONArray;
import java.io.BufferedInputStream;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;

/** Carcasa: pantalla en WebView (assets/index.html) + puente nativo para red sin CORS, paginas renderizadas, copiar y compartir. */
public class MainActivity extends Activity {
    static final String UA = "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36";
    static final String LEER = "(function(){function m(s){var e=document.querySelector(s);return e&&e.content?e.content:''}"
            + "var c=document.querySelector('.Caption');return JSON.stringify({cap:c?c.innerText:'',og:m('meta[property=\"og:description\"]'),"
            + "ogt:m('meta[property=\"og:title\"]'),title:document.title||'',body:document.body?document.body.innerText.slice(0,3000):''})})()";

    WebView web;
    final Handler ui = new Handler(Looper.getMainLooper());
    static final String BASE = "https://jorgeacostalizza-prog.github.io/ig-vault/";
    static final String WEB = BASE + "src/assets/index.html";
    static final int MAX_FOTOS = 40;
    String compartido, fotos;
    boolean cargada;

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        web = new WebView(this);
        web.setBackgroundColor(Color.parseColor("#0F1115"));
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setAllowFileAccess(true);
        web.addJavascriptInterface(new Puente(), "Native");
        web.setWebViewClient(new WebViewClient() {
            @Override public void onPageFinished(WebView v, String u) { cargada = true; enviarCompartido(); }
        });
        setContentView(web);
        procesar(getIntent());
        arranque();
    }

    /** Autoupdate: baja la interfaz publicada (2,5 s max), la guarda y la usa; sin red usa la ultima copia o la incluida en la APK. */
    void arranque() {
        new Thread(() -> {
            File cache = new File(getFilesDir(), "index.html");
            try {
                HttpURLConnection c = (HttpURLConnection) new URL(WEB + "?t=" + System.currentTimeMillis()).openConnection();
                c.setConnectTimeout(2500);
                c.setReadTimeout(2500);
                if (c.getResponseCode() == 200) {
                    InputStream in = c.getInputStream();
                    byte[] b = leer(in, 3000000);
                    in.close();
                    if (new String(b, "UTF-8").contains("</html>")) { FileOutputStream o = new FileOutputStream(cache); o.write(b); o.close(); }
                }
            } catch (Exception e) { }
            String html = "";
            try {
                InputStream in = cache.exists() ? new FileInputStream(cache) : getAssets().open("index.html");
                html = new String(leer(in, 3000000), "UTF-8");
                in.close();
            } catch (Exception e) { }
            final String h = html;
            ui.post(() -> web.loadDataWithBaseURL(BASE, h, "text/html", "UTF-8", null));
        }).start();
    }

    static byte[] leer(InputStream in, int max) throws java.io.IOException {
        ByteArrayOutputStream bo = new ByteArrayOutputStream();
        byte[] buf = new byte[8192];
        int n;
        while (bo.size() < max && (n = in.read(buf)) > 0) bo.write(buf, 0, n);
        return bo.toByteArray();
    }

    /** Recibe lo compartido: texto suelto, el archivo de "Exportar chat" de WhatsApp (.txt, o .zip con fotos) y fotos sueltas. */
    void procesar(Intent i) {
        compartido = null;
        fotos = null;
        if (i == null) return;
        String a = i.getAction();
        if (!Intent.ACTION_SEND.equals(a) && !Intent.ACTION_SEND_MULTIPLE.equals(a)) return;
        final String previo = i.getStringExtra(Intent.EXTRA_TEXT);
        final ArrayList<Uri> us = new ArrayList<>();
        if (Intent.ACTION_SEND.equals(a)) { Uri u = i.getParcelableExtra(Intent.EXTRA_STREAM); if (u != null) us.add(u); }
        else { ArrayList<Uri> l = i.getParcelableArrayListExtra(Intent.EXTRA_STREAM); if (l != null) us.addAll(l); }
        if (us.isEmpty()) { compartido = previo; return; }
        new Thread(() -> {
            StringBuilder txt = new StringBuilder(previo == null ? "" : previo + "\n");
            JSONArray fs = new JSONArray();
            File dir = new File(getCacheDir(), "chat");
            File[] viejos = dir.listFiles();
            if (viejos != null) for (File f : viejos) f.delete();
            dir.mkdirs();
            for (Uri u : us) {
                try {
                    InputStream in = new BufferedInputStream(getContentResolver().openInputStream(u));
                    in.mark(4);
                    byte[] m = new byte[2];
                    int r = in.read(m);
                    in.reset();
                    String tipo = getContentResolver().getType(u);
                    if (r == 2 && m[0] == 'P' && m[1] == 'K') {
                        ZipInputStream z = new ZipInputStream(in);
                        ZipEntry e;
                        while ((e = z.getNextEntry()) != null) {
                            String n = e.getName().toLowerCase();
                            if (n.endsWith(".txt")) txt.append(new String(leer(z, 5000000), "UTF-8")).append("\n");
                            else if (fs.length() < MAX_FOTOS && n.matches(".*\\.(jpe?g|png|webp)$")) guardarFoto(z, dir, fs);
                        }
                    } else if (tipo != null && tipo.startsWith("image/")) {
                        if (fs.length() < MAX_FOTOS) guardarFoto(in, dir, fs);
                    } else txt.append(new String(leer(in, 5000000), "UTF-8")).append("\n");
                    in.close();
                } catch (Exception e) { }
            }
            compartido = txt.toString();
            fotos = fs.toString();
            ui.post(this::enviarCompartido);
        }).start();
    }

    void guardarFoto(InputStream in, File dir, JSONArray fs) throws Exception {
        String n = "f" + fs.length() + ".jpg";
        FileOutputStream o = new FileOutputStream(new File(dir, n));
        o.write(leer(in, 10000000));
        o.close();
        fs.put(n);
    }

    void enviarCompartido() {
        if (!cargada || (compartido == null && fotos == null)) return;
        web.evaluateJavascript("window.__chat&&window.__chat(" + JSONObject.quote(compartido == null ? "" : compartido) + "," + (fotos == null ? "[]" : fotos) + ")", null);
        compartido = null;
        fotos = null;
    }

    @Override
    protected void onNewIntent(Intent i) {
        super.onNewIntent(i);
        procesar(i);
        ui.post(this::enviarCompartido);
    }

    @Override
    public void onBackPressed() {
        web.evaluateJavascript("window.__atras?window.__atras():false", v -> { if (!"true".equals(v)) moveTaskToBack(true); });
    }

    void responder(int id, String datos) {
        ui.post(() -> web.evaluateJavascript("window.__r(" + id + "," + JSONObject.quote(datos) + ")", null));
    }

    class Puente {
        /** Peticion HTTP sin CORS. Devuelve por __r(id, json {status,url,body}). */
        @JavascriptInterface
        public void http(final int id, final String metodo, final String url, final String cabeceras, final String cuerpo) {
            new Thread(() -> {
                JSONObject out = new JSONObject();
                try {
                    HttpURLConnection c = (HttpURLConnection) new URL(url).openConnection();
                    c.setConnectTimeout(15000);
                    c.setReadTimeout(30000);
                    c.setInstanceFollowRedirects(true);
                    c.setRequestMethod(metodo);
                    c.setRequestProperty("User-Agent", UA);
                    c.setRequestProperty("Accept-Language", "es,en;q=0.8");
                    JSONObject h = new JSONObject(cabeceras == null || cabeceras.isEmpty() ? "{}" : cabeceras);
                    for (java.util.Iterator<String> k = h.keys(); k.hasNext(); ) { String n = k.next(); c.setRequestProperty(n, h.getString(n)); }
                    if (cuerpo != null && !cuerpo.isEmpty()) {
                        c.setDoOutput(true);
                        OutputStream o = c.getOutputStream();
                        o.write(cuerpo.getBytes("UTF-8"));
                        o.close();
                    }
                    int st = c.getResponseCode();
                    InputStream in = st >= 400 ? c.getErrorStream() : c.getInputStream();
                    ByteArrayOutputStream bo = new ByteArrayOutputStream();
                    if (in != null) {
                        byte[] buf = new byte[8192];
                        int n;
                        while ((n = in.read(buf)) > 0 && bo.size() < 1500000) bo.write(buf, 0, n);
                        in.close();
                    }
                    out.put("status", st).put("url", c.getURL().toString()).put("body", bo.toString("UTF-8"));
                } catch (Exception e) {
                    try { out.put("status", 0).put("body", "").put("error", String.valueOf(e)); } catch (Exception x) { }
                }
                responder(id, out.toString());
            }).start();
        }

        /** Carga una pagina con JavaScript (como un navegador) y devuelve su texto: {cap,og,ogt,title,body}. */
        @JavascriptInterface
        public void pagina(final int id, final String url) {
            ui.post(() -> {
                final WebView w = new WebView(MainActivity.this);
                WebSettings s = w.getSettings();
                s.setJavaScriptEnabled(true);
                s.setDomStorageEnabled(true);
                s.setUserAgentString(UA);
                final boolean[] listo = {false};
                final int[] intentos = {0};
                final Runnable[] sondeo = new Runnable[1];
                final Runnable fin = () -> {
                    if (listo[0]) return;
                    listo[0] = true;
                    w.evaluateJavascript(LEER, v -> {
                        String r = "{}";
                        try { Object o = new JSONTokener(v).nextValue(); if (o instanceof String) r = (String) o; } catch (Exception e) { }
                        w.destroy();
                        responder(id, r);
                    });
                };
                sondeo[0] = () -> {
                    if (listo[0]) return;
                    intentos[0]++;
                    w.evaluateJavascript("document.querySelector('.Caption')?1:0", v -> {
                        if ("1".equals(v) || intentos[0] >= 12) fin.run();
                        else ui.postDelayed(sondeo[0], 800);
                    });
                };
                w.setWebViewClient(new WebViewClient() {
                    @Override public void onPageFinished(WebView v, String u) { ui.postDelayed(sondeo[0], 800); }
                    @Override public void onReceivedError(WebView v, android.webkit.WebResourceRequest q, android.webkit.WebResourceError e) {
                        if (q.isForMainFrame()) fin.run();
                    }
                });
                ui.postDelayed(fin, 20000);
                w.loadUrl(url);
            });
        }

        /** Foto del chat reducida (max 1280 px, JPEG) como data URL, lista para un modelo de vision. */
        @JavascriptInterface
        public void foto(final int id, final String nombre) {
            new Thread(() -> {
                JSONObject out = new JSONObject();
                try {
                    String p = new File(new File(getCacheDir(), "chat"), new File(nombre).getName()).getPath();
                    BitmapFactory.Options o = new BitmapFactory.Options();
                    o.inJustDecodeBounds = true;
                    BitmapFactory.decodeFile(p, o);
                    o.inSampleSize = Math.max(1, Math.max(o.outWidth, o.outHeight) / 1280);
                    o.inJustDecodeBounds = false;
                    Bitmap b = BitmapFactory.decodeFile(p, o);
                    ByteArrayOutputStream bo = new ByteArrayOutputStream();
                    b.compress(Bitmap.CompressFormat.JPEG, 80, bo);
                    out.put("status", 200).put("body", "data:image/jpeg;base64," + Base64.encodeToString(bo.toByteArray(), Base64.NO_WRAP));
                } catch (Exception e) {
                    try { out.put("status", 0).put("body", "").put("error", String.valueOf(e)); } catch (Exception x) { }
                }
                responder(id, out.toString());
            }).start();
        }

        /** Claves guardadas dentro de la APK al compilar (no estan en el repo). */
        @JavascriptInterface
        public String claves() {
            try { InputStream in = getAssets().open("claves.json"); String s = new String(leer(in, 10000), "UTF-8"); in.close(); return s; } catch (Exception e) { return "{}"; }
        }

        @JavascriptInterface
        public void copiar(final String texto) {
            ui.post(() -> {
                ((ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE)).setPrimaryClip(ClipData.newPlainText("IG Vault", texto));
                Toast.makeText(MainActivity.this, "Copiado", Toast.LENGTH_SHORT).show();
            });
        }

        @JavascriptInterface
        public void compartir(final String texto, final String asunto) {
            ui.post(() -> {
                Intent i = new Intent(Intent.ACTION_SEND).setType("text/plain").putExtra(Intent.EXTRA_TEXT, texto).putExtra(Intent.EXTRA_SUBJECT, asunto);
                startActivity(Intent.createChooser(i, "Compartir"));
            });
        }

        @JavascriptInterface
        public void abrir(final String url) {
            ui.post(() -> startActivity(new Intent(Intent.ACTION_VIEW, android.net.Uri.parse(url))));
        }

        @JavascriptInterface
        public String pegado() {
            try {
                ClipData d = ((ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE)).getPrimaryClip();
                return d != null && d.getItemCount() > 0 ? String.valueOf(d.getItemAt(0).coerceToText(MainActivity.this)) : "";
            } catch (Exception e) { return ""; }
        }
    }
}
