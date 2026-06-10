import streamlit as st
def main():
        st.header("Attendy - AI-Powered Attendance Management System",width="content")
        name = st.text_input("Enter your name to mark attendance:")
        col1,col2=st.columns(2)
        # print(name)
        with col1:
             if st.button("Hi",type="primary",key="btn1",width="stretch"):
                        print("hi",name)
                        st.text("Hi "+name)
        with col2:
                if st.button("Bye",type="secondary",key="btn2",width="stretch"):
                        print("Bye",name)


        st.markdown("""
                <div style={}>Hello, I am from Attendy</div>

""",unsafe_allow_html=True)
main()