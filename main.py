import streamlit as st
import os
from PIL import Image
import google.generativeai as genai
import speech_recognition as sr
from gtts import gTTS  # Import gTTS for text-to-speech
from dotenv import load_dotenv
from fpdf import FPDF
import tempfile

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Streamlit Page Configuration
st.set_page_config(page_title="AI Image & Speech Chatbot", layout="wide")

# Custom CSS Styling
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] {display: none;}
        .stApp { background-color: #FBFBFB !important; padding: 20px; }
        .title-container { text-align: center; margin-bottom: 30px;}
        .upload-container { text-align: center; margin-bottom: 40px; }
        .stButton>button { background-color: #1A2A50 !important; color:#E8F9FF !important; border-radius: 10px !important; padding: 12px 24px !important; font-size: 16px; }
        .stTextArea textarea { border-radius: 10px !important; border: 1px solid #C4D9FF !important; padding: 10px !important; }
        .center-button { display: flex; justify-content: center; margin-top: 30px; }
        .footer { background-color: #FBFBFB; color: black; padding: 10px; text-align: center; border-radius: 10px; margin-top: 40px; }
    </style>
    """,
    unsafe_allow_html=True
)
if st.button("💬 Just Chat"):
    st.switch_page("pages/qachat.py")


# Function to get Gemini AI response
def get_gemini_response(input_text, speech_text, image):
    model = genai.GenerativeModel('gemini-1.5-flash')
    combined_input = f"{input_text}\n{speech_text}" if speech_text else input_text
    if combined_input.strip():
        response = model.generate_content([combined_input, image] if image else [combined_input])
        return response.text
    return "Please provide some input."

# Function to Convert Text to Speech (TTS)
def text_to_speech(response_text):
    tts = gTTS(text=response_text, lang="en")
    audio_path = "response_audio.mp3"
    tts.save(audio_path)  # Save the audio file
    return audio_path

# Function to Generate PDF
def generate_pdf(input_text, speech_text, ai_response, image_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Add Title
    pdf.cell(200, 10, txt="Conversational Image Recognition Chatbot Report", ln=True, align="C")

    # Add Input Text
    pdf.cell(200, 10, txt="Input Text:", ln=True)
    pdf.multi_cell(0, 10, txt=input_text)

    # Add Recognized Speech
    pdf.cell(200, 10, txt="Recognized Speech:", ln=True)
    pdf.multi_cell(0, 10, txt=speech_text)

    # Add AI Response
    pdf.cell(200, 10, txt="AI Response:", ln=True)
    pdf.multi_cell(0, 10, txt=ai_response)

    # Add Image
    if image_path:
        image_width = 180  # Desired width of the image
        page_width = 210  # A4 page width in mm
        x_position = (page_width - image_width) / 2  # Center the image
        pdf.image(image_path, x=x_position, y=pdf.get_y(), w=image_width)

    # Save PDF
    pdf_path = "chatbot_report.pdf"
    pdf.output(pdf_path)
    return pdf_path

# Initialize session state for recognized speech and AI response
if "recognized_text" not in st.session_state:
    st.session_state["recognized_text"] = ""

if "ai_response" not in st.session_state:
    st.session_state["ai_response"] = ""

if "audio_file" not in st.session_state:
    st.session_state["audio_file"] = None

# Title
st.markdown("<h1 class='title-container'>   Enhancing AI Image Recognition Chatbot with PDF Generation and Download Capability</h1>", unsafe_allow_html=True)
st.markdown("<p class='title-container'>Upload an image, enter text or speak to interact with AI</p>",
            unsafe_allow_html=True)

# Image Upload Section
st.markdown("<div class='upload-container'><h2>📸 Upload an Image</h2></div>", unsafe_allow_html=True)
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"], key="image_uploader")

image = None
image_path = None  # Variable to store the temporary image path
if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_container_width=True, output_format="JPEG")

    # Save the uploaded image to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
        image.save(tmp_file, format="PNG")
        image_path = tmp_file.name  # Store the temporary file path

st.markdown("<br><br>", unsafe_allow_html=True)  # Add some space

# Layout with Two Columns
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📜 Enter Text")
    input_text = st.text_area("Type your input:", placeholder="Enter prompt here...", height=150)

with col2:
    st.subheader("🎤 Speak Input")

    # Recognized Speech Area
    st.text_area("Recognized Speech:", st.session_state["recognized_text"], height=100, disabled=True)

    # Speech Recognition Button
    if st.button("Start Speech Recognition", key="speech_button"):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            st.info("Listening...")
            try:
                audio = recognizer.listen(source)
                spoken_text = recognizer.recognize_google(audio)
                st.session_state["recognized_text"] = spoken_text  # Store in session state
                st.rerun()  # Refresh UI to update text area
            except sr.UnknownValueError:
                st.warning("Could not understand the audio.")
            except sr.RequestError:
                st.error("Speech recognition service error.")

# Combine inputs
final_text = input_text.strip() + "\n" + st.session_state["recognized_text"].strip()

# Centered "Generate Response" Button
st.markdown("<div class='center-button'>", unsafe_allow_html=True)
if st.button("🚀 Generate Response", key="generate_button"):
    if not final_text.strip():
        st.warning("Please enter text or speak before generating a response.")
    else:
        with st.spinner("Generating response..."):
            response = get_gemini_response(input_text, st.session_state["recognized_text"], image)
            st.session_state["ai_response"] = response  # Store response
            st.session_state["audio_file"] = text_to_speech(response)  # Convert to speech
        st.success("Response Generated!")
        st.write(response)
st.markdown("</div>", unsafe_allow_html=True)

# Play Audio Response
if st.session_state["audio_file"]:
    st.audio(st.session_state["audio_file"], format="audio/mp3")

# Generate and Download PDF
if st.session_state["ai_response"]:
    if st.button("📄 Generate and Download PDF"):
        pdf_path = generate_pdf(input_text, st.session_state["recognized_text"], st.session_state["ai_response"], image_path)
        with open(pdf_path, "rb") as pdf_file:
            st.download_button(
                label="Download PDF",
                data=pdf_file,
                file_name="chatbot_report.pdf",
                mime="application/pdf"
            )

        # Clean up the temporary image file after PDF generation
        if image_path and os.path.exists(image_path):
            os.remove(image_path)

# Footer Section
st.markdown(
    """
    <div class='footer'>
        <p><strong>College:</strong> D.B.I.T</p>
        <p><strong>Department:</strong> Artificial Intelligence & Data Science Department</p>
        <p><strong>Guide:</strong> Dr. Gowramma G S</p>
        <p>&copy; 2025 AI Image & Speech Chatbot. All rights reserved.</p>
    </div>
    """,
    unsafe_allow_html=True
)