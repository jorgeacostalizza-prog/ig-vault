package app.igvault.movil;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;

/** Voz del video -> texto, todo en el movil (sin PC). Router: Groq turbo -> Groq v3 -> Gemini 3.5 -> Gemini 3.8. */
public class Voz {
    static final int MAX = 12_000_000; // primeros ~12 MB: suficiente para el audio de un reel y cabe en cada proveedor
    static final String UA = "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36";
    static final String[][] ORDEN = {{"groq", "whisper-large-v3-turbo"}, {"groq", "whisper-large-v3"}, {"gemini", "gemini-3.5-flash-lite"}, {"gemini", "gemini-3.8-flash"}};

    /** Devuelve {proveedor/modelo, texto} o {"", "error: ..."}. */
    public static String[] transcribir(String videoUrl, String groq, String gemini) {
        byte[] v;
        try { v = bajar(videoUrl); } catch (Exception e) { return new String[]{"", "error descarga: " + e}; }
        if (v.length < 2000) return new String[]{"", "error descarga: vacio"};
        StringBuilder err = new StringBuilder();
        java.util.Set<String> muerto = new java.util.HashSet<>(); // proveedor con clave mala: no reintentar su otro modelo
        int g400 = 0;
        for (String[] p : ORDEN) {
            String k = p[0].equals("groq") ? groq : gemini;
            if (k == null || k.isEmpty() || muerto.contains(p[0])) continue;
            try {
                String t = p[0].equals("groq") ? groq(v, k, p[1]) : gemini(java.util.Arrays.copyOf(v, Math.min(v.length, 3_000_000)), k, p[1]);
                if (t != null && t.trim().length() > 0) return new String[]{p[1], t.trim()};
                err.append(p[1]).append(":vacio ");
            } catch (Exception e) { String m = String.valueOf(e.getMessage());
                if (p[0].equals("groq") && m.equals("HTTP 400") && ++g400 == 2) return new String[]{"", "sin audio (Groq 400)"}; // ambos modelos 400: no esperar a Gemini
                if (m.contains("401") || m.contains("403")) muerto.add(p[0]); err.append(p[1]).append(":").append(m).append(" "); }
        }
        return new String[]{"", "error: " + (err.length() == 0 ? "sin claves de voz" : err)};
    }

    static byte[] bajar(String u) throws Exception {
        HttpURLConnection c = (HttpURLConnection) new URL(u).openConnection();
        c.setConnectTimeout(10000);
        c.setReadTimeout(30000);
        c.setRequestProperty("User-Agent", UA);
        c.setRequestProperty("Range", "bytes=0-" + (MAX - 1));
        int s = c.getResponseCode();
        if (s != 200 && s != 206) throw new Exception("HTTP " + s);
        InputStream in = c.getInputStream();
        ByteArrayOutputStream bo = new ByteArrayOutputStream();
        byte[] b = new byte[16384];
        int n;
        while (bo.size() < MAX && (n = in.read(b)) > 0) bo.write(b, 0, n);
        in.close();
        return bo.toByteArray();
    }

    static String groq(byte[] v, String key, String modelo) throws Exception {
        String bd = "----igv" + System.nanoTime();
        HttpURLConnection c = (HttpURLConnection) new URL("https://api.groq.com/openai/v1/audio/transcriptions").openConnection();
        c.setConnectTimeout(10000);
        c.setReadTimeout(30000);
        c.setDoOutput(true);
        c.setRequestMethod("POST");
        c.setRequestProperty("Authorization", "Bearer " + key);
        c.setRequestProperty("Content-Type", "multipart/form-data; boundary=" + bd);
        OutputStream o = c.getOutputStream();
        o.write(("--" + bd + "\r\nContent-Disposition: form-data; name=\"model\"\r\n\r\n" + modelo + "\r\n"
                + "--" + bd + "\r\nContent-Disposition: form-data; name=\"response_format\"\r\n\r\njson\r\n"
                + "--" + bd + "\r\nContent-Disposition: form-data; name=\"file\"; filename=\"v.mp4\"\r\nContent-Type: video/mp4\r\n\r\n").getBytes("UTF-8"));
        o.write(v);
        o.write(("\r\n--" + bd + "--\r\n").getBytes("UTF-8"));
        o.close();
        return campo(leerResp(c), "text");
    }

    static String gemini(byte[] v, String key, String modelo) throws Exception {
        String cuerpo = "{\"contents\":[{\"parts\":[{\"text\":\"Transcribe literalmente lo que se dice en el audio, en su idioma original. Devuelve solo la transcripcion; si no hay voz, devuelve la palabra SINVOZ.\"},"
                + "{\"inline_data\":{\"mime_type\":\"video/mp4\",\"data\":\"" + java.util.Base64.getEncoder().encodeToString(v) + "\"}}]}]}";
        HttpURLConnection c = (HttpURLConnection) new URL("https://generativelanguage.googleapis.com/v1beta/models/" + modelo + ":generateContent").openConnection();
        c.setConnectTimeout(10000);
        c.setReadTimeout(45000);
        c.setDoOutput(true);
        c.setRequestMethod("POST");
        c.setRequestProperty("x-goog-api-key", key);
        c.setRequestProperty("Content-Type", "application/json");
        OutputStream o = c.getOutputStream();
        o.write(cuerpo.getBytes("UTF-8"));
        o.close();
        String t = campo(leerResp(c), "text");
        return t != null && t.trim().equals("SINVOZ") ? "" : t;
    }

    static String leerResp(HttpURLConnection c) throws Exception {
        int s = c.getResponseCode();
        InputStream in = s >= 400 ? c.getErrorStream() : c.getInputStream();
        ByteArrayOutputStream bo = new ByteArrayOutputStream();
        if (in != null) { byte[] b = new byte[8192]; int n; while ((n = in.read(b)) > 0) bo.write(b, 0, n); in.close(); }
        String r = bo.toString("UTF-8");
        if (s >= 400) throw new Exception("HTTP " + s);
        return r;
    }

    /** Primer "campo":"valor" de un JSON, con los escapes resueltos. */
    static String campo(String j, String campo) {
        int i = j.indexOf("\"" + campo + "\"");
        if (i < 0) return null;
        i = j.indexOf('"', j.indexOf(':', i) + 1);
        if (i < 0) return null;
        StringBuilder s = new StringBuilder();
        for (i++; i < j.length(); i++) {
            char ch = j.charAt(i);
            if (ch == '"') break;
            if (ch == '\\' && i + 1 < j.length()) {
                char e = j.charAt(++i);
                if (e == 'n') s.append('\n');
                else if (e == 't') s.append(' ');
                else if (e == 'u' && i + 4 < j.length()) { s.append((char) Integer.parseInt(j.substring(i + 1, i + 5), 16)); i += 4; }
                else s.append(e);
            } else s.append(ch);
        }
        return s.toString();
    }

    /** Prueba en el PC: java Voz URL (claves en GROQ_API_KEY y GEMINI_API_KEY). */
    public static void main(String[] a) {
        String[] r = transcribir(a[0], System.getenv("GROQ_API_KEY"), System.getenv("GEMINI_API_KEY"));
        System.out.println(r[0] + " | " + r[1]);
    }
}
