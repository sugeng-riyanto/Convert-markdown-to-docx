import streamlit as st
import sqlite3
import os
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
import markdown
from bs4 import BeautifulSoup

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

# Function to convert Markdown to DOCX with proper formatting
def markdown_to_docx(md_content, output_filename):
    doc = Document()
    
    # Convert Markdown to HTML
    html_content = markdown.markdown(md_content)
    
    # Parse HTML using BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    for element in soup:
        if element.name == 'h1':
            heading = doc.add_heading(level=1)
            run = heading.add_run(element.text)
            run.bold = True
            run.font.size = Pt(16)
        elif element.name == 'h2':
            heading = doc.add_heading(level=2)
            run = heading.add_run(element.text)
            run.bold = True
            run.font.size = Pt(14)
        elif element.name == 'h3':
            heading = doc.add_heading(level=3)
            run = heading.add_run(element.text)
            run.bold = True
            run.font.size = Pt(12)
        elif element.name == 'p':
            paragraph = doc.add_paragraph()
            run = paragraph.add_run(element.text)
            run.font.size = Pt(11)
        elif element.name == 'strong':
            paragraph = doc.add_paragraph()
            run = paragraph.add_run(element.text)
            run.bold = True
        elif element.name == 'em':
            paragraph = doc.add_paragraph()
            run = paragraph.add_run(element.text)
            run.italic = True
    
    # Save the DOCX file
    doc.save(output_filename)

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
        
        # Display each file with a download button
        for file_id, filename in files:
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.write(f"**{filename}**")
            
            with col2:
                # Button to delete the file
                if st.button(f"Delete {filename}", key=f"delete_{file_id}"):
                    delete_file_from_database(file_id)
                    st.experimental_rerun()  # Refresh the page after deletion
            
            with col3:
                # Button to view the content of the file
                if st.button(f"View {filename}", key=f"view_{file_id}"):
                    content = fetch_file_content(file_id)
                    st.text_area("Markdown Content:", content, height=300)
            
            # Button to download as DOCX
            if st.button(f"Download {filename} as DOCX", key=f"docx_{file_id}"):
                content = fetch_file_content(file_id)
                docx_filename = f"{os.path.splitext(filename)[0]}.docx"
                markdown_to_docx(content, docx_filename)
                
                with open(docx_filename, "rb") as docx_file:
                    st.download_button(
                        label=f"Download {filename} as DOCX",
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