import streamlit as st

from src.components.footer_home import footer_dashboard
from src.components.header import header_dashboard
from src.ui.base_layout import style_background_dashboard, style_base_layout

def student_screen():

    style_background_dashboard()
    style_base_layout() 
    c1,c2=st.columns(2,vertical_alignment='center',gap='xxlarge')
    with c1:

        header_dashboard()  
    with c2:
           if st.button('Go Back', type='secondary', icon=':material/arrow_back:',shortcut='control+Backspace', icon_position='left',key='loginbackbtn'):
                st.session_state['login_type']=None
                st.rerun()
    
    st.markdown("<h1 style='color:#000000; text-align:center'>Login Using Face ID</h1>", unsafe_allow_html=True)

    st.space()
    st.space()

    st.camera_input("Position you face in the center")
    footer_dashboard()