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