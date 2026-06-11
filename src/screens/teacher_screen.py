import streamlit as st
from src.components.footer_home import footer_dashboard
from src.ui.base_layout import style_base_layout, style_background_home,style_background_dashboard

from src.components.header import header_dashboard

def teacher_screen():

    
    style_background_dashboard()
    style_base_layout()


    if 'teacher_login_type' not in st.session_state or st.session_state['teacher_login_type']=='login':
        teacher_Screen_login()
    elif st.session_state['teacher_login_type']=='register':
        teacher_Screen_register()
         
   




def teacher_Screen_login():
    c1,c2=st.columns(2,vertical_alignment='center',gap='xxlarge')
    with c1:

        header_dashboard()  
    with c2:
           if st.button('Go Back', type='secondary', icon=':material/arrow_back:',shortcut='control+Backspace', icon_position='left',key='loginbackbtn'):
                st.session_state['login_type']=None
                st.rerun()
    
    st.markdown("<h1 style='color:#000000; text-align:center'>Login Using Password</h1>", unsafe_allow_html=True)

    st.space()
    st.space()

    
    teacher_username=st.text_input("Enter you username",placeholder="Username")
    
    

    teacher_password=st.text_input("Enter your password",placeholder="Password",type='password')

    

    st.divider()


    btn1,btn2=st.columns(2)

    with btn1:
            st.button('Login',icon=':material/passkey:',shortcut='control+enter',width='stretch')
    with btn2:
           if st.button('Register', type='primary', icon=':material/person_add:',width='stretch'):
                st.session_state.teacher_login_type='register'
                st.rerun()

    footer_dashboard()

          
def teacher_Screen_register():
    c1,c2=st.columns(2,vertical_alignment='center',gap='xxlarge')
    with c1:

        header_dashboard()  
    with c2:
          if st.button('Go Back', type='secondary', icon=':material/arrow_back:',shortcut='control+Backspace' , icon_position='left'):
               st.session_state.teacher_login_type='login'
               st.session_state['login_type']=None
               st.rerun()


    st.markdown("<h1 style='color:#000000; text-align:center'>Register as a Teacher</h1>", unsafe_allow_html=True)

    st.space()
    st.space()

    teacher_username=st.text_input("Enter you username",placeholder="Username", key='teacher_username')

    teacher_name=st.text_input("Enter you name",placeholder="Name")

    teacher_password=st.text_input("Enter your password",placeholder="Password",type='password', key='teacher_password')

    teacher_password_confirm=st.text_input("Confirm your password",placeholder="Password",type='password')

    st.divider()

    btn1,btn2=st.columns(2)

    with btn1:
         st.button('Register',icon=':material/passkey:',shortcut='control+enter',width='stretch')
    with btn2:
         if st.button('login instead', type='primary',icon=':material/person_add:',width='stretch'):
              st.session_state.teacher_login_type='login' 
              st.rerun()


def teacher_dashboard():

    st.markdown("<h1 style='color:#000000'>Teacher Dashboard</h1>", unsafe_allow_html=True)