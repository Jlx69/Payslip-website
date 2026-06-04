from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import io


# ── Company details ─────────────────────────────────────────────────
COMPANY_DETAILS = {
    "Andrew": {
        "name":    "MATHEW ENTERPRISES",
        "address": "VERNA INDUSTRIAL ESTATE",
        "client":  "ANDREW",
    },
    "Commscope": {
        "name":    "MATHEW ENTERPRISES",
        "address": "VERNA INDUSTRIAL ESTATE",
        "client":  "COMMSCOPE",
    },
}

MONTH_SHORT = {
    "January": "JAN", "February": "FEB", "March": "MAR",
    "April": "APR", "May": "MAY", "June": "JUN",
    "July": "JUL", "August": "AUG", "September": "SEP",
    "October": "OCT", "November": "NOV", "December": "DEC"
}


# ── Number to words ─────────────────────────────────────────────────
def number_to_words(n: float) -> str:
    n = int(n)
    ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven",
            "Eight", "Nine", "Ten", "Eleven", "Twelve", "Thirteen",
            "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty",
            "Sixty", "Seventy", "Eighty", "Ninety"]

    def helper(num):
        if num == 0:          return ""
        elif num < 20:        return ones[num] + " "
        elif num < 100:       return tens[num // 10] + " " + helper(num % 10)
        elif num < 1000:      return ones[num // 100] + " Hundred " + helper(num % 100)
        elif num < 100000:    return helper(num // 1000) + "Thousand " + helper(num % 1000)
        elif num < 10000000:  return helper(num // 100000) + "Lakh " + helper(num % 100000)
        else:                 return helper(num // 10000000) + "Crore " + helper(num % 10000000)

    result = helper(n).strip()
    return f"Rupees {result} Only" if result else "Rupees Zero Only"


# ── Style helpers ───────────────────────────────────────────────────
def p_left(size=9, bold=False):
    return ParagraphStyle(f"pl_{size}_{bold}", fontSize=size,
        fontName="Helvetica-Bold" if bold else "Helvetica", alignment=TA_LEFT)

def p_right(size=9, bold=False):
    return ParagraphStyle(f"pr_{size}_{bold}", fontSize=size,
        fontName="Helvetica-Bold" if bold else "Helvetica", alignment=TA_RIGHT)

def p_center(size=9, bold=False):
    return ParagraphStyle(f"pc_{size}_{bold}", fontSize=size,
        fontName="Helvetica-Bold" if bold else "Helvetica", alignment=TA_CENTER)


# ── Main PDF Generator ──────────────────────────────────────────────
def generate_payslip_pdf(employee: dict, payslip: dict) -> bytes:
    buffer = io.BytesIO()
    doc    = SimpleDocTemplate(buffer, pagesize=A4,
        rightMargin=15*mm, leftMargin=15*mm,
        topMargin=12*mm,   bottomMargin=12*mm)
    elements = []

    # ── Company details ──────────────────────────────────────────────
    company    = employee.get("company", "Andrew")
    co         = COMPANY_DETAILS.get(company, COMPANY_DETAILS["Andrew"])
    month_str  = payslip["month"]
    month_abbr = MONTH_SHORT.get(month_str, month_str[:3].upper())
    year       = payslip["year"]

    # ── Header block ─────────────────────────────────────────────────
    # Line 1: MATHEW ENTERPRISES
    elements.append(Paragraph(co["name"], p_center(13, bold=True)))
    # Line 2: VERNA INDUSTRIAL ESTATE
    elements.append(Paragraph(co["address"], p_center(11, bold=True)))
    # Line 3: FORM XV See Rule77(2) (b)
    elements.append(Paragraph("FORM XV See Rule77(2) (b)", p_center(10, bold=False)))
    # Line 4: Wage Slip ANDREW APR / 2026
    elements.append(Paragraph(
        f"Wage Slip {co['client']} {month_abbr} / {year}",
        p_center(11, bold=True)
    ))
    elements.append(Spacer(1, 4*mm))

    # ── Employee Info ────────────────────────────────────────────────
    emp_info = [
        [
            Paragraph("<b>Emp ID</b>",         p_left()),
            Paragraph(employee["employee_id"],  p_left()),
            Paragraph("<b>Employee Name:</b>",  p_left()),
            Paragraph(employee["name"].upper(), p_left()),
        ],
        [
            Paragraph("<b>ESI No.</b>",                   p_left()),
            Paragraph(employee.get("esi_no") or "\u2014", p_left()),
            Paragraph("<b>NDP</b>",                       p_left()),
            Paragraph(str(int(payslip["paid_days"])),      p_left()),
        ],
        [
            Paragraph("<b>UAN</b>",                      p_left()),
            Paragraph(employee.get("uan") or "\u2014",    p_left()),
            Paragraph("", p_left()),
            Paragraph("", p_left()),
        ],
    ]
    emp_table = Table(emp_info, colWidths=[28*mm, 60*mm, 42*mm, 60*mm])
    emp_table.setStyle(TableStyle([
        ("FONTSIZE",      (0,0), (-1,-1), 9),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
    ]))
    elements.append(emp_table)
    elements.append(Spacer(1, 4*mm))

    # ── Earnings & Deductions ────────────────────────────────────────
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
    while len(deductions) < len(earnings):
        deductions.append(("", ""))

    COL = [55*mm, 35*mm, 55*mm, 35*mm]

    table_data = [[
        Paragraph("<b>Earnings</b>",   p_left(bold=True)),
        Paragraph("<b>Amount</b>",     p_right(bold=True)),
        Paragraph("<b>Deductions</b>", p_left(bold=True)),
        Paragraph("<b>Amount</b>",     p_right(bold=True)),
    ]]
    for i in range(len(earnings)):
        e_name, e_amt = earnings[i]
        d_name, d_amt = deductions[i]
        e_str = f"{e_amt:,.2f}" if isinstance(e_amt, (int,float)) and e_amt else ""
        d_str = f"{d_amt:,.2f}" if isinstance(d_amt, (int,float)) and d_amt else ""
        table_data.append([
            Paragraph(e_name, p_left()),  Paragraph(e_str,  p_right()),
            Paragraph(d_name, p_left()),  Paragraph(d_str,  p_right()),
        ])
    for _ in range(3):
        table_data.append([Paragraph("", p_left())] * 4)
    table_data.append([
        Paragraph("<b>Total</b>",                              p_left(bold=True)),
        Paragraph(f"<b>{payslip['gross_salary']:,.2f}</b>",    p_right(bold=True)),
        Paragraph("<b>Total</b>",                              p_left(bold=True)),
        Paragraph(f"<b>{payslip['total_deduction']:,.2f}</b>", p_right(bold=True)),
    ])

    pay_table = Table(table_data, colWidths=COL)
    pay_table.setStyle(TableStyle([
        ("BOX",          (0,0), (-1,-1),  0.75, colors.black),
        ("LINEAFTER",    (1,0), (1,-1),   0.75, colors.black),
        ("LINEABOVE",    (0,-1),(-1,-1),  0.75, colors.black),
        ("TOPPADDING",   (0,0), (-1,-1),  6),
        ("BOTTOMPADDING",(0,0), (-1,-1),  6),
        ("LEFTPADDING",  (0,0), (-1,-1),  6),
        ("RIGHTPADDING", (0,0), (-1,-1),  6),
        ("FONTSIZE",     (0,0), (-1,-1),  9),
        ("VALIGN",       (0,0), (-1,-1),  "MIDDLE"),
    ]))
    elements.append(pay_table)

    # ── Net Pay ──────────────────────────────────────────────────────
    net_table = Table([[
        Paragraph("<b>Net Pay</b>", p_left(bold=True)),
        Paragraph(f"<b>{payslip['net_salary']:,.2f}</b>", p_right(bold=True)),
        Paragraph("", p_left()), Paragraph("", p_left()),
    ]], colWidths=COL)
    net_table.setStyle(TableStyle([
        ("BOX",          (0,0),(-1,-1), 0.75, colors.black),
        ("LINEAFTER",    (1,0),(1,0),   0.75, colors.black),
        ("TOPPADDING",   (0,0),(-1,-1), 6),
        ("BOTTOMPADDING",(0,0),(-1,-1), 6),
        ("LEFTPADDING",  (0,0),(-1,-1), 6),
        ("RIGHTPADDING", (0,0),(-1,-1), 6),
        ("FONTSIZE",     (0,0),(-1,-1), 9),
    ]))
    elements.append(net_table)

    # ── In Words ─────────────────────────────────────────────────────
    words_table = Table([[
        Paragraph("<b>In Words</b>", p_left(bold=True)),
        Paragraph(number_to_words(payslip["net_salary"]), p_left()),
    ]], colWidths=[28*mm, 152*mm])
    words_table.setStyle(TableStyle([
        ("BOX",          (0,0),(-1,-1), 0.75, colors.black),
        ("TOPPADDING",   (0,0),(-1,-1), 6),
        ("BOTTOMPADDING",(0,0),(-1,-1), 6),
        ("LEFTPADDING",  (0,0),(-1,-1), 6),
        ("RIGHTPADDING", (0,0),(-1,-1), 6),
        ("FONTSIZE",     (0,0),(-1,-1), 9),
        ("VALIGN",       (0,0),(-1,-1), "MIDDLE"),
    ]))
    elements.append(words_table)

    # ── Signature ────────────────────────────────────────────────────
    elements.append(Spacer(1, 10*mm))
    elements.append(Paragraph("Signature",
        ParagraphStyle("sig", fontSize=9, alignment=TA_RIGHT, fontName="Helvetica")))

    doc.build(elements)
    buffer.seek(0)
    return buffer.read()
