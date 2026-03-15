import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import pytesseract
import cv2
import numpy as np
import io
import textwrap

st.title("Auto Generator Kartu Peserta")

# =========================
# Utility
# =========================

def load_font(size):
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except:
        return ImageFont.load_default()


def draw_autofit(draw, text, box):

    x,y,w,h = box

    for size in range(48,14,-2):

        font = load_font(size)

        lines = textwrap.wrap(str(text), width=40)
        txt = "\n".join(lines)

        bbox = draw.multiline_textbbox((0,0),txt,font=font)

        tw = bbox[2]-bbox[0]
        th = bbox[3]-bbox[1]

        if tw<w and th<h:

            draw.multiline_text(
                (x,y),
                txt,
                fill="black",
                font=font
            )

            return

    draw.text((x,y),str(text),fill="black",font=load_font(14))


# =========================
# OCR Placeholder Detection
# =========================

def detect_placeholders(img):

    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DATAFRAME)

    boxes = {}

    for i,row in data.iterrows():

        txt = str(row.text)

        if "{{" in txt and "}}" in txt:

            key = txt.replace("{","").replace("}","").lower()

            boxes[key] = (
                int(row.left),
                int(row.top),
                int(row.width),
                int(row.height)
            )

    return boxes


# =========================
# Upload Template
# =========================

template_file = st.file_uploader("Upload Template", type=["png","jpg","jpeg"])

if template_file:

    template = Image.open(template_file).convert("RGB")

    st.image(template,width=600)

    with st.spinner("Detecting placeholders..."):

        boxes = detect_placeholders(template)

    st.write("Detected fields:",boxes)

# =========================
# Upload Data
# =========================

data_file = st.file_uploader("Upload Excel / CSV", type=["csv","xlsx"])

if data_file:

    if data_file.name.endswith("csv"):
        df = pd.read_csv(data_file)
    else:
        df = pd.read_excel(data_file)

    st.dataframe(df.head())

# =========================
# Mapping
# =========================

if template_file and data_file:

    cols = df.columns

    nomor = st.selectbox("Nomor",cols)
    nama = st.selectbox("Nama",cols)
    nisn = st.selectbox("NISN",cols)
    ttl = st.selectbox("TTL",cols)
    program = st.selectbox("Program",cols)

# =========================
# Generate
# =========================

if st.button("Generate Kartu"):

    cards=[]

    for _,row in df.iterrows():

        img = template.copy()

        draw = ImageDraw.Draw(img)

        mapping = {
            "nomor":row[nomor],
            "nama":row[nama],
            "nisn":row[nisn],
            "ttl":row[ttl],
            "program":row[program]
        }

        for k,v in mapping.items():

            if k in boxes:

                draw_autofit(draw,v,boxes[k])

        cards.append(img)

    # ====================
    # PDF
    # ====================

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
