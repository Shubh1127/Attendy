import streamlit as st



def style_background_home():

    st.markdown("""
        <style>

                .stApp {
                    background: #5865F2 !important;
                    height: 100vh !important;
                    overflow: hidden !important;
                }

                .block-container {
                    padding-top: 1rem !important;
                    padding-bottom: 0rem !important;
                }

                .stApp div[data-testid="stColumn"]{
                    background-color:#E0E3FF !important;
                    padding:1.5rem !important;
                    border-radius: 5rem !important;
                    }
        </style>  

                """
            ,unsafe_allow_html=True)
    

def style_background_dashboard():

    st.markdown("""
        <style>

                .stApp {
                    background: #E0E3FF !important;
                }

        </style>  

                """
            ,unsafe_allow_html=True)
    

    

def style_base_layout():
# asdasd
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300..700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@100..900&display=swap');


                
         /* Hide Top Bar of streamlit except header (keeps rerun button visible) */
                
            #MainMenu, footer {
                visibility: hidden;
            }
                
            # .block-container {
            #     padding-top:1.5rem !important;    
            # }

            h1 {
                font-family: 'Space Grotesk', sans-serif !important;
                font-size: 3.5rem !important;
                line-height: 1.1 !important;
                margin-bottom:0rem !important;
            }
            h1 { color: #000000 !important; }
                

            h2 {
                font-family: 'Space Grotesk', sans-serif !important;
                font-size: 2rem !important;
                line-height:0.9 !important;
                margin-bottom:0rem !important;
            }
                
            h3, h4, p {
                  font-family: 'Inter', sans-serif !important;
            }   

            div[data-testid="stWidgetLabel"],
            div[data-testid="stWidgetLabel"] p,
            label {
                color: #000000 !important;
            }

            div[data-baseweb="input"] {
                background-color: #FFFFFF !important;
                border-radius: 1rem !important;
                border: 1px solid #FFFFFF !important;
            }

            div[data-baseweb="input"] input {
                background-color: #FFFFFF !important;
                color: #000000 !important;
                caret-color: #000000 !important;
                border: none !important;
                box-shadow: none !important;
            }

            div[data-baseweb="input"]:focus-within {
                border-color: #FFFFFF !important;
                box-shadow: none !important;
            }

            div[data-baseweb="input"] button {
                background-color: #FFFFFF !important;
                border: none !important;
                box-shadow: none !important;
            }

            div[data-baseweb="input"] button:hover,
            div[data-baseweb="input"] button:focus,
            div[data-baseweb="input"] button:active {
                background-color: #FFFFFF !important;
                box-shadow: none !important;
            }

            div[data-baseweb="input"] button svg {
                fill: #000000 !important;
            }
            div[data-baseweb="input"] input::placeholder {
                color: #6B7280 !important;
            }
                

            button{
                border-radius: 1.5rem !important;
                background-color: #5865F2 !important;
                color: white !important;
                padding: 10px 20px !important;
                border: none !important;
                transition: transform 0.25s ease-in-out !important;
                }

            button[kind="secondary"]{
                border-radius: 1.5rem !important;
                background-color: #EB459E !important;
                color: white !important;
                padding: 10px 20px !important;
                border: none !important;
                transition: transform 0.25s ease-in-out !important;
                }

            button[kind="tertiary"]{
                border-radius: 1.5rem !important;
                background-color: black !important;
                color: white !important;
                padding: 10px 20px !important;
                border: none !important;
                transition: transform 0.25s ease-in-out !important;
                }

            button:hover{
                transform :scale(1.05)}
        </style>  

                """
            ,unsafe_allow_html=True)