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
    
    px_per_cm_x = w_px / 9.5
    px_per_cm_y = h_px / 7.5

    x_cm = 5.37
    y_cm_list = [3.09, 3.51, 3.93, 4.35, 4.78]
    fields = ["nomor", "nama", "nisn", "ttl", "program"]
    
    box_w_px = int(4.0 * px_per_cm_x)
    box_h_px = int(0.42 * px_per_cm_y)

    for i, field in enumerate(fields):
        curr_x = int(x_cm * px_per_cm_x) + x_offset_manual
        curr_y = int(y_cm_list[i] * px_per_cm_y)
        
        text = str(row[col_map[field]]) if pd.notna(row[col_map[field]]) else ""
        draw.rectangle([curr_x, curr_y, curr_x + box_w_px, curr_y + box_h_px], fill="white")
        
        is_bold = True if field in ["nomor", "nama"] else False
        font = get_font("bold" if is_bold else "regular", font_size_base)
        
        bbox = draw.textbbox((0, 0), text, font=font)
        th = bbox[3] - bbox[1]
        final_y = curr_y + (box_h_px - th) // 2 + y_offset_manual
        
        draw.text((curr_x, final_y), text, font=font, fill="black")
        
    return img

st.title("🖨️ Generator Kartu Ujian (Live Calibration)")

template_file = st.file_uploader("1. Upload Template (9.5 x 7.5 cm)", type=["png", "jpg", "jpeg"])
data_file = st.file_uploader("2. Upload Data Excel", type=["xlsx", "csv"])

if template_file and data_file:
    template = Image.open(template_file).convert("RGB")
    df = pd.read_excel(data_file) if data_file.name.endswith("xlsx") else pd.read_csv(data_file)
    cols = list(df.columns)
    
    def find_idx(kw, opts):
        for i, o in enumerate(opts):
            if kw.lower() in str(o).lower(): return i
        return 0

    # --- MAIN LAYOUT ---
    main_col_left, main_col_right = st.columns([1, 2])

    with main_col_left:
        st.subheader("📋 Pilih Kolom Data")
        c_no = st.selectbox("Kolom Nomor", cols, index=find_idx("nomor", cols))
        c_na = st.selectbox("Kolom Nama", cols, index=find_idx("nama", cols))
        c_ni = st.selectbox("Kolom NISN", cols, index=find_idx("nisn", cols))
        c_tt = st.selectbox("Kolom TTL", cols, index=find_idx("tgl", cols))
        c_pr = st.selectbox("Kolom Program", cols, index=find_idx("program", cols))
        
        st.divider()
        generate_btn = st.button("🚀 Generate & Pecah PDF (F4)", use_container_width=True)

    with main_col_right:
        st.subheader("🔍 Preview & Kalibrasi")
        
        # Sub-kolom untuk menaruh Preview dan Kontrol berdampingan
        prev_col, ctrl_col = st.columns([3, 1])
        
        with ctrl_col:
            st.write("🔧 **Tune**")
            f_size = st.number_input("Font Size", 10, 150, 42)
            x_off = st.number_input("Geser X", value=0, step=1)
            y_off = st.number_input("Geser Y", value=0, step=1)
            st.caption("Tips: Gunakan angka negatif untuk naik/kiri")

        col_map = {"nomor": c_no, "nama": c_na, "nisn": c_ni, "ttl": c_tt, "program": c_pr}
        
        with prev_col:
            preview = draw_card(template, df.iloc[0], col_map, f_size, x_off, y_off)
            st.image(preview, use_container_width=True, caption="Pratinjau real-time")

    # --- LOGIKA GENERATE ---
    if generate_btn:
        with st.spinner("Memproses seluruh data..."):
            all_cards = [draw_card(template, row, col_map, f_size, x_off, y_off) for _, row in df.iterrows()]
            
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

            st.success(f"Berhasil! Total {len(pages)} halaman.")
            
            limit = 10
            dl_cols = st.columns(3) # Tampilkan tombol download dalam grid agar hemat tempat
            for f_idx in range(math.ceil(len(pages) / limit)):
                out = io.BytesIO()
                batch = pages[f_idx*limit : (f_idx+1)*limit]
                batch[0].save(out, format="PDF", save_all=True, append_images=batch[1:] if len(batch) > 1 else [], resolution=300.0)
                out.seek(0)
                with dl_cols[f_idx % 3]:
                    st.download_button(f"📥 Part {f_idx+1}", out, f"kartu_ujian_part_{f_idx+1}.pdf", key=f"d_{f_idx}")
