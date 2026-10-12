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

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
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
    String compartido;

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
            @Override public void onPageFinished(WebView v, String u) { enviarCompartido(); }
        });
        setContentView(web);
        compartido = textoCompartido(getIntent());
        web.loadUrl("file:///android_asset/index.html");
    }

    String textoCompartido(Intent i) {
        return i != null && Intent.ACTION_SEND.equals(i.getAction()) ? i.getStringExtra(Intent.EXTRA_TEXT) : null;
    }

    void enviarCompartido() {
        if (compartido != null) {
            web.evaluateJavascript("window.__compartido&&window.__compartido(" + JSONObject.quote(compartido) + ")", null);
            compartido = null;
        }
    }

    @Override
    protected void onNewIntent(Intent i) {
        super.onNewIntent(i);
        compartido = textoCompartido(i);
        enviarCompartido();
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
