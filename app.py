import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import io
import math

st.set_page_config(page_title="Generator Kartu SMAN 1 Batukliang", layout="wide")

# --- Fungsi Helper Font ---
def get_font(font_type, size):
    try:
        # Gunakan path font lokal Anda
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
        text = str(row[col_map[field]])
        
        # 1. Hapus placeholder (Putih)
        draw.rectangle([x, y, x + w, y + h], fill="white")
        
        # 2. Pengaturan Font
        # Jika user input 7.2, kita skalakan sedikit karena ukuran pixel vs point berbeda
        current_font_size = font_size_base 
        is_bold = True if field in ["nomor", "nama"] else False
        font = get_font("bold" if is_bold else "regular", current_font_size)
        
        # 3. Render Teks (Aligment Kiri Tengah)
        bbox = draw.textbbox((0, 0), text, font=font)
        th = bbox[3] - bbox[1]
        draw.text((x, y + (h - th) // 2), text, font=font, fill="black")
        
    return img

# --- UI Sidebar & Upload ---
st.title("🖨️ Generator Kartu Ujian Sekolah")

with st.sidebar:
    st.header("Pengaturan Layout")
    font_size = st.slider("Ukuran Font", 10, 80, 45) # Skala pixel biasanya lebih besar dari point
    st.info("Saran: Gunakan ukuran 40-50 untuk hasil serupa ukuran 7.2pt")

template_file = st.file_uploader("Upload Template Kartu", type=["png", "jpg", "jpeg"])
data_file = st.file_uploader("Upload Data (Excel/CSV)", type=["xlsx", "csv"])

if template_file and data_file:
    template = Image.open(template_file).convert("RGB")
    df = pd.read_excel(data_file) if data_file.name.endswith("xlsx") else pd.read_csv(data_file)
    
    # Mapping Kolom
    cols = list(df.columns)
    c1, c2 = st.columns(2)
    with c1:
        c_no = st.selectbox("Kolom Nomor Peserta", cols, index=min(0, len(cols)-1))
        c_na = st.selectbox("Kolom Nama Peserta", cols, index=min(1, len(cols)-1))
        c_ni = st.selectbox("Kolom NISN", cols, index=min(2, len(cols)-1))
    with c2:
        c_tt = st.selectbox("Kolom Tempat & Tgl Lahir", cols, index=min(3, len(cols)-1))
        c_pr = st.selectbox("Kolom Program", cols, index=min(4, len(cols)-1))

    col_map = {"nomor": c_no, "nama": c_na, "nisn": c_ni, "ttl": c_tt, "program": c_pr}

    # KOORDINAT BERDASARKAN GAMBAR TEMPLATE (X, Y, W, H)
    # Sesuaikan Y agar pas di depan titik dua masing-masing baris
    boxes = {
        "nomor":   (470, 410, 450, 48),
        "nama":    (470, 460, 450, 48),
        "nisn":    (470, 510, 450, 48),
        "ttl":     (470, 560, 450, 48),
        "program": (470, 610, 450, 48)
    }

    # --- Preview ---
    st.subheader("🔍 Preview")
    preview_img = draw_card(template, df.iloc[0], col_map, boxes, font_size)
    st.image(preview_img, width=500)

    # --- Proses ---
    if st.button("🚀 Generate & Pecah PDF"):
        all_cards = [draw_card(template, row, col_map, boxes, font_size) for _, row in df.iterrows()]
        
        # Setting F4
        page_w, page_h = 2540, 3900 
        card_w, card_h = template.size
        spacing = 60
        start_x = (page_w - ((card_w * 2) + spacing)) // 2
        start_y = (page_h - ((card_h * 4) + (spacing * 3))) // 2

        pages = []
        for i in range(0, len(all_cards), 8):
            page = Image.new("RGB", (page_w, page_h), "white")
            batch = all_cards[i:i+8]
            for j, card in enumerate(batch):
                pos_x = start_x + (j % 2) * (card_w + spacing)
                pos_y = start_y + (j // 2) * (card_h + spacing)
                page.paste(card, (pos_x, pos_y))
            pages.append(page)

        # Download per 10 Halaman
        limit = 10
        for f_idx in range(math.ceil(len(pages) / limit)):
            start_p = f_idx * limit
            end_p = start_p + limit
            pdf_batch = pages[start_p:end_p]
            
            output = io.BytesIO()
            pdf_batch[0].save(output, format="PDF", save_all=True, append_images=pdf_batch[1:], resolution=300.0)
            output.seek(0)
            
            st.download_button(
                label=f"📥 Download Part {f_idx+1} (Hal {start_p+1}-{min(end_p, len(pages))})",
                data=output,
                file_name=f"kartu_ujian_part_{f_idx+1}.pdf",
                key=f"dl_{f_idx}"
            )
