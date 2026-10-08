#!/usr/bin/env python3
"""PDF zu Foto – wandelt jede Folie einer PDF in ein FullHD-taugliches PNG um.

Abhängigkeit:  pip3 install pymupdf
Start:         python3 pdf_zu_foto.py
"""

import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import fitz  # PyMuPDF

# Zielbox: Jede Folie wird so skaliert, dass sie vollständig in 1920x1080 passt
# (Seitenverhältnis bleibt erhalten, egal welches Format die PDF hat).
ZIEL_BREITE = 1920
ZIEL_HOEHE = 1080


def konvertiere(pdf_pfad, fortschritt=lambda i, n: None):
    """Rendert alle Seiten. Gibt (ausgabeort, anzahl) zurück."""
    ordner = os.path.dirname(pdf_pfad)
    name = os.path.splitext(os.path.basename(pdf_pfad))[0]

    with fitz.open(pdf_pfad) as doc:
        n = doc.page_count
        if n == 0:
            raise ValueError("Die PDF enthält keine Seiten.")

        if n == 1:
            ziel_ordner = ordner
        else:
            ziel_ordner = os.path.join(ordner, name)
            os.makedirs(ziel_ordner, exist_ok=True)

        for i, seite in enumerate(doc, start=1):
            rect = seite.rect  # berücksichtigt bereits die Seitenrotation
            if rect.width <= 0 or rect.height <= 0:
                raise ValueError(f"Seite {i} hat ungültige Maße.")

            zoom = min(ZIEL_BREITE / rect.width, ZIEL_HOEHE / rect.height)
            pix = seite.get_pixmap(
                matrix=fitz.Matrix(zoom, zoom),
                colorspace=fitz.csRGB,
                alpha=False,  # weißer Hintergrund statt Transparenz
            )

            datei = f"{name}_foto.png" if n == 1 else f"{name}_foto{i}.png"
            pix.save(os.path.join(ziel_ordner, datei))
            fortschritt(i, n)

    return ziel_ordner, n


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PDF zu Foto")
        self.geometry("420x220")
        self.resizable(False, False)

        rahmen = ttk.Frame(self, padding=20)
        rahmen.pack(fill="both", expand=True)

        ttk.Label(
            rahmen,
            text="Wandelt jede Folie einer PDF\nin ein Foto (FullHD) um.",
            justify="center",
        ).pack(pady=(0, 15))

        self.knopf = ttk.Button(rahmen, text="PDF auswählen", command=self.waehle_pdf)
        self.knopf.pack(ipadx=20, ipady=6)

        self.balken = ttk.Progressbar(rahmen, mode="determinate", length=300)
        self.balken.pack(pady=(20, 5))

        self.status = ttk.Label(rahmen, text="Bereit.")
        self.status.pack()

    def waehle_pdf(self):
        pfad = filedialog.askopenfilename(
            title="PDF auswählen",
            filetypes=[("PDF-Dateien", "*.pdf"), ("Alle Dateien", "*.*")],
        )
        if not pfad:
            return

        self.knopf.state(["disabled"])
        self.balken["value"] = 0
        self.status.config(text="Konvertiere …")
        threading.Thread(target=self._arbeite, args=(pfad,), daemon=True).start()

    def _arbeite(self, pfad):
        def fortschritt(i, n):
            self.after(0, self._update, i, n)

        try:
            ziel, n = konvertiere(pfad, fortschritt)
            self.after(0, self._fertig, ziel, n)
        except Exception as e:  # noqa: BLE001
            self.after(0, self._fehler, str(e))

    def _update(self, i, n):
        self.balken["value"] = i / n * 100
        self.status.config(text=f"Folie {i} von {n}")

    def _fertig(self, ziel, n):
        self.knopf.state(["!disabled"])
        self.status.config(text=f"Fertig: {n} Foto(s) erstellt.")
        messagebox.showinfo("Fertig", f"{n} Foto(s) gespeichert in:\n{ziel}")
        os.system(f'open "{ziel}"')  # Finder öffnen

    def _fehler(self, text):
        self.knopf.state(["!disabled"])
        self.status.config(text="Fehler.")
        messagebox.showerror("Fehler", text)


if __name__ == "__main__":
    App().mainloop()
