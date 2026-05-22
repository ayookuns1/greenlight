"""
Generate two PDFs for Team Greenlight:
  1. greenlight_simple.pdf  — plain-English overview for non-technical partner
  2. greenlight_technical.pdf — full solution paper for judges / technical partner
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from pathlib import Path

OUT = Path("C:/Users/Ayoola/Downloads/greenlight/results")
OUT.mkdir(exist_ok=True)

# ─── Colour palette ──────────────────────────────────────────────────────────
GREEN  = colors.HexColor("#1B5E20")
LGREEN = colors.HexColor("#4CAF50")
MINT   = colors.HexColor("#E8F5E9")
GREY   = colors.HexColor("#F5F5F5")
DGREY  = colors.HexColor("#424242")
WHITE  = colors.white

W, H = A4
# usable width = 21cm - 2.5cm - 2.5cm = 16cm
PAGE_W = 16 * cm


# ══════════════════════════════════════════════════════════════════════════════
# SIMPLE PDF
# ══════════════════════════════════════════════════════════════════════════════
def make_simple():
    doc = SimpleDocTemplate(
        str(OUT / "greenlight_simple.pdf"),
        pagesize=A4,
        leftMargin=2.5*cm, rightMargin=2.5*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )

    base = getSampleStyleSheet()

    title_s = ParagraphStyle("stitle", parent=base["Title"],
        fontSize=26, textColor=GREEN, spaceAfter=4, alignment=TA_CENTER,
        fontName="Helvetica-Bold")

    sub_s = ParagraphStyle("ssub", parent=base["Normal"],
        fontSize=13, textColor=DGREY, alignment=TA_CENTER, spaceAfter=16)

    h1_s = ParagraphStyle("sh1", parent=base["Heading1"],
        fontSize=16, textColor=GREEN, spaceBefore=18, spaceAfter=6,
        fontName="Helvetica-Bold", borderPad=0)

    h2_s = ParagraphStyle("sh2", parent=base["Heading2"],
        fontSize=13, textColor=LGREEN, spaceBefore=12, spaceAfter=4,
        fontName="Helvetica-Bold")

    body_s = ParagraphStyle("sbody", parent=base["Normal"],
        fontSize=11, leading=17, spaceAfter=8, alignment=TA_JUSTIFY,
        textColor=DGREY)

    bullet_s = ParagraphStyle("sbullet", parent=body_s,
        leftIndent=18, bulletIndent=6, spaceAfter=5)

    caption_s = ParagraphStyle("scap", parent=base["Normal"],
        fontSize=9, textColor=colors.grey, alignment=TA_CENTER, spaceAfter=4)

    def hr(): return HRFlowable(width="100%", thickness=1,
                                color=LGREEN, spaceAfter=10, spaceBefore=4)

    def sp(n=8): return Spacer(1, n)

    def box(text, bg=MINT, border=LGREEN):
        t = Table([[Paragraph(text, body_s)]],
                  colWidths=[PAGE_W])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), bg),
            ("BOX",        (0,0), (-1,-1), 1, border),
            ("LEFTPADDING",(0,0), (-1,-1), 12),
            ("RIGHTPADDING",(0,0),(-1,-1), 12),
            ("TOPPADDING", (0,0), (-1,-1), 8),
            ("BOTTOMPADDING",(0,0),(-1,-1), 8),
        ]))
        return t

    story = []

    # ── Cover ─────────────────────────────────────────────────────────────────
    story += [
        sp(30),
        Paragraph("Team Greenlight", title_s),
        Paragraph("DSN x BCT LLM Agent Hackathon 3.0", sub_s),
        sp(6),
        Paragraph("Project Overview — Plain English Edition", ParagraphStyle(
            "cov", parent=sub_s, fontSize=11, textColor=LGREEN)),
        sp(6),
        hr(),
        sp(40),
        Paragraph("What We Built  |  How It Works  |  Why It Matters",
                  ParagraphStyle("cov2", parent=caption_s, fontSize=10,
                                 textColor=DGREY)),
        PageBreak(),
    ]

    # ── Section 1: The Big Picture ────────────────────────────────────────────
    story += [
        Paragraph("1. What Is This Project About?", h1_s), hr(),
        box(
            "We built an AI system that reads thousands of product and "
            "restaurant reviews, learns each person's taste, and then does "
            "two powerful things: (1) writes a new review the way that "
            "specific person would write it, and (2) recommends products "
            "that person would actually enjoy — all in Nigerian English."
        ),
        sp(),
        Paragraph(
            "Think of it like this: if you gave our AI your name, it would "
            "study all your past reviews, figure out whether you love spicy "
            "food or prefer mild, whether you write long detailed opinions "
            "or short punchy ones, and whether you tend to rate things 4 "
            "stars or 2 stars. Then it could write a review <i>as you</i> "
            "for any new item, or suggest products you'd probably love.",
            body_s),
        sp(),
        Paragraph(
            "This is called <b>User Modelling and Personalised "
            "Recommendation</b> — two of the most in-demand skills in AI "
            "right now, used by Netflix, Spotify, and Amazon every day.",
            body_s),
    ]

    # ── Section 2: The Two Tasks ──────────────────────────────────────────────
    story += [
        sp(), Paragraph("2. The Two Things Our System Does", h1_s), hr(),

        Paragraph("Task A — Writing Reviews in Your Style", h2_s),
        Paragraph(
            "You give the system a user ID and a product name. The AI "
            "looks up that user's history, understands their personality "
            "(Do they love things? Are they critical? Do they write essays "
            "or one-liners?), and generates a completely new review that "
            "sounds exactly like them — in Nigerian English with natural "
            "Pidgin phrases like <i>\"I no go lie,\"</i> "
            "<i>\"e dey sweet,\"</i> and <i>\"abeg.\"</i>",
            body_s),
        sp(4),

        Paragraph("Task B — Recommending Things You'd Love", h2_s),
        Paragraph(
            "You give the system a user ID and it searches through nearly "
            "10,000 real reviews to find items that match that person's "
            "taste. It doesn't just match keywords — it understands meaning. "
            "If you love 'bold flavours' it finds items described as "
            "'intense' or 'rich' too. Then an AI reranks the results and "
            "explains each recommendation in Pidgin English.",
            body_s),
        sp(4),

        Paragraph("Cold-Start (New Users)", h2_s),
        Paragraph(
            "What if someone is brand new with no history? Our system "
            "handles that too. You just describe what you want in plain "
            "English — <i>\"healthy low-sugar office snacks\"</i> — and "
            "it finds matching items without needing any past reviews.",
            body_s),
    ]

    # ── Section 3: The Data ───────────────────────────────────────────────────
    story += [
        sp(), Paragraph("3. Where Did the Data Come From?", h1_s), hr(),
        Paragraph(
            "We used three large public datasets totalling nearly 10,000 "
            "real human reviews:", body_s),
        Paragraph("• <b>Yelp</b> — restaurant and business reviews (5,000 reviews)",
                  bullet_s),
        Paragraph("• <b>Amazon Grocery</b> — food product reviews (3,000 reviews)",
                  bullet_s),
        Paragraph("• <b>Amazon Books</b> — book reviews used in place of Goodreads, "
                  "which is no longer publicly available (2,000 reviews)", bullet_s),
        sp(4),
        Paragraph(
            "From these we built profiles for 1,271 users — storing each "
            "person's average rating, writing style, typical review length, "
            "and most-used words. All of this is processed automatically "
            "by our data pipeline.", body_s),
    ]

    # ── Section 4: Nigerian English ───────────────────────────────────────────
    story += [
        sp(), Paragraph("4. Why Nigerian English?", h1_s), hr(),
        box(
            "The hackathon specifically rewards cultural relevance for "
            "African markets. We localised the entire output layer to use "
            "natural Nigerian English and Pidgin expressions — not "
            "awkward translations, but the way Nigerians actually talk "
            "online and in reviews."
        ),
        sp(),
        Paragraph(
            "Phrases like <i>\"I no go lie, this burger dey mad!\"</i> or "
            "<i>\"abeg, the service na wa o\"</i> are baked into our AI "
            "prompts so every recommendation explanation and generated "
            "review feels local and authentic, not foreign.",
            body_s),
    ]

    # ── Section 5: Results ────────────────────────────────────────────────────
    story += [
        sp(), Paragraph("5. How Well Does It Work?", h1_s), hr(),
        Paragraph("Task A — Review Generation Results (16 users tested):",
                  ParagraphStyle("rh", parent=body_s, fontName="Helvetica-Bold")),
        sp(4),
    ]

    data_a = [
        ["Metric", "Score", "What It Means"],
        ["Text Similarity (ROUGE-L)", "0.1357", "Vocabulary overlap with real reviews"],
        ["Rating Accuracy (RMSE)",    "0.87 stars", "Average star prediction error"],
        ["Style Match Rate",          "100%", "User profile found every time"],
        ["Avg Review Length",         "1,142 chars", "Detailed, substantial reviews"],
    ]
    ta = Table(data_a, colWidths=[6*cm, 3.5*cm, 6.5*cm])
    ta.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  GREEN),
        ("TEXTCOLOR",     (0,0), (-1,0),  WHITE),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 10),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [WHITE, GREY]),
        ("GRID",          (0,0), (-1,-1), 0.5, colors.lightgrey),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
        ("RIGHTPADDING",  (0,0), (-1,-1), 8),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(ta)
    story.append(sp(10))

    story.append(Paragraph("Task B — Recommendation Results (20 users + 5 cold-start):",
                  ParagraphStyle("rh2", parent=body_s, fontName="Helvetica-Bold")))
    story.append(sp(4))
    data_b = [
        ["Metric", "Score", "What It Means"],
        ["Hit Rate@5",        "0.6500 (65%)", "Ground truth item in top 5 for 13 of 20 users"],
        ["NDCG@5",            "0.2968",       "Relevant items appear near the top of rankings"],
        ["Cold-start success","5/5 (100%)",   "All new users got relevant recommendations"],
        ["Users evaluated",   "20/20",        "Full evaluation set completed"],
    ]
    tb = Table(data_b, colWidths=[5.5*cm, 3.5*cm, 7*cm])
    tb.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  GREEN),
        ("TEXTCOLOR",     (0,0), (-1,0),  WHITE),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 10),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [WHITE, GREY]),
        ("GRID",          (0,0), (-1,-1), 0.5, colors.lightgrey),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
        ("RIGHTPADDING",  (0,0), (-1,-1), 8),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(tb)

    # ── Section 6: Tech Summary ───────────────────────────────────────────────
    story += [
        sp(), Paragraph("6. Technology (Simplified)", h1_s), hr(),
        Paragraph(
            "Here is what is powering everything under the hood, "
            "in plain terms:", body_s),
        Paragraph("• <b>Google Gemini 2.5 Flash</b> — the large language model that reads "
                  "user profiles and writes reviews and recommendation explanations", bullet_s),
        Paragraph("• <b>FAISS</b> — a Facebook search engine that finds similar "
                  "reviews at lightning speed (like Google but for meaning)", bullet_s),
        Paragraph("• <b>Sentence Transformers</b> — converts text into numbers so "
                  "the search engine can compare meaning, not just words", bullet_s),
        Paragraph("• <b>FastAPI</b> — the web framework that serves everything as "
                  "a professional API with two separate services", bullet_s),
        Paragraph("• <b>Docker</b> — packages everything into containers so the "
                  "system runs identically anywhere", bullet_s),
        sp(6),
        box("The entire system is containerised, documented, and ready to "
            "deploy. Both APIs have health checks, full error handling, and "
            "professional documentation built in."),
    ]

    # ── Section 7: Team ───────────────────────────────────────────────────────
    story += [
        sp(), Paragraph("7. Team Greenlight", h1_s), hr(),
        Paragraph(
            "We are competing in the DSN x BCT LLM Agent Hackathon 3.0 "
            "under the team name <b>Greenlight</b>. This document covers "
            "our submission for the User Modelling and Recommendation "
            "track. The full technical solution paper is available "
            "separately for judges and technical reviewers.",
            body_s),
        sp(20),
        Paragraph("— Team Greenlight, May 2026", ParagraphStyle(
            "sig", parent=body_s, alignment=TA_CENTER,
            textColor=DGREY, fontName="Helvetica-Oblique")),
    ]

    doc.build(story)
    print("greenlight_simple.pdf created")


# ══════════════════════════════════════════════════════════════════════════════
# TECHNICAL PDF
# ══════════════════════════════════════════════════════════════════════════════
def make_technical():
    doc = SimpleDocTemplate(
        str(OUT / "greenlight_technical.pdf"),
        pagesize=A4,
        leftMargin=2.5*cm, rightMargin=2.5*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )

    base = getSampleStyleSheet()

    title_s = ParagraphStyle("ttitle", parent=base["Title"],
        fontSize=24, textColor=GREEN, spaceAfter=4, alignment=TA_CENTER,
        fontName="Helvetica-Bold")

    sub_s = ParagraphStyle("tsub", parent=base["Normal"],
        fontSize=11, textColor=DGREY, alignment=TA_CENTER, spaceAfter=12)

    h1_s = ParagraphStyle("th1", parent=base["Heading1"],
        fontSize=15, textColor=GREEN, spaceBefore=20, spaceAfter=6,
        fontName="Helvetica-Bold")

    h2_s = ParagraphStyle("th2", parent=base["Heading2"],
        fontSize=12, textColor=LGREEN, spaceBefore=14, spaceAfter=5,
        fontName="Helvetica-Bold")

    h3_s = ParagraphStyle("th3", parent=base["Heading3"],
        fontSize=11, textColor=DGREY, spaceBefore=10, spaceAfter=4,
        fontName="Helvetica-Bold")

    body_s = ParagraphStyle("tbody", parent=base["Normal"],
        fontSize=10, leading=15, spaceAfter=7, alignment=TA_JUSTIFY,
        textColor=DGREY)

    bullet_s = ParagraphStyle("tbullet", parent=body_s,
        leftIndent=16, bulletIndent=6, spaceAfter=5, alignment=TA_LEFT)

    code_s = ParagraphStyle("tcode", parent=base["Code"],
        fontSize=8.5, leading=13, leftIndent=12, spaceAfter=6,
        backColor=GREY, fontName="Courier", borderPad=6)

    small_s = ParagraphStyle("tsmall", parent=body_s,
        fontSize=8.5, leading=12, spaceAfter=0)

    caption_s = ParagraphStyle("tcap", parent=base["Normal"],
        fontSize=8.5, textColor=colors.grey, alignment=TA_CENTER, spaceAfter=4)

    note_s = ParagraphStyle("tnote", parent=body_s,
        fontSize=9, textColor=colors.grey,
        fontName="Helvetica-Oblique", spaceAfter=6)

    def hr(): return HRFlowable(width="100%", thickness=1,
                                color=LGREEN, spaceAfter=8, spaceBefore=2)

    def sp(n=8): return Spacer(1, n)

    def box(text, bg=MINT, border=LGREEN):
        t = Table([[Paragraph(text, ParagraphStyle("bx", parent=body_s,
                                                    fontSize=9.5, spaceAfter=0))]],
                  colWidths=[PAGE_W])
        t.setStyle(TableStyle([
            ("BACKGROUND",   (0,0), (-1,-1), bg),
            ("BOX",          (0,0), (-1,-1), 1, border),
            ("LEFTPADDING",  (0,0), (-1,-1), 10),
            ("RIGHTPADDING", (0,0), (-1,-1), 10),
            ("TOPPADDING",   (0,0), (-1,-1), 8),
            ("BOTTOMPADDING",(0,0), (-1,-1), 8),
        ]))
        return t

    # Helper: build a data table with Paragraph cells (prevents overflow)
    def ptable(data, col_widths, header_bg=GREEN, font_size=9):
        cell_s = ParagraphStyle("cs", parent=body_s,
                                fontSize=font_size, leading=font_size+3,
                                spaceAfter=0, alignment=TA_LEFT)
        head_s = ParagraphStyle("hs", parent=cell_s,
                                fontName="Helvetica-Bold", textColor=WHITE)
        rows = []
        for ri, row in enumerate(data):
            cells = []
            for ci, val in enumerate(row):
                s = head_s if ri == 0 else cell_s
                cells.append(Paragraph(str(val), s))
            rows.append(cells)
        t = Table(rows, colWidths=col_widths)
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0),  header_bg),
            ("ROWBACKGROUNDS",(0,1), (-1,-1), [WHITE, GREY]),
            ("GRID",          (0,0), (-1,-1), 0.4, colors.lightgrey),
            ("LEFTPADDING",   (0,0), (-1,-1), 7),
            ("RIGHTPADDING",  (0,0), (-1,-1), 7),
            ("TOPPADDING",    (0,0), (-1,-1), 5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
            ("VALIGN",        (0,0), (-1,-1), "TOP"),
        ]))
        return t

    story = []

    # ── Cover ─────────────────────────────────────────────────────────────────
    story += [
        sp(24),
        Paragraph("Team Greenlight", title_s),
        Paragraph("DSN x BCT LLM Agent Hackathon 3.0", sub_s),
        Paragraph("Technical Solution Paper", ParagraphStyle(
            "tp", parent=sub_s, fontSize=13, textColor=LGREEN,
            fontName="Helvetica-Bold")),
        sp(6), hr(), sp(6),
        Paragraph(
            "User Modelling &amp; Personalised Recommendation System<br/>"
            "with Nigerian English Contextualisation",
            ParagraphStyle("tc", parent=sub_s, fontSize=11, textColor=DGREY)),
        sp(8),
        Paragraph(
            "May 2026  |  Task A (port 8001) + Task B (port 8002)  |  "
            "FastAPI · FAISS · Gemini 2.5 Flash",
            caption_s),
        PageBreak(),
    ]

    # ── 1. Executive Summary ──────────────────────────────────────────────────
    story += [
        Paragraph("1. Executive Summary", h1_s), hr(),
        Paragraph(
            "Team Greenlight presents a dual-task LLM agent system for the "
            "DSN x BCT Hackathon. <b>Task A</b> implements personalised review "
            "generation using a two-step agentic pipeline: user profile "
            "extraction followed by Gemini 2.5 Flash review synthesis with a "
            "local sentiment-based rating stage. <b>Task B</b> implements a "
            "three-step retrieval-augmented recommendation pipeline: "
            "LLM-driven intent reasoning, FAISS neural retrieval using "
            "all-MiniLM-L6-v2 (384-dimensional embeddings), and LLM reranking "
            "with Nigerian Pidgin explanations. Both tasks include authentic "
            "Pidgin contextualisation throughout all outputs. Both services "
            "are containerised via Docker and exposed as production-grade "
            "FastAPI REST APIs.",
            body_s),
        sp(6),
        ptable([
            ["Component",          "Technology",                              "Port"],
            ["Task A — User Modelling",  "FastAPI + Gemini 2.5 Flash",       "8001"],
            ["Task B — Recommendation", "FastAPI + FAISS + Gemini 2.5 Flash","8002"],
            ["Embeddings",         "all-MiniLM-L6-v2 (sentence-transformers)","—"],
            ["Vector Index",       "FAISS IndexFlatIP (cosine-normalised)",   "—"],
            ["Container Runtime",  "Docker (python:3.10-slim base)",          "—"],
        ], [6*cm, 8*cm, 2*cm]),
    ]

    # ── 2. Data Pipeline ──────────────────────────────────────────────────────
    story += [
        sp(), Paragraph("2. Data Pipeline", h1_s), hr(),

        Paragraph("2.1 Dataset Sources", h2_s),
        ptable([
            ["Dataset",         "HuggingFace Source",                        "Records", "Domain"],
            ["Yelp Reviews",    "Yelp/yelp_review_full",                     "5,000",   "Restaurants / Businesses"],
            ["Amazon Grocery",  "McAuley-Lab/Amazon-Reviews-2023 (Grocery)", "3,000",   "Food Products"],
            ["Amazon Books",    "McAuley-Lab/Amazon-Reviews-2023 (Books)",   "2,000",   "Books"],
            ["TOTAL",           "—",                                         "9,999",   "1,271 user profiles"],
        ], [4*cm, 6*cm, 2.5*cm, 3.5*cm]),
        sp(5),
        Paragraph(
            "Note: Goodreads data is no longer publicly distributed. Amazon "
            "Books is used as a high-quality substitute with comparable review "
            "depth and user diversity, disclosed per competition rules.",
            note_s),

        Paragraph("2.2 Unified Review Schema", h2_s),
        Paragraph(
            "All records are normalised to a common six-field schema before "
            "indexing: <b>user_id</b>, <b>rating</b> (1–5 stars), "
            "<b>review_text</b>, <b>item_name</b>, <b>item_category</b>, "
            "and <b>source_dataset</b>. This unified representation lets both "
            "Task A and Task B operate on a single data file "
            "(<i>data/combined_sample.json</i>).",
            body_s),

        Paragraph("2.3 User Profile Construction", h2_s),
        Paragraph(
            "For each user with two or more reviews a profile is built at "
            "data-pipeline time and stored in <i>data/user_profiles.json</i>. "
            "Each profile captures six fields:", body_s),
        Paragraph("• <b>avg_rating</b> — mean star rating across all reviews", bullet_s),
        Paragraph("• <b>sentiment_style</b> — positive / neutral / negative (derived from avg_rating threshold)", bullet_s),
        Paragraph("• <b>typical_length</b> — short (&lt;100 words) / medium / long (&gt;300 words)", bullet_s),
        Paragraph("• <b>common_words</b> — top-20 TF-IDF-style content words with stopwords removed", bullet_s),
        Paragraph("• <b>avg_review_length</b> — mean character count", bullet_s),
        Paragraph("• <b>review_count</b> — total number of reviews contributed", bullet_s),
    ]

    # ── 3. Task A Architecture ────────────────────────────────────────────────
    story += [
        PageBreak(),
        Paragraph("3. Task A — User Modelling Architecture", h1_s), hr(),

        Paragraph("3.1 API Endpoint", h2_s),
        Paragraph(
            "<b>POST /generate-review</b> accepts five fields: "
            "<i>user_id</i>, <i>item_name</i>, <i>item_category</i>, "
            "<i>item_description</i>, and <i>price_range</i>. "
            "It returns <i>review_text</i>, <i>star_rating</i> (1.0–5.0), "
            "<i>confidence</i> (0–1), <i>user_style_matched</i>, and "
            "<i>user_found</i>. A <b>GET /health</b> endpoint is also "
            "available for Docker health checks.",
            body_s),

        Paragraph("3.2 Two-Step Agentic Pipeline", h2_s),
        box(
            "Step 1 — Profile-conditioned review generation: Gemini 2.5 Flash "
            "receives the user's full profile (sentiment style, typical length, "
            "avg rating, top vocabulary) and generates a plain-text review in "
            "Nigerian English. Plain text is used instead of JSON schema output "
            "mode, which caused double-nested responses when thinking tokens were "
            "enabled. thinking_budget is set to 0 to prevent output-token "
            "exhaustion on long reviews.\n\n"
            "Step 2 — Local sentiment rating: The generated review is scored "
            "offline using a weighted positive/negative keyword lexicon, then "
            "interpolated with the user's historical avg_rating to produce a "
            "final 1.0–5.0 star value. This avoids a second Gemini call, which "
            "consistently triggered safety filters (finish_reason=2) on rating prompts."
        ),
        sp(6),

        Paragraph("3.3 Nigerian English Contextualisation", h2_s),
        Paragraph(
            "The system prompt embeds authentic Pidgin expressions directly "
            "into the generation instructions so outputs feel natural rather "
            "than translated. Key phrases include: <i>\"I no go lie\"</i> "
            "(honest-opinion opener), <i>\"abeg\"</i> (please / emphasis), "
            "<i>\"chai!\"</i> (surprise or delight), <i>\"omo\"</i> "
            "(street-level enthusiasm), <i>\"na wa o\"</i> (mild frustration "
            "or disbelief), <i>\"e dey sweet\"</i> (it is delicious), "
            "<i>\"sharp sharp\"</i> (immediately / promptly), and "
            "<i>\"wetin\"</i> / <i>\"dem\"</i> (what / them). Usage examples "
            "for each phrase are included in the prompt so the model applies "
            "them contextually rather than randomly.",
            body_s),

        Paragraph("3.4 Key Design Decisions", h2_s),
        Paragraph(
            "Several engineering choices in Task A emerged from debugging "
            "real failure modes during development:", body_s),
        Paragraph(
            "• <b>Plain-text review, not JSON schema output:</b> Gemini's "
            "<i>response_mime_type=\"application/json\"</i> mode caused "
            "double-nested JSON objects when thinking tokens were active. "
            "Plain-text generation followed by local parsing is more robust.",
            bullet_s),
        Paragraph(
            "• <b>thinking_budget=0:</b> Default reasoning tokens consumed "
            "the output budget and produced truncated reviews. Disabling them "
            "keeps the full 2,048 output tokens available for the review text.",
            bullet_s),
        Paragraph(
            "• <b>Local sentiment heuristic for the rating:</b> A dedicated "
            "rating prompt reliably triggered a safety-filter refusal "
            "(finish_reason=2). Offline keyword scoring is deterministic, "
            "free, and achieves comparable accuracy.",
            bullet_s),
        Paragraph(
            "• <b>avg_rating anchor:</b> The sentiment score is interpolated "
            "with the user's historical average rating so a habitually harsh "
            "reviewer still produces sub-4-star predictions even when their "
            "generated text sounds positive.",
            bullet_s),
    ]

    # ── 4. Task B Architecture ────────────────────────────────────────────────
    story += [
        PageBreak(),
        Paragraph("4. Task B — Recommendation Architecture", h1_s), hr(),

        Paragraph("4.1 API Endpoints", h2_s),
        Paragraph(
            "<b>POST /recommend</b> (warm-start) — accepts <i>user_id</i>, "
            "<i>conversation_history</i>, and <i>top_k</i>. Looks up the user "
            "profile, runs FAISS retrieval over the user's past review texts, "
            "and returns personalised recommendations with Nigerian Pidgin "
            "explanations.",
            body_s),
        Paragraph(
            "<b>POST /recommend/cold-start</b> (new users) — accepts "
            "<i>item_category</i>, <i>description_of_what_i_want</i>, and "
            "<i>top_k</i>. Skips profile lookup entirely and uses the "
            "user-supplied description as the FAISS query directly.",
            body_s),

        Paragraph("4.2 Three-Step Agentic Pipeline", h2_s),
        box(
            "Step 1 — Intent reasoning: Gemini extracts a concise search "
            "query from the user's profile and conversation history.\n\n"
            "Step 2 — FAISS neural retrieval: all-MiniLM-L6-v2 encodes the "
            "query into a 384-dimensional vector; FAISS IndexFlatIP retrieves "
            "the top-50 cosine-similar items from 9,999 pre-indexed reviews. "
            "For warm-start users the query is built from the user's actual "
            "past review texts (not a generic LLM summary) — this grounds "
            "retrieval in demonstrated preferences and achieves 90% recall "
            "of ground-truth items in the top-50 candidates.\n\n"
            "Step 3 — LLM reranking: Gemini selects and reorders the top "
            "candidates, adding a Nigerian Pidgin explanation for each. "
            "If Gemini is unavailable the system degrades gracefully to "
            "FAISS ranking order, still achieving 65% Hit Rate@5."
        ),
        sp(6),

        Paragraph("4.3 FAISS Index Design", h2_s),
        ptable([
            ["Property",        "Value / Detail"],
            ["Embedding model", "all-MiniLM-L6-v2 (sentence-transformers)"],
            ["Vector dimension", "384"],
            ["Index type",      "IndexFlatIP — exact inner product (cosine after L2 normalisation)"],
            ["Index size",      "9,999 vectors, pre-built and cached to data/faiss_index.pkl"],
            ["Build time",      "~20 minutes on CPU (one-off); subsequent starts load in under 2 seconds"],
            ["Query latency",   "Under 50 ms per search after cache is loaded"],
            ["Retrieval k",     "top-50 candidates retrieved; top-15 passed to the reranker"],
            ["Fallback",        "scikit-learn TF-IDF if sentence-transformers are unavailable"],
        ], [4.5*cm, 11.5*cm]),
        sp(6),

        Paragraph("4.4 Reranking Output Format", h2_s),
        Paragraph(
            "Early iterations used JSON for the reranking response. When "
            "Gemini's output budget was exhausted mid-object the entire "
            "result became unparseable. The final design uses a line-by-line "
            "delimiter format so any fully-written item is parseable even if "
            "the response is cut short:",
            body_s),
        Paragraph(
            "RANK: 1\nNAME: [exact item name from candidates]\n"
            "CAT: [category]\nSCORE: [0.0-1.0]\nSOURCE: [dataset]\n"
            "WHY: [Nigerian Pidgin explanation]\n---",
            ParagraphStyle("cod2", parent=code_s, fontSize=8.5)),
        Paragraph(
            "A critical instruction in the reranking prompt requires the "
            "model to copy item names character-for-character from the "
            "candidate list. This prevents the model from paraphrasing item "
            "IDs, which was the root cause of zero Hit Rate in early evaluation.",
            body_s),

        Paragraph("4.5 Key Design Decisions", h2_s),
        Paragraph(
            "The most impactful engineering choice in Task B was switching "
            "the retrieval query from a Gemini-generated need summary to the "
            "user's actual past review texts. Semantic search over what a "
            "user has genuinely written outperforms a generic LLM description "
            "by a wide margin — the Hit Rate@5 rose from 0% to 65% and "
            "recall@50 reached 90%.",
            body_s),
        Paragraph(
            "Other notable decisions:",
            body_s),
        Paragraph(
            "• <b>Candidates expanded to top-50:</b> Wider FAISS retrieval "
            "gives the reranker better raw material without meaningfully "
            "increasing latency.",
            bullet_s),
        Paragraph(
            "• <b>SentenceTransformer cached globally:</b> The encoder is "
            "instantiated once at module level to avoid a costly reload on "
            "every request.",
            bullet_s),
        Paragraph(
            "• <b>Graceful degradation:</b> All reranker calls are wrapped "
            "in try/except. If Gemini fails (e.g. quota exhausted) the "
            "system falls back to raw FAISS order and still serves results.",
            bullet_s),
        Paragraph(
            "• <b>Cold-start via direct query:</b> New users skip the "
            "profile lookup; their free-text description becomes the FAISS "
            "query directly, achieving 100% cold-start success in evaluation.",
            bullet_s),
    ]

    # ── 5. Evaluation ─────────────────────────────────────────────────────────
    story += [
        PageBreak(),
        Paragraph("5. Evaluation Results", h1_s), hr(),

        Paragraph("5.1 Task A — Review Generation (16 users)", h2_s),
        Paragraph(
            "The evaluation held out each user's most recent review as ground "
            "truth. The agent generated a new review for the same item without "
            "access to the ground truth. 16 users completed successfully; "
            "4 additional users were skipped due to Gemini free-tier rate "
            "limits (20 requests per day).",
            body_s),
        sp(4),
        ptable([
            ["Metric",              "Score",   "Notes"],
            ["Avg ROUGE-L",         "0.1357",  "Vocabulary overlap with held-out reviews. Scores of 0.10–0.15 are typical for open-ended generative tasks where paraphrasing is expected."],
            ["RMSE (star rating)",  "0.8725",  "Mean squared error on 1–5 star scale. Largest errors occur when sentiment signal is ambiguous."],
            ["MAE (star rating)",   "0.6625",  "Mean absolute error. The majority of predictions fall within 1 star of ground truth."],
            ["Style match rate",    "100%",    "User profile was found and applied for every test user."],
            ["Avg review length",   "1,142 chars", "Generated reviews are detailed and substantially longer than many ground truth samples."],
        ], [3.5*cm, 2.5*cm, 10*cm]),
        sp(8),

        Paragraph("Individual Results (16 users)", h3_s),
        sp(3),
    ]

    # Build individual results with Paragraph cells so long IDs wrap cleanly
    ind_data = [
        ["User ID", "ROUGE-L", "Pred ★", "Act ★", "Error"],
        ["yelp_user_0228",              "0.1193", "3.9", "3.0", "0.90"],
        ["yelp_user_0051",              "0.1206", "4.2", "4.0", "0.20"],
        ["yelp_user_0563",              "0.1453", "3.8", "4.0", "0.20"],
        ["yelp_user_0501",              "0.1176", "4.1", "2.0", "2.10"],
        ["yelp_user_0457",              "0.1086", "4.0", "3.0", "1.00"],
        ["yelp_user_0285",              "0.1296", "3.0", "2.0", "1.00"],
        ["yelp_user_0209",              "0.1270", "5.0", "4.0", "1.00"],
        ["amazon_AGBJ...7VK",           "0.2936", "5.0", "5.0", "0.00"],
        ["yelp_user_0178",              "0.0818", "3.4", "3.0", "0.40"],
        ["yelp_user_0191",              "0.0754", "4.3", "3.0", "1.30"],
        ["yelp_user_0447",              "0.1160", "4.1", "3.0", "1.10"],
        ["yelp_user_0476",              "0.1289", "4.8", "4.0", "0.80"],
        ["amazon_AEVP...I2U",           "0.1143", "4.7", "5.0", "0.30"],
        ["gr_AH4O...VTS",               "0.1871", "5.0", "5.0", "0.00"],
        ["yelp_user_0054",              "0.0905", "3.7", "4.0", "0.30"],
        ["amazon_AH2I...XY",            "0.2154", "5.0", "5.0", "0.00"],
        ["AVERAGE",                     "0.1357", "—",   "—",   "0.6625"],
    ]
    story.append(ptable(ind_data, [5.5*cm, 2.5*cm, 2*cm, 2*cm, 4*cm], font_size=8.5))
    story.append(Paragraph(
        "User IDs abbreviated for display. Full IDs: "
        "amazon_AGBJABSJLN7H7AALE7VK, amazon_AEVPPTMG43C6GWSR7I2U, "
        "gr_AH4O5W3EM4CKQGHMBVTS, amazon_AH2IW7MZIXM53IRDZ2XY.", note_s))
    story.append(sp(8))

    story += [
        Paragraph("5.2 Task B — Recommendation (20 users + 5 cold-start)", h2_s),
        Paragraph(
            "Full evaluation across all 20 test users. The system ran "
            "primarily on FAISS fallback due to API rate limits, demonstrating "
            "that review-text retrieval alone achieves strong results without "
            "LLM reranking.",
            body_s),
        sp(4),
        ptable([
            ["Metric",             "Score",           "Notes"],
            ["Hit Rate@5",         "0.6500 (65%)",    "Ground truth item in top 5 for 13 of 20 users."],
            ["NDCG@5",             "0.2968",          "Relevant items surface near position 1 in the ranked list."],
            ["Cold-start success", "5/5 (100%)",      "All 5 new users received relevant recommendations."],
            ["Users evaluated",    "20/20",           "Full test set completed without any failures."],
        ], [4*cm, 3.5*cm, 8.5*cm]),
        sp(6),
        Paragraph(
            "The key insight: using the user's actual past review texts as "
            "the FAISS query (rather than a Gemini-generated need summary) "
            "pushed recall@50 to 90% and Hit@5 from 0% to 65%. This is "
            "because real review text directly encodes demonstrated taste, "
            "while a generic LLM summary loses specificity.",
            body_s),
    ]

    # ── 6. System Architecture ────────────────────────────────────────────────
    story += [
        PageBreak(),
        Paragraph("6. System Architecture & Deployment", h1_s), hr(),

        Paragraph("6.1 Project Structure", h2_s),
        Paragraph(
            "The repository is organised into two independent service "
            "directories, a shared data directory, evaluation notebooks, "
            "and results storage:",
            body_s),
        Paragraph(
            "greenlight/\n"
            "  task_a/          Task A API — User Modelling (port 8001)\n"
            "    agent.py       Gemini pipeline + local sentiment rating\n"
            "    main.py        FastAPI routes + Pydantic models\n"
            "    Dockerfile\n"
            "  task_b/          Task B API — Recommendation (port 8002)\n"
            "    agent.py       FAISS retrieval + Gemini reranking\n"
            "    main.py        FastAPI routes\n"
            "    Dockerfile\n"
            "  data/\n"
            "    combined_sample.json   9,999 unified reviews\n"
            "    user_profiles.json     1,271 user profiles\n"
            "    faiss_index.pkl        pre-built FAISS index + item metadata\n"
            "  notebooks/\n"
            "    build_data.py          data pipeline (run once)\n"
            "    evaluate_task_a.ipynb  ROUGE-L + RMSE evaluation\n"
            "    evaluate_task_b.ipynb  Hit Rate@5 + NDCG@5 evaluation\n"
            "  results/\n"
            "    task_a_results.json    saved evaluation output\n"
            "    task_b_results.json    saved evaluation output\n"
            "  docker-compose.yml\n"
            "  .env                    GEMINI_API_KEY (not committed)",
            ParagraphStyle("cod3", parent=code_s, fontSize=8, leading=12)),
        sp(6),

        Paragraph("6.2 Docker & Deployment", h2_s),
        Paragraph(
            "Both services use a <i>python:3.10-slim</i> base image. "
            "Task B's Dockerfile pre-downloads the sentence-transformer "
            "model at build time so the container starts fully self-contained "
            "with no network dependency at runtime. A single "
            "<i>docker-compose.yml</i> at the project root orchestrates both "
            "services with a shared read-only data volume and passes "
            "GEMINI_API_KEY from the host environment.",
            body_s),
        Paragraph(
            "Additional API design notes:",
            body_s),
        Paragraph(
            "• <b>UTF-8 JSON patch:</b> JSONResponse.render is monkey-patched "
            "with ensure_ascii=False so the Naira symbol (₦) renders correctly "
            "in all clients.",
            bullet_s),
        Paragraph(
            "• <b>CORS middleware:</b> Enabled on both services for "
            "browser-based testing and frontend integration.",
            bullet_s),
        Paragraph(
            "• <b>FAISS cache:</b> The index is built once (~20 min) and "
            "pickled to <i>data/faiss_index.pkl</i>. Subsequent container "
            "starts load it in under 2 seconds.",
            bullet_s),
        Paragraph(
            "• <b>TF-IDF fallback:</b> If sentence-transformers are "
            "unavailable, Task B automatically falls back to scikit-learn "
            "TF-IDF retrieval without any code changes.",
            bullet_s),
        Paragraph(
            "• <b>Pydantic validation:</b> All request inputs are validated "
            "with field_validators; the API returns helpful 422 errors for "
            "bad inputs.",
            bullet_s),
        Paragraph(
            "• <b>Health endpoints:</b> GET /health on both services; "
            "Docker HEALTHCHECK is configured with appropriate start_period "
            "delays (30 s for Task A, 60 s for Task B which needs extra time "
            "to load the FAISS index).",
            bullet_s),
    ]

    # ── 7. Limitations & Future Work ──────────────────────────────────────────
    story += [
        sp(), Paragraph("7. Limitations and Future Work", h1_s), hr(),

        Paragraph("Current Limitations", h2_s),
        Paragraph(
            "• <b>Rating accuracy:</b> The local sentiment heuristic "
            "occasionally misses context-dependent signals such as sarcasm "
            "or cultural idioms. A fine-tuned sentiment classifier would "
            "improve RMSE meaningfully.",
            bullet_s),
        Paragraph(
            "• <b>ROUGE-L ceiling:</b> Generative reviews inherently score "
            "low on n-gram overlap because the model paraphrases rather than "
            "reproduces text verbatim. Semantic similarity metrics such as "
            "BERTScore would better capture generation quality.",
            bullet_s),
        Paragraph(
            "• <b>Gemini free-tier quota:</b> 20 requests per day limited "
            "evaluation throughput. Pay-as-you-go billing resolves this at "
            "an estimated cost of under $0.20 for the full evaluation suite.",
            bullet_s),
        Paragraph(
            "• <b>Goodreads unavailability:</b> The original dataset was "
            "removed from public distribution. Amazon Books provides "
            "comparable quality but covers a narrower domain.",
            bullet_s),
        sp(4),

        Paragraph("Future Improvements", h2_s),
        Paragraph(
            "• Switch to <b>gemini-2.5-pro</b> for higher-quality review "
            "generation and more nuanced reranking explanations.",
            bullet_s),
        Paragraph(
            "• Add <b>collaborative filtering</b> signals alongside semantic "
            "similarity for Task B (users who liked X also liked Y).",
            bullet_s),
        Paragraph(
            "• Expand Pidgin vocabulary with a curated Nigerian slang "
            "lexicon and evaluate outputs with native speakers.",
            bullet_s),
        Paragraph(
            "• Implement <b>streaming responses</b> (Server-Sent Events) "
            "for Task A to reduce perceived latency on long reviews.",
            bullet_s),
        Paragraph(
            "• Evaluate with <b>BERTScore</b> in addition to ROUGE-L "
            "to better capture semantic quality of generated reviews.",
            bullet_s),
    ]

    # ── 8. References ─────────────────────────────────────────────────────────
    story += [
        sp(), Paragraph("8. References", h1_s), hr(),
        Paragraph(
            "1. Yelp Open Dataset — "
            "https://huggingface.co/datasets/Yelp/yelp_review_full",
            bullet_s),
        Paragraph(
            "2. McAuley-Lab Amazon Reviews 2023 — "
            "https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023",
            bullet_s),
        Paragraph(
            "3. Reimers &amp; Gurevych (2019). Sentence-BERT: Sentence "
            "Embeddings using Siamese BERT-Networks. EMNLP 2019.",
            bullet_s),
        Paragraph(
            "4. Johnson, Douze &amp; Jégou (2019). Billion-scale similarity "
            "search with GPUs. IEEE Transactions on Big Data.",
            bullet_s),
        Paragraph(
            "5. Google Gemini API Documentation — "
            "https://ai.google.dev/gemini-api/docs",
            bullet_s),
        Paragraph(
            "6. FastAPI Documentation — https://fastapi.tiangolo.com",
            bullet_s),
        sp(20),
        Paragraph(
            "Team Greenlight  ·  DSN x BCT LLM Agent Hackathon 3.0  ·  May 2026",
            ParagraphStyle("foot", parent=caption_s, textColor=DGREY)),
    ]

    doc.build(story)
    print("greenlight_technical.pdf created")


if __name__ == "__main__":
    make_simple()
    make_technical()
    print("\nBoth PDFs saved to: C:/Users/Ayoola/Downloads/greenlight/results/")
