from pathlib import Path

import streamlit as st

st.set_page_config(page_title="MOVEXA", page_icon="🚘", layout="wide")

ASSET_PATH = Path(__file__).resolve().parent.parent / "assets" / "movexa_inicio.png"

st.markdown(
    """
    <style>
    .movexa-intro {
        text-align: center;
        padding: 4rem 1rem 2rem;
        max-width: 720px;
        margin: 0 auto;
    }
    .movexa-intro h1 {
        font-size: 3.2rem;
        font-weight: 800;
        letter-spacing: -0.06em;
        margin: 1.2rem 0 0.4rem;
        color: #f4f5f7;
    }
    .movexa-intro .tagline {
        opacity: 0.8;
        font-size: 1.15rem;
        color: #aab1bc;
        margin-bottom: 2rem;
    }
    .movexa-intro .footer {
        margin-top: 3rem;
        font-size: 0.78rem;
        color: #69727e;
        letter-spacing: 0.04em;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="movexa-intro">', unsafe_allow_html=True)

if ASSET_PATH.exists():
    st.image(str(ASSET_PATH), width=280)
else:
    st.info("Adicione o logo oficial em `assets/movexa_inicio.png` para exibi-lo nesta tela.")

st.markdown(
    """
    <h1>MOVEXA</h1>
    <p class="tagline">Gestão inteligente para qualquer tipo de veículo.</p>
    <p class="footer">Built by ArqTech Labs</p>
    </div>
    """,
    unsafe_allow_html=True,
)
