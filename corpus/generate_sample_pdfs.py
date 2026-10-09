from pathlib import Path

try:
    from fpdf import FPDF
except ImportError:
    import subprocess
    import sys

    subprocess.check_call([sys.executable, "-m", "pip", "install", "fpdf"])
    from fpdf import FPDF

corpus = Path("corpus")
corpus.mkdir(exist_ok=True)

docs = {
    "wages_act_2019.pdf": [
        "Wages Act 2019\nThis document outlines the minimum wages, overtime, and salary protections for workers.",
        "Chapter 2: Employer Obligations\nEmployers must pay timely wages, maintain wage statements, and ensure no unlawful deductions.",
        "Chapter 3: Worker Rights\nWorkers are entitled to overtime pay, leave, and protection from termination without notice.",
    ],
    "consumer_protection_act_2019.pdf": [
        "Consumer Protection Act 2019\nThis act protects consumers from defective products and deceptive trade practices.",
        "Chapter 5: Rights of Consumers\nConsumers are entitled to refunds, replacements, and adequate information from sellers.",
        "Chapter 8: Consumer Disputes\nCustomers can file complaints for fraud, defective goods, and unfair warranties.",
    ],
    "domestic_violence_act_2005.pdf": [
        "Domestic Violence Act 2005\nThis legislation protects individuals from physical, emotional, and economic abuse by household members.",
        "Section 4: Protection Orders\nA victim may obtain shelter, monetary relief, and custody support from the court.",
        "Section 6: Duties of Agencies\nPolice and shelter homes must assist survivors of domestic violence and provide safe accommodation.",
    ],
    "shops_establishments_act.pdf": [
        "Shops and Establishments Act\nThe act regulates working conditions, opening hours, and leave for shops and commercial establishments.",
        "Section 10: Employee Rights\nEmployees in shops are entitled to weekly holidays, overtime pay, and a safe workplace.",
        "Section 14: Employer Responsibilities\nEmployers must register establishments, maintain records, and comply with labour inspections.",
    ],
}

for filename, pages in docs.items():
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    for page_text in pages:
        pdf.add_page()
        for line in page_text.split("\n"):
            pdf.multi_cell(0, 8, line)
        pdf.ln(4)
    pdf.output(corpus / filename)
    print(f"Created {filename}")
