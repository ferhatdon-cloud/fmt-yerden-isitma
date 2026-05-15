"""
FMT - Yerden Isıtma Hesabı Masaüstü Programı v1.0
Copyright ©2026 "Ferhat Dön - Mak.Yük.Müh." All rights reserved.

Gereksinimler:
    pip install reportlab

EXE yapmak için (GitHub Actions veya lokal):
    pip install pyinstaller
    pyinstaller --onefile --windowed --name "FMT_YerdenIsitma" fmt_yerden_isitma.py
"""

import sys
import os
import math
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date

# ── PyInstaller uyumlu kaynak yolu ────────────────────────────────────────
def resource_path(relative_path):
    """PyInstaller ile paketlenmiş veya normal çalışmada doğru yolu döndürür."""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# ── reportlab güvenli import ───────────────────────────────────────────────
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    Table, TableStyle, HRFlowable, PageBreak)
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_OK = True
except ImportError:
    REPORTLAB_OK = False

# ─── Sabitler ─────────────────────────────────────────────────────────────
VERSION              = "v1.0"
MAX_MAHAL            = 10
KATLAR               = ["BODRUM", "ZEMIN KAT", "1. KAT", "2. KAT"]
GUC_KATSAYI          = 133.33333          # W/m²  (50°C giriş suyu)
IZOLASYON_PLAKA_M2   = (1215 * 615) / 1_000_000   # ~0.7472 m²/plaka
KOLLEKTOR_MAX_AGIZ   = 12
TERMOSTAT_MAX_AKT    = 5
TERMINAL_MAX_TERM    = 6
BORU_TOP_MT          = 600               # 1 top = 600 mt
BORU_MAX_AGIZ_MT     = 90               # 1 kollektör ağzı max 90 mt

# ─── Renk paleti ──────────────────────────────────────────────────────────
C = {
    "bg":       "#1e2533",
    "panel":    "#252d3d",
    "card":     "#2d3748",
    "accent":   "#3b82f6",
    "accent2":  "#10b981",
    "warn":     "#f59e0b",
    "danger":   "#ef4444",
    "text":     "#f1f5f9",
    "subtext":  "#94a3b8",
    "border":   "#374151",
    "entry_bg": "#1a2235",
    "header":   "#1a2235",
}

# ══════════════════════════════════════════════════════════════════════════
class FMTApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"FMT – Yerden Isitma Hesabi 2026  {VERSION}")
        self.geometry("1320x860")
        self.minsize(1100, 700)
        self.configure(bg=C["bg"])
        self._last_kat_data = {}
        self._last_genel    = {}
        self._setup_style()
        self._build_ui()
        self._hesapla()

    # ─── Style ────────────────────────────────────────────────────────────
    def _setup_style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("TNotebook",        background=C["bg"],    borderwidth=0)
        s.configure("TNotebook.Tab",    background=C["card"],  foreground=C["subtext"],
                    padding=[14, 6],    font=("Segoe UI", 10))
        s.map("TNotebook.Tab",
              background=[("selected", C["accent"])],
              foreground=[("selected", "white")])
        s.configure("TFrame",           background=C["bg"])
        s.configure("Panel.TFrame",     background=C["panel"])
        s.configure("Card.TFrame",      background=C["card"])
        s.configure("TLabel",           background=C["card"],  foreground=C["text"],
                    font=("Segoe UI", 10))
        s.configure("Head.TLabel",      background=C["panel"], foreground=C["text"],
                    font=("Segoe UI", 11, "bold"))
        s.configure("Result.TLabel",    background=C["card"],  foreground=C["accent"],
                    font=("Segoe UI", 11, "bold"))
        s.configure("BigResult.TLabel", background=C["card"],  foreground=C["accent2"],
                    font=("Segoe UI", 14, "bold"))
        s.configure("TEntry",           fieldbackground=C["entry_bg"], foreground=C["text"],
                    insertcolor=C["text"], bordercolor=C["border"])
        s.configure("TButton",          background=C["accent"], foreground="white",
                    font=("Segoe UI", 10, "bold"), relief="flat", padding=[10, 6])
        s.map("TButton",  background=[("active", "#2563eb")])
        s.configure("PDF.TButton",      background="#059669", foreground="white",
                    font=("Segoe UI", 10, "bold"), relief="flat", padding=[10, 6])
        s.map("PDF.TButton", background=[("active", "#047857")])
        s.configure("TScrollbar",       background=C["card"],  troughcolor=C["bg"],
                    arrowcolor=C["subtext"])

    # ─── Ana UI ───────────────────────────────────────────────────────────
    def _build_ui(self):
        # Başlık
        hdr = tk.Frame(self, bg=C["header"], pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="  FMT – YERDEN ISITMA HESABI 2026",
                 bg=C["header"], fg=C["text"],
                 font=("Segoe UI", 15, "bold")).pack(side="left", padx=16)
        tk.Label(hdr, text=f"Ferhat Don – Mak.Yuk.Muh.  {VERSION}",
                 bg=C["header"], fg=C["subtext"],
                 font=("Segoe UI", 9)).pack(side="right", padx=16)

        # Genel bilgiler + butonlar
        gen = tk.Frame(self, bg=C["panel"], pady=6)
        gen.pack(fill="x")
        self._proje_adi = self._lbl_entry(gen, "Proje Adi:", 0, width=28)
        self._mimari    = self._lbl_entry(gen, "Mimarlik:",  1, width=24)
        self._tarih     = self._lbl_entry(gen, "Tarih:",     2, width=14,
                                          default=date.today().strftime("%d.%m.%Y"))
        self._sayi      = self._lbl_entry(gen, "Sayi:",      3, width=8, default="P1")

        btn_frame = tk.Frame(gen, bg=C["panel"])
        btn_frame.grid(row=0, column=8, rowspan=2, padx=12, pady=4)
        ttk.Button(btn_frame, text="  Hesapla",
                   command=self._hesapla).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="  PDF Cikti", style="PDF.TButton",
                   command=self._pdf_cikti).pack(side="left", padx=4)

        # Notebook
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=8, pady=6)

        self._kat_frames  = []
        self._mahal_vars  = {}
        self._ozet_vars   = {}

        for kat in KATLAR:
            frm = ttk.Frame(nb)
            nb.add(frm, text=f"  {kat}  ")
            self._build_kat_tab(frm, kat)
            self._kat_frames.append(frm)

        res_frm = ttk.Frame(nb)
        nb.add(res_frm, text="  SONUCLAR  ")
        self._build_results_tab(res_frm)

        uyari_frm = ttk.Frame(nb)
        nb.add(uyari_frm, text="  UYARILAR  ")
        self._build_uyari_tab(uyari_frm)

    def _lbl_entry(self, parent, label, col, width=18, default=""):
        tk.Label(parent, text=label, bg=C["panel"], fg=C["subtext"],
                 font=("Segoe UI", 9)).grid(row=0, column=col*2, padx=(12,2), pady=4, sticky="e")
        var = tk.StringVar(value=default)
        ttk.Entry(parent, textvariable=var, width=width).grid(
            row=0, column=col*2+1, padx=(0,6), pady=4)
        return var

    # ─── Kat sekmesi ──────────────────────────────────────────────────────
    def _build_kat_tab(self, parent, kat):
        parent.configure(style="Panel.TFrame")

        hdrs  = ["No", "Mahal Adi", "Alan (m2)", "Modulasyon (cm)", "Boru (mt)", "Aktuator", "Termostat"]
        col_w = [4, 22, 10, 14, 12, 10, 10]
        for c, (h, w) in enumerate(zip(hdrs, col_w)):
            tk.Label(parent, text=h, bg=C["header"], fg=C["subtext"],
                     font=("Segoe UI", 9, "bold"), width=w, anchor="center",
                     relief="flat", padx=4, pady=6).grid(
                row=0, column=c, sticky="ew", padx=1, pady=(8,2))

        rows = []
        for i in range(MAX_MAHAL):
            ad_v   = tk.StringVar()
            al_v   = tk.DoubleVar(value=0)
            mod_v  = tk.IntVar(value=12)
            boru_v = tk.StringVar(value="0.0")
            akt_v  = tk.StringVar(value="0")
            term_v = tk.StringVar(value="")
            r = i + 1

            tk.Label(parent, text=str(r), bg=C["card"], fg=C["subtext"],
                     width=4, anchor="center").grid(row=r, column=0, sticky="ew", padx=1, pady=1)
            ttk.Entry(parent, textvariable=ad_v, width=22).grid(
                row=r, column=1, padx=1, pady=1, sticky="ew")

            e_al = ttk.Entry(parent, textvariable=al_v, width=10)
            e_al.grid(row=r, column=2, padx=1, pady=1)
            e_al.bind("<FocusOut>", lambda e: self._hesapla())
            e_al.bind("<Return>",   lambda e: self._hesapla())

            mod_cb = ttk.Combobox(parent, textvariable=mod_v, width=6,
                                  values=[10, 12, 15, 20, 25, 30], state="readonly")
            mod_cb.grid(row=r, column=3, padx=1, pady=1)
            mod_cb.bind("<<ComboboxSelected>>", lambda e: self._hesapla())

            tk.Label(parent, textvariable=boru_v, bg=C["card"], fg=C["accent"],
                     width=12, anchor="center").grid(row=r, column=4, padx=1, pady=1)
            tk.Label(parent, textvariable=akt_v,  bg=C["card"], fg=C["accent2"],
                     width=10, anchor="center").grid(row=r, column=5, padx=1, pady=1)

            term_cb = ttk.Combobox(parent, textvariable=term_v, width=8,
                                   values=["", "Var"], state="readonly")
            term_cb.grid(row=r, column=6, padx=1, pady=1)
            term_cb.bind("<<ComboboxSelected>>", lambda e: self._hesapla())

            rows.append((ad_v, al_v, mod_v, boru_v, akt_v, term_v))

        # Güzergah alanı
        rg = MAX_MAHAL + 1
        tk.Label(parent, text="* Güzergah Alani (m2)", bg=C["card"], fg=C["subtext"],
                 font=("Segoe UI", 9)).grid(row=rg, column=1, pady=(6,2), sticky="w", padx=4)
        guz_v = tk.DoubleVar(value=0)
        e_guz = ttk.Entry(parent, textvariable=guz_v, width=10)
        e_guz.grid(row=rg, column=2, pady=(6,2))
        e_guz.bind("<FocusOut>", lambda e: self._hesapla())
        e_guz.bind("<Return>",   lambda e: self._hesapla())

        # Toplam satırı
        rt = MAX_MAHAL + 2
        tk.Label(parent, text="TOPLAM", bg=C["header"], fg=C["text"],
                 font=("Segoe UI", 10, "bold")).grid(row=rt, column=1, pady=6, padx=8, sticky="w")
        tot_alan = tk.StringVar(value="0")
        tot_boru = tk.StringVar(value="0.0")
        tot_akt  = tk.StringVar(value="0")
        tot_term = tk.StringVar(value="0")
        for col_i, tv in zip([2, 4, 5, 6], [tot_alan, tot_boru, tot_akt, tot_term]):
            tk.Label(parent, textvariable=tv, bg=C["header"], fg=C["accent"],
                     font=("Segoe UI", 10, "bold"), anchor="center").grid(
                row=rt, column=col_i, pady=6, sticky="ew")

        # Kat özet kutusu
        oz_frm = tk.Frame(parent, bg=C["panel"])
        oz_frm.grid(row=rt+1, column=0, columnspan=7, sticky="ew", padx=4, pady=8)
        self._build_kat_ozet(oz_frm, kat)

        self._mahal_vars[kat] = {
            "rows": rows, "guz": guz_v,
            "tot_alan": tot_alan, "tot_boru": tot_boru,
            "tot_akt": tot_akt,   "tot_term": tot_term,
        }

    def _build_kat_ozet(self, parent, kat):
        labels = ["Kollektor Agzi", "Kollektor Dolabi", "Iki Yollu Vana", "Guc (W)"]
        vd = {}
        for i, lbl in enumerate(labels):
            tk.Label(parent, text=lbl+":", bg=C["panel"], fg=C["subtext"],
                     font=("Segoe UI", 9)).grid(row=0, column=i*2, padx=(14,2), pady=6)
            v = tk.StringVar(value="–")
            tk.Label(parent, textvariable=v, bg=C["panel"], fg=C["accent"],
                     font=("Segoe UI", 10, "bold"), width=20).grid(row=0, column=i*2+1, padx=(0,12))
            vd[lbl] = v
        self._ozet_vars[kat] = vd

    # ─── Sonuçlar sekmesi ─────────────────────────────────────────────────
    def _build_results_tab(self, parent):
        parent.configure(style="Panel.TFrame")
        canvas = tk.Canvas(parent, bg=C["panel"], highlightthickness=0)
        sb = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)
        inner = tk.Frame(canvas, bg=C["panel"])
        canvas.create_window((0,0), window=inner, anchor="nw")
        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        self._res_vars = {}
        items = [
            ("Toplam Alan",           "m2",   "BigResult.TLabel"),
            ("Toplam Boru O16mm",     "mt",   "BigResult.TLabel"),
            ("Izolasyon (Plaka)",     "adet", "Result.TLabel"),
            ("Boru Sevk (Top)",       "adet", "Result.TLabel"),
            ("Toplam Aktuator",       "adet", "Result.TLabel"),
            ("Toplam Oda Termostati", "adet", "Result.TLabel"),
            ("Boru Baglanti Rakoru",  "adet", "Result.TLabel"),
            ("Sap Katki Maddesi",     "kg",   "Result.TLabel"),
            ("Sap Katki Sevk",        "adet", "Result.TLabel"),
            ("Izolasyon Bandi",       "mt",   "Result.TLabel"),
            ('Kesme Vanasi 1"',       "adet", "Result.TLabel"),
            ("Terminal Kutusu",       "adet", "Result.TLabel"),
            ("Toplam Guc (50C)",      "kW",   "BigResult.TLabel"),
        ]
        for r, (name, unit, style) in enumerate(items):
            card = tk.Frame(inner, bg=C["card"], padx=16, pady=10)
            card.grid(row=r//3, column=r%3, padx=8, pady=6, sticky="ew")
            inner.columnconfigure(r%3, weight=1)
            tk.Label(card, text=name, bg=C["card"], fg=C["subtext"],
                     font=("Segoe UI", 9)).pack(anchor="w")
            v = tk.StringVar(value="–")
            tk.Label(card, textvariable=v, style=style).pack(anchor="w")
            tk.Label(card, text=unit, bg=C["card"], fg=C["subtext"],
                     font=("Segoe UI", 8)).pack(anchor="w")
            self._res_vars[name] = v

        # Kat güçleri
        guc_card = tk.Frame(inner, bg=C["card"], padx=16, pady=10)
        guc_card.grid(row=len(items)//3+1, column=0, columnspan=3,
                      padx=8, pady=6, sticky="ew")
        tk.Label(guc_card, text="Katlara Gore Guc Dagilimi", bg=C["card"],
                 fg=C["text"], font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0,6))
        self._guc_vars = {}
        guc_row = tk.Frame(guc_card, bg=C["card"])
        guc_row.pack(fill="x")
        for kat in KATLAR:
            f = tk.Frame(guc_row, bg=C["card"], padx=12)
            f.pack(side="left", expand=True)
            tk.Label(f, text=kat, bg=C["card"], fg=C["subtext"],
                     font=("Segoe UI", 9, "bold")).pack()
            v = tk.StringVar(value="–")
            tk.Label(f, textvariable=v, bg=C["card"], fg=C["accent"],
                     font=("Segoe UI", 12, "bold")).pack()
            tk.Label(f, text="W", bg=C["card"], fg=C["subtext"],
                     font=("Segoe UI", 8)).pack()
            self._guc_vars[kat] = v

    # ─── Uyarılar sekmesi ─────────────────────────────────────────────────
    def _build_uyari_tab(self, parent):
        parent.configure(style="Panel.TFrame")
        frm = tk.Frame(parent, bg=C["panel"])
        frm.pack(fill="both", expand=True, padx=16, pady=16)
        self._uyari_text = tk.Text(frm, bg=C["card"], fg=C["text"],
                                   font=("Consolas", 10), relief="flat",
                                   padx=12, pady=10, wrap="word")
        self._uyari_text.pack(fill="both", expand=True)
        self._uyari_text.tag_config("warn",   foreground=C["warn"])
        self._uyari_text.tag_config("danger", foreground=C["danger"])
        self._uyari_text.tag_config("ok",     foreground=C["accent2"])
        self._uyari_text.tag_config("head",   foreground=C["accent"],
                                    font=("Segoe UI", 11, "bold"))

    # ══════════════════════════════════════════════════════════════════════
    # ─── Hesaplama motoru ─────────────────────────────────────────────────
    # ══════════════════════════════════════════════════════════════════════
    def _hesapla(self):
        kat_data = {}
        for kat in KATLAR:
            mv = self._mahal_vars.get(kat)
            if not mv:
                continue
            mahaller = []
            for (ad_v, al_v, mod_v, boru_v, akt_v, term_v) in mv["rows"]:
                try:
                    alan = float(al_v.get())
                except Exception:
                    alan = 0.0
                mod   = int(mod_v.get())
                boru  = (alan / mod) * 100 if mod > 0 else 0.0
                devre = max(1, math.ceil(boru / BORU_MAX_AGIZ_MT)) if boru > 0 else 0
                akt   = devre
                has_term = bool(term_v.get().strip())
                boru_v.set(f"{boru:.1f}")
                akt_v.set(str(akt))
                mahaller.append({
                    "ad": ad_v.get(), "alan": alan, "mod": mod,
                    "boru": boru, "akt": akt, "term": has_term,
                })

            try:
                guz = float(mv["guz"].get())
            except Exception:
                guz = 0.0

            tot_alan = sum(m["alan"] for m in mahaller) + guz
            tot_boru = sum(m["boru"] for m in mahaller)
            tot_akt  = sum(m["akt"]  for m in mahaller)
            tot_term = sum(1 for m in mahaller if m["term"])

            mv["tot_alan"].set(f"{tot_alan:.0f}")
            mv["tot_boru"].set(f"{tot_boru:.1f}")
            mv["tot_akt"].set(str(tot_akt))
            mv["tot_term"].set(str(tot_term))

            kollektor_agiz = tot_akt
            guc      = tot_alan * GUC_KATSAYI
            dolap    = self._dolap_tipi(kollektor_agiz)
            iki_yollu = "Var" if kollektor_agiz > KOLLEKTOR_MAX_AGIZ else "Yok"

            oz = self._ozet_vars.get(kat, {})
            oz.get("Kollektor Agzi",  tk.StringVar()).set(
                str(kollektor_agiz) + ("  (!>12)" if kollektor_agiz > KOLLEKTOR_MAX_AGIZ else ""))
            oz.get("Kollektor Dolabi", tk.StringVar()).set(dolap)
            oz.get("Iki Yollu Vana",   tk.StringVar()).set(iki_yollu)
            oz.get("Guc (W)",          tk.StringVar()).set(f"{guc:,.0f} W")

            kat_data[kat] = {
                "mahaller": mahaller, "guz": guz,
                "tot_alan": tot_alan, "tot_boru": tot_boru,
                "tot_akt":  tot_akt,  "tot_term": tot_term,
                "kollektor_agiz": kollektor_agiz,
                "guc": guc, "dolap": dolap, "iki_yollu": iki_yollu,
            }

        # Genel toplamlar
        genel_alan = sum(d["tot_alan"] for d in kat_data.values())
        genel_boru = sum(d["tot_boru"] for d in kat_data.values())
        genel_akt  = sum(d["tot_akt"]  for d in kat_data.values())
        genel_term = sum(d["tot_term"] for d in kat_data.values())
        genel_guc  = sum(d["guc"]      for d in kat_data.values())

        izolasyon  = math.ceil(genel_alan / IZOLASYON_PLAKA_M2)
        boru_top   = math.ceil(genel_boru / BORU_TOP_MT)
        rakoru     = genel_akt * 2
        sap_kg     = genel_alan * 0.15
        sap_top    = math.ceil(sap_kg / 10)
        izol_bant  = int(genel_alan * 0.8)
        kesme_vana = len(kat_data) * 2
        terminal   = max(1, math.ceil(genel_term / TERMINAL_MAX_TERM)) if genel_term > 0 else 0
        guc_kw     = genel_guc / 1000

        rv = getattr(self, "_res_vars", {})
        rv.get("Toplam Alan",           tk.StringVar()).set(f"{genel_alan:.0f}")
        rv.get("Toplam Boru O16mm",     tk.StringVar()).set(f"{genel_boru:.1f}")
        rv.get("Izolasyon (Plaka)",     tk.StringVar()).set(str(izolasyon))
        rv.get("Boru Sevk (Top)",       tk.StringVar()).set(str(boru_top))
        rv.get("Toplam Aktuator",       tk.StringVar()).set(str(genel_akt))
        rv.get("Toplam Oda Termostati", tk.StringVar()).set(str(genel_term))
        rv.get("Boru Baglanti Rakoru",  tk.StringVar()).set(str(rakoru))
        rv.get("Sap Katki Maddesi",     tk.StringVar()).set(f"{sap_kg:.2f}")
        rv.get("Sap Katki Sevk",        tk.StringVar()).set(str(sap_top))
        rv.get("Izolasyon Bandi",       tk.StringVar()).set(str(izol_bant))
        rv.get('Kesme Vanasi 1"',       tk.StringVar()).set(str(kesme_vana))
        rv.get("Terminal Kutusu",       tk.StringVar()).set(str(terminal))
        rv.get("Toplam Guc (50C)",      tk.StringVar()).set(f"{guc_kw:.2f}")

        for kat, d in kat_data.items():
            self._guc_vars.get(kat, tk.StringVar()).set(f"{d['guc']:,.0f}")

        self._guncelle_uyarilar(kat_data, genel_akt, genel_term, terminal)

        # PDF için son veriyi sakla
        self._last_kat_data = kat_data
        self._last_genel = {
            "alan": genel_alan, "boru": genel_boru, "akt": genel_akt,
            "term": genel_term, "guc_kw": guc_kw,
            "izolasyon": izolasyon, "boru_top": boru_top, "rakoru": rakoru,
            "sap_kg": sap_kg, "sap_top": sap_top, "izol_bant": izol_bant,
            "kesme_vana": kesme_vana, "terminal": terminal,
        }

    def _dolap_tipi(self, agiz):
        if agiz == 0:                   return "–"
        if agiz > KOLLEKTOR_MAX_AGIZ:   return "KONTROL! (>12 agiz)"
        if agiz <= 6:                   return "Tip 1 – 600x700x110"
        if agiz <= 9:                   return "Tip 2 – 800x700x110"
        return                                 "Tip 3 – 1000x700x110"

    def _guncelle_uyarilar(self, kat_data, genel_akt, genel_term, terminal):
        if not hasattr(self, "_uyari_text"):
            return
        t = self._uyari_text
        t.config(state="normal")
        t.delete("1.0", "end")

        def wrt(msg, tag=""):
            t.insert("end", msg + "\n", tag)

        wrt("KONTROL SONUCLARI", "head")
        wrt("")
        uyari = 0
        for kat, d in kat_data.items():
            wrt(f"-- {kat} --", "head")
            if d["kollektor_agiz"] > KOLLEKTOR_MAX_AGIZ:
                wrt(f"  [!] Kollektor agzi {d['kollektor_agiz']} > 12! Kollektoru bolun.", "danger")
                uyari += 1
            else:
                wrt(f"  [OK] Kollektor agzi: {d['kollektor_agiz']}", "ok")

            mahalsiz = [m["ad"] or f"Mahal {i+1}"
                        for i, m in enumerate(d["mahaller"])
                        if m["alan"] > 0 and not m["term"]]
            if mahalsiz:
                wrt(f"  [!] Termostat girilmemis mahal(ler): {', '.join(mahalsiz)}", "warn")
                uyari += 1

            if d["iki_yollu"] == "Var":
                wrt("  [!] Iki Yollu Vana var -> Aktuator ekle, dolap olcusunu kontrol et.", "warn")
                uyari += 1
            wrt("")

        wrt("-- GENEL --", "head")
        if genel_term > 0 and genel_akt / max(genel_term, 1) > TERMOSTAT_MAX_AKT:
            wrt("  [!] Termostata max 5 aktuator baglanabilir! Termostat sayisini artirin.", "danger")
            uyari += 1
        else:
            wrt("  [OK] Termostat / Aktuator orani uygun.", "ok")

        if terminal > 3:
            wrt(f"  [!] Terminal kutusu sayisi {terminal} -> Arttirilmasi gerekebilir.", "warn")
            uyari += 1
        else:
            wrt(f"  [OK] Terminal kutusu: {terminal} adet", "ok")

        wrt("")
        wrt("  Tum kontroller basarili, uyari yok." if uyari == 0
            else f"  Toplam {uyari} uyari bulundu.",
            "ok" if uyari == 0 else "warn")

        wrt("")
        wrt("BILGI NOTU:", "head")
        wrt("  * Franskiche markasina gore hazirlanmistir.")
        wrt("  * 1 adet termostat en fazla 5 adet aktuator kontrol edebilir.")
        wrt("  * 1 adet terminal kutusuna en fazla 6 adet termostat baglanabilir.")
        wrt("  * 1 kollektor agzi ile en fazla 90 mt boru hatti dosenebilir.")
        t.config(state="disabled")

    # ══════════════════════════════════════════════════════════════════════
    # ─── PDF Çıktısı ──────────────────────────────────────────────────────
    # ══════════════════════════════════════════════════════════════════════
    def _pdf_cikti(self):
        if not REPORTLAB_OK:
            messagebox.showerror(
                "Eksik Kutuphane",
                "PDF olusturmak icin reportlab gereklidir.\n\n"
                "Kurmak icin terminale yazin:\n\n"
                "  pip install reportlab"
            )
            return

        self._hesapla()
        if not self._last_kat_data:
            messagebox.showwarning("Uyari", "Once veri giriniz.")
            return

        default_name = (self._proje_adi.get() or "FMT_YerdenIsitma").replace(" ", "_") + ".pdf"
        path = filedialog.asksaveasfilename(
            title="PDF Kaydet",
            defaultextension=".pdf",
            filetypes=[("PDF Dosyasi", "*.pdf")],
            initialfile=default_name,
        )
        if not path:
            return

        try:
            self._build_pdf(path)
            messagebox.showinfo("Basarili", f"PDF kaydedildi:\n{path}")
            # Dosyayı otomatik aç
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                os.system(f'open "{path}"')
            else:
                os.system(f'xdg-open "{path}"')
        except Exception as exc:
            messagebox.showerror("PDF Hatasi", str(exc))

    def _build_pdf(self, path):
        doc = SimpleDocTemplate(
            path, pagesize=A4,
            leftMargin=1.5*cm, rightMargin=1.5*cm,
            topMargin=2*cm,    bottomMargin=2*cm,
        )
        W = A4[0] - 3*cm  # kullanılabilir genişlik

        # ── Stiller ──
        st_title = ParagraphStyle("title", fontSize=14, alignment=TA_CENTER,
                                  fontName="Helvetica-Bold",
                                  textColor=colors.HexColor("#1e3a5f"), spaceAfter=4)
        st_sub   = ParagraphStyle("sub",   fontSize=9,  alignment=TA_CENTER,
                                  fontName="Helvetica",
                                  textColor=colors.HexColor("#555555"), spaceAfter=2)
        st_sec   = ParagraphStyle("sec",   fontSize=11, fontName="Helvetica-Bold",
                                  textColor=colors.HexColor("#1e3a5f"),
                                  spaceBefore=10, spaceAfter=4)
        st_norm  = ParagraphStyle("norm",  fontSize=9,  fontName="Helvetica",
                                  textColor=colors.black)
        st_warn  = ParagraphStyle("warn",  fontSize=9,  fontName="Helvetica-Bold",
                                  textColor=colors.HexColor("#c05000"))
        st_ok    = ParagraphStyle("ok",    fontSize=9,  fontName="Helvetica-Bold",
                                  textColor=colors.HexColor("#006630"))
        st_foot  = ParagraphStyle("foot",  fontSize=7,  alignment=TA_CENTER,
                                  fontName="Helvetica",
                                  textColor=colors.HexColor("#888888"))

        HDR_BG  = colors.HexColor("#1e3a5f")
        HDR_FG  = colors.white
        ROW_ALT = colors.HexColor("#eaf0fb")
        ROW_NRM = colors.HexColor("#f7f9fd")
        TOT_BG  = colors.HexColor("#c8daf5")

        def tbl_style_base(n_data, has_total=True):
            cmds = [
                ("BACKGROUND",    (0,0), (-1,0),  HDR_BG),
                ("TEXTCOLOR",     (0,0), (-1,0),  HDR_FG),
                ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
                ("FONTSIZE",      (0,0), (-1,-1), 8),
                ("ALIGN",         (0,0), (-1,-1), "CENTER"),
                ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
                ("TOPPADDING",    (0,0), (-1,-1), 4),
                ("BOTTOMPADDING", (0,0), (-1,-1), 4),
                ("GRID",          (0,0), (-1,-1), 0.3, colors.HexColor("#cccccc")),
                ("ROWBACKGROUNDS",(0,1), (-1, n_data), [ROW_NRM, ROW_ALT]),
            ]
            if has_total:
                cmds += [
                    ("BACKGROUND", (0,-1), (-1,-1), TOT_BG),
                    ("FONTNAME",   (0,-1), (-1,-1), "Helvetica-Bold"),
                ]
            return TableStyle(cmds)

        story = []

        # ── Başlık ──────────────────────────────────────────────────────
        story.append(Paragraph("FMT – YERDEN ISITMA HESABI", st_title))
        story.append(Paragraph(
            "Ferhat Don – Mak.Yuk.Muh.  |  Copyright &copy;2026  |  Franskiche", st_sub))
        story.append(HRFlowable(width=W, thickness=1.5,
                                color=colors.HexColor("#1e3a5f")))
        story.append(Spacer(1, 6))

        # Proje bilgi tablosu
        bilgi = [
            ["Proje Adi:", self._proje_adi.get() or "–",
             "Mimarlik:",  self._mimari.get() or "–"],
            ["Tarih:",     self._tarih.get() or "–",
             "Sayi:",      self._sayi.get() or "–"],
        ]
        tb_bilgi = Table(bilgi, colWidths=[3*cm, 6*cm, 3*cm, 6*cm])
        tb_bilgi.setStyle(TableStyle([
            ("FONTNAME",      (0,0), (0,-1), "Helvetica-Bold"),
            ("FONTNAME",      (2,0), (2,-1), "Helvetica-Bold"),
            ("FONTSIZE",      (0,0), (-1,-1), 9),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
            ("TOPPADDING",    (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ]))
        story.append(tb_bilgi)
        story.append(Spacer(1, 10))

        # ── Her kat için detay tablosu ───────────────────────────────────
        for kat, d in self._last_kat_data.items():
            story.append(Paragraph(kat, st_sec))

            hdrs_pdf = ["No", "Mahal Adi", "Alan\n(m2)", "Mod.\n(cm)",
                        "Boru\n(mt)", "Akt.", "Termostat"]
            data = [hdrs_pdf]
            for i, m in enumerate(d["mahaller"]):
                if m["alan"] <= 0:
                    continue
                data.append([
                    str(i+1),
                    m["ad"] or f"Mahal {i+1}",
                    f"{m['alan']:.0f}",
                    str(m["mod"]),
                    f"{m['boru']:.1f}",
                    str(m["akt"]),
                    "Var" if m["term"] else "–",
                ])
            if d["guz"] > 0:
                data.append(["*", "Güzergah Alani", f"{d['guz']:.0f}", "–", "–", "–", "–"])
            data.append(["", "TOPLAM",
                         f"{d['tot_alan']:.0f}", "",
                         f"{d['tot_boru']:.1f}",
                         str(d["tot_akt"]),
                         str(d["tot_term"])])

            cw = [0.7*cm, 4.8*cm, 1.8*cm, 1.8*cm, 2*cm, 1.8*cm, 2.1*cm]
            tb = Table(data, colWidths=cw, repeatRows=1)
            tb.setStyle(tbl_style_base(len(data)-2))
            story.append(tb)
            story.append(Spacer(1, 4))

            # Kat özet satırı
            ozet = [
                ["Kollektor Agzi", "Kollektor Dolabi", "Iki Yollu Vana", "Guc (W)"],
                [
                    str(d["kollektor_agiz"]) +
                    (" (!>12)" if d["kollektor_agiz"] > KOLLEKTOR_MAX_AGIZ else ""),
                    d["dolap"],
                    d["iki_yollu"],
                    f"{d['guc']:,.0f}",
                ],
            ]
            tb2 = Table(ozet, colWidths=[W/4]*4)
            tb2.setStyle(TableStyle([
                ("BACKGROUND",    (0,0), (-1,0),  colors.HexColor("#3b5a8f")),
                ("TEXTCOLOR",     (0,0), (-1,0),  colors.white),
                ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
                ("FONTSIZE",      (0,0), (-1,-1), 8),
                ("ALIGN",         (0,0), (-1,-1), "CENTER"),
                ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
                ("GRID",          (0,0), (-1,-1), 0.3, colors.HexColor("#cccccc")),
                ("BACKGROUND",    (0,1), (-1,1),  colors.HexColor("#dce8f8")),
                ("TOPPADDING",    (0,0), (-1,-1), 5),
                ("BOTTOMPADDING", (0,0), (-1,-1), 5),
            ]))
            story.append(tb2)
            story.append(Spacer(1, 12))

        # ── Genel Sonuçlar ───────────────────────────────────────────────
        story.append(PageBreak())
        story.append(Paragraph("GENEL SONUCLAR", st_sec))
        story.append(HRFlowable(width=W, thickness=1,
                                color=colors.HexColor("#1e3a5f")))
        story.append(Spacer(1, 6))

        g = self._last_genel
        sonuc_data = [
            ["Malzeme / Kalem", "Miktar", "Birim", "Aciklama"],
            ["Toplam Alan",            f"{g['alan']:.0f}",    "m2",   ""],
            ["Toplam Boru O16 mm",     f"{g['boru']:.1f}",   "mt",
             f"Sevk: {g['boru_top']} Top (1 Top = 600 mt)"],
            ["Izolasyon Plakasi",      str(g["izolasyon"]),  "adet", "MD-1215x615x45 mm"],
            ["Toplam Aktuator",        str(g["akt"]),        "adet", ""],
            ["Toplam Oda Termostati",  str(g["term"]),       "adet", ""],
            ["Boru Baglanti Rakoru",   str(g["rakoru"]),     "adet", "Kose + Düz"],
            ["Sap Katki Maddesi",      f"{g['sap_kg']:.1f}", "kg",
             f"Sevk: {g['sap_top']} paket (10 kg/paket)"],
            ["Izolasyon Bandi",        str(g["izol_bant"]),  "mt",   ""],
            ['Kesme Vanasi 1"',        str(g["kesme_vana"]), "adet", ""],
            ["Terminal Kutusu",        str(g["terminal"]),   "adet", "Max 6 termostat/kutu"],
            ["TOPLAM GUC (50 C giris)","","", ""],   # ayraç
            ["",                       f"{g['guc_kw']:.2f}", "kW",   "Giris Suyu 50 degC"],
        ]
        cw_s = [5.5*cm, 2.2*cm, 1.5*cm, W - 9.2*cm]
        tb_s = Table(sonuc_data, colWidths=cw_s, repeatRows=1)
        base_s = tbl_style_base(len(sonuc_data)-2, has_total=False)
        base_s.add("BACKGROUND", (0,-2), (-1,-2), colors.HexColor("#1e3a5f"))
        base_s.add("TEXTCOLOR",  (0,-2), (-1,-2), colors.white)
        base_s.add("FONTNAME",   (0,-2), (-1,-2), "Helvetica-Bold")
        base_s.add("BACKGROUND", (0,-1), (-1,-1), colors.HexColor("#c8daf5"))
        base_s.add("FONTNAME",   (0,-1), (-1,-1), "Helvetica-Bold")
        base_s.add("FONTSIZE",   (0,-1), (-1,-1), 10)
        tb_s.setStyle(base_s)
        story.append(tb_s)
        story.append(Spacer(1, 12))

        # Kat güç tablosu
        story.append(Paragraph("Katlara Gore Guc Dagilimi", st_sec))
        kat_list  = list(self._last_kat_data.keys())
        guc_hdr   = ["Kat"] + kat_list
        guc_vals  = ["Guc (W)"] + [f"{self._last_kat_data[k]['guc']:,.0f}" for k in kat_list]
        tb_g = Table([guc_hdr, guc_vals], colWidths=[W/(len(kat_list)+1)]*(len(kat_list)+1))
        tb_g.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0),  HDR_BG),
            ("TEXTCOLOR",     (0,0), (-1,0),  HDR_FG),
            ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
            ("FONTSIZE",      (0,0), (-1,-1), 9),
            ("ALIGN",         (0,0), (-1,-1), "CENTER"),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
            ("GRID",          (0,0), (-1,-1), 0.3, colors.HexColor("#cccccc")),
            ("BACKGROUND",    (0,1), (-1,1),  ROW_ALT),
            ("TOPPADDING",    (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ]))
        story.append(tb_g)
        story.append(Spacer(1, 14))

        # ── Kontrol / Uyarılar ───────────────────────────────────────────
        story.append(Paragraph("KONTROL VE UYARILAR", st_sec))
        story.append(HRFlowable(width=W, thickness=1,
                                color=colors.HexColor("#1e3a5f")))
        story.append(Spacer(1, 4))

        uyari_toplam = 0
        for kat, d in self._last_kat_data.items():
            story.append(Paragraph(f"<b>{kat}</b>", st_norm))
            if d["kollektor_agiz"] > KOLLEKTOR_MAX_AGIZ:
                story.append(Paragraph(
                    f"  [!] Kollektor agzi {d['kollektor_agiz']} > 12! Kollektoru bolun.", st_warn))
                uyari_toplam += 1
            else:
                story.append(Paragraph(
                    f"  [OK] Kollektor agzi: {d['kollektor_agiz']}", st_ok))

            mahalsiz = [m["ad"] or f"Mahal {i+1}"
                        for i, m in enumerate(d["mahaller"])
                        if m["alan"] > 0 and not m["term"]]
            if mahalsiz:
                story.append(Paragraph(
                    f"  [!] Termostat girilmemis: {', '.join(mahalsiz)}", st_warn))
                uyari_toplam += 1

            if d["iki_yollu"] == "Var":
                story.append(Paragraph(
                    "  [!] Iki Yollu Vana var – Aktuator ekle, dolap olcusunu kontrol et.",
                    st_warn))
                uyari_toplam += 1

        story.append(Paragraph("<b>GENEL</b>", st_norm))
        g_akt  = self._last_genel["akt"]
        g_term = self._last_genel["term"]
        g_term_k = self._last_genel["terminal"]
        if g_term > 0 and g_akt / max(g_term, 1) > TERMOSTAT_MAX_AKT:
            story.append(Paragraph(
                "  [!] Termostata max 5 aktuator baglanabilir! Termostat sayisini artirin.",
                st_warn))
            uyari_toplam += 1
        else:
            story.append(Paragraph("  [OK] Termostat / Aktuator orani uygun.", st_ok))

        story.append(Spacer(1, 8))
        if uyari_toplam == 0:
            story.append(Paragraph("Tum kontroller basarili – uyari yok.", st_ok))
        else:
            story.append(Paragraph(f"Toplam {uyari_toplam} uyari bulundu.", st_warn))

        # Bilgi notu
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width=W, thickness=0.5,
                                color=colors.HexColor("#aaaaaa")))
        for b in [
            "Franskiche markasina gore hazirlanmistir.",
            "1 adet termostat en fazla 5 adet aktuator kontrol edebilir.",
            "1 adet terminal kutusuna en fazla 6 adet termostat baglanabilir.",
            "1 kollektor agzi ile en fazla 90 mt boru hatti dosenebilir.",
        ]:
            story.append(Paragraph(f"• {b}", st_norm))

        # Dipnot
        story.append(Spacer(1, 16))
        story.append(HRFlowable(width=W, thickness=0.5,
                                color=colors.HexColor("#aaaaaa")))
        story.append(Paragraph(
            f'Copyright &copy;2026 "Ferhat Don – Mak.Yuk.Muh."  |  '
            f'Olusturulma: {date.today().strftime("%d.%m.%Y")}  |  {VERSION}',
            st_foot))

        doc.build(story)


# ══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = FMTApp()
    app.mainloop()
