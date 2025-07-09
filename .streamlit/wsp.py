
import fitz
import streamlit as st
from file_functions.submit_api import submit, file_upload,GetFile,fetch_pdf_by_name
from file_functions.prev_record import get_previous_record
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import pandas as pd


st.set_page_config(page_title="WSP File Uploader", layout="wide")

# ---- SESSION STATE ----
if "page" not in st.session_state:
    st.session_state.page = "front"
if "current_page" not in st.session_state:
    st.session_state.current_page = 1
if "df" not in st.session_state:
    st.session_state.df = None


st.sidebar.title("Navigation")
nav = st.sidebar.radio(
    "Click to go",
    options=["Main Page", "Upload","view"],
    index=["front", "upload","view"].index(st.session_state.page) if st.session_state.page in ["front", "upload","view"] else 0
)

if nav == "Main Page":
    st.session_state.page = "front"
elif nav == "Upload":
    st.session_state.page = "upload"
elif nav == "view":
    st.session_state.page = "view"

# ---- FRONT PAGE ----
if st.session_state.page == "front":
    
    st.image("/Users/blakechang/desktop/wsplogo.png", width=300)
    st.title("WSP File Uploader")
    st.markdown("---")
    st.subheader("Search Your Files")
    col1= st.columns(1)[0]
    with col1:
        user_name = st.text_input("Enter your full name here:",width= 300)
    # with col2:
    #     last_name = st.text_input("Last Name")
    if st.button("Search"):
        st.session_state.df = GetFile(user_name)
        st.session_state.last_search = user_name

    # Pull df out of session_state so it's available on every run:
    df = st.session_state.df

    if df is not None and not df.empty:
        # Build & render the grid on every rerun
        gb = GridOptionsBuilder.from_dataframe(df[["file_name"]])
        gb.configure_selection(selection_mode="single", use_checkbox=True)
        grid_opts = gb.build()

        grid_resp = AgGrid(
            df[["file_name"]],
            gridOptions=grid_opts,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            enable_enterprise_modules=False,
            fit_columns_on_grid_load=True,
        )

        # This now *will* fire as soon as you click a row
        selected = grid_resp["selected_rows"]
        # st.write("TYPE:", type(selected), "COLUMNS:", selected.columns.tolist())
        st.text("Please click if you can't find the file here:")
        st.button("Upload New File", on_click=lambda: setattr(st.session_state, 'page', 'upload'))
        if hasattr(selected, "iloc") and not selected.empty:
            
            first_row = selected.iloc[0]            # get the first row as a Series
            chosen = first_row["file_name"] 
            sel_df = fetch_pdf_by_name(user_name, chosen)
            
            st.session_state.pdf_name  = sel_df["file_name"].iloc[0]
            st.session_state.pdf_bytes = sel_df["file"].iloc[0]
            st.session_state.page = "view"
            st.rerun()
    # st.warning("No files found for this user.")
    else:
        st.text("Please click if you can't find the file here:")
        st.button("Upload New File", on_click=lambda: setattr(st.session_state, 'page', 'upload'))

       
    



# ---- PAGE 1: UPLOAD ----
if st.session_state.page == "upload":
    if st.button("Back to Main"):
            st.session_state.page = "front"
            st.rerun()
    st.header("Upload Files")
    uploaded = st.file_uploader("PDF File upload button", type=["pdf"])
    col1 = st.columns(1)[0]  # Get the first column for author input
    with col1:
        author = st.text_input("Uploader Name", placeholder="Enter your name here:")



    #TODO: upload the real file to destination which is the VM currently

    if uploaded and author:
        if "file_uploaded" not in st.session_state or st.session_state.pdf_name != uploaded.name:
            data = uploaded.read()
            #set all the PDF session state variables here for the 'view' page
            st.session_state.pdf_bytes = data
            st.session_state.pdf_name = uploaded.name
            file_upload(author, uploaded.name, data)
            st.session_state.file_uploaded = True
        if st.button("Next →"):
            st.session_state.page = "view"
            

# ---- PAGE 2: VIEW & ANNOTATE ----

elif st.session_state.page == "view":
    #TODO: scroll 
    st.header(f"Viewing: {st.session_state.pdf_name}")

    if st.button("Back to Main"):
            st.session_state.page = "front"
            st.rerun()

    # open with fitz
    pdf_doc = fitz.open(stream=st.session_state.pdf_bytes, filetype="pdf")
    total = pdf_doc.page_count
    cp = st.session_state.current_page

    # navigation
    n1, n2, n3 = st.columns([1,2,1])
    with n1:
        if st.button("◀️ Previous") and cp > 1:
            st.session_state.current_page -= 1
            st.rerun()
    with n2:
        st.markdown(f"#### Page {cp} / {total}")
    with n3:
        if st.button("Next ▶️") and cp < total:
            st.session_state.current_page += 1
            st.rerun()

    # render the current page to an image
    page = pdf_doc.load_page(cp - 1)
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2× zoom for readability
    img_data = pix.tobytes("png")

    checker = get_previous_record(st.session_state.pdf_name, st.session_state.current_page)
    if checker is not None:
        st.warning("Edited", width=90)
        

    # layout: viewer + description
    vc, dc,author = st.columns([3, 1,1])
    with vc:
        st.image(img_data, use_container_width=True)
    with dc:
        desc = st.text_area("Description for this page", height=500)
    with author:
        author_name = st.text_input("Author Name", placeholder="Enter author name:")
        if st.session_state.get("show_update_warning", False):
            st.markdown(f"**Previous Record:** {checker['description'].values[0]}")
            prev_author = checker['author'].values[0]
            st.markdown(f"**Author:** {prev_author}")
            if st.button("Update Record"):
                submit(st.session_state.pdf_name, prev_author, st.session_state.current_page, desc)
                st.success("✅ Updated and Saved!")
                st.session_state.show_update_warning = False  # Reset flag
        else:
            if st.button("Submit"):
                if checker is not None:
                    st.session_state.show_update_warning = True
                    st.rerun()
                else:
                    submit(st.session_state.pdf_name, author_name, st.session_state.current_page, desc)
                    st.success("✅ Saved!")

# ---- PAGE 3: HISTORY CHECK PAGE----
#TODO: A page for user to check the current completeness
#TODO: It shows: the uploaded files,  the completeness percentage


