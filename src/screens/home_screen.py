import streamlit as st
from src.components.header import header_home
from src.ui.style_base_layout import style_base_layout
from src.ui.style_base_layout import style_background_home
def home_screen():
    st.header("Home Page")

      
    header_home()
    style_background_home()
    style_base_layout()
    col1,col2=st.columns(2)

    with col1:
            if st.button("Teacher Portal"):
                st.session_state['login_type']='teacher'
                st.rerun()
    with col2:
            if st.button("student portal"):
                  st.session_state['login_type']='student'
                  st.rerun()