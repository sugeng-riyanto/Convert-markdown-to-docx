import streamlit as st
import sqlite3
import os
from docx import Document
from docx.shared import Pt, Inches
from bs4 import BeautifulSoup
import pypandoc
import pypandoc

# Download Pandoc if it's not already available
try:
    pypandoc.get_pandoc_version()
except OSError:
    pypandoc.download_pandoc()
    
# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('markdown_files.db', check_same_thread=False)
c = conn.cursor()

# Create table if it doesn't exist
c.execute('''
    CREATE TABLE IF NOT EXISTS markdown_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        content TEXT
    )
''')
conn.commit()

# Function to save Markdown file to the database
def save_to_database(filename, content):
    c.execute('''
        INSERT INTO markdown_files (filename, content)
        VALUES (?, ?)
    ''', (filename, content))
    conn.commit()

# Function to fetch all Markdown files from the database
def fetch_all_files():
    c.execute('SELECT id, filename FROM markdown_files')
    return c.fetchall()

# Function to fetch content of a specific Markdown file by ID
def fetch_file_content(file_id):
    c.execute('SELECT content FROM markdown_files WHERE id = ?', (file_id,))
    return c.fetchone()[0]

# Function to delete a Markdown file from the database
def delete_file_from_database(file_id):
    c.execute('DELETE FROM markdown_files WHERE id = ?', (file_id,))
    conn.commit()

# Function to convert Markdown to DOCX with proper formatting using Pandoc
import os
import pypandoc

def markdown_to_docx(md_content, output_filename):
    try:
        # Create a temporary file for Pandoc to write the DOCX output
        temp_file = "temp_output.docx"
        
        # Convert Markdown to DOCX using Pandoc
        output = pypandoc.convert_text(
            md_content,
            'docx',
            format='markdown+tex_math_dollars',  # Supports LaTeX-style equations
            outputfile=temp_file
        )
        
        # Check if the temporary file was created successfully
        if os.path.exists(temp_file):
            # Rename the temporary file to the desired output filename
            os.rename(temp_file, output_filename)
            return True
        else:
            st.error("Error: Temporary DOCX file was not created.")
            return False
    except Exception as e:
        st.error(f"Error converting Markdown to DOCX: {e}")
        return False
# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Upload Markdown", "View Markdown Files"])

# Upload Markdown Page
if page == "Upload Markdown":
    st.title("Upload Markdown File")
    # File uploader for Markdown file
    uploaded_file = st.file_uploader("Upload a Markdown file", type=["md"])
    if uploaded_file is not None:
        # Read the content of the uploaded Markdown file
        md_content = uploaded_file.read().decode("utf-8")
        # Display the Markdown content
        st.subheader("Uploaded Markdown Content:")
        st.text(md_content)
        # Save the Markdown content to the database
        if st.button("Save to Database"):
            save_to_database(uploaded_file.name, md_content)
            st.success(f"File '{uploaded_file.name}' saved to database!")

# View Markdown Files Page
elif page == "View Markdown Files":
    st.title("View Saved Markdown Files")
    # Fetch all saved Markdown files from the database
    files = fetch_all_files()
    if files:
        st.subheader("List of Saved Markdown Files:")
        # Dropdown to select a file for preview
        selected_file = st.selectbox("Select a Markdown file to preview", [filename for _, filename in files])
        # Get the selected file's ID and content
        selected_file_id = next(id for id, filename in files if filename == selected_file)
        selected_file_content = fetch_file_content(selected_file_id)
        # Show the full-page Markdown preview
        st.subheader(f"Preview: {selected_file}")
        st.markdown(selected_file_content, unsafe_allow_html=True)  # Render Markdown
        # Buttons for actions (Delete, Download as DOCX)
        col1, col2 = st.columns(2)
        with col1:
            # Button to delete the file
            if st.button(f"Delete {selected_file}", key=f"delete_{selected_file_id}"):
                delete_file_from_database(selected_file_id)
                st.experimental_rerun()  # Refresh the page after deletion
        with col2:
            # Button to download as DOCX
            if st.button(f"Download {selected_file} as DOCX", key=f"docx_{selected_file_id}"):
                docx_filename = f"{os.path.splitext(selected_file)[0]}.docx"
                success = markdown_to_docx(selected_file_content, docx_filename)
                if success:
                    with open(docx_filename, "rb") as docx_file:
                        st.download_button(
                            label=f"Download {selected_file} as DOCX",
                            data=docx_file,
                            file_name=docx_filename,
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                    # Clean up temporary DOCX file
                    os.remove(docx_filename)
    else:
        st.info("No Markdown files saved yet.")

# Close the database connection when the app is closed
conn.close()
