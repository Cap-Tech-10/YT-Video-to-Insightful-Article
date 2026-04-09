import re
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled
from fpdf import FPDF
import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# ✅ Use stable model (works across versions)
model = genai.GenerativeModel("gemini-flash-latest")


# 🎯 Extract Video ID
def extract_video_id(url):
    pattern = r"(?:v=|youtu.be/)([a-zA-Z0-9_-]+)"
    match = re.search(pattern, url)
    return match.group(1) if match else None


# 📜 Get Transcript
def get_transcript(video_id):
    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)

        try:
            transcript = transcript_list.find_transcript(['en'])
        except:
            transcript = transcript_list.find_transcript(
                [t.language_code for t in transcript_list]
            )

        fetched = transcript.fetch()
        text = " ".join([entry.text for entry in fetched])

        return text

    except NoTranscriptFound:
        return "ERROR: No transcript found for this video."

    except TranscriptsDisabled:
        return "ERROR: Transcripts are disabled for this video."

    except Exception as e:
        return f"ERROR: Could not fetch transcript ({str(e)})"


# 🔥 Split text
def chunk_text(text, chunk_size=3000):
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]


# 🧠 Gemini wrapper (FINAL FIX)
def generate_with_gemini(prompt):
    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.7,
                "max_output_tokens": 2048,
            }
        )
        return response.text

    except Exception as e:
        return f"ERROR: Gemini API failed -> {e}"


# 🧠 Summarize chunks
def summarize_chunk(chunk):
    prompt = f"""
    Summarize the following transcript into clear bullet points:

    {chunk}
    """
    return generate_with_gemini(prompt)


# 🧠 Final article generation
def generate_article(text):
    if text.startswith("ERROR"):
        return text

    chunks = chunk_text(text)
    summaries = []

    for chunk in chunks:
        summaries.append(summarize_chunk(chunk))

    combined_summary = "\n".join(summaries)

    final_prompt = f"""
    Convert the following content into a structured article.

    Requirements:
    - Title
    - Introduction
    - Key Points (bullet points)
    - Conclusion
    - Clean formatting

    Content:
    {combined_summary}
    """

    return generate_with_gemini(final_prompt)


# 📄 Save PDF
def save_pdf(content, filename="output.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.set_font("Arial", size=12)

    # ✅ FIX: convert to latin-1 safely
    content = content.encode("latin-1", "replace").decode("latin-1")

    for line in content.split("\n"):
        pdf.multi_cell(0, 8, line)

    pdf.output(filename)