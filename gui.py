import streamlit as st


st.title("<title goes here>")
dicom_file = st.file_uploader("Upload DICOM file here for analysis.")
dbutton = st.button("Click this button to fiew DICOM file.")

if dbutton == True:
    st.image(dicom_file)
    st.balloons()