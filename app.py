import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import io

st.set_page_config(page_title="Generator Kartu Peserta", layout="centered")

st.title("Generator Kartu Peserta Otomatis")

# =============================
# Upload template
# =============================

template_file = st.file_uploader("Upload Template Kartu (PNG/JPG)", type=["png","jpg","jpeg"])

# =============================
# Upload data
# =============================

data_file = st.file_uploader("Upload Data Peserta (CSV / XLSX)", type=["csv","xlsx"])

df = None

if data_file:

    if data_file.name.endswith(".csv"):
        df = pd.read_csv(data_file)

    if data_file.name.endswith(".xlsx"):
        excel = pd.ExcelFile(data_file)
        sheet = st.selectbox("Pilih Sheet", excel.sheet_names)
        df = excel.parse(sheet)

if df is not None:

    st.write("Preview Data")
    st.dataframe(df.head())

    cols = df.columns.tolist()

    st.subheader("Mapping Kolom")

    nomor_col = st.selectbox("Nomor Peserta", cols)
    nama_col = st.selectbox("Nama Peserta", cols)
    nisn_col = st.selectbox("NISN", cols)
    ttl_col = st.selectbox("Tempat Tanggal Lahir", cols)
    program_col = st.selectbox("Program", cols)

    output_mode = st.radio(
        "Mode Output",
        ["PDF Satuan (1 kartu per halaman)", "PDF Cetak (8 kartu per F4)"]
    )

    if st.button("Generate Kartu"):

        template = Image.open(template_file).convert("RGB")

        # font
        font = ImageFont.load_default()

        cards = []

        for _, row in df.iterrows():

            img = template.copy()
            draw = ImageDraw.Draw(img)

            draw.text((760,520), str(row[nomor_col]), fill="black", font=font)
            draw.text((760,600), str(row[nama_col]), fill="black", font=font)
            draw.text((760,680), str(row[nisn_col]), fill="black", font=font)
            draw.text((760,760), str(row[ttl_col]), fill="black", font=font)
            draw.text((760,840), str(row[program_col]), fill="black", font=font)

            cards.append(img)

        # =====================================
        # MODE 1 : PDF SATUAN
        # =====================================

        if output_mode == "PDF Satuan (1 kartu per halaman)":

            pdf_bytes = io.BytesIO()

            cards[0].save(
                pdf_bytes,
                format="PDF",
                save_all=True,
                append_images=cards[1:]
            )

            st.success("PDF berhasil dibuat")

            st.download_button(
                "Download PDF",
                pdf_bytes.getvalue(),
                "kartu_peserta.pdf",
                "application/pdf"
            )

        # =====================================
        # MODE 2 : KOLOM 8 PER F4
        # =====================================

        if output_mode == "PDF Cetak (8 kartu per F4)":

            dpi = 300

            def cm_to_px(cm):
                return int(cm/2.54 * dpi)

            page_w = cm_to_px(21)
            page_h = cm_to_px(33)

            card_w = cm_to_px(9.5)
            card_h = cm_to_px(7.5)

            gap = cm_to_px(0.5)

            cols = 2
            rows = 4

            per_page = cols * rows

            grid_w = cols*card_w + (cols-1)*gap
            grid_h = rows*card_h + (rows-1)*gap

            offset_x = (page_w-grid_w)//2
            offset_y = (page_h-grid_h)//2

            pages = []

            for i in range(0, len(cards), per_page):

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

            st.success("PDF Cetak berhasil dibuat")

            st.download_button(
                "Download PDF",
                pdf_bytes.getvalue(),
                "kartu_cetak_f4.pdf",
                "application/pdf"
            )
