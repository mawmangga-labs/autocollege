import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import io
import math

st.set_page_config(page_title="Generator Kartu Presisi", layout="wide")

# --- Fungsi Helper Font ---
def get_font(font_type, size):
    try:
        # Sesuaikan path dengan lokasi file font Anda
        path = f"fonts/TimesLTStd-{'Bold' if font_type == 'bold' else 'Roman'}.ttf"
        return ImageFont.truetype(path, int(size))
    except:
        return ImageFont.load_default()

# --- Fungsi Inti Menggambar Kartu ---
def draw_card(template, row, col_map, font_size_base, x_offset_manual, y_offset_manual):
    img = template.copy()
    w_px, h_px = img.size
    draw = ImageDraw.Draw(img)
    
    # Rasio pixel per cm (Berdasarkan dimensi template user 9.5 x 7.5 cm)
    px_per_cm_x = w_px / 9.5
    px_per_cm_y = h_px / 7.5

    # Koordinat CM (Data dari User)
    x_cm_base = 5.37
    y_cm_list = [3.09, 3.51, 3.93, 4.35, 4.78]
    fields = ["nomor", "nama", "nisn", "ttl", "program"]
    
    # Konfigurasi Batas Kotak Putih Dinamis
    right_limit_px = int(9.3 * px_per_cm_x) # Batas aman kanan kartu (9.3cm)
    box_h_px = int(0.42 * px_per_cm_y)      # Tinggi baris
    inner_padding_px = int(0.15 * px_per_cm_x) # Jarak teks dari pinggir kotak putih

    for i, field in enumerate(fields):
        # Titik mulai (X dasar + offset kalibrasi)
        curr_x = int(x_cm_base * px_per_cm_x) + x_offset_manual
        curr_y = int(y_cm_list[i] * px_per_cm_y)
        
        # Lebar kotak putih otomatis menyesuaikan agar tidak "balapan" ke kanan
        dynamic_box_w = right_limit_px - curr_x
        safe_limit_w = dynamic_box_w - (inner_padding_px * 2)
        
        text = str(row[col_map[field]]) if pd.notna(row[col_map[field]]) else ""
        
        # 1. Gambar Kotak Putih (Menghapus Placeholder)
        draw.rectangle([curr_x, curr_y, curr_x + dynamic_box_w, curr_y + box_h_px], fill="white")
        
        # 2. Logika Auto-Shrink (Mengecilkan font jika kepanjangan)
        is_bold = True if field in ["nomor", "nama"] else False
        current_size = font_size_base
        font = get_font("bold" if is_bold else "regular", current_size)
        
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]

        while text_w > safe_limit_w and current_size > 10:
            current_size -= 1
            font = get_font("bold" if is_bold else "regular", current_size)
            bbox = draw.textbbox((0, 0), text, font=font)
            text_w = bbox[2] - bbox[0]

        # 3. Hitung Posisi Akhir (Vertical Centering + Manual Y Offset)
        th = bbox[3] - bbox[1]
        final_y = curr_y + (box_h_px - th) // 2 + y_offset_manual
        
        # Gambar Teks
        draw.text((curr_x + inner_padding_px, final_y), text, font=font, fill="black")
        
    return img

# --- Antarmuka Streamlit (UI) ---
st.title("🖨️ Generator Kartu Ujian - SMAN 1 Batukliang")

template_file = st.file_uploader("1. Upload Template Kartu (9.5 x 7.5 cm)", type=["png", "jpg", "jpeg"])
data_file = st.file_uploader("2. Upload Data Excel/CSV", type=["xlsx", "csv"])

if template_file and data_file:
    template = Image.open(template_file).convert("RGB")
    df = pd.read_excel(data_file) if data_file.name.endswith("xlsx") else pd.read_csv(data_file)
    cols = list(df.columns)
    
    # Fungsi pencari kolom otomatis
    def find_idx(kw, opts):
        for i, o in enumerate(opts):
            if kw.lower() in str(o).lower(): return i
        return 0

    # Layout Utama
    main_left, main_right = st.columns([1, 2])

    with main_left:
        st.subheader("📋 Mapping Data")
        c_no = st.selectbox("Kolom Nomor Peserta", cols, index=find_idx("nomor", cols))
        c_na = st.selectbox("Kolom Nama Peserta", cols, index=find_idx("nama", cols))
        c_ni = st.selectbox("Kolom NISN", cols, index=find_idx("nisn", cols))
        c_tt = st.selectbox("Kolom Tempat Tgl Lahir", cols, index=find_idx("tgl", cols))
        c_pr = st.selectbox("Kolom Program/Jurusan", cols, index=find_idx("program", cols))
        
        st.divider()
        st.info("💡 Klik tombol di bawah setelah kalibrasi preview dirasa pas.")
        generate_btn = st.button("🚀 Generate Semua & Cetak F4", use_container_width=True)

    with main_right:
        st.subheader("🔍 Kalibrasi & Preview")
        
        prev_area, tune_area = st.columns([3, 1])
        
        with tune_area:
            st.write("🔧 **Fine Tuning**")
            f_size = st.number_input("Ukuran Font", 10, 150, 42, help="Ukuran dasar font")
            x_off = st.number_input("Geser X (Pixel)", value=0, step=1, help="Kanan (+), Kiri (-)")
            y_off = st.number_input("Geser Y (Pixel)", value=0, step=1, help="Bawah (+), Atas (-)")
            st.warning("Nama panjang otomatis mengecil dengan padding aman.")

        col_map = {"nomor": c_no, "nama": c_na, "nisn": c_ni, "ttl": c_tt, "program": c_pr}
        
        with prev_area:
            # Preview menggunakan baris pertama data
            preview_img = draw_card(template, df.iloc[0], col_map, f_size, x_off, y_off)
            st.image(preview_img, use_container_width=True, caption="Pratinjau Hasil Kalibrasi")

    # --- Proses Generate PDF ---
    if generate_btn:
        with st.spinner("Memproses seluruh kartu ujian..."):
            # 1. Generate semua gambar kartu
            all_cards = [draw_card(template, row, col_map, f_size, x_off, y_off) for _, row in df.iterrows()]
            
            # 2. Susun ke kertas F4 (300 DPI)
            # Standar F4: 21.5cm x 33cm -> ~2540px x 3900px
            page_w, page_h = 2540, 3900 
            card_w, card_h = template.size
            
            f4_px_per_cm = page_w / 21.5
            spacing = int(0.5 * f4_px_per_cm) # Spasi 0.5 cm
            
            # Hitung Grid agar Center di F4
            grid_w = (card_w * 2) + spacing
            grid_h = (card_h * 4) + (spacing * 3)
            start_x = (page_w - grid_w) // 2
            start_y = (page_h - grid_h) // 2

            pages = []
            for i in range(0, len(all_cards), 8):
                page = Image.new("RGB", (page_w, page_h), "white")
                batch = all_cards[i:i+8]
                for j, card in enumerate(batch):
                    px = start_x + (j % 2) * (card_w + spacing)
                    py = start_y + (j // 2) * (card_h + spacing)
                    page.paste(card, (px, py))
                pages.append(page)

            # 3. Output & Split PDF (Per 10 Halaman)
            st.success(f"Berhasil membuat {len(all_cards)} kartu dalam {len(pages)} halaman.")
            
            limit = 10
            dl_cols = st.columns(3)
            for f_idx in range(math.ceil(len(pages) / limit)):
                out = io.BytesIO()
                batch_pdf = pages[f_idx*limit : (f_idx+1)*limit]
                
                # Simpan PDF
                batch_pdf[0].save(
                    out, 
                    format="PDF", 
                    save_all=True, 
                    append_images=batch_pdf[1:] if len(batch_pdf) > 1 else [], 
                    resolution=300.0
                )
                out.seek(0)
                
                with dl_cols[f_idx % 3]:
                    st.download_button(
                        label=f"📥 Download Part {f_idx+1}", 
                        data=out, 
                        file_name=f"kartu_ujian_part_{f_idx+1}.pdf", 
                        key=f"btn_{f_idx}"
                    )
