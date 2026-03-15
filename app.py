import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import io
import math

st.set_page_config(page_title="Generator Kartu Presisi", layout="wide")

# --- 1. Fungsi Font ---
def get_font(font_type, size):
    try:
        path = f"fonts/TimesLTStd-{'Bold' if font_type == 'bold' else 'Roman'}.ttf"
        return ImageFont.truetype(path, int(size))
    except:
        return ImageFont.load_default()

# --- 2. Fungsi Menggambar Satu Kartu ---
def draw_card(template, row, col_map, font_size_base, x_offset_manual, y_offset_manual):
    img = template.copy()
    w_px, h_px = img.size
    draw = ImageDraw.Draw(img)
    px_per_cm_x = w_px / 9.5
    px_per_cm_y = h_px / 7.5

    x_cm_base = 5.37
    y_cm_list = [3.09, 3.51, 3.93, 4.35, 4.78]
    fields = ["nomor", "nama", "nisn", "ttl", "program"]
    
    right_limit_px = int(9.3 * px_per_cm_x) 
    box_h_px = int(0.42 * px_per_cm_y)      
    inner_padding_px = int(0.15 * px_per_cm_x) 

    for i, field in enumerate(fields):
        curr_x = int(x_cm_base * px_per_cm_x) + x_offset_manual
        curr_y = int(y_cm_list[i] * px_per_cm_y)
        dynamic_box_w = max(10, right_limit_px - curr_x)
        safe_limit_w = dynamic_box_w - (inner_padding_px * 2)
        
        text = str(row[col_map[field]]) if pd.notna(row[col_map[field]]) else ""
        draw.rectangle([curr_x, curr_y, curr_x + dynamic_box_w, curr_y + box_h_px], fill="white")
        
        is_bold = True if field in ["nomor"] else False
        current_size = font_size_base
        font = get_font("bold" if is_bold else "regular", current_size)
        
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        while text_w > safe_limit_w and current_size > 10:
            current_size -= 1
            font = get_font("bold" if is_bold else "regular", current_size)
            bbox = draw.textbbox((0, 0), text, font=font)
            text_w = bbox[2] - bbox[0]

        th = bbox[3] - bbox[1]
        final_y = curr_y + (box_h_px - th) // 2 + y_offset_manual
        draw.text((curr_x + inner_padding_px, final_y), text, font=font, fill="black")
        
    return img

# --- 3. UI ---
st.title("🖨️ Generator Kartu Ujian (Single File PDF)")

t_file = st.file_uploader("1. Upload Template", type=["png", "jpg", "jpeg"])
d_file = st.file_uploader("2. Upload Data", type=["xlsx", "csv"])

if t_file and d_file:
    template = Image.open(t_file).convert("RGB")
    df = pd.read_excel(d_file) if d_file.name.endswith("xlsx") else pd.read_csv(d_file)
    cols = list(df.columns)
    
    def find_idx(kw, opts):
        for i, o in enumerate(opts):
            if kw.lower() in str(o).lower(): return i
        return 0

    L, R = st.columns([1, 2])
    with L:
        st.subheader("📋 Mapping Data")
        c_no = st.selectbox("Nomor Peserta", cols, index=find_idx("nomor", cols))
        c_na = st.selectbox("Nama Peserta", cols, index=find_idx("nama", cols))
        c_ni = st.selectbox("NISN", cols, index=find_idx("nisn", cols))
        c_tt = st.selectbox("Tempat Tgl Lahir", cols, index=find_idx("tgl", cols))
        c_pr = st.selectbox("Program/Jurusan", cols, index=find_idx("program", cols))
        col_map = {"nomor": c_no, "nama": c_na, "nisn": c_ni, "ttl": c_tt, "program": c_pr}
        st.divider()
        generate_btn = st.button("🚀 GENERATE SINGLE PDF", use_container_width=True, type="primary")

    with R:
        st.subheader("🔍 Kalibrasi")
        prev_col, ctrl_col = st.columns([2.5, 1])
        with ctrl_col:
            f_size = st.number_input("Ukuran Font", 10, 150, 42)
            x_off = st.number_input("Geser X (Px)", value=0)
            y_off = st.number_input("Geser Y (Px)", value=0)
        with prev_col:
            preview_img = draw_card(template, df.iloc[0], col_map, f_size, x_off, y_off)
            st.image(preview_img, use_container_width=True)

    # --- 4. Logika Generate Single File (Optimized) ---
    if generate_btn:
        with st.spinner("Sedang memproses seluruh kartu menjadi satu file..."):
            page_w, page_h = 2540, 3900 
            card_w, card_h = template.size
            f4_px_per_cm = page_w / 21.5
            spacing = int(0.5 * f4_px_per_cm) 
            
            grid_w = (card_w * 2) + spacing
            grid_h = (card_h * 4) + (spacing * 3)
            start_x = (page_w - grid_w) // 2
            start_y = (page_h - grid_h) // 2

            pages = []
            total_data = len(df)
            
            # Buat progress bar agar user tidak bosan
            progress_bar = st.progress(0)
            
            for i in range(0, total_data, 8):
                # Update progress
                progress_bar.progress(min((i + 8) / total_data, 1.0))
                
                page = Image.new("RGB", (page_w, page_h), "white")
                batch_df = df.iloc[i : i+8]
                
                for j, (_, row) in enumerate(batch_df.iterrows()):
                    card_img = draw_card(template, row, col_map, f_size, x_off, y_off)
                    pos_x = start_x + (j % 2) * (card_w + spacing)
                    pos_y = start_y + (j // 2) * (card_h + spacing)
                    page.paste(card_img, (pos_x, pos_y))
                    card_img.close()
                
                pages.append(page)

            # SAVE SEBAGAI SINGLE FILE
            if pages:
                out = io.BytesIO()
                # Gunakan parameter optimize dan kompresi tambahan
                pages[0].save(
                    out, 
                    format="PDF", 
                    save_all=True, 
                    append_images=pages[1:] if len(pages) > 1 else [], 
                    resolution=300.0, 
                    optimize=True
                )
                out.seek(0)
                
                st.success(f"Selesai! {len(df)} kartu dalam satu file PDF.")
                st.download_button(
                    label="📥 DOWNLOAD KARTU (SINGLE PDF)", 
                    data=out, 
                    file_name="semua_kartu_ujian.pdf", 
                    mime="application/pdf",
                    use_container_width=True
                )
                
                # Penting: Bersihkan memori segera
                for p in pages: p.close()
                del pages
