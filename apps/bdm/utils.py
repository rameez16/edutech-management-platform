from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO


def render_to_pdf(template_src, context, filename="document.pdf"):
    
    template = get_template(template_src)
    html = template.render(context)

    result = BytesIO()
    pdf = pisa.CreatePDF(
        html,
        dest=result
    )

    if pdf.err:
        return HttpResponse("Error generating PDF", status=500)

    response = HttpResponse(
        result.getvalue(),
        content_type="application/pdf"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response





def generate_card_number(student):
    return f"{student.full_name.split()[0][:3].upper()}{student.id:07d}"


import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url

# Configuration       
cloudinary.config( 
    cloud_name = "dxj7z8eqd", 
    api_key = "224736626162712",
    api_secret = "KQSdgqLQahENIi3q2VCm9Gc8Hsk", 
    secure=True
)

# Upload an image
upload_result = cloudinary.uploader.upload("https://res.cloudinary.com/demo/image/upload/getting-started/shoes.jpg",
                                           public_id="shoes")
print(upload_result["secure_url"])

# Optimize delivery by resizing and applying auto-format and auto-quality
optimize_url, _ = cloudinary_url("shoes", fetch_format="auto", quality="auto")
print(optimize_url)

# Transform the image: auto-crop to square aspect_ratio
auto_crop_url, _ = cloudinary_url("shoes", width=500, height=500, crop="auto", gravity="auto")
print(auto_crop_url)