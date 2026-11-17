"""Comprime las fotos nuevas de publico/, regenera fotos.json y hace push.
Uso: python actualizar.py            (comprime + json + commit + push)
     python actualizar.py --sin-push (solo comprime + json)"""
import json, subprocess, sys
from pathlib import Path
from PIL import Image

ORIGEN = Path("F:/CLAUDIO/agente-lanzamientos/Vibras/fotos_para_enviar/publico")
AQUI = Path(__file__).parent
DESTINO = AQUI / "fotos"


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
    if "--sin-push" in sys.argv or not nuevas:
        return
    git = lambda *a: subprocess.run(["git", "-C", str(AQUI), *a], check=True)
    git("add", "fotos", "fotos.json")
    git("commit", "-m", f"Fotos nuevas: {nuevas}")
    git("push")


if __name__ == "__main__":
    main()
