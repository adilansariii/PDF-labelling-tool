from flask import Flask, render_template, request, send_file
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

import io
import os
import re
from datetime import datetime

app = Flask(**name**)

app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

def clean_label(filename):

```
name = os.path.splitext(filename)[0]

name = re.sub(r'[_\-]+', ' ', name)

name = re.sub(
    r'\b(final|copy|v\d+)\b',
    '',
    name,
    flags=re.IGNORECASE
)

name = re.sub(r'\s+', ' ', name)

return name.strip()
```

def create_stamp(
text,
width,
height,
position="top-left",
font_size=20,
padding=6,
margin=15,
opacity=0.4
):

```
packet = io.BytesIO()

can = canvas.Canvas(
    packet,
    pagesize=(width, height)
)

can.setFont(
    "Helvetica-Bold",
    font_size
)

text_width = can.stringWidth(
    text,
    "Helvetica-Bold",
    font_size
)

box_width = text_width + (padding * 2)
box_height = font_size + (padding * 2)

if position == "top-left":
    x = margin
    y = height - box_height - margin

elif position == "top-right":
    x = width - box_width - margin
    y = height - box_height - margin

elif position == "bottom-left":
    x = margin
    y = margin

elif position == "bottom-right":
    x = width - box_width - margin
    y = margin

elif position == "center":
    x = (width - box_width) / 2
    y = (height - box_height) / 2

else:
    x = margin
    y = height - box_height - margin

bg_blue = 0.4 + (0.6 * (1 - opacity))
text_green_blue = opacity * 0.2

can.setFillColorRGB(1, 1, bg_blue)

can.roundRect(
    x,
    y,
    box_width,
    box_height,
    6,
    fill=1,
    stroke=0
)

can.setFillColorRGB(
    1,
    text_green_blue,
    text_green_blue
)

can.drawString(
    x + padding,
    y + padding,
    text
)

can.setStrokeColorRGB(1, 0, 0)
can.setLineWidth(2)

can.roundRect(
    x,
    y,
    box_width,
    box_height,
    6,
    fill=0,
    stroke=1
)

can.save()

packet.seek(0)

return PdfReader(packet)
```

def process_pdf(
file,
name,
position,
font_size,
opacity
):

```
reader = PdfReader(file)

writer = PdfWriter()

for page in reader.pages:

    width = float(page.mediabox.width)
    height = float(page.mediabox.height)

    stamp_pdf = create_stamp(
        text=name,
        width=width,
        height=height,
        position=position,
        font_size=font_size,
        opacity=opacity
    )

    page.merge_page(stamp_pdf.pages[0])

    writer.add_page(page)

return writer
```

@app.route("/", methods=["GET", "POST"])
def index():

```
if request.method == "POST":

    files = request.files.getlist("pdfs")

    labels = request.form.getlist("labels")

    position = request.form.get("position", "top-left")

    font_size = int(
        request.form.get("font_size", 20)
    )

    opacity = float(
        request.form.get("opacity", 0.4)
    )

    final_writer = PdfWriter()

    for idx, file in enumerate(files):

        if file.filename == "":
            continue

        label = (
            labels[idx]
            if idx < len(labels)
            else clean_label(file.filename)
        )

        processed = process_pdf(
            file=file,
            name=label,
            position=position,
            font_size=font_size,
            opacity=opacity
        )

        for page in processed.pages:
            final_writer.add_page(page)

    output = io.BytesIO()

    final_writer.write(output)

    output.seek(0)

    filename = (
        f"Freespace_Labelled_PDF_"
        f"{datetime.now().strftime('%Y-%m-%d')}.pdf"
    )

    return send_file(
        output,
        download_name=filename,
        as_attachment=True
    )

return render_template("index.html")
```

if **name** == "**main**":
app.run(debug=True)
