import streamlit as st
from src.ui.base_layout import style_base_layout, style_background_home,style_background_dashboard

from src.components.header import header_dashboard

def teacher_screen():

    
    style_background_dashboard()
    style_base_layout()
    teacher_login()

def teacher_login():
    c1,c2=st.columns(2,vertical_alignment='center',gap='xxlarge')
    with c1:

        header_dashboard()  
    with c2:
            st.button('Go Back', type='secondary', icon=':material/arrow_back:',shortcut='control+Backspace', icon_position='left', on_click=lambda: st.session_state.update({'login_type': None}),key='loginbackbtn')
    
    st.markdown("<h1 style='color:#000000',text-align:center'>Login Using Password</h1>", unsafe_allow_html=True)

    teacher_username=st.text_input("Enter you username",placeholder="Username", key='teacher_username')

    teacher_password=st.text_input("Enter your password",placeholder="Password", type='password', key='teacher_password')

    st.divider()

    btn1,btn2=st.columns(2)

    with btn1:
         st.button('Login', type='primary', on_click=teacher_dashboard, key='teacherloginbtn',icon=':material/passkey:',shortcut='control+enter')
def teacher_register():
    c1,c2=st.columns(2,vertical_alignment='center',gap='xxlarge')
    with c1:

        header_dashboard()  
    with c2:
            st.button('Go Back', type='secondary', icon=':material/arrow_back:',shortcut='control+Backspace', icon_position='left', on_click=lambda: st.session_state.update({'login_type': None}),key='loginbackbtn')
    
    st.markdown("<h1 style='color:#000000',text-align:center'>Register as a Teacher</h1>", unsafe_allow_html=True)
def teacher_dashboard():

    st.markdown("<h1 style='color:#000000'>Teacher Dashboard</h1>", unsafe_allow_html=True)