import streamlit as st
import time
from src.components.footer_home import footer_dashboard
from src.database.db import check_teacher_exists, create_teacher, teacher_login
from src.ui.base_layout import style_base_layout, style_background_home,style_background_dashboard

from src.components.header import header_dashboard


def show_top_popup(message, kind="success", duration=1.5):
    bg_color = "#16A34A" if kind == "success" else "#DC2626"
    popup = st.empty()
    popup.markdown(
        f"""
        <style>
            .top-popup-wrap {{
                position: fixed;
                top: 1rem;
                left: 50%;
                transform: translateX(-50%);
                z-index: 999999;
                pointer-events: none;
                animation: popupDrop 0.18s ease-out;
            }}

            .top-popup-card {{
                padding: 0.9rem 1.25rem;
                border-radius: 1rem;
                background: {bg_color};
                color: #FFFFFF;
                font-weight: 700;
                box-shadow: 0 12px 30px rgba(0, 0, 0, 0.18);
                min-width: 240px;
                text-align: center;
            }}

            @keyframes popupDrop {{
                from {{ opacity: 0; transform: translateX(-50%) translateY(-10px); }}
                to {{ opacity: 1; transform: translateX(-50%) translateY(0); }}
            }}
        </style>
        <div class="top-popup-wrap">
            <div class="top-popup-card">{message}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    time.sleep(duration)
    popup.empty()


def login_teacher(username,password):
    if not username or not password:
        return False
    teacher = teacher_login(username,password)
    if teacher:
        st.session_state.user.role='teacher'
        st.session_state.teacher_data=teacher
        st.session_state.is_logged_in=True
        return True
    return False
def teacher_screen():

    
    style_background_dashboard()
    style_base_layout()

    if 'teacher_data' in st.session_state:
        teacher_dashboard()
    elif 'teacher_login_type' not in st.session_state or st.session_state['teacher_login_type']=='login':
        teacher_Screen_login()
    elif st.session_state['teacher_login_type']=='register':
        teacher_Screen_register()
         
   




def teacher_Screen_login():
    

    
    teacher_username=st.text_input("Enter you username",placeholder="Username")
    
    

    teacher_password=st.text_input("Enter your password",placeholder="Password",type='password')

    

    st.divider()


    btn1,btn2=st.columns(2)

    with btn1:
        if st.button('Login',icon=':material/passkey:',shortcut='control+enter',width='stretch'):
            if login_teacher(teacher_username,teacher_password):
                show_top_popup("Login successful", "success")
                st.rerun()
            else:
                st.error("Invalid username or password")
                show_top_popup("Invalid username or password", "error")
            
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

    teacher_name=st.text_input("Enter you name",placeholder="Name",key='teacher_name')

    teacher_password=st.text_input("Enter your password",placeholder="Password",type='password', key='teacher_password')

    teacher_password_confirm=st.text_input("Confirm your password",placeholder="Password",type='password')

    st.divider()

    btn1,btn2=st.columns(2)

    with btn1:
        if st.button('Register',icon=':material/passkey:',shortcut='control+enter',width='stretch'):
            sucess,message=register_teacher(teacher_username,teacher_name,teacher_password,teacher_password_confirm)
            if sucess:
                show_top_popup(message, "success")
                st.session_state.teacher_login_type='login'
                st.rerun()
            else:
                st.error(message)
                show_top_popup(message, "error")
    with btn2:
         if st.button('login instead', type='primary',icon=':material/person_add:',width='stretch'):
              st.session_state.teacher_login_type='login' 
              st.rerun()


def register_teacher(teacher_username,teacher_name,teacher_password,teacher_password_confirm):
    if not teacher_username or not teacher_name or not teacher_password or not teacher_password_confirm:
        return False,"Please fill all the fields"
    
    if check_teacher_exists(teacher_username):
        return False,"Teacher with this username already exists"

    if teacher_password!=teacher_password_confirm:
        return False,"Passwords do not match"
    

    try:
        create_teacher(teacher_username,teacher_password,teacher_name)
        return True,"Teacher created successfully, Please login now"
    except Exception as e:
        return False, str(e) or "An error occurred while creating teacher" 

def teacher_dashboard():
    teacher_data=st.session_state.teacher_data

    st.markdown("<h1 style='color:#000000'>Teacher Dashboard</h1>", unsafe_allow_html=True)

    st.header(f"Welcome, {teacher_data['name']}")