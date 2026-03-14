import streamlit as st
from PIL import Image
import io

st.title("Generator Foto F4 (8 per halaman)")

uploaded_files = st.file_uploader(
    "Upload foto", 
    type=["jpg","jpeg","png"], 
    accept_multiple_files=True
)

if uploaded_files:

    uploaded_files = sorted(uploaded_files, key=lambda x: x.name)

    dpi = 300

    def cm_to_px(cm):
        return int(cm/2.54 * dpi)

    # ukuran kertas F4
    page_w = cm_to_px(21)
    page_h = cm_to_px(33)

    # ukuran foto
    img_w = cm_to_px(9.5)
    img_h = cm_to_px(7.5)

    cols = 2
    rows = 4
    per_page = cols * rows

    pages = []

    for i in range(0, len(uploaded_files), per_page):

        page = Image.new("RGB",(page_w,page_h),"white")

        batch = uploaded_files[i:i+per_page]

        for j,file in enumerate(batch):

            img = Image.open(file).convert("RGB")
            img = img.resize((img_w,img_h))

            col = j % cols
            row = j // cols

            x = col * img_w
            y = row * img_h

            page.paste(img,(x,y))

        pages.append(page)

    pdf_bytes = io.BytesIO()

    pages[0].save(
        pdf_bytes,
        format="PDF",
        save_all=True,
        append_images=pages[1:]
    )

    st.success("PDF berhasil dibuat")

    st.download_button(
        label="Download PDF",
        data=pdf_bytes.getvalue(),
        file_name="foto_f4.pdf",
        mime="application/pdf"
    )
