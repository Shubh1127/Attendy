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
        st.session_state.user_role='teacher'
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
    teacher_data = st.session_state.teacher_data
    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')
    with c1:
        header_dashboard()
    with c2:
        st.subheader(f"""Welcome, {teacher_data['name']} """)
        if st.button("Logout", type='secondary', key='loginbackbtn', shortcut="control+backspace"):
            st.session_state['is_logged_in'] = False
            del st.session_state.teacher_data 
            st.rerun()


    st.space()

    if "current_teacher_tab" not in st.session_state:
        st.session_state.current_teacher_tab = 'take_attendance'
    tab1, tab2, tab3 = st.columns(3)


    with tab1:
        type1 = "primary" if st.session_state.current_teacher_tab == 'take_attendance' else "tertiary"
        if st.button('Take Attendance',type=type1, width='stretch', icon=':material/ar_on_you:'):
            st.session_state.current_teacher_tab = 'take_attendance'
            st.rerun()

    with tab2:
        type2 = "primary" if st.session_state.current_teacher_tab == 'manage_subjects' else "tertiary"
        if st.button('Manage Subjects', type=type2, width='stretch', icon=':material/book_ribbon:'):
            st.session_state.current_teacher_tab = 'manage_subjects'
            st.rerun()

    with tab3:
        type3 = "primary" if st.session_state.current_teacher_tab == 'attendance_records' else "tertiary"
        if st.button('Attendance Records',type=type3, width='stretch', icon=':material/cards_stack:'):
            st.session_state.current_teacher_tab = 'attendance_records'
            st.rerun()



    st.divider()

    if st.session_state.current_teacher_tab == "take_attendance":
        teacher_tab_take_attendance()
    if st.session_state.current_teacher_tab == "manage_subjects":
        teacher_tab_manage_subjects()
    if st.session_state.current_teacher_tab == "attendance_records":
        teacher_tab_attendance_records()


    footer_dashboard()

def teacher_tab_take_attendance():
        st.info("To take attendance, please go to the student login page and ask your students to log in using their face ID. You can monitor the attendance logs in the 'Attendance Records' tab.")
            # voice_attendance_dialog(selected_subject_id)



def teacher_tab_manage_subjects():
    teacher_id = st.session_state.teacher_data['teacher_id']
    col1, col2 = st.columns(2)
    with col1:
        st.header('Manage Subjects', width='stretch')

    with col2:
        if st.button('Create New Subject', width='stretch'):
            create_subject_dialog(teacher_id)


    # LIST all SUBJECTS
    subjects = get_teacher_subjects(teacher_id)
    if subjects:
        for sub in subjects:
            stats = [
                ("🫂", "Students", sub['total_students']),
                ("🕰️", "Classes", sub['total_classes']),
            ]
        def share_btn():
            if st.button(f"Share Code: {sub['name']}", key=f"share_{sub['subject_code']}", icon=":material/share:"):
                share_subject_dialog(sub['name'], sub['subject_code'])
            st.space()

        subject_card(
            name = sub['name'],
            code = sub['subject_code'],
            section = sub['section'],
            stats=stats,
            footer_callback=share_btn
        )
    else:
        st.info("NO SUBJECTS FOUND. CREATE ONE ABOVE")


def teacher_tab_attendance_records():
        st.info("Attendance records will be displayed here once you start taking attendance for your subjects.")
    # st.dataframe(display_df, width='stretch', hide_index=True)