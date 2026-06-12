import time

import streamlit as st

from database.db import get_all_students
from src.components.footer_home import footer_dashboard
from src.components.header import header_dashboard
from src.ui.base_layout import style_background_dashboard, style_base_layout
from PIL import Image
import numpy as np
from src.pipelines.face_pipeline import predict_attendance
from src.database.db import create_student
from src.pipelines.face_pipeline import get_face_embedding, train_classifier
from src.pipelines.voice_pipeline import get_voice_embedding

def student_dashboard():
     st.header("Student Dashboard")
def student_screen():

    style_background_dashboard()
    style_base_layout() 

    if "student_data" in st.session_state and st.session_state.student_data:
         student_dashboard()
         return
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

    show_registration=False
    photo_source=st.camera_input("Position you face in the center")


    if photo_source:
         img=np.array(Image.open(photo_source))

         with st.spinner('Processing...'):
              detected,all_ids,num_faces=predict_attendance(img)

              if num_faces==0:
                    st.warning('No face detected. Please try again.')
              elif num_faces>1:
                    st.warning('Multiple faces detected. Please ensure only your face is visible and try again.')
              else:
                    if detected:
                         student_id=list(detected.keys())[0]
                         all_students=get_all_students()
                         student=next((s for s in all_students if s['student_id']==student_id),None)

                         if student:
                              st.session_state.is_logged_in=True
                              st.session_state.user_role='student' 
                              st.session_state.student_data=student
                              st.toast('Welcome, {}!'.format(student['name']), icon='👋')
                              time.sleep(1)
                              st.rerun
                    else:
                         st.info('Face not recognized. Please try again or contact your teacher for assistance.')
                         show_registration=True
    if show_registration:
        with st.container(border=True):
            st.header('Register new Profile')
            new_name = st.text_input("Enter your name", placeholder='E.g. Hamza Rizvi')

            st.subheader('Optional : Voice Enrollment')
            st.info("Enroll your for voice only attendance")


            audio_data = None

            try:
                audio_data = st.audio_input('Record a short phrase like I am present, My name is Akash.')
            except Exception:
                st.error('Audio Data failed!')

            if st.button('Create Account', type='primary'):
                if new_name:
                    with st.spinner('Creating profile..'):
                        img = np.array(Image.open(photo_source))
                        encodings= get_face_embedding(img)
                        if encodings:
                            face_emb = encodings[0].tolist()

                            voice_emb = None
                            if audio_data:
                                voice_emb = get_voice_embedding(audio_data.read())

                            response_data = create_student(new_name, face_embedding=face_emb, voice_embedding=voice_emb)

                            if response_data:
                                train_classifier()
                                st.session_state.is_logged_in = True
                                st.session_state.user_role = 'student'
                                st.session_state.student_data = response_data[0]
                                st.toast(f'Profile Created! Hi {new_name}!')
                                time.sleep(1)
                                st.rerun()
                        else:
                            st.error('Couldnt capture your facial features for registration')

                else:
                    st.warning('Please enter your name!')
    footer_dashboard()
