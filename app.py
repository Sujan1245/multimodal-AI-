from flask import Flask, render_template, request, url_for
from PIL import Image
import os
from google import genai 
from werkzeug.utils import secure_filename
import mimetypes # Used to guess file type for display

app = Flask(__name__)

# ---------------- CONFIGURE GEMINI CLIENT ----------------
# *** IMPORTANT: Replace with your actual key ***
API_KEY = "input API KEY" 
client = genai.Client(api_key=API_KEY) 

MODEL_NAME = "gemini-2.5-flash" 

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024 # Increased limit for audio/video

# --- LLM Function ---
def generate_llm_response(user_text, file_path):
    """
    Generates a response from Gemini using text and a file (Image, Audio, or Video).
    """
    try:
        # 1. Upload the file to the Gemini File API service
        uploaded_file = client.files.upload(file=file_path)
        
        # 2. Structure the contents: list of text and the uploaded file part
        # Gemini handles transcribing audio or understanding the image/video.
        contents = [
            user_text,
            uploaded_file
        ]

        # 3. Generate content
        response = client.models.generate_content(
            model=MODEL_NAME, 
            contents=contents
        )
        
        # 4. Clean up the file from the Gemini service after use
        client.files.delete(name=uploaded_file.name)
        
        return response.text
    
    except Exception as e:
        print("LLM ERROR:", e)
        # Handle API key or other specific errors
        if "API_KEY_INVALID" in str(e):
            return "ERROR: The API key is invalid or not set correctly."
        return f"Could not generate response using Gemini AI. Error: {e}"

@app.route("/", methods=["GET", "POST"])
def index():
    response_text = ""
    uploaded_file_url = None
    user_text = ""
    file_type = None

    if request.method == "POST":
        # Text input from the textarea
        user_text = request.form.get("text", "")
        # Media file input (can be uploaded or a recorded blob)
        media_file = request.files.get("media_file")

        if media_file and media_file.filename != "":
            # Save file safely
            filename = secure_filename(media_file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            media_file.save(file_path)
            
            # Determine file type for display
            mime_type, _ = mimetypes.guess_type(filename)
            if mime_type:
                if mime_type.startswith('image'):
                    file_type = 'image'
                elif mime_type.startswith('audio'):
                    file_type = 'audio'
                elif mime_type.startswith('video'):
                    file_type = 'video'
            
            # Generate response
            response_text = generate_llm_response(user_text, file_path) 
            
            uploaded_file_url = url_for('static', filename=f"uploads/{filename}")
            
            # Optional: Clean up the local file after processing (if not debugging)
            # os.remove(file_path)
            
        else:
            response_text = "Please provide both text and a media file (or record audio)."

    return render_template(
        "index.html",
        user_text=user_text,
        response=response_text,
        uploaded_file_url=uploaded_file_url,
        file_type=file_type
    )

if __name__ == "__main__":
    app.run(debug=True)