"""Comprime las fotos nuevas de publico/, regenera fotos.json y hace push.
Uso: python actualizar.py            (comprime + json + commit + push)
     python actualizar.py --sin-push (solo comprime + json)"""
import json, subprocess, sys
from pathlib import Path
from PIL import Image

ORIGEN = Path("F:/CLAUDIO/agente-lanzamientos/Vibras/fotos_para_enviar/publico")
AQUI = Path(__file__).parent
DESTINO = AQUI / "fotos"


ESTADO = Path("F:/CLAUDIO/agente-lanzamientos/vibras_dm_estado.json")


def exportar_sala(con_muneco):
    """2026-11-21: sala.json público para que Atenea sepa si alguien ya está en la sala y qué tiene (solo @ y puesto, sin comentarios)."""
    import re
    e = json.loads(ESTADO.read_text(encoding="utf-8"))
    supremo = set(e.get("supremo_avisado", {}))
    sala = {}
    for u, r in e.get("sala", {}).items():
        t, pide = r.get("tipo") or "", r.get("pide") or ""
        etiq = {m.lower() for c in e.get("personas", {}).get(u, {}).get("comentarios", []) for m in re.findall(r"@([\w.]*\w)", c.get("texto", ""))} - {"randy.pro", u.lower()}
        if t == "musico":
            puesto = f"banda ({pide}) confirmado" if r.get("frase") else f"pidió banda ({pide})"
        elif t == "equipo_ok":
            puesto = f"equipo ({pide}) confirmado"
        elif t == "equipo":
            puesto = f"pidió equipo ({pide}): le falta comentar una frase de la canción"
        elif t == "vip_ok":
            puesto = "VIP confirmado"
        elif t == "vip":
            puesto = f"pidió VIP: lleva {len(etiq)} de 5 etiquetas"
        elif t == "bailar":
            puesto = "baile con su pareja " + ", ".join("@" + x for x in r.get("pareja", [])) + " confirmado"
        elif t == "bailar_p":
            puesto = "pidió bailar: le falta etiquetar a su pareja"
        elif t == "elegido":
            puesto = "escenario con Los Elegidos confirmado"
        elif t == "millonario_ok":
            puesto = "el millonario confirmado"
        else:
            puesto = "asiento"
        if u in supremo:
            puesto += f"; pidió VIP Supremo: lleva {len(etiq)} de 10 etiquetas (lo demás lo confirma Randy)"
        sala[u.lower()] = {"puesto": puesto, "fila": r.get("fila"), "cartel": bool(r.get("cartel")),
                           "ya_tiene_muneco": u.lower() in con_muneco,
                           "etiquetas": len(etiq)}
    for u in con_muneco - set(sala):   # salen en la sala pero entraron por otra vía (equipo, banda, bailarines…)
        sala[u] = {"puesto": "sale en la sala", "fila": None, "cartel": False, "ya_tiene_muneco": True, "etiquetas": None}
    nuevo = json.dumps(sala, ensure_ascii=False, indent=0, sort_keys=True)
    f = AQUI / "sala.json"
    if f.exists() and f.read_text(encoding="utf-8") == nuevo:
        return False
    f.write_text(nuevo, encoding="utf-8")
    return True


def main():
    DESTINO.mkdir(exist_ok=True)
    nuevas = 0
    for f in sorted(ORIGEN.glob("@*.jpg")):
        dst = DESTINO / (f.stem[1:].lower() + ".webp")
        if dst.exists() and dst.stat().st_mtime >= f.stat().st_mtime:
            continue
        im = Image.open(f).convert("RGB")
        im = im.resize((720, round(im.height * 720 / im.width)), Image.LANCZOS)
        im.save(dst, "WEBP", quality=90, method=6)
        nuevas += 1
    usuarios = sorted(p.stem for p in DESTINO.glob("*.webp"))
    (AQUI / "fotos.json").write_text(json.dumps(usuarios, ensure_ascii=False), encoding="utf-8")
    print(f"{nuevas} comprimidas, {len(usuarios)} en total")
    cambio_sala = exportar_sala(set(usuarios))
    if "--sin-push" in sys.argv or not (nuevas or cambio_sala):
        return
    git = lambda *a: subprocess.run(["git", "-C", str(AQUI), *a], check=True)
    git("add", "fotos", "fotos.json", "sala.json")
    git("commit", "-m", f"Fotos nuevas: {nuevas}" if nuevas else "Sala al día")
    for _ in range(3):   # a veces el push falla con 128 y al reintentar pasa
        if subprocess.run(["git", "-C", str(AQUI), "push"]).returncode == 0:
            break


if __name__ == "__main__":
    main()
