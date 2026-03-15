import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import io
import textwrap
import math

st.set_page_config(page_title="Kartu Peserta Generator", layout="wide")

st.title("Generator Kartu Peserta Ujian")

# =============================
# Utility
# =============================

def cm_to_px(cm, dpi=300):
    return int(cm / 2.54 * dpi)

def load_font(size):
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except:
        return ImageFont.load_default()

def draw_text_autofit(draw, text, box, max_font=48, min_font=18, padding=10):

    x1,y1,x2,y2 = box

    x1 += padding
    y1 += padding
    x2 -= padding
    y2 -= padding

    width = x2-x1
    height = y2-y1

    for size in range(max_font, min_font-1, -1):

        font = load_font(size)

        lines = textwrap.wrap(text, width=40)

        wrapped = "\n".join(lines)

        bbox = draw.multiline_textbbox((0,0), wrapped, font=font)

        w = bbox[2]-bbox[0]
        h = bbox[3]-bbox[1]

        if w <= width and h <= height:

            draw.multiline_text(
                (x1,y1),
                wrapped,
                font=font,
                fill="black"
            )
            return

    font = load_font(min_font)

    draw.multiline_text(
        (x1,y1),
        text,
        font=font,
        fill="black"
    )

# =============================
# Upload Template
# =============================

template_file = st.file_uploader(
    "Upload Template Kartu",
    type=["png","jpg","jpeg"]
)

if template_file is None:
    st.stop()

template = Image.open(template_file).convert("RGB")

st.subheader("Preview Template")
st.image(template, width=600)

img_w, img_h = template.size

# =============================
# Definisi Field
# =============================

st.subheader("Definisikan Area Field")

fields = ["nomor","nama","nisn","ttl","program"]

boxes = {}

for f in fields:

    st.markdown(f"### Field: {f}")

    col1,col2 = st.columns(2)

    with col1:
        x1 = st.slider(f"{f} x1",0,img_w, int(img_w*0.55))
        y1 = st.slider(f"{f} y1",0,img_h, int(img_h*0.45))

    with col2:
        x2 = st.slider(f"{f} x2",0,img_w, int(img_w*0.9))
        y2 = st.slider(f"{f} y2",0,img_h, int(img_h*0.55))

    boxes[f] = (x1,y1,x2,y2)

# =============================
# Upload Data
# =============================

st.subheader("Upload Data Peserta")

data_file = st.file_uploader(
    "CSV / XLSX",
    type=["csv","xlsx"]
)

if data_file is None:
    st.stop()

if data_file.name.endswith(".csv"):
    df = pd.read_csv(data_file)

else:
    excel = pd.ExcelFile(data_file)
    sheet = st.selectbox("Sheet", excel.sheet_names)
    df = excel.parse(sheet)

st.write("Preview Data")
st.dataframe(df.head())

cols = df.columns.tolist()

st.subheader("Mapping Kolom")

nomor_col = st.selectbox("Nomor", cols)
nama_col = st.selectbox("Nama", cols)
nisn_col = st.selectbox("NISN", cols)
ttl_col = st.selectbox("TTL", cols)
program_col = st.selectbox("Program", cols)

mode = st.radio(
    "Mode Output",
    [
        "PDF Satuan",
        "PDF Cetak (8 kartu per F4)"
    ]
)

# =============================
# Generate
# =============================

if st.button("Generate Kartu"):

    cards = []

    for _,row in df.iterrows():

        img = template.copy()

        draw = ImageDraw.Draw(img)

        draw_text_autofit(draw,str(row[nomor_col]),boxes["nomor"])
        draw_text_autofit(draw,str(row[nama_col]),boxes["nama"])
        draw_text_autofit(draw,str(row[nisn_col]),boxes["nisn"])
        draw_text_autofit(draw,str(row[ttl_col]),boxes["ttl"])
        draw_text_autofit(draw,str(row[program_col]),boxes["program"])

        cards.append(img)

    st.success(f"{len(cards)} kartu berhasil dibuat")

    # =================================
    # MODE PDF SATUAN
    # =================================

    if mode == "PDF Satuan":

        pdf_bytes = io.BytesIO()

        cards[0].save(
            pdf_bytes,
            format="PDF",
            save_all=True,
            append_images=cards[1:]
        )

        pdf_bytes.seek(0)

        st.download_button(
            "Download PDF",
            pdf_bytes,
            "kartu_peserta.pdf",
            "application/pdf"
        )

    # =================================
    # MODE CETAK 8 KARTU
    # =================================

    if mode == "PDF Cetak (8 kartu per F4)":

        dpi = 300

        page_w = cm_to_px(21)
        page_h = cm_to_px(33)

        card_w = cm_to_px(9.5)
        card_h = cm_to_px(7.5)

        gap = cm_to_px(0.5)

        cols = 2
        rows = 4

        per_page = cols*rows

        grid_w = cols*card_w + (cols-1)*gap
        grid_h = rows*card_h + (rows-1)*gap

        offset_x = (page_w-grid_w)//2
        offset_y = (page_h-grid_h)//2

        pages = []

        for i in range(0,len(cards),per_page):

            page = Image.new("RGB",(page_w,page_h),"white")

            batch = cards[i:i+per_page]

            for j,card in enumerate(batch):

                card = card.resize((card_w,card_h))

                col = j % cols
                row = j // cols

                x = offset_x + col*(card_w+gap)
                y = offset_y + row*(card_h+gap)

                page.paste(card,(x,y))

            pages.append(page)

        pdf_bytes = io.BytesIO()

        pages[0].save(
            pdf_bytes,
            format="PDF",
            save_all=True,
            append_images=pages[1:]
        )

        pdf_bytes.seek(0)

        st.download_button(
            "Download PDF Cetak",
            pdf_bytes,
            "kartu_cetak_f4.pdf",
            "application/pdf"
        )
