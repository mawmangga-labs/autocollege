import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import io

st.title("Generator Kartu Peserta")

# ======================
# font
# ======================

def font_regular(size):
    return ImageFont.truetype("times.ttf", size)

def font_bold(size):
    return ImageFont.truetype("timesbd.ttf", size)


# ======================
# autofit text
# ======================

def draw_text_autofit(draw, text, box, bold=False):

    x,y,w,h = box

    for size in range(14,6,-1):

        font = font_bold(size) if bold else font_regular(size)

        bbox = draw.textbbox((0,0),text,font=font)

        tw = bbox[2]-bbox[0]
        th = bbox[3]-bbox[1]

        if tw <= w and th <= h:

            draw.text((x,y),text,font=font,fill="black")
            return

    draw.text((x,y),text,font=font_regular(6),fill="black")


# ======================
# template upload
# ======================

template_file = st.file_uploader("Upload Template", type=["png","jpg","jpeg"])

if template_file:

    template = Image.open(template_file).convert("RGB")

    st.image(template,width=600)

# ======================
# data upload
# ======================

data_file = st.file_uploader("Upload Excel / CSV", type=["xlsx","csv"])

if data_file:

    if data_file.name.endswith("csv"):
        df = pd.read_csv(data_file)
    else:
        df = pd.read_excel(data_file)

    st.dataframe(df.head())

# ======================
# mapping
# ======================

if template_file and data_file:

    cols = df.columns

    nomor = st.selectbox("Nomor Peserta",cols)
    nama = st.selectbox("Nama",cols)
    nisn = st.selectbox("NISN",cols)
    ttl = st.selectbox("TTL",cols)
    program = st.selectbox("Program",cols)

    merge_mode = st.checkbox("Merge 8 kartu per F4")

# ======================
# posisi field (sekali set)
# ======================

boxes = {

"nomor":(730,510,380,40),
"nama":(730,560,380,40),
"nisn":(730,610,380,40),
"ttl":(730,660,380,40),
"program":(730,710,380,40)

}

# ======================
# generate
# ======================

if st.button("Generate"):

    cards=[]

    for _,row in df.iterrows():

        img = template.copy()

        draw = ImageDraw.Draw(img)

        draw_text_autofit(draw,str(row[nomor]),boxes["nomor"],bold=True)
        draw_text_autofit(draw,str(row[nama]),boxes["nama"])
        draw_text_autofit(draw,str(row[nisn]),boxes["nisn"])
        draw_text_autofit(draw,str(row[ttl]),boxes["ttl"])
        draw_text_autofit(draw,str(row[program]),boxes["program"])

        cards.append(img)

    # ======================
    # normal pdf
    # ======================

    if not merge_mode:

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
            "kartu_peserta.pdf"
        )

    # ======================
    # merge 8 per F4
    # ======================

    else:

        page_w = 2480
        page_h = 3508

        card_w = page_w//2
        card_h = page_h//4

        pages=[]

        for i in range(0,len(cards),8):

            page = Image.new("RGB",(page_w,page_h),"white")

            batch = cards[i:i+8]

            for j,card in enumerate(batch):

                card = card.resize((card_w,card_h))

                col = j%2
                row = j//2

                x = col*card_w
                y = row*card_h

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
            "Download PDF F4",
            pdf_bytes,
            "kartu_cetak.pdf"
        )
    
