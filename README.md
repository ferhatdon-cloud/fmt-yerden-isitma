# FMT – Yerden Isıtma Hesabı 2026

> **Ferhat Dön – Mak.Yük.Müh.** tarafından geliştirilmiştir.  
> Copyright ©2026 – Tüm hakları saklıdır.

---

## Hakkında

FMT Yerden Isıtma Hesabı, Franskiche markası esas alınarak hazırlanmış, yerden ısıtma sistemleri için boru, aktüatör, kollektör, termostat ve malzeme miktarlarını otomatik hesaplayan bir masaüstü uygulamasıdır.

---

## Özellikler

- 4 kat (Bodrum, Zemin Kat, 1. Kat, 2. Kat) için ayrı ayrı mahal girişi
- Her mahalde alan, modülasyon, boru boyu, aktüatör hesabı
- Kollektör ağzı, dolap tipi ve iki yollu vana tespiti
- Genel sonuçlar: boru topu, izolasyon plakası, şap katkısı, terminal kutusu vb.
- Otomatik kontrol ve uyarı sistemi
- **PDF çıktısı** – tek tıkla profesyonel rapor oluşturma
- Koyu tema arayüz

---

## Kurulum ve Çalıştırma

### Gereksinimler

- Python 3.10 veya üzeri
- `tkinter` (Python ile birlikte gelir)
- `reportlab` (PDF çıktısı için)

### Adımlar

```bash
# 1. Repoyu klonlayın
git clone https://github.com/KULLANICI_ADI/fmt-yerden-isitma.git
cd fmt-yerden-isitma

# 2. Bağımlılıkları kurun
pip install -r requirements.txt

# 3. Programı başlatın
python fmt_yerden_isitma.py
```

---

## EXE Olarak İndirme (Windows)

Kaynak kodu derlemeye gerek yoktur.  
GitHub Actions her `main` push'unda otomatik olarak Windows EXE üretir.

**İndirme adımları:**

1. Bu reponun üst menüsünde **Actions** sekmesine tıklayın
2. Sol taraftan **Build EXE** iş akışını seçin
3. En son başarılı çalışmaya tıklayın
4. Sayfanın altındaki **Artifacts** bölümünden `FMT_YerdenIsitma_Windows` dosyasını indirin
5. ZIP içinden `FMT_YerdenIsitma.exe` dosyasını çıkarıp çalıştırın

> EXE dosyası ek kurulum gerektirmez, doğrudan çalışır.

---

## Kendiniz Derlemek İsterseniz

```bash
pip install pyinstaller reportlab
pyinstaller --onefile --windowed --name "FMT_YerdenIsitma" fmt_yerden_isitma.py
# Çıktı: dist/FMT_YerdenIsitma.exe
```

---

## Hesaplama Mantığı

| Parametre | Formül |
|---|---|
| Boru uzunluğu | `(Alan / Modülasyon) × 100` mt |
| Aktüatör / Devre sayısı | `ceil(Boru / 90 mt)` |
| Isıtma gücü | `Alan × 133.33 W/m²` (50°C giriş) |
| İzolasyon plakası | `ceil(Alan / 0.7472 m²)` adet |
| Şap katkı maddesi | `Alan × 0.15 kg/m²` |
| İzolasyon bandı | `Alan × 0.8 mt/m²` |

---

## Teknik Notlar

- 1 kollektör ağzı → max **90 mt** boru
- 1 kollektör → max **12 ağız**
- 1 termostat → max **5 aktüatör**
- 1 terminal kutusu → max **6 termostat**
- Franskiche markasına göre hazırlanmıştır

---

## Dosya Yapısı

```
fmt-yerden-isitma/
├── fmt_yerden_isitma.py      # Ana program
├── requirements.txt          # Python bağımlılıkları
├── .github/
│   └── workflows/
│       └── build.yml         # GitHub Actions – otomatik EXE build
└── README.md
```

---

## Lisans

Copyright ©2026 **Ferhat Dön – Mak.Yük.Müh.**  
Bu yazılım özel kullanım içindir. İzinsiz dağıtımı ve değiştirilmesi yasaktır.
