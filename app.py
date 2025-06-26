import streamlit as st
import requests
from PyPDF2 import PdfReader, PdfWriter
from pypdf import PdfReader as PypdfReader, PdfWriter as PypdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from io import BytesIO
import fitz  # PyMuPDF
from reportlab.lib.colors import toColor
from reportlab.lib import colors
import base64
from datetime import datetime
import math
import json
import pyrebase
from streamlit_option_menu import option_menu
import time

# ================================
# FIREBASE AUTHENTICATION SETUP
# ================================
st.set_page_config(
    page_title="Smart PDF Tools", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)
# Firebase configuration - Replace with your Firebase config
firebase_config = {
    "apiKey": st.secrets["apiKey"],
    "authDomain": st.secrets["authDomain"],
    "projectId": st.secrets["projectId"],
    "storageBucket": st.secrets["storageBucket"],
    "messagingSenderId": st.secrets["messagingSenderId"],
    "appId": st.secrets["appId"],
    "measurementId": st.secrets["measurementId"],
    "databaseURL":st.secrets["databaseURL"]
}

# Initialize Firebase (only if not already initialized)
if 'firebase' not in st.session_state:
    firebase = pyrebase.initialize_app(firebase_config)
    st.session_state.firebase = firebase
    st.session_state.auth = firebase.auth()
    st.session_state.db = firebase.database()

# Authentication functions
def sign_up(email, password):
    try:
        user = st.session_state.auth.create_user_with_email_and_password(email, password)
        return user, None
    except Exception as e:
        return None, str(e)

def sign_in(email, password):
    try:
        user = st.session_state.auth.sign_in_with_email_and_password(email, password)
        return user, None
    except Exception as e:
        return None, str(e)

def reset_password(email):
    try:
        st.session_state.auth.send_password_reset_email(email)
        return True
    except:
        return False

def sign_out():
    st.session_state.user = None
    st.session_state.user_info = None

# Check authentication state
def check_auth():
    return 'user' in st.session_state and st.session_state.user is not None

def get_user_info():
    if check_auth():
        return st.session_state.get('user_info', {})
    return None

# ================================
# AUTHENTICATION UI
# ================================

def show_auth_page():
    # st.set_page_config(page_title="PDF Tools - Login", layout="centered", initial_sidebar_state="collapsed")
    
    # Custom CSS for auth page
    st.markdown("""
    <style>
    .auth-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        background: white;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .auth-title {
        text-align: center;
        color: #1f1f1f;
        margin-bottom: 2rem;
    }
    .stButton > button {
        width: 100%;
        margin-top: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<h1 class='auth-title'>📄 Smart PDF Tools</h1>", unsafe_allow_html=True)
    
    # Authentication tabs
    auth_tab = st.radio("", ["Sign In", "Sign Up", "Reset Password"], horizontal=True, label_visibility="collapsed")
    
    if auth_tab == "Sign In":
        with st.form("signin_form"):
            st.subheader("🔐 Sign In")
            email = st.text_input("Email", placeholder="Enter your email")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            if st.form_submit_button("Sign In", type="primary"):
                if email and password:
                    with st.spinner("Signing in..."):
                        user, error = sign_in(email, password)
                        if user:
                            st.session_state.user = user
                            st.session_state.user_info = {
                                'email': user['email'],
                                'uid': user['localId']
                            }
                            st.success("✅ Successfully signed in!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"❌ Sign in failed: {error}")
                else:
                    st.error("Please fill in all fields")
    
    elif auth_tab == "Sign Up":
        with st.form("signup_form"):
            st.subheader("👤 Create Account")
            email = st.text_input("Email", placeholder="Enter your email")
            password = st.text_input("Password", type="password", placeholder="Choose a password")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
            
            if st.form_submit_button("Create Account", type="primary"):
                if email and password and confirm_password:
                    if password == confirm_password:
                        if len(password) >= 6:
                            with st.spinner("Creating account..."):
                                user, error = sign_up(email, password)
                                if user:
                                    st.success("✅ Account created successfully! Please sign in.")
                                    time.sleep(2)
                                    st.rerun()
                                else:
                                    st.error(f"❌ Account creation failed: {error}")
                        else:
                            st.error("Password must be at least 6 characters long")
                    else:
                        st.error("Passwords don't match")
                else:
                    st.error("Please fill in all fields")
    
    else:  # Reset Password
        with st.form("reset_form"):
            st.subheader("🔄 Reset Password")
            email = st.text_input("Email", placeholder="Enter your email")
            
            if st.form_submit_button("Send Reset Email", type="primary"):
                if email:
                    with st.spinner("Sending reset email..."):
                        if reset_password(email):
                            st.success("✅ Password reset email sent! Check your inbox.")
                        else:
                            st.error("❌ Failed to send reset email. Please check your email address.")
                else:
                    st.error("Please enter your email address")

# ================================
# MAIN APP (Your existing PDF tools code)
# ================================

# [All your existing font styles, templates, and PDF processing functions remain the same]
# st.set_page_config(page_title="Enhanced PDF Tools", layout="wide")
def main_app():

    st.title("📄 Smart PDF Tool")

    # ---------- Font Styles Dictionary ----------
    FONT_STYLES = {
        "Helvetica": "Helvetica",
        "Helvetica Bold": "Helvetica-Bold",
        "Helvetica Italic": "Helvetica-Oblique",
        "Helvetica Bold Italic": "Helvetica-BoldOblique",
        "Times Roman": "Times-Roman",
        "Times Bold": "Times-Bold",
        "Times Italic": "Times-Italic",
        "Times Bold Italic": "Times-BoldItalic",
        "Courier": "Courier",
        "Courier Bold": "Courier-Bold",
        "Courier Italic": "Courier-Oblique",
        "Courier Bold Italic": "Courier-BoldOblique",
        "Arial": "Helvetica",  # Fallback to Helvetica
        "Georgia": "Times-Roman",  # Fallback to Times
        "Verdana": "Helvetica",  # Fallback to Helvetica
    }

    # ---------- Header/Footer Templates ----------
    HEADER_TEMPLATES = {
        "Custom": "",
        "Date": f"Date: {datetime.now().strftime('%B %d, %Y')}",
        "Confidential": "CONFIDENTIAL - Internal Use Only"
    }

    FOOTER_TEMPLATES = {
        "Custom": "",
        "Page Numbers": "{page}",
        "Date & Page": f"{datetime.now().strftime('%m/%d/%Y')} - {{page}}",
        "Disclaimer": "This document contains confidential information",
    }

    # ---------- Watermark Positions ----------
    WATERMARK_POSITIONS = {
        "Center": "center",
        "Top Left": "top_left",
        "Top Right": "top_right",
        "Bottom Left": "bottom_left",
        "Bottom Right": "bottom_right",
        "Diagonal": "diagonal"
    }

    # ---------- Combine PDFs ----------
    def combine_pdfs(uploaded_files):
        writer = PypdfWriter()
        for uploaded_file in uploaded_files:
            reader = PypdfReader(uploaded_file)
            for page in reader.pages:
                writer.add_page(page)
        output = BytesIO()
        writer.write(output)
        output.seek(0)
        return output

    # ---------- Create Overlay ----------
    def create_page_number_overlay(page_num, total_pages, mediabox):
        width = float(mediabox.right) - float(mediabox.left)
        height = float(mediabox.top) - float(mediabox.bottom)

        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=(width, height))
        can.setFont("Helvetica", 10)
        can.drawCentredString(width / 2, 0.5 * inch, f"Page {page_num} of {total_pages}")
        can.save()
        packet.seek(0)
        return PdfReader(packet).pages[0]

    # ---------- Add Page Numbers ----------
    def add_page_numbers_to_pdf(uploaded_pdf):
        reader = PdfReader(uploaded_pdf)
        writer = PdfWriter()
        total_pages = len(reader.pages)
        for i, page in enumerate(reader.pages, start=1):
            overlay = create_page_number_overlay(i, total_pages, page.mediabox)
            page.merge_page(overlay)
            writer.add_page(page)
        output = BytesIO()
        writer.write(output)
        output.seek(0)
        return output

    # ---------- Compress PDF ----------
    def compress_pdf_with_quality(uploaded_pdf, quality):
        original_data = uploaded_pdf.read()
        doc = fitz.open(stream=original_data, filetype="pdf")

        zoom_factor = quality / 100  # Scale images based on quality

        for page in doc:
            images = page.get_images(full=True)
            for img in images:
                xref = img[0]
                pix = fitz.Pixmap(doc, xref)
                if pix.n > 4:  # CMYK
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                new_pix = fitz.Pixmap(pix, 0)
                new_width = int(pix.width * zoom_factor)
                new_height = int(pix.height * zoom_factor)
                scaled_pix = fitz.Pixmap(pix, 0).scaled(new_width, new_height)
                page.clean_contents()
                page.insert_image(page.rect, pixmap=scaled_pix, overlay=True)

        output = BytesIO()
        doc.save(output, garbage=4, deflate=True)
        output.seek(0)

        return output, len(original_data), len(output.getbuffer())

    # ---------- Google Drive Helper ----------
    def download_from_drive(drive_link):
        if "drive.google.com" not in drive_link:
            return None, "❌ Not a valid Google Drive link."
        try:
            if "uc?id=" in drive_link:
                file_id = drive_link.split("uc?id=")[1].split("&")[0]
            elif "file/d/" in drive_link:
                file_id = drive_link.split("file/d/")[1].split("/")[0]
            else:
                return None, "❌ Could not extract file ID from link."
            url = f"https://drive.google.com/uc?export=download&id={file_id}"
            response = requests.get(url)
            if response.status_code != 200:
                return None, "❌ Failed to download file from Google Drive."
            return BytesIO(response.content), None
        except Exception as e:
            return None, f"❌ Error: {str(e)}"

    # ---------- Enhanced Text Styling ----------
    def apply_text_decorations(can, x, y, text, font_name, font_size, underline=False, strikethrough=False):
        """Apply underline and strikethrough decorations"""
        text_width = can.stringWidth(text, font_name, font_size)
        
        if underline:
            can.line(x, y-2, x + text_width, y-2)
        
        if strikethrough:
            can.line(x, y + font_size/3, x + text_width, y + font_size/3)

    def get_aligned_x(align, text, canvas_obj, page_width, font_size, font_name):
        text_width = canvas_obj.stringWidth(text, font_name, font_size)
        if align == 'Left':
            return 0.5 * inch
        elif align == 'Center':
            return (page_width - text_width) / 2
        elif align == 'Right':
            return page_width - text_width - 0.5 * inch
        elif align == 'Justify':
            return 0.5 * inch  # For justify, we'll use left alignment
        return (page_width - text_width) / 2  # default center

    # ---------- Create Watermark Overlay ----------
    def create_watermark_overlay(width, height, watermark_text, font_name, font_size, 
                            opacity, color, position, rotation=0):
        """Create a watermark overlay for a PDF page"""
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=(width, height))
        
        # Set font and color with opacity
        can.setFont(font_name, font_size)
        
        # Convert hex color to RGB and apply opacity
        if color.startswith('#'):
            color = color[1:]
        r = int(color[0:2], 16) / 255.0
        g = int(color[2:4], 16) / 255.0
        b = int(color[4:6], 16) / 255.0
        can.setFillColorRGB(r, g, b, alpha=opacity)
        
        # Calculate text dimensions
        text_width = can.stringWidth(watermark_text, font_name, font_size)
        
        # Determine position
        if position == "center":
            x = (width - text_width) / 2
            y = height / 2
        elif position == "top_left":
            x = 50
            y = height - 50
        elif position == "top_right":
            x = width - text_width - 50
            y = height - 50
        elif position == "bottom_left":
            x = 50
            y = 50
        elif position == "bottom_right":
            x = width - text_width - 50
            y = 50
        elif position == "diagonal":
            x = width / 4
            y = height / 4
            rotation = 45
        else:
            x = (width - text_width) / 2
            y = height / 2
        
        # Apply rotation if needed
        if rotation != 0:
            can.saveState()
            can.translate(x + text_width/2, y + font_size/2)
            can.rotate(rotation)
            can.drawString(-text_width/2, -font_size/4, watermark_text)
            can.restoreState()
        else:
            can.drawString(x, y, watermark_text)
        
        can.save()
        packet.seek(0)
        return PdfReader(packet).pages[0]

    # ---------- Add Watermark to PDF ----------
    def add_watermark_to_pdf(uploaded_pdf, watermark_text, font_name, font_size, 
                            opacity, color, position, rotation, page_range="all"):
        """Add watermark to specified pages of PDF"""
        reader = PdfReader(uploaded_pdf)
        writer = PdfWriter()
        total_pages = len(reader.pages)
        
        # Parse page range
        if page_range == "all":
            pages_to_watermark = list(range(total_pages))
        else:
            pages_to_watermark = []
            for part in page_range.split(','):
                if '-' in part:
                    start, end = map(int, part.split('-'))
                    pages_to_watermark.extend(range(start-1, min(end, total_pages)))
                else:
                    page_num = int(part) - 1
                    if 0 <= page_num < total_pages:
                        pages_to_watermark.append(page_num)
        
        for i, page in enumerate(reader.pages):
            if i in pages_to_watermark:
                mediabox = page.mediabox
                width = float(mediabox.right) - float(mediabox.left)
                height = float(mediabox.top) - float(mediabox.bottom)
                
                watermark_overlay = create_watermark_overlay(
                    width, height, watermark_text, font_name, font_size,
                    opacity, color, position, rotation
                )
                page.merge_page(watermark_overlay)
            
            writer.add_page(page)
        
        output = BytesIO()
        writer.write(output)
        output.seek(0)
        return output

    # ---------- Page-Specific Header/Footer Functions ----------
    def create_page_specific_overlay(width, height, page_num, total_pages, page_configs):
        """Create overlay with page-specific header/footer configuration"""
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=(width, height))
        
        # Find the most specific configuration for this page
        config = None
        for page_config in page_configs:
            if page_config['page_range'] == 'all' or page_num in parse_page_range(page_config['page_range'], total_pages):
                config = page_config
        
        if not config:
            can.save()
            packet.seek(0)
            return PdfReader(packet).pages[0]
        
        # Process header
        if config['position'] in ['Header', 'Both'] and config['header_text']:
            processed_header = config['header_text'].replace('{page}', str(page_num)).replace('{total}', str(total_pages))
            
            can.setFont(config['header_font_name'], config['header_font_size'])
            can.setFillColor(toColor(config['header_font_color']))
            
            y = height - 0.5 * inch
            x = get_aligned_x(config['header_align'], processed_header, can, width, 
                            config['header_font_size'], config['header_font_name'])
            can.drawString(x, y, processed_header)
            
            apply_text_decorations(can, x, y, processed_header, config['header_font_name'], 
                                config['header_font_size'], config['header_underline'], 
                                config['header_strikethrough'])

        # Process footer
        if config['position'] in ['Footer', 'Both'] and config['footer_text']:
            processed_footer = config['footer_text'].replace('{page}', str(page_num)).replace('{total}', str(total_pages))
            
            can.setFont(config['footer_font_name'], config['footer_font_size'])
            can.setFillColor(toColor(config['footer_font_color']))
            
            y = 0.5 * inch
            x = get_aligned_x(config['footer_align'], processed_footer, can, width, 
                            config['footer_font_size'], config['footer_font_name'])
            can.drawString(x, y, processed_footer)
            
            apply_text_decorations(can, x, y, processed_footer, config['footer_font_name'], 
                                config['footer_font_size'], config['footer_underline'], 
                                config['footer_strikethrough'])

        can.save()
        packet.seek(0)
        return PdfReader(packet).pages[0]

    def parse_page_range(page_range, total_pages):
        """Parse page range string and return list of page numbers"""
        if page_range == "all":
            return list(range(1, total_pages + 1))
        
        pages = []
        for part in page_range.split(','):
            part = part.strip()
            if '-' in part:
                start, end = map(int, part.split('-'))
                pages.extend(range(start, min(end + 1, total_pages + 1)))
            else:
                page_num = int(part)
                if 1 <= page_num <= total_pages:
                    pages.append(page_num)
        
        return list(set(pages))  # Remove duplicates


    # ---------- Enhanced overlay creation (keeping original function) ----------
    def create_enhanced_overlay(width, height, header_text, footer_text,
                            header_align, footer_align, header_font_size, footer_font_size, 
                            header_font_name, footer_font_name, header_font_color, footer_font_color,
                            position, header_underline=False, footer_underline=False,
                            header_strikethrough=False, footer_strikethrough=False,
                            page_num=1, total_pages=1):

        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=(width, height))

        # Process header
        if position in ['Header', 'Both'] and header_text:
            processed_header = header_text.replace('{page}', str(page_num)).replace('{total}', str(total_pages))
            
            can.setFont(header_font_name, header_font_size)
            can.setFillColor(toColor(header_font_color))
            
            y = height - 0.5 * inch
            x = get_aligned_x(header_align, processed_header, can, width, header_font_size, header_font_name)
            can.drawString(x, y, processed_header)
            
            apply_text_decorations(can, x, y, processed_header, header_font_name, header_font_size, 
                                header_underline, header_strikethrough)

        # Process footer
        if position in ['Footer', 'Both'] and footer_text:
            processed_footer = footer_text.replace('{page}', str(page_num)).replace('{total}', str(total_pages))
            
            can.setFont(footer_font_name, footer_font_size)
            can.setFillColor(toColor(footer_font_color))
            
            y = 0.5 * inch
            x = get_aligned_x(footer_align, processed_footer, can, width, footer_font_size, footer_font_name)
            can.drawString(x, y, processed_footer)
            
            apply_text_decorations(can, x, y, processed_footer, footer_font_name, footer_font_size, 
                                footer_underline, footer_strikethrough)

        can.save()
        packet.seek(0)
        return PdfReader(packet).pages[0]

    def add_enhanced_header_footer(uploaded_pdf, header_text, footer_text,
                                header_align, footer_align, header_font_size, footer_font_size,
                                header_font_name, footer_font_name, header_font_color, footer_font_color,
                                position, header_underline=False, footer_underline=False,
                                header_strikethrough=False, footer_strikethrough=False):

        reader = PdfReader(uploaded_pdf)
        writer = PdfWriter()
        total_pages = len(reader.pages)

        for i, page in enumerate(reader.pages, start=1):
            mediabox = page.mediabox
            width = float(mediabox.right) - float(mediabox.left)
            height = float(mediabox.top) - float(mediabox.bottom)

            overlay = create_enhanced_overlay(
                width, height, header_text, footer_text,
                header_align, footer_align, header_font_size, footer_font_size,
                header_font_name, footer_font_name, header_font_color, footer_font_color,
                position, header_underline, footer_underline,
                header_strikethrough, footer_strikethrough, i, total_pages
            )
            page.merge_page(overlay)
            writer.add_page(page)

        output = BytesIO()
        writer.write(output)
        output.seek(0)
        return output

    def create_preview_pdf(header_text, footer_text, header_align, footer_align, 
                        header_font_size, footer_font_size, header_font_name, footer_font_name,
                        header_font_color, footer_font_color, position, 
                        header_underline=False, footer_underline=False,
                        header_strikethrough=False, footer_strikethrough=False):
        """Create a preview PDF to show how the header/footer will look"""
        
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=(612, 792))  # Standard letter size
        
        # Add some sample content
        can.setFont("Helvetica", 12)
        can.setFillColor(colors.black)
        can.drawString(100, 400, "This is a preview of your PDF with custom header/footer.")
        can.drawString(100, 370, "The actual content of your PDF will appear here.")
        can.drawString(100, 340, "You can see how your header and footer will look.")
        
        # Add header/footer using the same logic
        if position in ['Header', 'Both'] and header_text:
            processed_header = header_text.replace('{page}', '1').replace('{total}', '1')
            can.setFont(header_font_name, header_font_size)
            can.setFillColor(toColor(header_font_color))
            y = 792 - 0.5 * inch
            x = get_aligned_x(header_align, processed_header, can, 612, header_font_size, header_font_name)
            can.drawString(x, y, processed_header)
            apply_text_decorations(can, x, y, processed_header, header_font_name, header_font_size, 
                                header_underline, header_strikethrough)

        if position in ['Footer', 'Both'] and footer_text:
            processed_footer = footer_text.replace('{page}', '1').replace('{total}', '1')
            can.setFont(footer_font_name, footer_font_size)
            can.setFillColor(toColor(footer_font_color))
            y = 0.5 * inch
            x = get_aligned_x(footer_align, processed_footer, can, 612, footer_font_size, footer_font_name)
            can.drawString(x, y, processed_footer)
            apply_text_decorations(can, x, y, processed_footer, footer_font_name, footer_font_size, 
                                footer_underline, footer_strikethrough)
        
        can.save()
        packet.seek(0)
        return packet

    # ---------- Streamlit UI Tabs ----------
    tab1, tab2, tab3, tab4, tab5= st.tabs([
        "🔗 Combine PDFs", "🔢 Add Page Numbers", "🗜️ Compress PDF", 
        "📝 Header/Footer", "💧 Watermark"
    ])

    # --------- Combine PDFs Tab ---------
    with tab1:
        st.subheader("📎 Upload or Drag & Drop multiple PDFs to combine them")
        uploaded_files = st.file_uploader("Choose PDF files", type="pdf", accept_multiple_files=True)
        drive_links = st.text_area("Paste Google Drive links (one per line)", height=100)
        drive_pdfs = []

        if drive_links.strip():
            st.info("Downloading from Google Drive...")
            for line in drive_links.strip().splitlines():
                file, error = download_from_drive(line.strip())
                if file:
                    drive_pdfs.append(file)
                else:
                    st.error(error)

        all_pdfs = uploaded_files + drive_pdfs
        if all_pdfs and st.button("🔗 Combine PDFs"):
            with st.spinner("Combining..."):
                combined_pdf = combine_pdfs(all_pdfs)
                st.success("✅ Combined PDF ready!")
                st.download_button("⬇️ Download Combined PDF", combined_pdf, file_name="combined_output.pdf", mime="application/pdf")

    # --------- Add Page Numbers Tab ---------
    with tab2:
        st.subheader("🔢 Add page numbers to your PDF")
        uploaded_file = st.file_uploader("Choose a PDF", type="pdf", key="number_pdf")
        drive_link_numbering = st.text_input("Or paste a Google Drive link for numbering:")
        pdf_to_number = uploaded_file

        if not uploaded_file and drive_link_numbering:
            file, error = download_from_drive(drive_link_numbering)
            if error:
                st.error(error)
            else:
                pdf_to_number = file

        if pdf_to_number and st.button("➕ Add Page Numbers"):
            with st.spinner("Adding page numbers..."):
                numbered_pdf = add_page_numbers_to_pdf(pdf_to_number)
                st.success("✅ Page numbers added!")
                st.download_button("⬇️ Download Numbered PDF", numbered_pdf, file_name="numbered_output.pdf", mime="application/pdf")

    # --------- Compress PDF Tab ---------
    with tab3:
        st.subheader("🗜️ Compress your PDF to reduce file size")
        uploaded_compress_file = st.file_uploader("Upload PDF to compress", type="pdf", key="compress_pdf")
        compression_quality = st.slider("Select Compression Quality", min_value=10, max_value=100, value=70,
                                        help="Lower value = more compression, smaller size but lower image quality")

        if uploaded_compress_file and st.button("🗜️ Compress PDF"):
            with st.spinner("Compressing..."):
                compressed_pdf, original_size, compressed_size = compress_pdf_with_quality(uploaded_compress_file, compression_quality)
                st.success(f"✅ Compression completed!")

                col1, col2 = st.columns(2)
                col1.metric("Original Size", f"{original_size / 1024:.2f} KB")
                col2.metric("Compressed Size", f"{compressed_size / 1024:.2f} KB")

                st.download_button("⬇️ Download Compressed PDF", compressed_pdf,
                                file_name="compressed_output.pdf", mime="application/pdf")

    # --------- Enhanced Header/Footer Tab ---------
    with tab4:
        st.subheader("📝 Add Custom Header and/or Footer to your PDF")
        
        col_left, col_right = st.columns([1, 1])
        
        with col_left:
            uploaded_file = st.file_uploader("Upload your PDF", type="pdf", key="hf_pdf")
            
            st.markdown("### ✍️ Content Templates")
            
            # Header template selection
            header_template = st.selectbox("Header Template", list(HEADER_TEMPLATES.keys()))
            if header_template != "Custom":
                header_text = HEADER_TEMPLATES[header_template]
            else:
                header_text = st.text_input("Custom Header Text", "")
            
            # Footer template selection
            footer_template = st.selectbox("Footer Template", list(FOOTER_TEMPLATES.keys()))
            if footer_template != "Custom":
                footer_text = FOOTER_TEMPLATES[footer_template]
            else:
                footer_text = st.text_input("Custom Footer Text", "")
            
            st.info("💡 Use {page} and {total} as placeholders for page numbers")
            
            st.markdown("### 🎯 Positioning")
            position = st.radio("Apply To", ["Header", "Footer", "Both"], horizontal=True)
            
            # Alignment options
            col_align1, col_align2 = st.columns(2)
            with col_align1:
                header_align = st.selectbox("Header Alignment", ["Left", "Center", "Right", "Justify"])
            with col_align2:
                footer_align = st.selectbox("Footer Alignment", ["Left", "Center", "Right", "Justify"])
        
        with col_right:
            st.markdown("### 🎨 Header Styling")
            col_h1, col_h2 = st.columns(2)
            with col_h1:
                header_font_size = st.slider("Header Font Size", min_value=6, max_value=36, value=12)
                header_font_color = st.color_picker("Header Color", "#000000")
            with col_h2:
                header_font_name = st.selectbox("Header Font", list(FONT_STYLES.keys()))
                header_font_mapped = FONT_STYLES[header_font_name]
            
            col_h3, col_h4 = st.columns(2)
            with col_h3:
                header_underline = st.checkbox("Header Underline")
            with col_h4:
                header_strikethrough = st.checkbox("Header Strikethrough")
            
            st.markdown("### 🎨 Footer Styling")
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                footer_font_size = st.slider("Footer Font Size", min_value=6, max_value=36, value=10)
                footer_font_color = st.color_picker("Footer Color", "#666666")
            with col_f2:
                footer_font_name = st.selectbox("Footer Font", list(FONT_STYLES.keys()))
                footer_font_mapped = FONT_STYLES[footer_font_name]
            
            col_f3, col_f4 = st.columns(2)
            with col_f3:
                footer_underline = st.checkbox("Footer Underline")
            with col_f4:
                footer_strikethrough = st.checkbox("Footer Strikethrough")
        
        # Live Preview (keeping original preview code)
        st.markdown("### 👁️ Live Preview")
        if header_text or footer_text:
            try:
                preview_pdf = create_preview_pdf(
                    header_text, footer_text, header_align, footer_align,
                    header_font_size, footer_font_size, header_font_mapped, footer_font_mapped,
                    header_font_color, footer_font_color, position,
                    header_underline, footer_underline, header_strikethrough, footer_strikethrough
                )
                
                # Convert to base64 for display
                pdf_bytes = preview_pdf.getvalue()
                base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
                
                # Display PDF preview
                pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="400" type="application/pdf"></iframe>'
                st.markdown(pdf_display, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Preview error: {str(e)}")
        
        # HTML Preview as fallback
        st.markdown("### 📋 Style Preview")
        preview_header = header_text.replace('{page}', '1').replace('{total}', '10') if header_text else ''
        preview_footer = footer_text.replace('{page}', '1').replace('{total}', '10') if footer_text else ''
        
        header_style = f"""
            text-align: {header_align.lower()}; 
            color: {header_font_color}; 
            font-size: {header_font_size}px;
            {'text-decoration: underline;' if header_underline else ''}
            {'text-decoration: line-through;' if header_strikethrough else ''}
            font-weight: {'bold' if 'Bold' in header_font_name else 'normal'};
            font-style: {'italic' if 'Italic' in header_font_name else 'normal'};
        """
        
        footer_style = f"""
            text-align: {footer_align.lower()}; 
            color: {footer_font_color}; 
            font-size: {footer_font_size}px;
            {'text-decoration: underline;' if footer_underline else ''}
            {'text-decoration: line-through;' if footer_strikethrough else ''}
            font-weight: {'bold' if 'Bold' in footer_font_name else 'normal'};
            font-style: {'italic' if 'Italic' in footer_font_name else 'normal'};
        """
        
        st.markdown(f"""
        <div style="border: 2px solid #ddd; padding: 20px; margin: 10px 0; background: white; min-height: 300px; position: relative;">
            <div style="{header_style} position: absolute; top: 10px; left: 10px; right: 10px;">
                {preview_header if position in ['Header', 'Both'] else ''}
            </div>
            
            <div style="padding: 50px 20px; text-align: center; color: #888;">
                <p>Your PDF content will appear here</p>
                <p>This shows how your header and footer will look</p>
            </div>
            
            <div style="{footer_style} position: absolute; bottom: 10px; left: 10px; right: 10px;">
                {preview_footer if position in ['Footer', 'Both'] else ''}
            </div>
        </div>
        """, unsafe_allow_html=True)

        if uploaded_file and st.button("📝 Apply Header/Footer"):
            with st.spinner("Applying custom header/footer to PDF..."):
                result = add_enhanced_header_footer(
                    uploaded_file, header_text, footer_text,
                    header_align, footer_align, header_font_size, footer_font_size,
                    header_font_mapped, footer_font_mapped, header_font_color, footer_font_color,
                    position, header_underline, footer_underline, header_strikethrough, footer_strikethrough
                )
                st.success("✅ Header/Footer applied successfully!")
                st.download_button("⬇️ Download Updated PDF", result,
                                file_name="header_footer_output.pdf", mime="application/pdf")

    # --------- Watermark Tab ---------
    with tab5:
        st.subheader("💧 Add Watermark to your PDF")
        
        col_wm_left, col_wm_right = st.columns([1, 1])
        
        with col_wm_left:
            uploaded_file_wm = st.file_uploader("Upload your PDF", type="pdf", key="wm_pdf")
            
            if uploaded_file_wm:
                reader = PdfReader(uploaded_file_wm)
                total_pages_wm = len(reader.pages)
                st.info(f"📄 Your PDF has {total_pages_wm} pages")
            
            st.markdown("### 💧 Watermark Content")
            watermark_text = st.text_input("Watermark Text", placeholder="e.g., CONFIDENTIAL, DRAFT, Company Name")
            
            st.markdown("### 📍 Positioning & Pages")
            watermark_position = st.selectbox("Watermark Position", list(WATERMARK_POSITIONS.keys()))
            watermark_rotation = st.slider("Rotation (degrees)", min_value=-90, max_value=90, value=0, 
                                        help="Positive values rotate clockwise")
            
            page_range_wm = st.text_input("Page Range", placeholder="e.g., 1-3, 5, 7-10 or 'all'", value="all",
                                        help="Enter page numbers (1-based). Examples: '1-3,5,7-10' or 'all' for all pages")
        
        with col_wm_right:
            st.markdown("### 🎨 Watermark Styling")
            
            col_wm1, col_wm2 = st.columns(2)
            with col_wm1:
                watermark_font_size = st.slider("Font Size", min_value=12, max_value=72, value=36)
                watermark_font_name = st.selectbox("Font", list(FONT_STYLES.keys()), key="wm_font")
                watermark_font_mapped = FONT_STYLES[watermark_font_name]
            
            with col_wm2:
                watermark_opacity = st.slider("Opacity", min_value=0.1, max_value=1.0, value=0.3, step=0.1,
                                            help="Lower values make watermark more transparent")
                watermark_color = st.color_picker("Color", "#CCCCCC")
            
            st.markdown("### 👁️ Watermark Preview")
            if watermark_text:
                preview_style = f"""
                    font-size: {watermark_font_size}px;
                    color: {watermark_color};
                    opacity: {watermark_opacity};
                    font-weight: {'bold' if 'Bold' in watermark_font_name else 'normal'};
                    font-style: {'italic' if 'Italic' in watermark_font_name else 'normal'};
                    transform: rotate({watermark_rotation}deg);
                    display: inline-block;
                """
                
                position_style = {
                    "center": "text-align: center; margin-top: 50px;",
                    "top_left": "text-align: left; margin-top: 10px;",
                    "top_right": "text-align: right; margin-top: 10px;",
                    "bottom_left": "text-align: left; margin-top: 90px;",
                    "bottom_right": "text-align: right; margin-top: 90px;",
                    "diagonal": "text-align: center; margin-top: 50px;"
                }
                
                st.markdown(f"""
                <div style="border: 2px solid #ddd; padding: 20px; margin: 10px 0; background: white; height: 200px; position: relative; overflow: hidden;">
                    <div style="{position_style.get(WATERMARK_POSITIONS[watermark_position], position_style['center'])}">
                        <span style="{preview_style}">{watermark_text}</span>
                    </div>
                    <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: #ddd; font-size: 14px;">
                        PDF content area
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        if uploaded_file_wm and watermark_text and st.button("💧 Apply Watermark", type="primary"):
            with st.spinner("Applying watermark to PDF..."):
                try:
                    result = add_watermark_to_pdf(
                        uploaded_file_wm, watermark_text, watermark_font_mapped, watermark_font_size,
                        watermark_opacity, watermark_color, WATERMARK_POSITIONS[watermark_position],
                        watermark_rotation, page_range_wm
                    )
                    st.success("✅ Watermark applied successfully!")
                    st.download_button("⬇️ Download Watermarked PDF", result,
                                    file_name="watermarked_output.pdf", mime="application/pdf")
                except Exception as e:
                    st.error(f"Error applying watermark: {str(e)}")
        
        # Watermark Tips
        st.markdown("""
        ### 💡 Watermark Tips
        - **Opacity**: Use 0.1-0.3 for subtle watermarks, 0.4-0.7 for visible but not intrusive
        - **Position**: 'Diagonal' works well for 'CONFIDENTIAL' or 'DRAFT' watermarks
        - **Font Size**: 36-48 typically works well for most documents
        - **Color**: Light gray (#CCCCCC) or light blue (#CCE5FF) are common choices
        - **Page Range**: Use specific ranges like '1,3-5' to watermark only certain pages
        """)

    # --------- Footer Information ---------
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**🔗 Combine Multiple PDFs**")
        st.caption("Upload multiple PDFs or provide Google Drive links to merge them into one document")

    with col2:
        st.markdown("**🎯 Page-Specific Formatting**")
        st.caption("Apply different headers/footers to specific page ranges with custom styling options")

    with col3:
        st.markdown("**💧 Professional Watermarks**")
        st.caption("Add translucent watermarks with custom positioning, rotation, and styling")

    st.markdown("**Built with Streamlit • Enhanced PDF Processing Tools**")

# ================================
# MAIN APPLICATION ENTRY POINT
# ================================

def main():
    try:
        # Initialize session state
        if 'user' not in st.session_state:
            st.session_state.user = None
        
        # Show appropriate page based on authentication
        if check_auth():
            main_app()
        else:
            show_auth_page()
            
    except Exception as e:
        st.error(f"Application Error: {str(e)}")
        st.info("Please refresh the page and try again.")
        
        # Show a basic version without auth as fallback
        st.markdown("---")
        st.subheader("Basic PDF Tools (No Authentication)")
        uploaded_file = st.file_uploader("Upload a PDF for basic processing", type="pdf")
        if uploaded_file:
            st.success("File uploaded successfully!")
            st.info("Basic PDF tools would work here")

if __name__ == "__main__":
    main()