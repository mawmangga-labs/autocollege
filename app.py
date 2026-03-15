import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import io

# Judul
st.title("Generator Kartu Peserta")

# Helper fonts (Pastikan file font tersedia di folder /fonts)
def font_regular(size):
    try:
        return ImageFont.truetype("fonts/TimesLTStd-Roman.ttf", size)
    except:
        return ImageFont.load_default()

def font_bold(size):
    try:
        return ImageFont.truetype("fonts/TimesLTStd-Bold.ttf", size)
    except:
        return ImageFont.load_default()

def draw_text_autofit(draw, text, box, bold=False):
    x, y, w, h = box
    
    # 1. TUTUP PLACEHOLDER ASLI (Background Clear)
    # Kita buat rectangle putih untuk "menghapus" {{teks}}
    draw.rectangle([x, y, x + w, y + h], fill="white")

    # 2. DRAW TEKS BARU
    # Gunakan range size yang lebih besar agar terlihat jelas
    for size in range(35, 10, -1): 
        font = font_bold(size) if bold else font_regular(size)
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        if tw <= w and th <= h:
            # Render teks (sedikit offset y agar center secara vertikal di box)
            draw.text((x, y + (h - th) // 2), text, font=font, fill="black")
            return
    draw.text((x, y), text, font=font_regular(10), fill="black")

# --- UI Upload ---
template_file = st.file_uploader("Upload Template", type=["png", "jpg", "jpeg"])
data_file = st.file_uploader("Upload Excel / CSV", type=["xlsx", "csv"])

if template_file and data_file:
    template = Image.open(template_file).convert("RGB")
    df = pd.read_excel(data_file) if data_file.name.endswith("xlsx") else pd.read_csv(data_file)
    
    cols = df.columns
    col_nomor = st.selectbox("Kolom Nomor", cols)
    col_nama = st.selectbox("Kolom Nama", cols)
    col_nisn = st.selectbox("Kolom NISN", cols)
    col_ttl = st.selectbox("Kolom TTL", cols)
    col_program = st.selectbox("Kolom Program", cols)

    # Sesuaikan koordinat ini dengan hasil crop template kamu (X, Y, Width, Height)
    # Tips: Koordinat ini harus menutupi {{nomor}} dst.
    boxes = {
        "nomor": (540, 410, 480, 45),
        "nama": (540, 460, 480, 45),
        "nisn": (540, 510, 480, 45),
        "ttl": (540, 560, 480, 45),
        "program": (540, 610, 480, 45)
    }

    if st.button("Generate & Merge ke F4"):
        cards = []
        for _, row in df.iterrows():
            img = template.copy()
            draw = ImageDraw.Draw(img)
            draw_text_autofit(draw, str(row[col_nomor]), boxes["nomor"], bold=True)
            draw_text_autofit(draw, str(row[col_nama]), boxes["nama"])
            draw_text_autofit(draw, str(row[col_nisn]), boxes["nisn"])
            draw_text_autofit(draw, str(row[col_ttl]), boxes["ttl"])
            draw_text_autofit(draw, str(row[col_program]), boxes["program"])
            cards.append(img)

        # SETTING KERTAS F4 (300 DPI)
        page_w, page_h = 2540, 3900 # Ukuran standar F4 dlm pixel
        card_w, card_h = template.size # Pakai ukuran asli template
        
        spacing = 60 # Jarak antar kartu (~0.5cm)
        
        # Hitung grid 2x4
        grid_w = (card_w * 2) + spacing
        grid_h = (card_h * 4) + (spacing * 3)
        
        # Hitung margin agar Center
        start_x = (page_w - grid_w) // 2
        start_y = (page_h - grid_h) // 2

        pages = []
        for i in range(0, len(cards), 8):
            page = Image.new("RGB", (page_w, page_h), "white")
            batch = cards[i:i+8]
            
            for j, card in enumerate(batch):
                col = j % 2
                row = j // 2
                
                pos_x = start_x + (col * (card_w + spacing))
                pos_y = start_y + (row * (card_h + spacing))
                
                page.paste(card, (pos_x, pos_y))
            pages.append(page)

        # Save PDF
        pdf_bytes = io.BytesIO()
        pages[0].save(pdf_bytes, format="PDF", save_all=True, append_images=pages[1:])
        st.download_button("Download Hasil Cetak F4", pdf_bytes.getvalue(), "kartu_siap_cetak.pdf")
