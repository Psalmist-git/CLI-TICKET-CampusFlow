import os
from html import escape
from datetime import datetime

import streamlit as st
import plotly.express as px

from historical_classifier import classify_unclassified_tickets
from reports import generate_dashboard_summary
from streamlit.errors import StreamlitSecretNotFoundError
from duplicate_detector import find_possible_duplicates
from storage import load_tickets, save_tickets
from ticket_manager import generate_ticket_id
from ai_assistant import (
    get_ai_suggestions,
    get_ticket_intelligence,
    get_chatbot_response,
    render_ai_provider_selector
)
from news_feed import get_education_news


# =====================================================
# PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="CampusFlow | Campus Support",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =====================================================
# GEMINI API CONFIGURATION
# =====================================================

if not os.getenv("GEMINI_API_KEY"):

    try:
        os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]

    except (StreamlitSecretNotFoundError, KeyError):
        pass


# =====================================================
# CAMPUSFLOW DESIGN
# =====================================================

st.markdown("""
<style>

.stApp {
    background-color: #0F172A;
    color: #F8FAFC;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1450px;
}

h1, h2, h3 {
    color: #F8FAFC !important;
    font-weight: 700;
}

p, label, .stMarkdown {
    color: #CBD5E1;
}

hr {
    border-color: #334155;
}

/* SIDEBAR */

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #111C31, #0F1A2D);
    border-right: 1px solid #26364F;
}

section[data-testid="stSidebar"] > div {
    padding-top: 1.5rem;
}

section[data-testid="stSidebar"] * {
    color: #F8FAFC;
}

.sidebar-brand {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 8px 18px 8px;
    margin-bottom: 8px;
}

.campusflow-logo {
    width: 48px;
    height: 48px;
    min-width: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(145deg, #14B8A6, #0F766E);
    border: 1px solid rgba(153, 246, 228, 0.35);
    border-radius: 15px;
    box-shadow: 0 5px 18px rgba(13, 148, 136, 0.25);
}

.campusflow-brand {
    font-size: 23px;
    font-weight: 800;
    letter-spacing: -0.8px;
    line-height: 1.1;
    color: #F8FAFC;
}

.campusflow-brand span {
    color: #2DD4BF;
}

.campusflow-caption {
    color: #94A3B8;
    font-size: 11px;
    letter-spacing: 1.1px;
    text-transform: uppercase;
    margin-top: 6px;
}

.sidebar-section-label {
    color: #64748B;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin: 18px 0 10px 8px;
}

section[data-testid="stSidebar"] div[data-testid="stRadio"] {
    width: 100%;
}

section[data-testid="stSidebar"] div[data-testid="stRadio"] > label {
    display: none;
}

section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] {
    gap: 7px;
}

section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 10px;
    padding: 10px 12px;
    transition: all 0.2s ease;
    min-height: 43px;
}

section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label:hover {
    background: #1E293B;
    border-color: #334155;
}

section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label p {
    color: #CBD5E1 !important;
    font-size: 14px;
    font-weight: 600;
}

section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) {
    background: linear-gradient(
        90deg,
        rgba(13, 148, 136, 0.22),
        rgba(13, 148, 136, 0.08)
    );
    border: 1px solid rgba(45, 212, 191, 0.35);
    border-left: 3px solid #2DD4BF;
}

section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) p {
    color: #5EEAD4 !important;
    font-weight: 700;
}

section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label > div:first-child {
    display: none;
}

.sidebar-footer {
    background: rgba(30, 41, 59, 0.65);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 13px;
    margin-top: 22px;
}

.sidebar-footer-title {
    color: #5EEAD4;
    font-size: 12px;
    font-weight: 700;
    margin-bottom: 5px;
}

.sidebar-footer-text {
    color: #94A3B8;
    font-size: 11px;
    line-height: 1.5;
}

/* METRICS */

div[data-testid="stMetric"] {
    background-color: #1E293B;
    border: 1px solid #334155;
    border-radius: 14px;
    padding: 20px;
    min-height: 120px;
}

div[data-testid="stMetricLabel"] {
    color: #94A3B8;
}

div[data-testid="stMetricValue"] {
    color: #F8FAFC;
    font-weight: 700;
}

/* BUTTONS */

.stButton > button,
.stFormSubmitButton > button {
    background-color: #0D9488;
    color: white;
    border: none;
    border-radius: 9px;
    padding: 0.55rem 1rem;
    font-weight: 600;
    transition: 0.2s ease;
}

.stButton > button:hover,
.stFormSubmitButton > button:hover {
    background-color: #0F766E;
    color: white;
    border: none;
    transform: translateY(-1px);
}

/* INPUTS */

.stTextInput input,
.stTextArea textarea {
    background-color: #1E293B;
    color: #F8FAFC;
    border: 1px solid #475569;
    border-radius: 9px;
}

div[data-baseweb="select"] > div {
    background-color: #1E293B;
    border-color: #475569;
}

div[data-testid="stExpander"] {
    background-color: #1E293B;
    border: 1px solid #334155;
    border-radius: 12px;
}

div[data-testid="stDataFrame"] {
    border: 1px solid #334155;
    border-radius: 10px;
}

/* CHAT */

div[data-testid="stChatMessage"] {
    background-color: #1E293B;
    border: 1px solid #334155;
    border-radius: 13px;
    padding: 12px;
}

/* WELCOME BANNER */

.welcome-banner {
    background: linear-gradient(120deg, #164E63, #0F766E);
    padding: 28px;
    border-radius: 18px;
    margin-bottom: 25px;
    border: 1px solid #0D9488;
}

.welcome-banner h2 {
    color: white !important;
    margin-bottom: 8px;
}

.welcome-banner p {
    color: #CCFBF1;
    margin-bottom: 0;
}

/* ANIMATED CAMPUS IMAGE SLIDESHOW */

.campus-hero {
    position: relative;
    height: 245px;
    overflow: hidden;
    border-radius: 18px;
    margin: 18px 0 28px 0;
    background: #164E63;
    border: 1px solid #334155;
}

.campus-hero-slide {
    position: absolute;
    inset: 0;
    background-size: cover;
    background-position: center;
    opacity: 0;
    animation: campusSlides 18s infinite;
}

.campus-slide-one {
    background-image:
        linear-gradient(
            90deg,
            rgba(15, 23, 42, 0.95),
            rgba(15, 23, 42, 0.25)
        ),
        url("https://images.unsplash.com/photo-1523050854058-8df90110c9f1?auto=format&fit=crop&w=1600&q=85");
    animation-delay: 0s;
}

.campus-slide-two {
    background-image:
        linear-gradient(
            90deg,
            rgba(15, 23, 42, 0.95),
            rgba(15, 23, 42, 0.25)
        ),
        url("https://images.unsplash.com/photo-1509062522246-3755977927d7?auto=format&fit=crop&w=1600&q=85");
    animation-delay: 6s;
}

.campus-slide-three {
    background-image:
        linear-gradient(
            90deg,
            rgba(15, 23, 42, 0.95),
            rgba(15, 23, 42, 0.25)
        ),
        url("https://images.unsplash.com/photo-1523580494863-6f3031224c94?auto=format&fit=crop&w=1600&q=85");
    animation-delay: 12s;
}

@keyframes campusSlides {

    0% {
        opacity: 0;
    }

    7% {
        opacity: 1;
    }

    29% {
        opacity: 1;
    }

    36% {
        opacity: 0;
    }

    100% {
        opacity: 0;
    }
}

.campus-hero-content {
    position: absolute;
    z-index: 5;
    left: 35px;
    top: 50%;
    transform: translateY(-50%);
    max-width: 600px;
}

.campus-hero-content h2 {
    color: white !important;
    font-size: 30px;
    margin-bottom: 10px;
}

.campus-hero-content p {
    color: #CCFBF1;
    font-size: 15px;
    line-height: 1.6;
}

/* GLOBAL EDUCATION NEWS */

.news-heading {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 12px;
}

.news-live-dot {
    width: 9px;
    height: 9px;
    border-radius: 50%;
    background: #2DD4BF;
    box-shadow: 0 0 12px #2DD4BF;
    animation: livePulse 1.5s infinite;
}

@keyframes livePulse {

    0%, 100% {
        opacity: 1;
        transform: scale(1);
    }

    50% {
        opacity: 0.4;
        transform: scale(1.5);
    }
}

.news-ticker {
    width: 100%;
    overflow: hidden;
    background: #172B3F;
    border: 1px solid #28516A;
    border-radius: 10px;
    padding: 14px 0;
    margin: 12px 0 22px 0;
}

.news-ticker-track {
    display: flex;
    width: max-content;
    animation: newsScroll 85s linear infinite;
}

.news-ticker:hover .news-ticker-track {
    animation-play-state: paused;
}

.news-ticker-group {
    display: flex;
    align-items: center;
    flex-shrink: 0;
}

.news-ticker-item {
    color: #E2E8F0;
    font-size: 13px;
    font-weight: 600;
    white-space: nowrap;
    padding: 0 25px;
}

.news-ticker-item span {
    color: #5EEAD4;
    margin-right: 9px;
}

@keyframes newsScroll {

    from {
        transform: translateX(0);
    }

    to {
        transform: translateX(-50%);
    }
}

/* NEWS CARDS */

.news-card {
    background: #1E293B;
    border: 1px solid #334155;
    border-radius: 14px;
    overflow: hidden;
    margin-bottom: 16px;
    min-height: 275px;
    transition: transform 0.25s ease, border-color 0.25s ease;
}

.news-card:hover {
    transform: translateY(-4px);
    border-color: #2DD4BF;
}

.news-card-image {
    width: 100%;
    height: 135px;
    object-fit: cover;
    display: block;
}

.news-card-no-image {
    height: 135px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(120deg, #164E63, #0F766E);
    font-size: 40px;
}

.news-card-content {
    padding: 15px;
}

.news-card-source {
    color: #5EEAD4;
    font-size: 10px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 8px;
}

.news-card-title {
    color: #F8FAFC;
    font-size: 14px;
    line-height: 1.5;
    font-weight: 700;
    margin-bottom: 9px;
}

.news-card-description {
    color: #94A3B8;
    font-size: 12px;
    line-height: 1.5;
    margin-bottom: 12px;
}

.news-card-link {
    color: #5EEAD4;
    font-size: 12px;
    font-weight: 700;
    text-decoration: none;
}

.news-card-link:hover {
    color: white;
}

.news-updated {
    color: #94A3B8;
    font-size: 11px;
}

/* INFORMATION CARDS */

.info-card {
    background-color: #1E293B;
    border: 1px solid #334155;
    border-radius: 13px;
    padding: 18px;
    margin-bottom: 12px;
}

.info-card h4 {
    color: #2DD4BF;
    margin-bottom: 7px;
}

.info-card p {
    color: #CBD5E1;
    margin-bottom: 0;
}

/* FLOATING CHAT */

div[data-testid="stPopover"] {
    position: fixed !important;
    right: 28px !important;
    bottom: 24px !important;
    z-index: 999999 !important;
}

div[data-testid="stPopover"] > button {
    background: linear-gradient(135deg, #0D9488, #14B8A6) !important;
    color: white !important;
    border: 2px solid #5EEAD4 !important;
    border-radius: 50px !important;
    min-height: 58px !important;
    min-width: 58px !important;
    padding: 12px 18px !important;
    font-size: 17px !important;
    font-weight: 700 !important;
    box-shadow: 0 5px 25px rgba(13, 148, 136, 0.45) !important;
}

div[data-testid="stPopover"] > button:hover {
    background: #0F766E !important;
    transform: translateY(-2px);
}

/* MOBILE RESPONSIVENESS */

@media (max-width: 768px) {

    .block-container {
        padding-top: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
        padding-bottom: 2rem;
    }

    .welcome-banner {
        padding: 20px;
        border-radius: 14px;
    }

    .welcome-banner h2 {
        font-size: 21px;
    }

    div[data-testid="stMetric"] {
        padding: 13px;
        min-height: 95px;
    }

    div[data-testid="stMetricValue"] {
        font-size: 23px;
    }

    .info-card {
        padding: 14px;
    }

    .campus-hero {
        height: 210px;
    }

    .campus-hero-content {
        left: 20px;
        right: 15px;
    }

    .campus-hero-content h2 {
        font-size: 22px;
    }

    .campus-hero-content p {
        font-size: 12px;
    }

    .news-card {
        min-height: auto;
    }

    div[data-testid="stPopover"] {
        right: 14px !important;
        bottom: 14px !important;
    }

    div[data-testid="stPopover"] > button {
        min-height: 52px !important;
        min-width: 52px !important;
        padding: 9px 13px !important;
        font-size: 14px !important;
    }
}

/* CAMPUSFLOW AI LOADING ANIMATION */

@keyframes campusflow-glow {
    0%, 100% {
        box-shadow: 0 0 8px rgba(20, 184, 166, 0.10);
        border-color: rgba(20, 184, 166, 0.25);
    }

    50% {
        box-shadow: 0 0 20px rgba(20, 184, 166, 0.30);
        border-color: rgba(20, 184, 166, 0.75);
    }
}

div[data-testid="stSpinner"] {
    padding: 15px 20px;
    border: 1px solid rgba(20, 184, 166, 0.25);
    border-radius: 12px;
    background: linear-gradient(
        120deg,
        rgba(20, 184, 166, 0.08),
        rgba(15, 23, 42, 0.85)
    );
    animation: campusflow-glow 2s ease-in-out infinite;
}

div[data-testid="stSpinner"] svg {
    stroke: #14B8A6 !important;
}

div[data-testid="stSpinner"] p {
    color: #CCFBF1 !important;
    font-weight: 600;
}

</style>
""", unsafe_allow_html=True)


# =====================================================
# SESSION STATE
# =====================================================

if "chat_messages" not in st.session_state:
    st.session_state["chat_messages"] = []

if "floating_chat_messages" not in st.session_state:
    st.session_state["floating_chat_messages"] = []

if "possible_duplicates" not in st.session_state:
    st.session_state["possible_duplicates"] = []

if "last_ticket" not in st.session_state:
    st.session_state["last_ticket"] = None


# =====================================================
# HELPER FUNCTIONS
# =====================================================

def update_saved_ticket(ticket_id, updates):
    """Update a saved ticket using its ID."""

    tickets = load_tickets()

    for ticket in tickets:

        if ticket.get("id") == ticket_id:

            ticket.update(updates)
            save_tickets(tickets)

            last_ticket = st.session_state.get("last_ticket")

            if last_ticket and last_ticket.get("id") == ticket_id:
                last_ticket.update(updates)

            return True

    return False


def display_welcome_banner(title, subtitle):
    """Display a consistent welcome banner."""

    st.html(f"""
    <div class="welcome-banner">
        <h2>{escape(title)}</h2>
        <p>{escape(subtitle)}</p>
    </div>
    """)


# =====================================================
# CAMPUS PHOTO GALLERY — PHONE-STYLE CAROUSEL
# =====================================================

def display_campus_slideshow():
    """Display all campus photos in a swipeable horizontal gallery."""

    from pathlib import Path
    import base64
    import html

    image_folder = Path("assets/campus")

    images = sorted(
        [
            file for file in image_folder.iterdir()
            if file.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")
        ]
    ) if image_folder.exists() else []

    st.subheader("🏫 Explore Our Campus")
    st.caption("Swipe or scroll to explore our campus gallery.")

    if not images:
        st.warning("No campus photographs were found.")
        return

    cards = []

    for image_path in images:

        image_data = base64.b64encode(
            image_path.read_bytes()
        ).decode("utf-8")

        extension = image_path.suffix.lower()

        mime_type = (
            "image/jpeg" if extension in (".jpg", ".jpeg")
            else f"image/{extension[1:]}"
        )

        image_name = html.escape(
            image_path.stem.replace("_", " ").title()
        )

        cards.append(f"""
            <div class="campus-photo-card">
                <img
                    src="data:{mime_type};base64,{image_data}"
                    alt="{image_name}"
                />
                <div class="campus-photo-caption">
                    {image_name}
                </div>
            </div>
        """)

    gallery_html = f"""
    <style>
        .campus-gallery {{
            display: flex;
            gap: 16px;
            overflow-x: auto;
            padding: 12px 4px 22px;
            scroll-snap-type: x mandatory;
            scroll-behavior: smooth;
            -webkit-overflow-scrolling: touch;
        }}

        .campus-gallery::-webkit-scrollbar {{
            height: 7px;
        }}

        .campus-gallery::-webkit-scrollbar-thumb {{
            background: #8b9aaa;
            border-radius: 20px;
        }}

        .campus-photo-card {{
            position: relative;
            flex: 0 0 260px;
            height: 190px;
            overflow: hidden;
            border-radius: 18px;
            scroll-snap-align: start;
            box-shadow: 0 5px 18px rgba(0,0,0,0.16);
            transition: transform 0.3s ease;
        }}

        .campus-photo-card:hover {{
            transform: translateY(-5px);
        }}

        .campus-photo-card img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
        }}

        .campus-photo-caption {{
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            padding: 25px 14px 13px;
            color: white;
            font-size: 15px;
            font-weight: 600;
            background: linear-gradient(
                transparent,
                rgba(0,0,0,0.8)
            );
        }}

        @media (max-width: 600px) {{
            .campus-photo-card {{
                flex-basis: 82%;
                height: 210px;
            }}
        }}
    </style>

    <div class="campus-gallery">
        {''.join(cards)}
    </div>
    """

    st.html(gallery_html)

    st.caption(f"📸 {len(images)} campus photographs")


# =====================================================
# GLOBAL EDUCATION NEWS
# =====================================================

@st.fragment(run_every="10m")
def render_global_education_news():
    """Display automatically refreshing global education news."""

    st.markdown("## 🌍 Global Education Watch")

    st.caption(
        "Education headlines and developments from around the world."
    )

    refresh_col, update_col = st.columns([1, 3])

    with refresh_col:

        refresh_clicked = st.button(
            "🔄 Refresh News",
            key="refresh_education_news"
        )

    if refresh_clicked:

        st.cache_data.clear()
        st.rerun(scope="fragment")

    news_data = get_education_news()

    articles = news_data["articles"]

    with update_col:

        updated_at = news_data.get("updated_at")

        if updated_at:

            try:

                update_time = datetime.fromisoformat(
                    updated_at
                ).strftime("%d %b %Y, %H:%M UTC")

                st.markdown(
                    f'<div class="news-updated">'
                    f'Last refreshed: {escape(update_time)}'
                    f'</div>',
                    unsafe_allow_html=True
                )

            except ValueError:
                pass

    if not articles:

        st.warning(
            "Education news is temporarily unavailable. "
            "Please try refreshing in a moment."
        )

        return

    # -----------------------------------------------
    # MOVING HEADLINE TICKER
    # -----------------------------------------------

    ticker_items = "".join(
        (
            '<div class="news-ticker-item">'
            f'<span>●</span>{escape(article["title"])}'
            '</div>'
        )
        for article in articles[:12]
    )

    st.html(f"""
    <div class="news-ticker">

        <div class="news-ticker-track">

            <div class="news-ticker-group">
                {ticker_items}
            </div>

            <div class="news-ticker-group" aria-hidden="true">
                {ticker_items}
            </div>

        </div>

    </div>
    """)

    # -----------------------------------------------
    # NEWS CARDS
    # -----------------------------------------------

    st.markdown("### 📰 Latest Headlines")

    selected_articles = articles[:9]

    for start in range(0, len(selected_articles), 3):

        columns = st.columns(3)

        batch = selected_articles[start:start + 3]

        for column, article in zip(columns, batch):

            with column:

                title = escape(article.get("title", "Untitled"))
                source = escape(article.get("source", "News source"))
                description = escape(
                    article.get("description", "")
                )

                link = article.get("link", "")

                if not link.startswith("https://"):
                    link = ""

                safe_link = escape(link, quote=True)

                image_url = article.get("image")

                if image_url and image_url.startswith("https://"):

                    safe_image = escape(
                        image_url,
                        quote=True
                    )

                    image_html = (
                        f'<img class="news-card-image" '
                        f'src="{safe_image}" '
                        f'alt="Education news image" '
                        f'loading="lazy">'
                    )

                else:

                    image_html = (
                        '<div class="news-card-no-image">'
                        '🎓'
                        '</div>'
                    )

                if link:

                    link_html = (
                        f'<a class="news-card-link" '
                        f'href="{safe_link}" '
                        f'target="_blank" '
                        f'rel="noopener noreferrer">'
                        f'Read full story ↗'
                        f'</a>'
                    )

                else:

                    link_html = (
                        '<span class="news-updated">'
                        'Article link unavailable'
                        '</span>'
                    )

                st.html(f"""
                <div class="news-card">

                    {image_html}

                    <div class="news-card-content">

                        <div class="news-card-source">
                            {source}
                        </div>

                        <div class="news-card-title">
                            {title}
                        </div>

                        <div class="news-card-description">
                            {description}
                        </div>

                        {link_html}

                    </div>

                </div>
                """)

    if news_data.get("failed_sources"):

        failed = ", ".join(news_data["failed_sources"])

        st.caption(
            f"Some news publishers could not be reached: {failed}. "
            "Available sources are still displayed."
        )

    st.caption(
        "Headlines belong to their respective publishers. "
        "Open an article to read the full report."
    )


# =====================================================
# FLOATING CHAT
# =====================================================

def render_floating_chat():
    """Display the floating CampusFlow AI chatbot."""

    with st.popover(
        "💬 Chat with AI",
        help="Open CampusFlow AI chat"
    ):

        st.markdown("### 🤖 CampusFlow AI")
        st.caption("Your campus support assistant.")

        st.divider()

        messages = st.session_state["floating_chat_messages"]

        if not messages:

            with st.chat_message("assistant"):

                st.markdown(
                    "Hello! 👋 I'm CampusFlow AI. "
                    "How can I help you with campus support today?"
                )

        with st.container(height=320):

            for message in messages:

                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        with st.form("floating_chat_form", clear_on_submit=True):

            prompt = st.text_input(
                "Your message",
                placeholder="Ask me anything..."
            )

            send_message = st.form_submit_button(
                "Send ➤",
                use_container_width=True
            )

        if send_message and prompt.strip():

            messages.append({
                "role": "user",
                "content": prompt.strip()
            })

            with st.spinner("CampusFlow AI is thinking..."):

                try:

                    response = get_chatbot_response(
                        messages,
                        load_tickets()
                    )

                except Exception as error:

                    print(
                        f"Floating chatbot error: "
                        f"{type(error).__name__}"
                    )

                    response = (
                        "I'm sorry, CampusFlow AI is temporarily "
                        "unavailable. Please try again."
                    )

            messages.append({
                "role": "assistant",
                "content": response
            })

            st.rerun()

        st.divider()

        if st.button(
            "🗑️ Clear floating chat",
            key="clear_floating_chat",
            use_container_width=True
        ):

            st.session_state["floating_chat_messages"] = []
            st.rerun()

# =====================================================
# GLOBAL STOCK MARKET EVENTS SLIDESHOW
# =====================================================

def render_global_market_events():

    events = [
        {
            "date": "October 1929",
            "title": "The Wall Street Crash",
            "description": (
                "A major stock market collapse in the United States "
                "that helped trigger the Great Depression."
            ),
            "impact": "Triggered widespread financial panic and economic hardship."
        },
        {
            "date": "October 19, 1987",
            "title": "Black Monday",
            "description": (
                "Stock markets around the world suffered a sudden crash. "
                "The Dow Jones Industrial Average fell about 22% in one day."
            ),
            "impact": "One of the largest single-day percentage falls in stock market history."
        },
        {
            "date": "1997",
            "title": "The Asian Financial Crisis",
            "description": (
                "Currency and financial crises spread across several "
                "Asian economies, affecting global markets."
            ),
            "impact": "Triggered financial instability across international markets."
        },
        {
            "date": "2000–2002",
            "title": "The Dot-com Bubble",
            "description": (
                "Technology stock valuations collapsed after years of "
                "speculation surrounding internet companies."
            ),
            "impact": "Many technology companies lost substantial market value."
        },
        {
            "date": "2007–2009",
            "title": "The Global Financial Crisis",
            "description": (
                "A banking and credit crisis spread internationally, "
                "causing severe disruption to financial markets."
            ),
            "impact": "Led to major bank failures, market declines and global recession."
        },
        {
            "date": "February–March 2020",
            "title": "The COVID-19 Market Crash",
            "description": (
                "Global stock markets fell sharply as the COVID-19 "
                "pandemic disrupted economies and businesses."
            ),
            "impact": "Governments and central banks introduced emergency support measures."
        },
        {
            "date": "2021",
            "title": "The Meme Stock Phenomenon",
            "description": (
                "Retail investors coordinated through online communities, "
                "causing dramatic price movements in stocks such as GameStop."
            ),
            "impact": "Highlighted the growing influence of individual investors and social media."
        },
        {
            "date": "2022",
            "title": "Inflation and Interest Rate Hikes",
            "description": (
                "High inflation pushed central banks, including the US Federal Reserve, "
                "to raise interest rates, putting pressure on global stock markets."
            ),
            "impact": "Investors reassessed company valuations and economic growth expectations."
        },
    ]

    st.subheader("🌍 Global Stock Market Events")

    st.caption(
        "Explore major historical events that shaped financial markets around the world."
    )

    if "market_event_index" not in st.session_state:
        st.session_state.market_event_index = 0

    index = st.session_state.market_event_index
    event = events[index]

    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #102a43, #243b53);
            padding: 25px;
            border-radius: 14px;
            color: white;
            min-height: 210px;
        ">
            <p style="color: #ffd166; font-size: 14px;">
                {event['date']} · EVENT {index + 1} OF {len(events)}
            </p>
            <h2 style="color: white;">{event['title']}</h2>
            <p style="font-size: 16px; line-height: 1.6;">
                {event['description']}
            </p>
            <hr style="border-color: #607d8b;">
            <p style="font-size: 14px;">
                <strong>Market impact:</strong> {event['impact']}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("")

    previous_col, counter_col, next_col = st.columns([1, 2, 1])

    with previous_col:
        if st.button("⬅ Previous", key="market_previous"):
            st.session_state.market_event_index = (
                index - 1
            ) % len(events)
            st.rerun()

    with counter_col:
        st.markdown(
            f"<p style='text-align:center;'>"
            f"Event {index + 1} / {len(events)}"
            f"</p>",
            unsafe_allow_html=True
        )

    with next_col:
        if st.button("Next ➡", key="market_next"):
            st.session_state.market_event_index = (
                index + 1
            ) % len(events)
            st.rerun()

# =====================================================
# WORLD CLOCKS
# =====================================================

def render_world_clocks():

    from datetime import datetime
    from zoneinfo import ZoneInfo

    cities = [
        ("🇳🇬 Lagos", "Africa/Lagos"),
        ("🇬🇧 London", "Europe/London"),
        ("🇩🇪 Berlin", "Europe/Berlin"),
        ("🇺🇸 New York", "America/New_York"),
        ("🇨🇳 Beijing", "Asia/Shanghai"),
        ("🇦🇪 Dubai", "Asia/Dubai"),
    ]

    st.subheader("🌐 World Clocks")

    columns = st.columns(3)

    for index, (city, timezone) in enumerate(cities):

        current_time = datetime.now(ZoneInfo(timezone))

        with columns[index % 3]:
            st.metric(
                label=city,
                value=current_time.strftime("%I:%M:%S %p"),
                delta=current_time.strftime("%A, %d %B")
            )

# =====================================================
# SIDEBAR NAVIGATION
# =====================================================

with st.sidebar:

    st.html("""
    <div class="sidebar-brand">

        <div class="campusflow-logo">

            <svg
                width="31"
                height="31"
                viewBox="0 0 48 48"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
            >

                <path
                    d="M12 13.5C16 9.5 22 8 28 10"
                    stroke="white"
                    stroke-width="3.5"
                    stroke-linecap="round"
                />

                <path
                    d="M12 24H30C34.4 24 38 27.6 38 32C38 36.4 34.4 40 30 40H23"
                    stroke="white"
                    stroke-width="3.5"
                    stroke-linecap="round"
                />

                <path
                    d="M12 24C12 18.5 16.5 14 22 14H27"
                    stroke="#CCFBF1"
                    stroke-width="3.5"
                    stroke-linecap="round"
                />

                <circle cx="12" cy="24" r="4" fill="white"/>
                <circle cx="30" cy="40" r="4" fill="#CCFBF1"/>

            </svg>

        </div>

        <div>

            <div class="campusflow-brand">
                Campus<span>Flow</span>
            </div>

            <div class="campusflow-caption">
                Campus Support Platform
            </div>

        </div>

    </div>
    """)

    st.markdown("---")

    # AI PROVIDER AND MODEL SELECTION
    render_ai_provider_selector()

    st.markdown("---")

    st.html("""
    <div class="sidebar-section-label">
        Workspace
    </div>
    """)

    page = st.radio(
        "NAVIGATION",
        [
            "🏠 Dashboard",
            "🎫 Create Ticket",
            "🛠️ Manage Tickets",
            "🤖 AI Assistant",
            "📊 Reports"
        ],
        label_visibility="collapsed",
        key="main_navigation"
    )

    st.markdown("---")

    st.html("""
    <div class="sidebar-footer">

        <div class="sidebar-footer-title">
            ✦ CampusFlow AI
        </div>

        <div class="sidebar-footer-text">
            Intelligent campus support and ticket management,
            powered by multiple AI providers.
        </div>

    </div>
    """)
# =====================================================
# LOAD TICKETS
# =====================================================

try:

    tickets = load_tickets()

except Exception as error:

    st.error("Unable to load CampusFlow ticket records.")

    print(f"Ticket loading error: {type(error).__name__}")

    tickets = []


# =====================================================
# DASHBOARD
# =====================================================

if page == "🏠 Dashboard":

    display_welcome_banner(
        "Welcome to CampusFlow 👋",
        "Your central platform for campus support, ticket management "
        "and AI-powered assistance."
    )

    display_campus_slideshow()

    render_global_market_events()

    st.divider()

    render_world_clocks()

    st.divider()

    render_global_education_news()

    st.divider()

    summary = generate_dashboard_summary(tickets)

    total = summary["total_tickets"]
    classified = summary["classified_tickets"]

    classification_rate = (
        (classified / total) * 100 if total > 0 else 0
    )

    resolved = summary["resolved_tickets"]
    resolution_rate = summary["resolution_rate"]

    st.subheader("📌 Campus Support Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("🎫 Total Tickets", total)

    with col2:
        st.metric("🟡 Open Tickets", summary["statuses"].get("Open", 0))

    with col3:
        st.metric(
            "🔵 In Progress",
            summary["statuses"].get("In Progress", 0)
        )

    with col4:
        st.metric("🟢 Resolved", resolved)

    st.divider()

    st.subheader("📈 Performance Overview")

    performance_col1, performance_col2 = st.columns(2)

    with performance_col1:
        st.write("**AI Classification Progress**")
        st.progress(classification_rate / 100)

        st.caption(
            f"{classified} of {total} tickets classified "
            f"({classification_rate:.1f}%)."
        )

    with performance_col2:
        st.write("**Ticket Resolution Progress**")
        st.progress(resolution_rate / 100)

        st.caption(
            f"{resolved} of {total} tickets resolved "
            f"({resolution_rate:.1f}%)."
        )

    st.divider()

    st.subheader("📊 Ticket Insights")

    chart_col1, chart_col2 = st.columns(2)

    # TICKET STATUS PIE CHART
    with chart_col1:
        st.markdown("### 🎯 Ticket Status")

        if summary["statuses"]:
            status_data = [
                {"Status": status, "Tickets": count}
                for status, count in summary["statuses"].items()
                if count > 0
            ]

            status_fig = px.pie(
                status_data,
                names="Status",
                values="Tickets",
                hole=0.55,
                title="Distribution by Status",
                color_discrete_sequence=px.colors.qualitative.Set2
            )

            status_fig.update_traces(
                textinfo="percent+label",
                textposition="inside",
                hovertemplate="%{label}<br>Tickets: %{value}<br>%{percent}<extra></extra>"
            )

            status_fig.update_layout(
                showlegend=True,
                legend_title_text="Status",
                margin=dict(t=50, b=20, l=10, r=10),
                height=350
            )

            st.plotly_chart(
                status_fig,
                use_container_width=True
            )
        else:
            st.info("No ticket status data available.")

    # TICKET PRIORITY PIE CHART
    with chart_col2:
        st.markdown("### 🚦 Ticket Priority")

        if summary["priorities"]:
            priority_data = [
                {"Priority": priority, "Tickets": count}
                for priority, count in summary["priorities"].items()
                if count > 0
            ]

            priority_fig = px.pie(
                priority_data,
                names="Priority",
                values="Tickets",
                hole=0.55,
                title="Distribution by Priority",
                color_discrete_sequence=px.colors.qualitative.Bold
            )

            priority_fig.update_traces(
                textinfo="percent+label",
                textposition="inside",
                hovertemplate="%{label}<br>Tickets: %{value}<br>%{percent}<extra></extra>"
            )

            priority_fig.update_layout(
                showlegend=True,
                legend_title_text="Priority",
                margin=dict(t=50, b=20, l=10, r=10),
                height=350
            )

            st.plotly_chart(
                priority_fig,
                use_container_width=True
            )
        else:
            st.info("No ticket priority data available.")

    st.divider()

    # DEPARTMENT WORKLOAD
    st.subheader("🏢 Department Workload")

    if summary["departments"]:
        department_data = [
            {"Department": department, "Tickets": count}
            for department, count in summary["departments"].items()
        ]

        department_data.sort(
            key=lambda item: item["Tickets"],
            reverse=True
        )

        department_fig = px.bar(
            department_data,
            x="Tickets",
            y="Department",
            orientation="h",
            text="Tickets",
            title="Tickets Handled by Department",
            color="Tickets",
            color_continuous_scale="Blues"
        )

        department_fig.update_traces(
            textposition="outside",
            hovertemplate="%{y}<br>Tickets: %{x}<extra></extra>"
        )

        department_fig.update_layout(
            yaxis=dict(autorange="reversed"),
            xaxis_title="Number of Tickets",
            yaxis_title="Department",
            showlegend=False,
            coloraxis_showscale=False,
            height=max(350, len(department_data) * 45),
            margin=dict(l=20, r=40, t=60, b=30)
        )

        st.plotly_chart(
            department_fig,
            use_container_width=True
        )
    else:
        st.info(
            "Department statistics will appear when tickets are created."
        )

    st.divider()

    st.subheader("📋 Recent Tickets")

    if tickets:
        recent_tickets = list(reversed(tickets[-5:]))

        st.dataframe(
            recent_tickets,
            width="stretch",
            hide_index=True
        )
    else:
        st.info("No tickets have been created yet.")


# =====================================================
# CREATE TICKET
# =====================================================

elif page == "🎫 Create Ticket":

    display_welcome_banner(
        "Create a Support Ticket 🎫",
        "Tell us what is happening. Our support team will help you."
    )

    st.subheader("Submit a New Campus Issue")

    with st.form("ticket_form"):

        title = st.text_input(
            "Ticket Title",
            placeholder="Example: Campus Wi-Fi not working"
        )

        description = st.text_area(
            "Describe the Problem",
            placeholder=(
                "Explain what happened, where it happened "
                "and when you noticed the issue..."
            ),
            height=150
        )

        submitted = st.form_submit_button(
            "🚀 Submit Support Ticket"
        )

    if submitted:

        if not title.strip():

            st.error("Please enter a ticket title.")

        elif not description.strip():

            st.error("Please describe the problem.")

        else:

            try:

                current_tickets = load_tickets()

                ticket_id = generate_ticket_id(current_tickets)

                new_ticket = {
                    "title": title.strip(),
                    "description": description.strip()
                }

                duplicates = find_possible_duplicates(
                    new_ticket,
                    current_tickets
                )

                ticket = {
                    "id": ticket_id,
                    "title": title.strip(),
                    "description": description.strip(),
                    "category": "Unclassified",
                    "priority": "Unassigned",
                    "department": "Unassigned",
                    "reason": "Awaiting AI analysis",
                    "status": "Open"
                }

                current_tickets.append(ticket)

                save_tickets(current_tickets)

                st.session_state["last_ticket"] = ticket
                st.session_state["possible_duplicates"] = duplicates

                st.session_state.pop("last_suggestions", None)

                st.success(
                    f"Ticket {ticket_id} created successfully!"
                )

                st.info(
                    "Your ticket has been saved. "
                    "You can request AI classification below."
                )

            except Exception as error:

                st.error(
                    "Unable to save your ticket. Please try again."
                )

                print(
                    f"Ticket creation error: {type(error).__name__}"
                )

    ticket = st.session_state.get("last_ticket")

    if ticket:

        st.divider()
        st.subheader("Your Latest Ticket")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Ticket ID", ticket["id"])

        with col2:
            st.metric("Status", ticket.get("status", "Open"))

        st.write("**Title:**", ticket["title"])
        st.write("**Description:**", ticket["description"])

        st.divider()
        st.subheader("🧠 Smart Ticket Intelligence")

        intelligence_col1, intelligence_col2 = st.columns(2)

        with intelligence_col1:
            st.metric("Category", ticket["category"])

        with intelligence_col2:
            st.metric("Priority", ticket["priority"])

        st.write(
            "**Recommended Department:**",
            ticket["department"]
        )

        st.info(
            f"**AI Explanation:** {ticket['reason']}"
        )

        if ticket["category"] == "Unclassified":

            if st.button("🧠 Analyse This Ticket with AI"):

                with st.spinner("Gemini is analysing your ticket..."):

                    intelligence = get_ticket_intelligence(
                        ticket["description"]
                    )

                if intelligence:

                    success = update_saved_ticket(
                        ticket["id"],
                        intelligence
                    )

                    if success:

                        st.success("AI classification completed!")
                        st.rerun()

                    else:

                        st.error("Unable to find the saved ticket.")

                else:

                    st.warning(
                        "AI analysis is unavailable. "
                        "Check your Gemini API configuration."
                    )

        st.divider()

        st.subheader("💡 Troubleshooting Suggestions")

        if st.button("Get AI Troubleshooting Suggestions"):

            with st.spinner("Gemini is preparing suggestions..."):

                suggestions = get_ai_suggestions(
                    ticket["description"]
                )

            st.session_state["last_suggestions"] = suggestions

        if "last_suggestions" in st.session_state:

            st.markdown(
                st.session_state["last_suggestions"]
            )

    duplicates = st.session_state.get(
        "possible_duplicates",
        []
    )

    if duplicates:

        st.divider()

        st.warning("⚠️ Possible Duplicate Tickets Detected")

        for duplicate in duplicates:

            st.write(
                f"**{duplicate['id']}** — "
                f"{duplicate['title']} "
                f"({duplicate['similarity']}% similarity)"
            )


# =====================================================
# MANAGE TICKETS
# =====================================================

# =====================================================
# TICKET MANAGEMENT AND STAFF ASSIGNMENT
# =====================================================

elif page == "🛠️ Manage Tickets":

    from datetime import datetime

    display_welcome_banner(
        "Ticket Management 🛠️",
        "Manage ticket statuses, assign staff and monitor workloads."
    )

    current_tickets = load_tickets()

    if current_tickets:

        # STAFF FILTER
        staff_members = sorted({
            ticket.get("assigned_to", "Unassigned")
            for ticket in current_tickets
            if ticket.get("assigned_to", "Unassigned") != "Unassigned"
        })

        st.subheader("👥 Staff Workload")

        workload_col1, workload_col2 = st.columns(2)

        with workload_col1:
            st.metric("Total Staff Assigned", len(staff_members))

        with workload_col2:
            assigned_count = sum(
                1 for ticket in current_tickets
                if ticket.get("assigned_to", "Unassigned") != "Unassigned"
            )
            st.metric("Assigned Tickets", assigned_count)

        st.divider()

        st.subheader("🔎 Filter Tickets")

        filter_options = ["All Staff", "Unassigned"] + staff_members

        selected_staff = st.selectbox(
            "Filter by Assigned Staff",
            filter_options,
            key="staff_ticket_filter"
        )

        if selected_staff == "All Staff":
            filtered_tickets = current_tickets

        elif selected_staff == "Unassigned":
            filtered_tickets = [
                ticket for ticket in current_tickets
                if ticket.get("assigned_to", "Unassigned") == "Unassigned"
            ]

        else:
            filtered_tickets = [
                ticket for ticket in current_tickets
                if ticket.get("assigned_to") == selected_staff
            ]

        st.divider()

        st.subheader("📋 All Campus Support Tickets")

        st.dataframe(
            list(reversed(filtered_tickets)),
            width="stretch",
            hide_index=True
        )

        st.divider()

        st.subheader("🛠️ Manage Individual Tickets")

        status_options = [
            "Open",
            "In Progress",
            "Resolved"
        ]

        for index, ticket in enumerate(reversed(filtered_tickets)):

            ticket_id = ticket.get("id", f"Ticket {index + 1}")

            ticket_title = ticket.get(
                "title",
                "Untitled Ticket"
            )

            current_status = ticket.get("status", "Open")

            if current_status not in status_options:
                current_status = "Open"

            assigned_to = ticket.get(
                "assigned_to",
                "Unassigned"
            )

            with st.expander(
                f"{ticket_id} — {ticket_title}"
            ):

                st.write(
                    "**Description:**",
                    ticket.get("description", "")
                )

                st.write(
                    "**Department:**",
                    ticket.get("department", "Unassigned")
                )

                st.write(
                    "**Priority:**",
                    ticket.get("priority", "Unassigned")
                )

                st.write(
                    "**Current Status:**",
                    current_status
                )

                st.write(
                    "**Assigned Staff:**",
                    assigned_to
                )

                st.write(
                    "**Assignment Date:**",
                    ticket.get("assigned_at", "Not yet assigned")
                )

                # STAFF ASSIGNMENT
                st.markdown("#### 👤 Assign or Reassign Staff")

                with st.form(f"assignment_form_{ticket_id}"):

                    staff_name = st.text_input(
                        "Staff Member's Name",
                        value=(
                            ""
                            if assigned_to == "Unassigned"
                            else assigned_to
                        ),
                        key=f"staff_name_{ticket_id}"
                    )

                    assignment_submitted = st.form_submit_button(
                        "Save Staff Assignment"
                    )

                if assignment_submitted:

                    staff_name = staff_name.strip()

                    if not staff_name:

                        st.error("Please enter a staff member's name.")

                    else:

                        assignment_data = {
                            "assigned_to": staff_name
                        }

                        if staff_name != assigned_to:

                            assignment_data["assigned_at"] = (
                                datetime.now()
                                .astimezone()
                                .isoformat(timespec="minutes")
                            )

                        try:

                            success = update_saved_ticket(
                                ticket_id,
                                assignment_data
                            )

                            if success:

                                st.success(
                                    f"{ticket_id} assigned to {staff_name}."
                                )

                                st.rerun()

                            else:

                                st.error("Ticket could not be found.")

                        except Exception as error:

                            st.error("Unable to save staff assignment.")

                            print(
                                f"Assignment error: {type(error).__name__}"
                            )

                st.divider()

                # STATUS MANAGEMENT
                st.markdown("#### 📌 Update Ticket Status")

                with st.form(f"status_form_{ticket_id}"):

                    new_status = st.selectbox(
                        "Choose New Status",
                        status_options,
                        index=status_options.index(current_status),
                        key=f"status_select_{ticket_id}"
                    )

                    status_submitted = st.form_submit_button(
                        "Save Status"
                    )

                if status_submitted:

                    try:

                        success = update_saved_ticket(
                            ticket_id,
                            {"status": new_status}
                        )

                        if success:

                            st.success(
                                f"{ticket_id} updated to {new_status}."
                            )

                            st.rerun()

                        else:

                            st.error("Ticket could not be found.")

                    except Exception as error:

                        st.error("Unable to update ticket status.")

                        print(
                            f"Status update error: {type(error).__name__}"
                        )

        # STAFF WORKLOAD VISUALISATIONS
        st.divider()
        st.subheader("📊 Staff Workload Analytics")

        workload_data = []

        for staff, count in staff_workload.items():
            workload_data.append({
                "Staff Member": staff,
                "Tickets Assigned": count
            })

        if workload_data:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### 🥧 Ticket Distribution")

                pie_fig = px.pie(
                    workload_data,
                    names="Staff Member",
                    values="Tickets Assigned",
                    hole=0.45,
                    title="Tickets Assigned per Staff"
                )

                pie_fig.update_traces(
                    textposition="inside",
                    textinfo="percent+label"
                )

                st.plotly_chart(
                    pie_fig,
                    use_container_width=True
                )

            with col2:
                st.markdown("#### 📦 Workload Box Plot")

                box_fig = px.box(
                    workload_data,
                    y="Tickets Assigned",
                    points="all",
                    title="Staff Workload Distribution"
                )

                box_fig.update_layout(
                    yaxis_title="Number of Assigned Tickets",
                    xaxis_title="Staff Workload",
                    showlegend=False
                )

                st.plotly_chart(
                    box_fig,
                    use_container_width=True
                )
        else:
            st.info("No staff workload data available yet.")



# =====================================================
# AI ASSISTANT - THREE AI MODULES
# =====================================================

elif page == "🤖 AI Assistant":

    display_welcome_banner(
        "CampusFlow AI Workspace 🤖",
        "Choose an AI tool to analyse tickets, receive solutions "
        "or chat with your intelligent campus assistant."
    )

    st.markdown("### Choose Your AI Module")

    ai_module = st.radio(
        "Select an AI service:",
        [
            "🎯 Ticket Intelligence",
            "💡 AI Suggestions",
            "💬 CampusFlow Chatbot"
        ],
        horizontal=True,
        label_visibility="collapsed",
        key="campusflow_ai_module"
    )

    st.divider()

    # -------------------------------------------------
    # MODULE 1: TICKET INTELLIGENCE
    # -------------------------------------------------

    if ai_module == "🎯 Ticket Intelligence":

        st.subheader("🎯 AI Ticket Intelligence")

        st.write(
            "Describe a campus problem. Gemini will identify "
            "its category, priority and responsible department."
        )

        description = st.text_area(
            "Describe the campus problem",
            placeholder="Example: The Wi-Fi connection in the library has stopped working.",
            height=150,
            key="intelligence_description"
        )

        if st.button("🔍 Analyse Ticket", use_container_width=True):

            if not description.strip():
                st.warning("Please describe the problem first.")

            else:
                with st.spinner("Gemini is analysing your ticket..."):
                    try:
                        result = get_ticket_intelligence(description)

                        if not result:
                            st.error(
                                "The AI could not analyse this ticket. "
                                "Check your Gemini API configuration and try again."
                            )

                        else:
                            st.success("Ticket analysis completed!")

                            col1, col2, col3 = st.columns(3)

                            with col1:
                                st.metric(
                                    "Category",
                                    result.get("category", "Unknown")
                                )

                            with col2:
                                st.metric(
                                    "Priority",
                                    result.get("priority", "Unknown")
                                )

                            with col3:
                                st.metric(
                                    "Department",
                                    result.get("department", "Unknown")
                                )

                            st.subheader("Analysis")
                            st.write(
                                result.get(
                                    "reason",
                                    "No additional explanation provided."
                                )
                            )

                    except Exception as error:
                        st.error(
                            f"Ticket analysis failed: {type(error).__name__}"
                        )

    # -------------------------------------------------
    # MODULE 2: AI SUGGESTIONS
    # -------------------------------------------------

    elif ai_module == "💡 AI Suggestions":

        st.subheader("💡 AI Troubleshooting Suggestions")

        st.write(
            "Describe a campus problem and receive practical "
            "troubleshooting steps and recommendations."
        )

        problem = st.text_area(
            "What problem are you experiencing?",
            placeholder="Example: My student portal refuses to accept my login credentials.",
            height=150,
            key="suggestion_description"
        )

        if st.button("✨ Generate Suggestions", use_container_width=True):

            if not problem.strip():
                st.warning("Please describe the problem first.")

            else:
                with st.spinner(
                    "CampusFlow AI is generating recommendations..."
                ):
                    try:
                        suggestions = get_ai_suggestions(problem)

                        st.success("AI recommendations generated!")
                        st.subheader("Recommended Solutions")
                        st.markdown(suggestions)

                    except Exception as error:
                        st.error(
                            f"Suggestion generation failed: {type(error).__name__}"
                        )

    # -------------------------------------------------
    # MODULE 3: CAMPUSFLOW CHATBOT
    # -------------------------------------------------

    elif ai_module == "💬 CampusFlow Chatbot":

        st.subheader("💬 Chat with CampusFlow AI")

        st.caption(
            "Ask questions about campus support, troubleshooting "
            "and available ticket information."
        )

        st.markdown("**Try asking:**")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.info("📶 How can I fix campus Wi-Fi problems?")

        with col2:
            st.info("🎫 How do I submit a support ticket?")

        with col3:
            st.info("📊 What do ticket statuses mean?")

        if "chat_messages" not in st.session_state:
            st.session_state["chat_messages"] = []

        clear_col, _ = st.columns([1, 5])

        with clear_col:
            if st.button("🗑️ Clear Chat"):
                st.session_state["chat_messages"] = []
                st.rerun()

        if not st.session_state["chat_messages"]:
            with st.chat_message("assistant"):
                st.markdown(
                    """
                    Hello! 👋 Welcome to CampusFlow AI.

                    I can help you understand campus support,
                    troubleshoot problems and answer ticket-related
                    questions.

                    What would you like help with?
                    """
                )

        for message in st.session_state["chat_messages"]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        user_prompt = st.chat_input(
            "Ask CampusFlow AI a question...",
            key="campusflow_chat_input"
        )

        if user_prompt:

            st.session_state["chat_messages"].append({
                "role": "user",
                "content": user_prompt
            })

            with st.chat_message("user"):
                st.markdown(user_prompt)

            with st.chat_message("assistant"):
                with st.spinner("CampusFlow AI is thinking..."):
                    try:
                        response = get_chatbot_response(
                            st.session_state["chat_messages"],
                            load_tickets()
                        )
                    except Exception as error:
                        response = (
                            "I'm sorry, I couldn't process that request. "
                            f"Error: {type(error).__name__}"
                        )

                st.markdown(response)

            st.session_state["chat_messages"].append({
                "role": "assistant",
                "content": response
            })


# =====================================================
# REPORTS
# =====================================================

elif page == "📊 Reports":

    display_welcome_banner(
        "CampusFlow Reports 📊",
        "Understand ticket resolution, department performance "
        "and campus support trends."
    )

    current_tickets = load_tickets()

    summary = generate_dashboard_summary(current_tickets)

    # -------------------------------------------------
    # TICKET RESOLUTION ANALYTICS
    # -------------------------------------------------

    st.subheader("Ticket Resolution Analytics")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Tickets", summary["total_tickets"])

    with col2:
        st.metric("Resolved Tickets", summary["resolved_tickets"])

    with col3:
        st.metric("Outstanding Tickets", summary["outstanding_tickets"])

    st.subheader("Overall Resolution Rate")

    st.progress(summary["resolution_rate"] / 100)

    st.caption(
        f"{summary['resolution_rate']:.1f}% of submitted tickets "
        "have been resolved."
    )

    st.divider()

    # -------------------------------------------------
    # DEPARTMENT RESOLUTION PERFORMANCE
    # -------------------------------------------------

    st.subheader("Department Resolution Performance")

    department_resolution = summary["department_resolution"]

    if department_resolution:

        department_rates = {
            department: details["resolution_rate"]
            for department, details in department_resolution.items()
        }

        st.bar_chart(
            department_rates,
            horizontal=True
        )

        department_table = []

        for department, details in department_resolution.items():

            department_table.append({
                "Department": department,
                "Total Tickets": details["total_tickets"],
                "Resolved Tickets": details["resolved_tickets"],
                "Resolution Rate": (
                    f"{details['resolution_rate']:.1f}%"
                )
            })

        st.dataframe(
            department_table,
            width="stretch",
            hide_index=True
        )

    else:

        st.info("Department resolution data will appear here.")

    st.divider()

    # -------------------------------------------------
    # TICKET CATEGORIES AND PRIORITIES
    # -------------------------------------------------

    st.subheader("Ticket Categories")
    st.bar_chart(summary["categories"])

    st.subheader("Ticket Priorities")
    st.bar_chart(summary["priorities"])

    st.divider()

    # -------------------------------------------------
    # DEPARTMENT WORKLOAD
    # -------------------------------------------------

    st.subheader("🏢 Department Workload")

    if summary["departments"]:

        department_data = [
            {
                "Department": department,
                "Tickets": count
            }
            for department, count in summary["departments"].items()
        ]

        department_data.sort(
            key=lambda item: item["Tickets"],
            reverse=True
        )

        department_fig = px.bar(
            department_data,
            x="Tickets",
            y="Department",
            orientation="h",
            text="Tickets",
            color="Tickets",
            color_continuous_scale="Teal"
        )

        department_fig.update_traces(
            textposition="outside"
        )

        department_fig.update_layout(
            title="Ticket Distribution Across Departments",
            yaxis=dict(autorange="reversed"),
            xaxis_title="Number of Tickets",
            yaxis_title="Department",
            coloraxis_showscale=False,
            height=max(350, len(department_data) * 45),
            margin=dict(l=20, r=40, t=60, b=30)
        )

        st.plotly_chart(
            department_fig,
            use_container_width=True
        )

    else:

        st.info(
            "Department statistics will appear when tickets are created."
        )

    st.divider()

    # -------------------------------------------------
    # HISTORICAL TICKET INTELLIGENCE
    # -------------------------------------------------

    st.header("🧠 Historical Ticket Intelligence")

    st.write(
        "Use AI to classify previously submitted tickets "
        "that have not yet received an AI classification."
    )

    unclassified_tickets = [
        ticket for ticket in current_tickets
        if ticket.get("category", "Unclassified") == "Unclassified"
    ]

    st.metric(
        "Tickets Awaiting AI Classification",
        len(unclassified_tickets)
    )

    if st.button("🚀 Classify Historical Tickets"):

        if not unclassified_tickets:

            st.success(
                "All tickets have already been classified!"
            )

        else:

            progress_bar = st.progress(0)
            status_text = st.empty()

            def update_progress(current, total):

                percentage = current / total

                progress_bar.progress(percentage)

                status_text.write(
                    f"Analysing ticket {current} of {total}..."
                )

            try:

                updated_tickets, updated, failed = (
                    classify_unclassified_tickets(
                        current_tickets,
                        progress_callback=update_progress
                    )
                )

                save_tickets(updated_tickets)

                progress_bar.progress(1.0)

                status_text.success(
                    "Historical analysis completed!"
                )

                st.success(
                    f"AI classification completed! "
                    f"{updated} ticket(s) updated."
                )

                if failed:

                    st.warning(
                        f"{failed} ticket(s) could not be classified. "
                        "You can try again later."
                    )

                st.rerun()

            except Exception as error:

                st.error(
                    "Historical classification encountered an error."
                )

                print(
                    f"Historical classification error: "
                    f"{type(error).__name__}: {error}"
                )

                st.success(
                    f"AI classification completed! "
                    f"{updated} ticket(s) updated."
                )

                if failed:

                    st.warning(
                        f"{failed} ticket(s) could not be classified. "
                        "You can try again later."
                    )

                st.rerun()

            except Exception as error:

                st.error(
                    "Historical classification encountered an error."
                )

                print(
                    f"Historical classification error: "
                    f"{type(error).__name__}: {error}"
                )


# =====================================================
# FLOATING CHAT — AVAILABLE ON EVERY PAGE
# =====================================================

render_floating_chat()