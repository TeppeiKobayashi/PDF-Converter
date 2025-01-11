from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
import io
import fitz  # PyMuPDF, for rendering pages to images
import tempfile

def create_4_in_1_page(pages):
    """Combine up to 4 PDF pages into one large page with their original size and high resolution."""
    packet = io.BytesIO()
    temp_writer = PdfWriter()

    for page in pages:
        if page is not None:
            temp_writer.add_page(page)
    temp_writer.write(packet)
    packet.seek(0)

    packet_data = packet.getvalue()
    doc = fitz.open("pdf", packet_data)
    first_page = doc[0]
    page_width = first_page.rect.width
    page_height = first_page.rect.height

    new_page_width = page_width * 2
    new_page_height = page_height * 2

    result = io.BytesIO()
    c = canvas.Canvas(result, pagesize=(new_page_width, new_page_height))

    positions = [(0, page_height), (page_width, page_height), (0, 0), (page_width, 0)]

    for i, page in enumerate(pages):
        if page is not None:
            x, y = positions[i]
            c.saveState()
            c.translate(x, y)

            pix = doc[i].get_pixmap(dpi=300)  # 高解像度のピクセルマップを取得

            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img_file:
                tmp_img_file.write(pix.tobytes("png"))
                tmp_img_file.close()

                c.drawImage(tmp_img_file.name, 0, 0, width=page_width, height=page_height)
            c.restoreState()

    c.save()
    result.seek(0)
    return PdfReader(result).pages[0]

def main(input_pdf_path, output_pdf_path):
    reader = PdfReader(input_pdf_path)
    writer = PdfWriter()

    page_group = []
    for page in reader.pages:
        page_group.append(page)
        if len(page_group) == 4:
            writer.add_page(create_4_in_1_page(page_group))
            page_group = []

    if page_group:
        while len(page_group) < 4:
            page_group.append(None)
        writer.add_page(create_4_in_1_page([p for p in page_group if p]))

    with open(output_pdf_path, 'wb') as output_pdf:
        writer.write(output_pdf)

if __name__ == "__main__":
    input_pdf_path = "/Users/teppeikobayashi/Downloads/Bind4SlidesInto1Page/73NT総括.pdf"
    output_pdf_path = "73NT総括_4枚結合済み.pdf"
    main(input_pdf_path, output_pdf_path)