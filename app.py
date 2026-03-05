from flask import Flask, render_template, request, send_file
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
import io
import os

app = Flask(__name__)

# Create stamp once per PDF
def create_stamp(text, width, height):
    packet = io.BytesIO()

    can = canvas.Canvas(packet, pagesize=(width, height))
    can.setFont("Helvetica", 10)
    can.drawString(10, height - 20, text)
    can.save()

    packet.seek(0)
    return PdfReader(packet).pages[0]


def process_pdf(file, name):

    reader = PdfReader(file)
    writer = PdfWriter()

    # Create stamp once
    first_page = reader.pages[0]
    width = float(first_page.mediabox.width)
    height = float(first_page.mediabox.height)

    stamp_page = create_stamp(name, width, height)

    for page in reader.pages:
        page.merge_page(stamp_page)
        writer.add_page(page)

    return writer


@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == "POST":

        files = request.files.getlist("pdfs")

        if not files:
            return "No files uploaded"

        final_writer = PdfWriter()

        for file in files:

            name = os.path.splitext(file.filename)[0]

            processed = process_pdf(file, name)

            for page in processed.pages:
                final_writer.add_page(page)

        output = io.BytesIO()
        final_writer.write(output)
        output.seek(0)

        return send_file(
            output,
            download_name="merged.pdf",
            as_attachment=True
        )

    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
