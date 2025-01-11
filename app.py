from flask import Flask, request, send_file, render_template
import io
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
import fitz  # PyMuPDF, for rendering pages to images
import tempfile

app = Flask(__name__)

def create_4_in_1_page(pages):
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
            pix = doc[i].get_pixmap(dpi=300)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img_file:
                tmp_img_file.write(pix.tobytes("png"))
                tmp_img_file.close()
                c.drawImage(tmp_img_file.name, 0, 0, width=page_width, height=page_height)
            c.restoreState()
    c.save()
    result.seek(0)
    return PdfReader(result).pages[0]

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        file = request.files['file']
        if file:
            reader = PdfReader(file)
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

            output = io.BytesIO()
            writer.write(output)
            output.seek(0)
            return send_file(output, mimetype='application/pdf', as_attachment=True, download_name='merged.pdf')

    return render_template("upload.html")

if __name__ == "__main__":
    app.run(debug=True)