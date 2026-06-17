import streamlit as st

def footer_home():

    st.markdown(f"""
        <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; margin-top:8px">
            <p style='text-align:center; color:#E0E3FF'>Made with ❤️ by Shubham</p>
        </div>   
                
                """, unsafe_allow_html=True)
    

def footer_dashboard():

    st.markdown(f"""
        <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; margin-top:8px">
            <p style='text-align:center; color:#000000'>Made  by shubham</p>
        </div>   
                
                """, unsafe_allow_html=True)