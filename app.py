from flask import Flask, render_template, request, send_file
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import red, yellow
import io, os

app = Flask(__name__)

def create_stamp(text, width, height):
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=(width, height))

    font_size = 20
    padding = 6

    can.setFont("Helvetica-Bold", font_size)

    text_width = can.stringWidth(text, "Helvetica-Bold", font_size)
    box_width = text_width + padding * 2
    box_height = font_size + padding * 2

    # Top-right position
    x = width - box_width - 15
    y = height - box_height - 15

    # Yellow background
    can.setFillColor(yellow)
    can.roundRect(x, y, box_width, box_height, 6, fill=1, stroke=0)

    # Red rounded border
    can.setStrokeColor(red)
    can.setLineWidth(2)
    can.roundRect(x, y, box_width, box_height, 6, fill=0, stroke=1)

    # Red text
    can.setFillColor(red)
    can.drawString(x + padding, y + padding, text)

    can.save()
    packet.seek(0)

    return PdfReader(packet)


def process_pdf(file, name):
    reader = PdfReader(file)
    writer = PdfWriter()

    for page in reader.pages:
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)

        stamp_pdf = create_stamp(name, width, height)
        stamp_page = stamp_pdf.pages[0]

        page.merge_page(stamp_page)
        writer.add_page(page)

    return writer


@app.route("/", methods=["GET","POST"])
def index():
    if request.method == "POST":

        files = request.files.getlist("pdfs")
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
    app.run()
