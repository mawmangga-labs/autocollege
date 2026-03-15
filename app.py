import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import io
import math

st.set_page_config(page_title="Generator Kartu F4", layout="wide")
st.title("🖨️ Generator Kartu (Preview & Auto-Split PDF)")

# --- Fungsi Helper Font & Draw (Sama seperti sebelumnya) ---
def get_font(font_type, size):
    try:
        path = "fonts/TimesLTStd-Bold.ttf" if font_type == "bold" else "fonts/TimesLTStd-Roman.ttf"
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

def draw_card(template, row, col_map, boxes):
    img = template.copy()
    draw = ImageDraw.Draw(img)
    
    fields = ["nomor", "nama", "nisn", "ttl", "program"]
    for field in fields:
        x, y, w, h = boxes[field]
        text = str(row[col_map[field]])
        
        # Tutup Placeholder
        draw.rectangle([x, y, x + w, y + h], fill="white")
        
        # Autofit Text
        best_size = 10
        for size in range(40, 8, -1):
            font = get_font("bold" if field=="nomor" else "regular", size)
            bbox = draw.textbbox((0, 0), text, font=font)
            if (bbox[2]-bbox[0]) <= w and (bbox[3]-bbox[1]) <= h:
                best_size = size
                break
        
        font = get_font("bold" if field=="nomor" else "regular", best_size)
        bbox = draw.textbbox((0, 0), text, font=font)
        draw.text((x, y + (h - (bbox[3]-bbox[1])) // 2), text, font=font, fill="black")
    return img

# --- UI Upload ---
template_file = st.file_uploader("1. Upload Template", type=["png", "jpg", "jpeg"])
data_file = st.file_uploader("2. Upload Data", type=["xlsx", "csv"])

if template_file and data_file:
    template = Image.open(template_file).convert("RGB")
    df = pd.read_excel(data_file) if data_file.name.endswith("xlsx") else pd.read_csv(data_file)
    
    col1, col2 = st.columns(2)
    with col1:
        c_no = st.selectbox("Kolom Nomor", df.columns)
        c_na = st.selectbox("Kolom Nama", df.columns)
        c_ni = st.selectbox("Kolom NISN", df.columns)
    with col2:
        c_tt = st.selectbox("Kolom TTL", df.columns)
        c_pr = st.selectbox("Kolom Program", df.columns)

    col_map = {"nomor": c_no, "nama": c_na, "nisn": c_ni, "ttl": c_tt, "program": c_pr}
    boxes = {
        "nomor": (540, 410, 480, 45), "nama": (540, 460, 480, 45),
        "nisn": (540, 510, 480, 45), "ttl": (540, 560, 480, 45), "program": (540, 610, 480, 45)
    }

    # --- BAGIAN PREVIEW ---
    st.subheader("👀 Preview (3 Data Pertama)")
    preview_cols = st.columns(3)
    for i in range(min(3, len(df))):
        p_img = draw_card(template, df.iloc[i], col_map, boxes)
        preview_cols[i].image(p_img, caption=f"Preview: {df.iloc[i][c_na]}", use_container_width=True)

    st.divider()

    # --- PROSES GENERATE & SPLIT ---
    st.subheader("💾 Download PDF (Per 10 Halaman / 80 Kartu)")
    
    if st.button("Siapkan File Download"):
        # 1. Generate semua kartu ke memori (hanya gambar kartu)
        all_cards = []
        progress_bar = st.progress(0)
        for i, (_, row) in enumerate(df.iterrows()):
            all_cards.append(draw_card(template, row, col_map, boxes))
            progress_bar.progress((i + 1) / len(df))

        # 2. Susun ke Halaman F4
        page_w, page_h = 2540, 3900 
        card_w, card_h = template.size
        spacing = 60
        start_x = (page_w - ((card_w * 2) + spacing)) // 2
        start_y = (page_h - ((card_h * 4) + (spacing * 3))) // 2

        all_pages = []
        for i in range(0, len(all_cards), 8):
            page = Image.new("RGB", (page_w, page_h), "white")
            batch = all_cards[i:i+8]
            for j, card in enumerate(batch):
                page.paste(card, (start_x + (j%2)*(card_w+spacing), start_y + (j//2)*(card_h+spacing)))
            all_pages.append(page)

        # 3. Split PDF per 10 Halaman
        limit = 10
        total_files = math.ceil(len(all_pages) / limit)
        
        for f_idx in range(total_files):
            start_p = f_idx * limit
            end_p = start_p + limit
            pdf_batch = all_pages[start_p:end_p]
            
            pdf_io = io.BytesIO()
            pdf_batch[0].save(
                pdf_io, format="PDF", save_all=True, 
                append_images=pdf_batch[1:], resolution=300.0
            )
            pdf_io.seek(0)
            
            st.download_button(
                label=f"📥 Download Bagian {f_idx + 1} (Hal {start_p+1}-{min(end_p, len(all_pages))})",
                data=pdf_io,
                file_name=f"kartu_part_{f_idx+1}.pdf",
                mime="application/pdf",
                key=f"dl_{f_idx}"
            )
        st.success("File siap! Silakan klik tombol di atas satu per satu.")
