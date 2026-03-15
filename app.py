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

def draw_card(template, row, col_map, font_size_base):
    img = template.copy()
    w_px, h_px = img.size
    draw = ImageDraw.Draw(img)
    
    # Hitung rasio pixel per cm berdasarkan dimensi template (9.5 x 7.5 cm)
    px_per_cm_x = w_px / 9.5
    px_per_cm_y = h_px / 7.5

    # Koordinat dalam CM sesuai input user
    x_cm = 5.37
    y_cm_list = [3.09, 3.51, 3.93, 4.35, 4.78]
    fields = ["nomor", "nama", "nisn", "ttl", "program"]
    
    # Lebar kotak estimasi 4cm, tinggi 0.4cm
    box_w_px = int(4.0 * px_per_cm_x)
    box_h_px = int(0.4 * px_per_cm_y)

    for i, field in enumerate(fields):
        # Konversi cm ke px
        curr_x = int(x_cm * px_per_cm_x)
        curr_y = int(y_cm_list[i] * px_per_cm_y)
        
        text = str(row[col_map[field]]) if pd.notna(row[col_map[field]]) else ""
        
        # 1. Hapus Placeholder
        draw.rectangle([curr_x, curr_y, curr_x + box_w_px, curr_y + box_h_px], fill="white")
        
        # 2. Setup Font
        is_bold = True if field in ["nomor", "nama"] else False
        font = get_font("bold" if is_bold else "regular", font_size_base)
        
        # 3. Gambar Teks (Vertical Center)
        bbox = draw.textbbox((0, 0), text, font=font)
        th = bbox[3] - bbox[1]
        draw.text((curr_x, curr_y + (box_h_px - th) // 2), text, font=font, fill="black")
        
    return img

# --- UI ---
st.title("🖨️ Generator Kartu Ujian (Satuan CM)")

template_file = st.file_uploader("1. Upload Template (9.5 x 7.5 cm)", type=["png", "jpg", "jpeg"])
data_file = st.file_uploader("2. Upload Data Excel", type=["xlsx", "csv"])

if template_file and data_file:
    template = Image.open(template_file).convert("RGB")
    df = pd.read_excel(data_file) if data_file.name.endswith("xlsx") else pd.read_csv(data_file)
    
    st.info(f"Dimensi Gambar Terdeteksi: {template.size[0]}x{template.size[1]} px")
    
    # Auto Mapping Kolom
    cols = list(df.columns)
    def find_idx(kw, opts):
        for i, o in enumerate(opts):
            if kw.lower() in str(o).lower(): return i
        return 0

    c1, c2, c3 = st.columns(3)
    with c1:
        c_no = st.selectbox("Kolom Nomor", cols, index=find_idx("nomor", cols))
        c_na = st.selectbox("Kolom Nama", cols, index=find_idx("nama", cols))
    with c2:
        c_ni = st.selectbox("Kolom NISN", cols, index=find_idx("nisn", cols))
        c_tt = st.selectbox("Kolom TTL", cols, index=find_idx("tgl", cols))
    with c3:
        c_pr = st.selectbox("Kolom Program", cols, index=find_idx("program", cols))
        # Skala font biasanya butuh penyesuaian tergantung DPI gambar
        f_size = st.number_input("Ukuran Font", 10, 200, 42)

    col_map = {"nomor": c_no, "nama": c_na, "nisn": c_ni, "ttl": c_tt, "program": c_pr}

    st.divider()
    st.subheader("🔍 Preview")
    preview = draw_card(template, df.iloc[0], col_map, f_size)
    st.image(preview, width=500)

    if st.button("🚀 Generate & Pecah PDF (F4)", use_container_width=True):
        with st.spinner("Memproses..."):
            all_cards = [draw_card(template, row, col_map, f_size) for _, row in df.iterrows()]
            
            # Setting Kertas F4 (300 DPI)
            page_w, page_h = 2540, 3900 
            card_w, card_h = template.size
            spacing = int(0.5 * (page_w / 21.5)) # 0.5 cm ke pixel F4
            
            # Hitung Margin Center
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

            # Split per 10 Halaman
            limit = 10
            for f_idx in range(math.ceil(len(pages) / limit)):
                out = io.BytesIO()
                batch = pages[f_idx*limit : (f_idx+1)*limit]
                batch[0].save(out, format="PDF", save_all=True, append_images=batch[1:], resolution=300.0)
                out.seek(0)
                st.download_button(f"📥 Download Part {f_idx+1}", out, f"kartu_part_{f_idx+1}.pdf", key=f"d_{f_idx}")
