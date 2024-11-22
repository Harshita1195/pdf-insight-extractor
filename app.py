import base64
import io
import os
import fitz
from PIL import Image
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import streamlit as st

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ensure OPENAI_API_KEY is loaded correctly
openai_api_key = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = openai_api_key

def pdf_to_base64_images(pdf_path: str):
    """
    Converts all pages of a PDF to base64-encoded images.

    Args:
        pdf_path (str): Path to the PDF file.

    Returns:
        dict: A dictionary where keys are page numbers (1-indexed) and values are base64-encoded images.
    """
    pdf_document = fitz.open(pdf_path)
    base64_images = {}

    for page_number in range(1, len(pdf_document) + 1):
        page = pdf_document.load_page(page_number - 1)  
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")

        base64_images[page_number] = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return base64_images


def query_model(base64_images: dict, query: str):
    """
    Sends a query and all base64-encoded images to the model.

    Args:
        base64_images (dict): Dictionary of base64-encoded images.
        query (str): Query text.

    Returns:
        str: Model's response.
    """
    llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
    
    # Combine all images into one content list for the model
    content = [{"type": "text", "text": query}]
    for page_number, base64_image in base64_images.items():
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
            }
        )

    message = HumanMessage(content=content)
    response = llm.invoke([message])
    return response.content


# Streamlit application
def main():

    st.set_page_config(
        page_title="PDF Insight Extractor" 
    )

    # Title and subtitle
    st.markdown(
        """
        <style>
        .main-title {
            font-size: 2.5rem;
            font-weight: bold;
            color: #4A90E2;
            text-align: center;
            margin-bottom: 10px;
        }
        .subtitle {
            font-size: 1.2rem;
            color: #333333;
            text-align: center;
            margin-bottom: 30px;
        }
        </style>
        <div class="main-title">PDF Insight Extractor</div>
        <div class="subtitle">Analyze PDFs to extract information from text, images, and tables with ease!</div>
        """,
        unsafe_allow_html=True,
    )

    # File uploader
    uploaded_file = st.file_uploader("📄 Upload your PDF file to get started:", type=["pdf"])

    if uploaded_file is not None:
        # Save the uploaded file to a temporary location
        with open("temp.pdf", "wb") as temp_pdf:
            temp_pdf.write(uploaded_file.getbuffer())

        st.success("✅ PDF uploaded successfully. Processing your document...")

        # Convert PDF pages to base64 images
        base64_images = pdf_to_base64_images("temp.pdf")
        st.success(f"📄 Processed {len(base64_images)} page(s). You can now ask questions!")

        # Highlight the capabilities
        st.info(
            """
            💡 This tool can extract insights from:
            - **Text**: Analyze and understand textual content.
            - **Images**: Extract context and meaning from visual data.
            - **Tables**: Retrieve structured information from tables.
            """
        )

        # User input for query
        st.markdown("---")
        query = st.text_input("💬 Enter your query:", placeholder="E.g., What data is presented in the table on page 2?")
        submit_button = st.button("🔍 Submit Query")

        # Spinner and response handling
        if submit_button and query:
            with st.spinner("⏳ Querying the model, please wait..."):
                response = query_model(base64_images, query)
            st.success("✅ Query processed successfully!")
            st.markdown(f"**🤖 Model's Response:**\n\n{response}")


if __name__ == "__main__":
    main()
