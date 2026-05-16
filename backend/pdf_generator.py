from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import io


# ── Convert number to words (Indian style) ─────────────────────────
def number_to_words(n: float) -> str:
    n = int(n)
    ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven",
            "Eight", "Nine", "Ten", "Eleven", "Twelve", "Thirteen",
            "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty",
            "Sixty", "Seventy", "Eighty", "Ninety"]

    def helper(num):
        if num == 0:
            return ""
        elif num < 20:
            return ones[num] + " "
        elif num < 100:
            return tens[num // 10] + " " + helper(num % 10)
        elif num < 1000:
            return ones[num // 100] + " Hundred " + helper(num % 100)
        elif num < 100000:
            return helper(num // 1000) + "Thousand " + helper(num % 1000)
        elif num < 10000000:
            return helper(num // 100000) + "Lakh " + helper(num % 100000)
        else:
            return helper(num // 10000000) + "Crore " + helper(num % 10000000)

    result = helper(n).strip()
    return f"Rupees {result} Only" if result else "Rupees Zero Only"


# ── Paragraph style helpers ─────────────────────────────────────────
def normal_left(size=9, bold=False):
    return ParagraphStyle(
        f"nl_{size}_{bold}",
        fontSize=size,
        fontName="Helvetica-Bold" if bold else "Helvetica",
        alignment=TA_LEFT,
    )

def normal_right(size=9, bold=False):
    return ParagraphStyle(
        f"nr_{size}_{bold}",
        fontSize=size,
        fontName="Helvetica-Bold" if bold else "Helvetica",
        alignment=TA_RIGHT,
    )


# ── Main PDF Generator ──────────────────────────────────────────────
def generate_payslip_pdf(employee: dict, payslip: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=12*mm,
        bottomMargin=12*mm
    )

    elements = []

    # ── Styles ──────────────────────────────────────────────────────
    header_style = ParagraphStyle(
        "header", fontSize=13, alignment=TA_CENTER,
        fontName="Helvetica-Bold", spaceAfter=2
    )
    subheader_style = ParagraphStyle(
        "subheader", fontSize=11, alignment=TA_CENTER,
        fontName="Helvetica-Bold", spaceAfter=6
    )

    # ── Company Header ───────────────────────────────────────────────
    elements.append(Paragraph("MATHEW ENTERPRISES", header_style))
    elements.append(Paragraph("VERNA INDUSTRIAL ESTATE", header_style))
    elements.append(Paragraph(
        f"WAGE SLIP ANDREW AMPHENOL for the month of "
        f"{payslip['month'][:3].upper()}/{payslip['year']}",
        subheader_style
    ))
    elements.append(Spacer(1, 4*mm))

    # ── Employee Info ────────────────────────────────────────────────
    emp_info = [
        [
            Paragraph("<b>Emp ID</b>",        normal_left()),
            Paragraph(employee["employee_id"], normal_left()),
            Paragraph("<b>Employee Name:</b>", normal_left()),
            Paragraph(employee["name"].upper(), normal_left()),
        ],
        [
            Paragraph("<b>ESI No.</b>",                    normal_left()),
            Paragraph(employee.get("esi_no") or "\u2014",  normal_left()),
            Paragraph("<b>NDP</b>",                        normal_left()),
            Paragraph(str(int(payslip["paid_days"])),       normal_left()),
        ],
        [
            Paragraph("<b>UAN</b>",                       normal_left()),
            Paragraph(employee.get("uan") or "\u2014",     normal_left()),
            Paragraph("", normal_left()),
            Paragraph("", normal_left()),
        ],
    ]

    emp_table = Table(emp_info, colWidths=[28*mm, 60*mm, 42*mm, 60*mm])
    emp_table.setStyle(TableStyle([
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
    ]))
    elements.append(emp_table)
    elements.append(Spacer(1, 4*mm))

    # ── Earnings & Deductions Table ──────────────────────────────────
    earnings = [
        ("BASIC",      payslip["basic"]),
        ("BONUS",      payslip["bonus"]),
        ("SHIFT ALLO", payslip["shift_allowance"]),
        ("INCENTIVE",  payslip["incentive"]),
        ("LWW",        payslip["lww"]),
    ]

    deductions = [
        ("PF",        payslip["pf"]),
        ("ESI",       payslip.get("esic") or 0),
        ("LWF",       payslip["lwf"]),
        ("TRANSPORT", payslip["transport"]),
    ]

    # Pad deductions to match earnings row count
    while len(deductions) < len(earnings):
        deductions.append(("", ""))

    # Column widths: label | amount | label | amount
    COL = [55*mm, 35*mm, 55*mm, 35*mm]

    # Header row
    table_data = [[
        Paragraph("<b>Earnings</b>",  normal_left(bold=True)),
        Paragraph("<b>Amount</b>",    normal_right(bold=True)),
        Paragraph("<b>Deductions</b>",normal_left(bold=True)),
        Paragraph("<b>Amount</b>",    normal_right(bold=True)),
    ]]

    # Data rows
    for i in range(len(earnings)):
        e_name, e_amt = earnings[i]
        d_name, d_amt = deductions[i]

        # Only show amount if non-zero
        e_str = f"{e_amt:,.2f}" if isinstance(e_amt, (int, float)) and e_amt else ""
        d_str = f"{d_amt:,.2f}" if isinstance(d_amt, (int, float)) and d_amt else ""

        table_data.append([
            Paragraph(e_name, normal_left()),
            Paragraph(e_str,  normal_right()),   # ✅ RIGHT aligned
            Paragraph(d_name, normal_left()),
            Paragraph(d_str,  normal_right()),   # ✅ RIGHT aligned
        ])

    # Empty spacer rows (to match original layout)
    for _ in range(3):
        table_data.append([
            Paragraph("", normal_left()),
            Paragraph("", normal_right()),
            Paragraph("", normal_left()),
            Paragraph("", normal_right()),
        ])

    # Totals row
    table_data.append([
        Paragraph("<b>Total</b>",                              normal_left(bold=True)),
        Paragraph(f"<b>{payslip['gross_salary']:,.2f}</b>",    normal_right(bold=True)),  # ✅ RIGHT
        Paragraph("<b>Total</b>",                              normal_left(bold=True)),
        Paragraph(f"<b>{payslip['total_deduction']:,.2f}</b>", normal_right(bold=True)),  # ✅ RIGHT
    ])

    pay_table = Table(table_data, colWidths=COL)
    pay_table.setStyle(TableStyle([
        ("BOX",          (0, 0), (-1, -1),  0.75, colors.black),
        ("LINEAFTER",    (1, 0), (1, -1),   0.75, colors.black),   # divider between E and D
        ("LINEABOVE",    (0, -1), (-1, -1), 0.75, colors.black),   # line above totals
        ("TOPPADDING",   (0, 0), (-1, -1),  6),
        ("BOTTOMPADDING",(0, 0), (-1, -1),  6),
        ("LEFTPADDING",  (0, 0), (-1, -1),  6),
        ("RIGHTPADDING", (0, 0), (-1, -1),  6),
        ("FONTSIZE",     (0, 0), (-1, -1),  9),
        ("VALIGN",       (0, 0), (-1, -1),  "MIDDLE"),
    ]))
    elements.append(pay_table)

    # ── Net Pay Row ──────────────────────────────────────────────────
    net_data = [[
        Paragraph("<b>Net Pay</b>", normal_left(bold=True)),
        Paragraph(f"<b>{payslip['net_salary']:,.2f}</b>", normal_right(bold=True)),  # ✅ RIGHT
        Paragraph("", normal_left()),
        Paragraph("", normal_left()),
    ]]
    net_table = Table(net_data, colWidths=COL)
    net_table.setStyle(TableStyle([
        ("BOX",          (0, 0), (-1, -1), 0.75, colors.black),
        ("LINEAFTER",    (1, 0), (1, 0),   0.75, colors.black),
        ("TOPPADDING",   (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("FONTSIZE",     (0, 0), (-1, -1), 9),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(net_table)

    # ── In Words Row ─────────────────────────────────────────────────
    words = number_to_words(payslip["net_salary"])
    words_data = [[
        Paragraph("<b>In Words</b>", normal_left(bold=True)),
        Paragraph(words, normal_left()),   # ✅ LEFT aligned
    ]]
    words_table = Table(words_data, colWidths=[28*mm, 152*mm])
    words_table.setStyle(TableStyle([
        ("BOX",          (0, 0), (-1, -1), 0.75, colors.black),
        ("TOPPADDING",   (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("FONTSIZE",     (0, 0), (-1, -1), 9),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(words_table)

    # ── Signature ────────────────────────────────────────────────────
    elements.append(Spacer(1, 10*mm))
    elements.append(Paragraph(
        "Signature",
        ParagraphStyle("sig", fontSize=9, alignment=TA_RIGHT, fontName="Helvetica")
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer.read()