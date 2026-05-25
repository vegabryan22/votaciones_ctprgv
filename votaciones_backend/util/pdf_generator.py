from datetime import datetime
import os
from flask import current_app
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def generar_pdf_acta(datos):
    buffer = BytesIO()  # Usar un buffer en memoria para el archivo PDF
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=25)  # Ajusta el topMargin según sea necesario
    story = []
    styles = getSampleStyleSheet()

    # Obtener la fecha actual
    fecha_actual = datetime.now().strftime("%d/%m/%Y")
    hora_actual = datetime.now().strftime("%H:%M")
    
    # Agregar encabezado con logotipos y texto centrado
    logo_izquierda_path = os.path.join(current_app.root_path, "static/uploads", "tee_logo.png")
    logo_derecha_path = os.path.join(current_app.root_path, "static/uploads", "ctprgv_logo.png")
    logo_izquierda = Image(logo_izquierda_path, width=100, height=100)
    logo_derecha = Image(logo_derecha_path, width=100, height=100)
    encabezado = [[logo_izquierda,  Paragraph('''
                Tribunal Electoral Estudiantil<br/>
                CTP Roberto Gamboa Valverde<br/>
                San Rafael Abajo de Desamparados<br/>
                Acta de cierre de mesa y resultado de la votación
                ''', styles['Title']), logo_derecha]]
    t_encabezado = Table(encabezado, colWidths=[150, 300, 150])
    t_encabezado.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(t_encabezado)
    story.append(Spacer(1, 20))  # Espacio entre el encabezado y los datos
# Texto adicional antes de la primera tabla
    texto_adicional = f"Se concluye el proceso de conteo electrónico a las {hora_actual} del {fecha_actual}."
    parrafo_adicional = Paragraph(texto_adicional, styles['Normal'])
    story.append(parrafo_adicional)
    story.append(Spacer(1, 20))  # Espacio entre el texto adicional y la tabla
    # Datos de Votos por Candidato
    data = [['','Candidato', 'Votos', 'Porcentaje (%)']]
    for item in datos['votos_por_candidato']:
        # Asegúrate de que la ruta a la imagen es correcta y accesible
        try:
            img_path = os.path.join(current_app.root_path, "static/uploads/", item['imagen'])
            img = Image(img_path, width=25, height=25)  # Ajusta el tamaño según sea necesario
        except Exception as e:
            img = "Imagen no disponible"  # En caso de que la imagen no se pueda cargar
        data.append([ img, item['nombre'], item['votos'], item['porcentaje']])
    t = Table(data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.gray),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),  # Alineación vertical al centro
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND',(0,1),(-1,-1),colors.beige),
    ]))
    story.append(t)
    story.append(Spacer(1, 20))  # Espacio entre las tablas
  # Datos de Participación y Abstención
    participacion_data = [
        ['Metricas', '', 'Tasas', ''],
        ['Participantes', datos['participacion']['participantes'],'Tasa de Participación (%)', datos['participacion']['tasa_participacion']],
        ['Abstencionistas', datos['participacion']['abstencionistas'], 'Tasa de Abstencionismo (%)', datos['participacion']['tasa_abstencionismo']]

        
    ]
    pt = Table(participacion_data)
    pt.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.gray),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),  # Alineación vertical al centro
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND',(0,1),(-1,-1),colors.beige),
    ]))
    story.append(pt)

    # Espacio entre las tablas y las firmas
    story.append(Spacer(1, 20))

    # Sección para las firmas
    firmas_data1 = [
        ['Presidencia del Tribunal', 'Docente Asesor'],
        ['____________________________', '____________________________',]
    ]
    ft1 = Table(firmas_data1)
    ft1.setStyle(TableStyle([
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),  # Alineación vertical al centro
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('TOPPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(ft1)
    firmas_data2 = [
        ['Miembro Delegado','Miembro Delegado','Miembro Delegado',],
        ['____________________________','____________________________','____________________________']
    ]
    ft2 = Table(firmas_data2)
    ft2.setStyle(TableStyle([
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),  # Alineación vertical al centro
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('TOPPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(ft2)

    doc.build(story)

    buffer.seek(0)  # Regresar al inicio del buffer
    return buffer.getvalue()  # Devuelve los bytes del buffer

def generar_pdf_corte(datos):
    buffer = BytesIO()  # Usar un buffer en memoria para el archivo PDF
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=25)  # Ajusta el topMargin según sea necesario
    story = []
    styles = getSampleStyleSheet()

    # Obtener la fecha actual
    fecha_actual = datetime.now().strftime("%d/%m/%Y")
    hora_actual = datetime.now().strftime("%H:%M")
    # Agregar encabezado con logotipos y texto centrado
    logo_izquierda_path = os.path.join(current_app.root_path, "static/uploads", "tee_logo.png")
    logo_derecha_path = os.path.join(current_app.root_path, "static/uploads", "ctprgv_logo.png")
    logo_izquierda = Image(logo_izquierda_path, width=100, height=100)
    logo_derecha = Image(logo_derecha_path, width=100, height=100)
    encabezado = [[logo_izquierda,  Paragraph(f'''
                Tribunal Electoral Estudiantil<br/>
                CTP Roberto Gamboa Valverde<br/>
                San Rafael Abajo de Desamparados<br/>
                Corte a las {hora_actual} del {fecha_actual}
                ''', styles['Title']), logo_derecha]]
    t_encabezado = Table(encabezado, colWidths=[150, 300, 150])
    t_encabezado.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(t_encabezado)
    story.append(Spacer(1, 20))  # Espacio entre el encabezado y los datos

    # Datos de Votos por Candidato
    data = [['','Candidato', 'Votos', 'Porcentaje (%)']]
    for item in datos['votos_por_candidato']:
        # Asegúrate de que la ruta a la imagen es correcta y accesible
        try:
            img_path = os.path.join(current_app.root_path, "static/uploads/", item['imagen'])
            img = Image(img_path, width=25, height=25)  # Ajusta el tamaño según sea necesario
        except Exception as e:
            img = "Imagen no disponible"  # En caso de que la imagen no se pueda cargar
        data.append([ img, item['nombre'], item['votos'], item['porcentaje']])
    t = Table(data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.gray),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),  # Alineación vertical al centro
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND',(0,1),(-1,-1),colors.beige),
    ]))
    story.append(t)
    story.append(Spacer(1, 20))  # Espacio entre las tablas
    # Datos de Participación y Abstención
    participacion_data = [
        ['Metricas', '', 'Tasas', ''],
        ['Participantes', datos['participacion']['participantes'],'Tasa de Participación (%)', datos['participacion']['tasa_participacion']],
        ['Abstencionistas', datos['participacion']['abstencionistas'], 'Tasa de Abstencionismo (%)', datos['participacion']['tasa_abstencionismo']]

        
    ]
    pt = Table(participacion_data)
    pt.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.gray),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),  # Alineación vertical al centro
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND',(0,1),(-1,-1),colors.beige),
    ]))
    story.append(pt)

    # Espacio entre las tablas y las firmas
    story.append(Spacer(1, 20))

    # Sección para las firmas
    firmas_data1 = [
        ['Presidencia del Tribunal', 'Docente Asesor'],
        ['____________________________', '____________________________',]
    ]
    ft1 = Table(firmas_data1)
    ft1.setStyle(TableStyle([
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),  # Alineación vertical al centro
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('TOPPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(ft1)
    firmas_data2 = [
        ['Miembro Delegado','Miembro Delegado','Miembro Delegado',],
        ['____________________________','____________________________','____________________________']
    ]
    ft2 = Table(firmas_data2)
    ft2.setStyle(TableStyle([
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),  # Alineación vertical al centro
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('TOPPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(ft2)

    doc.build(story)

    buffer.seek(0)  # Regresar al inicio del buffer
    return buffer.getvalue()  # Devuelve los bytes del buffer

