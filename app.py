import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import io

st.set_page_config(page_title="Generator Kartu F4", layout="centered")
st.title("🖨️ Generator Kartu Peserta (Grid 2x4)")

# --- Fungsi Helper ---
def get_font(font_type, size):
    try:
        # Gunakan path font yang benar atau fallback ke default
        path = "fonts/TimesLTStd-Bold.ttf" if font_type == "bold" else "fonts/TimesLTStd-Roman.ttf"
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

def draw_text_autofit(draw, text, box, bold=False):
    x, y, w, h = box
    text = str(text) if text else ""
    
    # 1. TUTUP PLACEHOLDER (Gunakan warna background template, asumsi putih)
    # Tips: Jika template bukan putih, ganti "white" dengan kode RGB backgroundnya
    draw.rectangle([x, y, x + w, y + h], fill="white")

    # 2. CARI UKURAN FONT TERBAIK
    best_size = 10
    for size in range(40, 8, -1):
        font = get_font("bold" if bold else "regular", size)
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        if tw <= w and th <= h:
            best_size = size
            break
    
    font = get_font("bold" if bold else "regular", best_size)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    
    # Render teks di tengah kotak secara vertikal
    draw.text((x, y + (h - th) // 2), text, font=font, fill="black")

# --- UI Upload ---
template_file = st.file_uploader("1. Upload Template Kartu", type=["png", "jpg", "jpeg"])
data_file = st.file_uploader("2. Upload Data (Excel/CSV)", type=["xlsx", "csv"])

if template_file and data_file:
    template = Image.open(template_file).convert("RGB")
    df = pd.read_excel(data_file) if data_file.name.endswith("xlsx") else pd.read_csv(data_file)
    
    st.info(f"Ukuran Template: {template.size[0]}px x {template.size[1]}px")
    
    col1, col2 = st.columns(2)
    with col1:
        col_nomor = st.selectbox("Kolom Nomor", df.columns)
        col_nama = st.selectbox("Kolom Nama", df.columns)
        col_nisn = st.selectbox("Kolom NISN", df.columns)
    with col2:
        col_ttl = st.selectbox("Kolom TTL", df.columns)
        col_program = st.selectbox("Kolom Program", df.columns)

    # PENTING: Pastikan koordinat ini menutupi teks {{placeholder}} di template Anda
    boxes = {
        "nomor": (540, 410, 480, 45),
        "nama": (540, 460, 480, 45),
        "nisn": (540, 510, 480, 45),
        "ttl": (540, 560, 480, 45),
        "program": (540, 610, 480, 45)
    }

    if st.button("🚀 Generate PDF Siap Cetak"):
        with st.spinner("Sedang memproses kartu..."):
            cards = []
            for _, row in df.iterrows():
                img = template.copy()
                draw = ImageDraw.Draw(img)
                
                # Gambar data ke tiap box
                draw_text_autofit(draw, row[col_nomor], boxes["nomor"], bold=True)
                draw_text_autofit(draw, row[col_nama], boxes["nama"])
                draw_text_autofit(draw, row[col_nisn], boxes["nisn"])
                draw_text_autofit(draw, row[col_ttl], boxes["ttl"])
                draw_text_autofit(draw, row[col_program], boxes["program"])
                cards.append(img)

            if not cards:
                st.error("Tidak ada data untuk diproses.")
            else:
                # KONFIGURASI KERTAS F4 (300 DPI)
                # F4 = 215mm x 330mm -> ~2540px x 3900px
                page_w, page_h = 2540, 3900 
                card_w, card_h = template.size
                
                # Jarak 0.5cm pada 300 DPI adalah sekitar 60 pixel
                spacing = 60 
                
                # Hitung dimensi total grid (2 kolom x 4 baris)
                total_grid_w = (card_w * 2) + spacing
                total_grid_h = (card_h * 4) + (spacing * 3)
                
                # Margin agar posisi grid CENTER di kertas
                margin_x = (page_w - total_grid_w) // 2
                margin_y = (page_h - total_grid_h) // 2

                pages = []
                for i in range(0, len(cards), 8):
                    # Buat halaman baru (Canvas Putih)
                    page = Image.new("RGB", (page_w, page_h), "white")
                    batch = cards[i:i+8]
                    
                    for j, card in enumerate(batch):
                        col = j % 2
                        row = j // 2
                        
                        pos_x = margin_x + (col * (card_w + spacing))
                        pos_y = margin_y + (row * (card_h + spacing))
                        
                        page.paste(card, (pos_x, pos_y))
                    
                    pages.append(page)

                # Export ke PDF
                if pages:
                    pdf_output = io.BytesIO()
                    pages[0].save(
                        pdf_output, 
                        format="PDF", 
                        save_all=True, 
                        append_images=pages[1:] if len(pages) > 1 else []
                    )
                    st.success(f"Berhasil membuat {len(df)} kartu dalam {len(pages)} halaman!")
                    st.download_button(
                        label="📥 Download PDF",
                        data=pdf_output.getvalue(),
                        file_name="kartu_peserta_F4.pdf",
                        mime="application/pdf"
                    )
