import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import io
import math

st.set_page_config(page_title="Generator Kartu Presisi", layout="wide")

def get_font(font_type, size):
    try:
        path = "fonts/TimesLTStd-Bold.ttf" if font_type == "bold" else "fonts/TimesLTStd-Roman.ttf"
        return ImageFont.truetype(path, int(size))
    except:
        return ImageFont.load_default()

def draw_card(template, row, col_map, font_size_base, x_offset_manual, y_offset_manual):
    img = template.copy()
    w_px, h_px = img.size
    draw = ImageDraw.Draw(img)
    
    # Rasio pixel per cm (Asumsi template 9.5 x 7.5 cm)
    px_per_cm_x = w_px / 9.5
    px_per_cm_y = h_px / 7.5

    # Koordinat CM dari User
    x_cm = 5.37
    y_cm_list = [3.09, 3.51, 3.93, 4.35, 4.78]
    fields = ["nomor", "nama", "nisn", "ttl", "program"]
    
    # Ukuran box pembersih (lebar 4cm, tinggi disesuaikan)
    box_w_px = int(4.0 * px_per_cm_x)
    box_h_px = int(0.42 * px_per_cm_y)

    for i, field in enumerate(fields):
        # Konversi CM ke Pixel + Manual Offset X
        curr_x = int(x_cm * px_per_cm_x) + x_offset_manual
        curr_y = int(y_cm_list[i] * px_per_cm_y)
        
        text = str(row[col_map[field]]) if pd.notna(row[col_map[field]]) else ""
        
        # 1. Hapus Placeholder (Warna Putih)
        draw.rectangle([curr_x, curr_y, curr_x + box_w_px, curr_y + box_h_px], fill="white")
        
        # 2. Setup Font
        is_bold = True if field in ["nomor", "nama"] else False
        font = get_font("bold" if is_bold else "regular", font_size_base)
        
        # 3. Hitung Posisi Teks agar Center secara Vertikal di dalam Box
        bbox = draw.textbbox((0, 0), text, font=font)
        th = bbox[3] - bbox[1]
        
        # final_y menggunakan Manual Offset Y
        final_y = curr_y + (box_h_px - th) // 2 + y_offset_manual
        
        draw.text((curr_x, final_y), text, font=font, fill="black")
        
    return img

# --- UI ---
st.title("🖨️ Generator Kartu Ujian (Kalibrasi X & Y)")

template_file = st.file_uploader("1. Upload Template (9.5 x 7.5 cm)", type=["png", "jpg", "jpeg"])
data_file = st.file_uploader("2. Upload Data Excel", type=["xlsx", "csv"])

if template_file and data_file:
    template = Image.open(template_file).convert("RGB")
    df = pd.read_excel(data_file) if data_file.name.endswith("xlsx") else pd.read_csv(data_file)
    
    st.subheader("⚙️ Konfigurasi & Kalibrasi")
    cols = list(df.columns)
    
    def find_idx(kw, opts):
        for i, o in enumerate(opts):
            if kw.lower() in str(o).lower(): return i
        return 0

    # Layout Kontrol (5 Kolom agar rapi)
    c1, c2, c3, c4, c5 = st.columns([2, 2, 1, 1, 1])
    with c1:
        c_no = st.selectbox("Kolom Nomor", cols, index=find_idx("nomor", cols))
        c_na = st.selectbox("Kolom Nama", cols, index=find_idx("nama", cols))
    with c2:
        c_ni = st.selectbox("Kolom NISN", cols, index=find_idx("nisn", cols))
        c_tt = st.selectbox("Kolom TTL", cols, index=find_idx("tgl", cols))
    with c3:
        c_pr = st.selectbox("Kolom Program", cols, index=find_idx("program", cols))
    with c4:
        f_size = st.number_input("Ukuran Font", 10, 150, 42)
    with c5:
        x_off = st.number_input("Geser X (Px)", value=0, step=1)
        y_off = st.number_input("Geser Y (Px)", value=0, step=1)

    col_map = {"nomor": c_no, "nama": c_na, "nisn": c_ni, "ttl": c_tt, "program": c_pr}

    st.divider()
    
    st.subheader("🔍 Preview Kalibrasi")
    # Tampilkan preview dengan offset X dan Y
    preview = draw_card(template, df.iloc[0], col_map, f_size, x_off, y_off)
    st.image(preview, width=700)
    
    st.caption("Gunakan angka negatif untuk geser ke Kiri (X) atau ke Atas (Y).")

    if st.button("🚀 Generate & Pecah PDF (F4)", use_container_width=True):
        with st.spinner("Memproses..."):
            all_cards = [draw_card(template, row, col_map, f_size, x_off, y_off) for _, row in df.iterrows()]
            
            # Setting Kertas F4 (300 DPI)
            page_w, page_h = 2540, 3900 
            card_w, card_h = template.size
            
            f4_px_per_cm = page_w / 21.5
            spacing = int(0.5 * f4_px_per_cm) 
            
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

            st.success(f"Berhasil! Tersedia {len(pages)} halaman.")
            
            limit = 10
            for f_idx in range(math.ceil(len(pages) / limit)):
                out = io.BytesIO()
                batch = pages[f_idx*limit : (f_idx+1)*limit]
                batch[0].save(out, format="PDF", save_all=True, append_images=batch[1:] if len(batch) > 1 else [], resolution=300.0)
                out.seek(0)
                st.download_button(f"📥 Download Part {f_idx+1}", out, f"kartu_part_{f_idx+1}.pdf", key=f"d_{f_idx}")
