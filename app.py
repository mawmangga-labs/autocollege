import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import io
import math

st.set_page_config(page_title="Generator Kartu SMAN 1 Batukliang", layout="wide")

# --- Fungsi Helper Font ---
def get_font(font_type, size):
    try:
        # Ganti path font sesuai folder Anda
        path = "fonts/TimesLTStd-Bold.ttf" if font_type == "bold" else "fonts/TimesLTStd-Roman.ttf"
        return ImageFont.truetype(path, int(size))
    except:
        return ImageFont.load_default()

def draw_card(template, row, col_map, boxes, font_size_base):
    img = template.copy()
    draw = ImageDraw.Draw(img)
    
    fields = ["nomor", "nama", "nisn", "ttl", "program"]
    for field in fields:
        x, y, w, h = boxes[field]
        text = str(row[col_map[field]]) if pd.notna(row[col_map[field]]) else ""
        
        # 1. Hapus placeholder (Putih)
        draw.rectangle([x, y, x + w, y + h], fill="white")
        
        # 2. Pengaturan Font
        is_bold = True if field in ["nomor", "nama"] else False
        font = get_font("bold" if is_bold else "regular", font_size_base)
        
        # 3. Render Teks (Vertical Center Alignment)
        bbox = draw.textbbox((0, 0), text, font=font)
        th = bbox[3] - bbox[1]
        # Offset y agar teks berada tepat di tengah box secara vertikal
        draw.text((x, y + (h - th) // 2), text, font=font, fill="black")
        
    return img

# --- UI Utama ---
st.title("🖨️ Generator Kartu Ujian Sekolah")

template_file = st.file_uploader("1. Upload Template Kartu", type=["png", "jpg", "jpeg"])
data_file = st.file_uploader("2. Upload Data (Excel/CSV)", type=["xlsx", "csv"])

if template_file and data_file:
    template = Image.open(template_file).convert("RGB")
    df = pd.read_excel(data_file) if data_file.name.endswith("xlsx") else pd.read_csv(data_file)
    
    st.subheader("⚙️ Konfigurasi Data & Ukuran")
    
    # Grid Kolom Data
    cols = list(df.columns)
    c1, c2, c3 = st.columns(3)
    with c1:
        c_no = st.selectbox("Kolom Nomor Peserta", cols, index=min(0, len(cols)-1))
        c_na = st.selectbox("Kolom Nama Peserta", cols, index=min(1, len(cols)-1))
    with c2:
        c_ni = st.selectbox("Kolom NISN", cols, index=min(2, len(cols)-1))
        c_tt = st.selectbox("Kolom Tempat & Tgl Lahir", cols, index=min(3, len(cols)-1))
    with c3:
        c_pr = st.selectbox("Kolom Program", cols, index=min(4, len(cols)-1))
        # INPUT ANGKA (Ganti Slider)
        font_size = st.number_input("Ukuran Font (Pixel)", min_value=10, max_value=150, value=45, step=1)

    col_map = {"nomor": c_no, "nama": c_na, "nisn": c_ni, "ttl": c_tt, "program": c_pr}

    # KOORDINAT BOXES (X, Y, Width, Height)
    # Angka ini sudah disesuaikan untuk posisi setelah titik dua (:)
    boxes = {
        "nomor":   (475, 410, 460, 45),
        "nama":    (475, 460, 460, 45),
        "nisn":    (475, 510, 460, 45),
        "ttl":     (475, 560, 460, 45),
        "program": (475, 610, 460, 45)
    }

    st.divider()

    # --- Bagian Preview ---
    st.subheader("🔍 Preview Hasil")
    preview_img = draw_card(template, df.iloc[0], col_map, boxes, font_size)
    
    # Menampilkan preview dengan ukuran yang nyaman dilihat
    st.image(preview_img, caption="Contoh data baris pertama", width=600)

    st.info("💡 Pastikan placeholder asli tertutup warna putih sempurna di preview atas.")

    # --- Proses Generate ---
    if st.button("🚀 Generate & Siapkan PDF", use_container_width=True):
        with st.spinner("Sedang memproses seluruh kartu..."):
            all_cards = [draw_card(template, row, col_map, boxes, font_size) for _, row in df.iterrows()]
            
            # Setting Kertas F4 (300 DPI)
            page_w, page_h = 2540, 3900 
            card_w, card_h = template.size
            spacing = 60 # Jarak antar kartu ~0.5cm
            
            total_grid_w = (card_w * 2) + spacing
            total_grid_h = (card_h * 4) + (spacing * 3)
            start_x = (page_w - total_grid_w) // 2
            start_y = (page_h - total_grid_h) // 2

            pages = []
            for i in range(0, len(all_cards), 8):
                page = Image.new("RGB", (page_w, page_h), "white")
                batch = all_cards[i:i+8]
                for j, card in enumerate(batch):
                    pos_x = start_x + (j % 2) * (card_w + spacing)
                    pos_y = start_y + (j // 2) * (card_h + spacing)
                    page.paste(card, (pos_x, pos_y))
                pages.append(page)

            # Membagi link download per 10 Halaman (80 kartu per file)
            st.success(f"Total {len(pages)} halaman berhasil dibuat!")
            
            limit = 10
            for f_idx in range(math.ceil(len(pages) / limit)):
                start_p = f_idx * limit
                end_p = start_p + limit
                pdf_batch = pages[start_p:end_p]
                
                output = io.BytesIO()
                # Simpan dengan resolution 300 agar ukuran fisik saat diprint pas (F4)
                pdf_batch[0].save(
                    output, 
                    format="PDF", 
                    save_all=True, 
                    append_images=pdf_batch[1:] if len(pdf_batch) > 1 else [], 
                    resolution=300.0
                )
                output.seek(0)
                
                st.download_button(
                    label=f"📥 Download Part {f_idx+1} (Halaman {start_p+1}-{min(end_p, len(pages))})",
                    data=output,
                    file_name=f"kartu_ujian_part_{f_idx+1}.pdf",
                    mime="application/pdf",
                    key=f"dl_btn_{f_idx}"
                )
