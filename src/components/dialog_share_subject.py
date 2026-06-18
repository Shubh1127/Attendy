import streamlit as st

import segno
import io


@st.dialog("Share Class Link")
def share_subject_dialog(subject_name, subject_code):
    app_domain = "snapclass-main.streamlit.app"
    join_url = f"{app_domain}/?join-code={subject_code}"

    st.markdown(
        """
        <style>
            [data-testid="stDialog"] [role="dialog"] {
                background: #f8fbff !important;
                color: #111827 !important;
                border: 1px solid #dbeafe;
                box-shadow: 0 18px 42px rgba(15, 23, 42, 0.18);
            }

            [data-testid="stDialog"] h1,
            [data-testid="stDialog"] h2,
            [data-testid="stDialog"] h3,
            [data-testid="stDialog"] p,
            [data-testid="stDialog"] label,
            [data-testid="stDialog"] span,
            [data-testid="stDialog"] div {
                color: #111827;
            }

            [data-testid="stDialog"] pre,
            [data-testid="stDialog"] code {
                background: #eef2ff !important;
                color: #0f172a !important;
                border-radius: 10px;
            }

            [data-testid="stDialog"] [data-testid="stAlert"] {
                background: #e0f2fe;
                border: 1px solid #bae6fd;
                color: #0c4a6e;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.header("Scan to Join")

    qr = segno.make(join_url)

    out = io.BytesIO()

    qr.save(out, kind='png', scale=10, border=1)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('### Copy Link')
        st.code(join_url, language="text")
        st.code(subject_code, language="text")
        st.info('Copy this link to share on Whatsapp or Email')

    with col2:
        st.markdown('### Scan to Join')
        st.image(out.getvalue(), caption='QRCODE for class joining')

        