import streamlit as st
from PIL import Image
import io

st.set_page_config(
    page_title="Generator Kartu Peserta",
    layout="centered"
)

st.title("Generator Layout Kartu Peserta (F4)")
st.write("Upload banyak foto lalu generate PDF otomatis.")

uploaded_files = st.file_uploader(
    "Upload foto",
    type=["jpg","jpeg","png"],
    accept_multiple_files=True
)

if uploaded_files:

    uploaded_files = sorted(uploaded_files, key=lambda x: x.name)

    st.write(f"Jumlah foto: {len(uploaded_files)}")

    dpi = 300

    def cm_to_px(cm):
        return int(cm/2.54 * dpi)

    # =====================
    # ukuran kertas F4
    # =====================

    page_w = cm_to_px(21)
    page_h = cm_to_px(33)

    # =====================
    # ukuran kartu
    # =====================

    img_w = cm_to_px(9.5)
    img_h = cm_to_px(7.5)

    # jarak antar kartu
    gap = cm_to_px(0.5)

    cols = 2
    rows = 4
    per_page = cols * rows

    # =====================
    # hitung grid agar center
    # =====================

    grid_w = cols * img_w + (cols - 1) * gap
    grid_h = rows * img_h + (rows - 1) * gap

    offset_x = (page_w - grid_w) // 2
    offset_y = (page_h - grid_h) // 2

    pages = []

    # =====================
    # generate halaman
    # =====================

    for i in range(0, len(uploaded_files), per_page):

        page = Image.new("RGB", (page_w, page_h), "white")

        batch = uploaded_files[i:i+per_page]

        for j, file in enumerate(batch):

            img = Image.open(file).convert("RGB")
            img = img.resize((img_w, img_h))

            col = j % cols
            row = j // cols

            x = offset_x + col * (img_w + gap)
            y = offset_y + row * (img_h + gap)

            page.paste(img, (x, y))

        pages.append(page)

    # =====================
    # buat PDF
    # =====================

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
        file_name="kartu_peserta_f4.pdf",
        mime="application/pdf"
    )
