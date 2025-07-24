
import fitz
import streamlit as st
from file_functions.submit_api import submit, file_upload,GetFile,fetch_pdf_by_name,latestPage
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

# ---- FRONT PAGE ----
if st.session_state.page == "front":
    
    st.image("logo.png", width=300) #put your own file path of the logo here 
    st.title("WSP File Uploader")
    st.markdown("---")
    st.subheader("Search Your Files")
    col1= st.columns(1)[0]
    with col1:
        user_name = st.text_input("Enter your full name here:",width= 300)
    # with col2:
    #     last_name = st.text_input("Last Name")
    if st.button("Search"):
        #TODO: fix GetFile to only read file_name and author at the tabl, otherwise it will takes 10 decades to load 
        st.session_state.df = GetFile(user_name)
        st.session_state.last_search = user_name

    # Pull df out of session_state so it's available on every run:
    df = st.session_state.df

    if df is not None and not df.empty:
        # Build & render the grid on every rerun

        st.text("Click the box of the file and wait for file loading")
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
            seleted_file = fetch_pdf_by_name(user_name, chosen)
            
            st.session_state.pdf_name  = seleted_file["file_name"].iloc[0]
            
            st.session_state.pdf_bytes = seleted_file["file"].iloc[0] # use a new api to get the file bytes instead of read entire table at first at line 33
            st.session_state.current_page = latestPage(user_name, chosen)
            st.session_state.page = "view"
            st.rerun()
    # st.warning("No files found for this user.")
    else:
        st.text("Please click if you can't find the file here:")
        st.button("Upload New File", on_click=lambda: setattr(st.session_state, 'page', 'upload'))


# ---- PAGE 1: UPLOAD ----
if st.session_state.page == "upload":

    if st.button("Back to Main"):
        keys_to_clear = [
        "page",
        "show_update_warning",
        "current_page",
        "pdf_name",
        "pdf_bytes",
        "df"
        ]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
    st.header("Upload Files")
    uploaded = st.file_uploader("PDF File upload button", type=["pdf"])
    col1 = st.columns(1)[0]  # Get the first column for author input
    with col1:
        author = st.text_input("Uploader Name", placeholder="Enter your name here:")

    if uploaded and author:
        if "file_uploaded" not in st.session_state or st.session_state.pdf_name != uploaded.name:
            data = uploaded.read()
            #set all the PDF session state variables here for the 'view' page
            st.session_state.pdf_bytes = data
            st.session_state.pdf_name = uploaded.name
            file_upload(author, uploaded.name, data) # upload the real file to MySQL source_file table
            st.session_state.file_uploaded = True
        if st.button("Next →"):
            st.session_state.page = "view"
            st.rerun()

# ---- PAGE 2: VIEW & ANNOTATE ----

elif st.session_state.page == "view":
    #TODO: scroll 
    st.header(f"Viewing: {st.session_state.pdf_name}")

    if st.button("Back to Main"):
        keys_to_clear = [
        "page",
        "show_update_warning",
        "current_page",
        "pdf_name",
        "pdf_bytes",
        "df"
        ]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    # open with fitz
    pdf_doc = fitz.open(stream=st.session_state.pdf_bytes, filetype="pdf")
    total = pdf_doc.page_count
    cp = int (st.session_state.current_page)


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

    # render the current page to an image(cp -1 because it's 0-indexed)
    page = pdf_doc.load_page(cp-1)
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
        # author_name = st.text_input("Author Name", placeholder="Enter author name:")
        author_name = st.text_area("Author Name", height=70)
        if st.session_state.get("show_update_warning", False):
            st.markdown(f"**Previous Record:** {checker['description'].values[0]}")
            prev_author = checker['author'].values[0]
            st.markdown(f"**Author:** {prev_author}")
            if st.button("Update Record"):
                if author_name: 
                    submit(st.session_state.pdf_name, author_name, st.session_state.current_page, desc)
                    st.success("✅ Updated and Saved!")
                    st.session_state.show_update_warning = False  # Reset flag
                else:
                    st.error("Please enter an author name to update the record.")
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


