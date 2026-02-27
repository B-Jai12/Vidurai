import os
from datetime import datetime

def generate_report(parsed_json, patient_name="Patient"):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.enums import TA_CENTER, TA_LEFT

        output_path = f"reports/MedSaathi_{patient_name}_{datetime.now().strftime('%d%m%Y_%H%M%S')}.pdf"
        os.makedirs("reports", exist_ok=True)

        doc = SimpleDocTemplate(output_path, pagesize=A4,
                                rightMargin=20*mm, leftMargin=20*mm,
                                topMargin=20*mm, bottomMargin=20*mm)

        styles = getSampleStyleSheet()
        story = []

        # Title
        title_style = ParagraphStyle('Title', parent=styles['Title'],
                                     fontSize=20, textColor=colors.HexColor('#1A73E8'),
                                     spaceAfter=6, alignment=TA_CENTER)
        story.append(Paragraph("MedSaathi Prescription Report", title_style))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%d %B %Y, %I:%M %p')}",
                                ParagraphStyle('sub', parent=styles['Normal'],
                                               fontSize=9, textColor=colors.grey, alignment=TA_CENTER)))
        story.append(Spacer(1, 10*mm))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E8EAED')))
        story.append(Spacer(1, 6*mm))

        # Patient info
        heading = ParagraphStyle('Heading', parent=styles['Heading2'],
                                 fontSize=13, textColor=colors.HexColor('#202124'), spaceAfter=4)
        normal = ParagraphStyle('Normal2', parent=styles['Normal'], fontSize=10, spaceAfter=3)

        story.append(Paragraph("Patient Information", heading))
        info_data = [
            ["Patient", parsed_json.get("patient_name", "N/A"),
             "Doctor", parsed_json.get("doctor_name", "N/A")],
            ["Age", parsed_json.get("patient_age", "N/A"),
             "Hospital", parsed_json.get("hospital_name", "N/A")],
            ["Date", parsed_json.get("prescription_date", "N/A"),
             "Follow Up", parsed_json.get("follow_up_date", "N/A")],
            ["Diagnosis", parsed_json.get("diagnosis", "N/A"), "", ""],
        ]
        t = Table(info_data, colWidths=[35*mm, 65*mm, 35*mm, 55*mm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F8F9FA')),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#F8F9FA')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E8EAED')),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(t)
        story.append(Spacer(1, 8*mm))

        # Medicines
        story.append(Paragraph("Medicines", heading))
        medicines = parsed_json.get("medicines", [])
        for i, med in enumerate(medicines):
            story.append(Paragraph(
                f"<b>{i+1}. {med.get('name', '')} — {med.get('dosage', '')}</b>",
                ParagraphStyle('medname', parent=styles['Normal'], fontSize=11,
                               textColor=colors.HexColor('#1A73E8'), spaceAfter=2)
            ))
            med_data = [
                ["Frequency", med.get("frequency", "N/A"),
                 "Timing", med.get("timing", "N/A")],
                ["Duration", med.get("duration", "N/A"),
                 "Generic", med.get("generic_name", "N/A")],
                ["Treats", med.get("what_it_treats", "N/A"),
                 "Drug Class", med.get("drug_class", "N/A")],
            ]
            mt = Table(med_data, colWidths=[30*mm, 65*mm, 30*mm, 65*mm])
            mt.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F1F8FF')),
                ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#F1F8FF')),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E8EAED')),
                ('PADDING', (0, 0), (-1, -1), 5),
            ]))
            story.append(mt)

            if med.get("simple_explanation"):
                story.append(Paragraph(
                    f"<i>What it does: {med.get('simple_explanation')}</i>",
                    ParagraphStyle('exp', parent=styles['Normal'],
                                   fontSize=9, textColor=colors.HexColor('#5F6368'), spaceAfter=2)
                ))
            if med.get("generic_cost_saving") and med.get("generic_cost_saving") != "Not specified":
                story.append(Paragraph(
                    f"💰 {med.get('generic_cost_saving')}",
                    ParagraphStyle('saving', parent=styles['Normal'],
                                   fontSize=9, textColor=colors.HexColor('#34A853'), spaceAfter=2)
                ))
            story.append(Spacer(1, 4*mm))

        # Drug interactions
        interactions = parsed_json.get("drug_interactions", [])
        if interactions:
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E8EAED')))
            story.append(Spacer(1, 4*mm))
            story.append(Paragraph("⚠️ Drug Interaction Warnings", heading))
            for inter in interactions:
                meds = " + ".join(inter.get("medicines", []))
                story.append(Paragraph(
                    f"<b>{meds}</b>: {inter.get('description', '')} — {inter.get('action', '')}",
                    ParagraphStyle('warn', parent=styles['Normal'],
                                   fontSize=9, textColor=colors.HexColor('#B31412'), spaceAfter=3)
                ))

        # Red flags
        red_flags = parsed_json.get("red_flags", [])
        if red_flags:
            story.append(Spacer(1, 4*mm))
            story.append(Paragraph("🚩 Red Flags", heading))
            for flag in red_flags:
                story.append(Paragraph(f"• {flag}", normal))

        # Special instructions
        special = parsed_json.get("special_instructions", "")
        if special and special != "Not specified":
            story.append(Spacer(1, 4*mm))
            story.append(Paragraph("Special Instructions", heading))
            story.append(Paragraph(special, normal))

        # Disclaimer
        story.append(Spacer(1, 8*mm))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E8EAED')))
        story.append(Spacer(1, 3*mm))
        story.append(Paragraph(
            "This report is generated by MedSaathi and is not a substitute for professional medical advice. Always consult your doctor.",
            ParagraphStyle('disc', parent=styles['Normal'],
                           fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
        ))

        doc.build(story)
        return output_path

    except Exception as e:
        print(f"Report generation error: {e}")
        return None