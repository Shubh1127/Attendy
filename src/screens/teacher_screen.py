import streamlit as st
from src.ui.base_layout import style_base_layout, style_background_home,style_background_dashboard

from src.components.header import header_dashboard

def teacher_screen():

    
    style_background_dashboard()
    style_base_layout()
    c1,c2=st.columns(2,vertical_alignment='center',gap='xxlarge')
    with c1:

        header_dashboard()  
    with c2:
            st.button('Go Back', type='secondary', icon=':material/arrow_back:', icon_position='left', on_click=lambda: st.session_state.update({'login_type': None}),key='loginbackbtn')

    st.header("Teacher Page")