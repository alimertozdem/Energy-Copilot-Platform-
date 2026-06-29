#!/usr/bin/env python3
"""Generate the EnergyLens sample client report PDF (illustrative, synthetic data).
Reusable: python3 scripts/build_sample_report.py [output.pdf]
Source narrative: docs/strategy/2026-06-18_sample-client-report-FINAL.md
Robust metrics only; under-review absolute EUR savings intentionally omitted."""
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
                                Spacer, Table, TableStyle, KeepTogether)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER

OUT = sys.argv[1] if len(sys.argv) > 1 else "EnergyLens_Sample_Report.pdf"

NAVY=colors.HexColor('#0A1628'); DEEP=colors.HexColor('#0F6E56'); EMER=colors.HexColor('#1D9E75')
MINT=colors.HexColor('#5DCAA5'); GLOW=colors.HexColor('#C0DD97'); PULSE=colors.HexColor('#639922')
RED=colors.HexColor('#C0392B'); AMBER=colors.HexColor('#B7791F'); SLATE=colors.HexColor('#5B6B7B')
INK=colors.HexColor('#2C2C2A'); CARD=colors.HexColor('#EAF5EF'); LINE=colors.HexColor('#D7E3DB')
REDBG=colors.HexColor('#F7E7E4'); GRNBG=colors.HexColor('#E7F4EE')
PW,PH=A4; M=15*mm; BAND=24*mm

def P(t,s): return Paragraph(t,s)
h1=ParagraphStyle('h1',fontName='Helvetica-Bold',fontSize=15,leading=18,textColor=NAVY,spaceAfter=2)
sub=ParagraphStyle('sub',fontName='Helvetica',fontSize=9,leading=12,textColor=SLATE,spaceAfter=8)
h2=ParagraphStyle('h2',fontName='Helvetica-Bold',fontSize=10.5,leading=13,textColor=DEEP,spaceBefore=9,spaceAfter=3)
body=ParagraphStyle('body',fontName='Helvetica',fontSize=8.6,leading=11.6,textColor=INK,spaceAfter=3)
small=ParagraphStyle('small',fontName='Helvetica-Oblique',fontSize=7.6,leading=10,textColor=SLATE,spaceAfter=2)
knum=ParagraphStyle('knum',fontName='Helvetica-Bold',fontSize=17,leading=18,textColor=DEEP,alignment=TA_LEFT)
klab=ParagraphStyle('klab',fontName='Helvetica',fontSize=7.7,leading=9.5,textColor=INK)
ch=ParagraphStyle('ch',fontName='Helvetica-Bold',fontSize=7.8,leading=9,textColor=colors.white,alignment=TA_CENTER)
cell=ParagraphStyle('cell',fontName='Helvetica',fontSize=8.3,leading=10,textColor=INK)
cellb=ParagraphStyle('cellb',fontName='Helvetica-Bold',fontSize=8.3,leading=10,textColor=NAVY)
cellc=ParagraphStyle('cellc',fontName='Helvetica',fontSize=8.3,leading=10,textColor=INK,alignment=TA_CENTER)
stp=ParagraphStyle('stp',fontName='Helvetica-Bold',fontSize=8,leading=9.5,alignment=TA_CENTER)

def deco(c,doc):
    c.saveState()
    c.setFillColor(NAVY); c.rect(0,PH-BAND,PW,BAND,fill=1,stroke=0)
    c.setFillColor(EMER); c.rect(0,PH-BAND-1.4*mm,PW,1.4*mm,fill=1,stroke=0)
    c.setFillColor(MINT); c.setFont('Helvetica-Bold',19); c.drawString(M,PH-12.5*mm,"EnergyLens")
    c.setFillColor(GLOW); c.setFont('Helvetica',8.3)
    c.drawString(M,PH-18*mm,"Energy & EU-compliance intelligence, from your bills")
    c.setFillColor(colors.white); c.setFont('Helvetica-Bold',8.2)
    c.drawRightString(PW-M,PH-11.5*mm,"SAMPLE REPORT")
    c.setFillColor(colors.HexColor('#9FB0C0')); c.setFont('Helvetica',7.4)
    c.drawRightString(PW-M,PH-16*mm,"Illustrative - synthetic data")
    c.setStrokeColor(EMER); c.setLineWidth(0.8); c.line(M,14.5*mm,PW-M,14.5*mm)
    c.setFillColor(SLATE); c.setFont('Helvetica',6.8)
    c.drawString(M,11*mm,"Illustrative example on sample data, not a real client. Screening-grade, ESRS-E1-aligned, assumptions stated - not a certified Energieausweis / iSFP.")
    c.drawString(M,8*mm,"Live demo: energy-copilot-platform.vercel.app/demo")
    c.drawRightString(PW-M,8*mm,"Page %d"%doc.page)
    c.restoreState()

doc=BaseDocTemplate(OUT,pagesize=A4,leftMargin=M,rightMargin=M,topMargin=BAND+4*mm,bottomMargin=16*mm,title="EnergyLens - Sample Portfolio Screening")
frame=Frame(M,16*mm,PW-2*M,PH-BAND-4*mm-16*mm,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
doc.addPageTemplates([PageTemplate(id='main',frames=[frame],onPage=deco)])
S=[]
S.append(P("Portfolio EPBD &amp; Carbon Screening",h1))
S.append(P("A 9-building mixed commercial portfolio assessed against EU compliance trajectories (EPBD / GEG), CRREM stranding and rising carbon cost - built from existing meter and bill data. No new hardware, no site visit.",sub))

def card(num,lab,nc=DEEP):
    n=ParagraphStyle('n',parent=knum,textColor=nc)
    return [P(num,n),Spacer(1,1),P(lab,klab)]
cards=Table([[card("3 / 9","assets already <b>stranded</b> vs the CRREM pathway - risk is live today, not future."),
              card("3.6x","worst asset vs the peer energy benchmark (~7 GWh/yr, ~&euro;1.5M/yr spend).",RED),
              card("On&nbsp;track","best asset (Berlin office, EPC B) - the method validates well-run stock, not blanket alarm.",EMER)]],
             colWidths=[(PW-2*M)/3.0]*3)
cards.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),CARD),('BOX',(0,0),(0,0),0,CARD),
    ('LINEABOVE',(0,0),(-1,0),1.4,EMER),('VALIGN',(0,0),(-1,-1),'TOP'),
    ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
    ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),
    ('LINEAFTER',(0,0),(0,0),3,colors.white),('LINEAFTER',(1,0),(1,0),3,colors.white)]))
S.append(cards); S.append(Spacer(1,6))

S.append(P("1.  Portfolio screening - order of priority",h2))
def st(txt,bg):
    return Table([[P(txt,ParagraphStyle('x',parent=stp,textColor=colors.white))]],colWidths=[26*mm],
        style=[('BACKGROUND',(0,0),(-1,-1),bg),('TOPPADDING',(0,0),(-1,-1),2),('BOTTOMPADDING',(0,0),(-1,-1),2),
        ('LEFTPADDING',(0,0),(-1,-1),2),('RIGHTPADDING',(0,0),(-1,-1),2)])
hd=lambda t:P(t,ParagraphStyle('hd',parent=cellb,textColor=colors.white,fontSize=8,alignment=TA_CENTER))
rows=[[P("Asset (type)",ParagraphStyle('h',parent=cellb,textColor=colors.white,fontSize=8)),hd("EPC"),hd("Carbon<br/>kg CO2/m2/yr"),hd("CRREM<br/>pathway"),hd("Status")]]
data=[("Healthcare, Frankfurt","C","232","92","Stranded ~2.5x",RED),
      ("Retail, Istanbul","E","151","44","Stranded",RED),
      ("Hotel, Vienna","C","85","72","Stranded",RED),
      ("Logistics, Hamburg","A","55","58","On track",EMER),
      ("Education, Amsterdam","D","50","55","On track",EMER),
      ("Office, Berlin","B","25","42","On track",EMER),
      ("+ 3 more assets","-","-","-","On track",EMER)]
for nm,epc,ci,cr,stt,col in data:
    rows.append([P(nm,cell),P(epc,cellc),P(ci,cellc),P(cr,cellc),st(stt,col)])
t=Table(rows,colWidths=[52*mm,14*mm,30*mm,24*mm,30*mm])
ts=[('BACKGROUND',(0,0),(-1,0),NAVY),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
    ('TOPPADDING',(0,0),(-1,-1),3.5),('BOTTOMPADDING',(0,0),(-1,-1),3.5),
    ('LEFTPADDING',(0,0),(-1,-1),5),('LINEBELOW',(0,0),(-1,-1),0.4,LINE),('ALIGN',(1,0),(3,-1),'CENTER')]
for i in range(1,len(rows)):
    if i%2==0: ts.append(('BACKGROUND',(0,i),(-1,i),colors.HexColor('#F6F8F7')))
t.setStyle(TableStyle(ts)); S.append(t)
S.append(P("Capital goes to the three stranded assets first. An atypical data-centre asset is excluded from the benchmark - its EUI is an order of magnitude above any habitable building and would distort the comparison.",small))

S.append(P("2.  Stranded-asset drill-down - Frankfurt healthcare facility",h2))
S.append(P("<b>Profile.</b> EPC C, EUI ~544 kWh/m2/yr = <b>363% of the peer benchmark</b>; ~7 GWh/yr; ~&euro;1.5M/yr energy spend.",body))
S.append(P("<b>Compliance risk.</b> Carbon intensity <b>232 vs 92</b> on the CRREM pathway -> <b>stranded now</b>, with a rising CO2 levy on top (open HIGH_CARBON_INTENSITY flag).",body))
S.append(P("<b>Operational faults (from existing data, no new sensors).</b> Supply-air-temperature faults on two AHUs and after-hours HVAC outside occupancy - low / no-capex first wins. HVAC is ~40% of load, so controls, scheduling and heat-recovery are the top levers.",body))
S.append(P("<b>Recommended measures, ranked by payback (not additive).</b> Building-management / controls optimisation, HVAC scheduling, peak-demand management, battery storage, and a mandatory energy audit (GEG / EnEfG obligation at this size). Several qualify for <b>BAFA / KfW</b> support. Absolute savings are indicative; the ranking and direction are the robust output - the headline is: this asset is non-compliant and over-spending, here is the fix order.",body))

S.append(P("3.  Well-managed contrast - Berlin office",h2))
S.append(P("EPC B, EUI ~74 kWh/m2/yr, carbon <b>25 vs 42</b> -> <b>on track</b>. Shown to prove the screening validates good assets rather than raising blanket alarm. Action: monitoring and protect-the-rating. The method separates real risk from well-run stock - credibility, not noise.",body))

S.append(P("4.  Recommended actions &amp; financing",h2))
S.append(P("<b>1. Operations first</b> (weeks, ~no capex): fix AHU faults and after-hours HVAC on the stranded asset.",body))
S.append(P("<b>2. Controls &amp; demand</b> (this year): BMS optimisation, HVAC scheduling, peak-demand management.",body))
S.append(P("<b>3. Fabric &amp; systems</b> (capital, subsidy-backed): envelope and plant where heat-loss and the CRREM gap are largest - screen BAFA / KfW first; 30%+ grants change the answer.",body))
S.append(P("<b>4. Track:</b> re-run after each measure and watch the stranding year move out.",body))

S.append(P("5.  Assumptions &amp; method",h2))
S.append(P("Screening / decision-support, not a certified Energieausweis or iSFP. Built from meter / bill plus building data; gaps filled by an estimation model with stated ranges. Carbon assessed vs CRREM 1.5-2 C; carbon cost on the German trajectory toward ETS2. ESRS-E1-aligned presentation (not a CSRD statement). Confirm figures before any capital commitment.",body))
doc.build(S)
print("OK ->",OUT)
