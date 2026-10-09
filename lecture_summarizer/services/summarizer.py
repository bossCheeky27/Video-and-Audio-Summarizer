import google.generativeai as genai
from config import GEMINI_API_KEY


def init_gemini():
    """Initialize the Gemini API client."""
    if not GEMINI_API_KEY:
        raise Exception("GEMINI_API_KEY not set. Please add it to your .env file.")
    genai.configure(api_key=GEMINI_API_KEY)


def generate_summary(transcript, slide_text=None, lecture_id=None):
    """
    Generate structured lecture notes from transcript and optional slide content.

    Args:
        transcript: The lecture transcript text
        slide_text: Optional text extracted from slides

    Returns:
        Formatted markdown summary
    """
    init_gemini()

    # Use Gemini 1.5 Flash (free tier)
    model = genai.GenerativeModel('gemini-2.5-flash')

    # Build the prompt
    prompt = """You are an expert at creating comprehensive, well-structured lecture notes.
Create detailed study notes from the following lecture content.

Your notes should include:
1. **Main Topic Heading** - A clear title for the lecture
2. **Overview** - A brief 2-3 sentence summary of what the lecture covers
3. **Key Concepts** - Major topics broken into sections with subheadings
4. **Definitions** - Important terms with clear definitions (format: **Term**: Definition)
5. **Important Ideas** - Key points and concepts explained clearly
6. **Details & Examples** - Supporting details, examples, and explanations
7. **Summary** - A concise recap of the main takeaways

Format the notes in clean Markdown with:
- Clear heading hierarchy (# for main title, ## for sections, ### for subsections)
- Bullet points for lists
- Bold for key terms and definitions
- Numbered lists where sequence matters

"""

    prompt += f"\n## Lecture Transcript:\n{transcript}\n"

    if slide_text:
        prompt += f"\n## Slide Content:\n{slide_text}\n"

    prompt += "\n\nNow create the structured lecture notes:"

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        raise Exception(f"Error generating summary: {str(e)}")


def generate_summary_chunked(transcript, slide_text=None, chunk_size=30000, lecture_id=None):
    """
    Generate summary for very long transcripts by processing in chunks.

    Args:
        transcript: The lecture transcript text
        slide_text: Optional text extracted from slides
        chunk_size: Maximum characters per chunk

    Returns:
        Formatted markdown summary
    """
    # If transcript is short enough, process normally
    if len(transcript) < chunk_size:
        if lecture_id is not None:
            import database as db
            db.update_lecture_progress(lecture_id, 50)
        result = generate_summary(transcript, slide_text, lecture_id=lecture_id)
        if lecture_id is not None:
            db.update_lecture_progress(lecture_id, 100)
        return result

    init_gemini()
    model = genai.GenerativeModel('gemini-2.5-flash')

    # Split transcript into chunks
    chunks = []
    for i in range(0, len(transcript), chunk_size):
        chunks.append(transcript[i:i + chunk_size])

    # Summarize each chunk
    # Progress: chunks take 80%, final combination takes 20%
    total_steps = len(chunks) + 1
    chunk_summaries = []
    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i + 1}/{len(chunks)}...")
        if lecture_id is not None:
            import database as db
            pct = int((i / total_steps) * 100)
            db.update_lecture_progress(lecture_id, pct)

        chunk_prompt = f"""Summarize this portion of a lecture transcript.
Extract the key points, definitions, and important concepts.

Transcript portion {i + 1}/{len(chunks)}:
{chunk}

Provide a detailed summary of this section:"""

        response = model.generate_content(chunk_prompt)
        chunk_summaries.append(response.text)

    # Combine chunk summaries into final notes
    if lecture_id is not None:
        import database as db
        db.update_lecture_progress(lecture_id, int((len(chunks) / total_steps) * 100))
    combined = "\n\n---\n\n".join(chunk_summaries)

    final_prompt = f"""You are an expert at creating comprehensive lecture notes.
I have summaries from different parts of a lecture. Combine them into well-structured study notes.

Your notes should include:
1. **Main Topic Heading** - A clear title for the lecture
2. **Overview** - A brief summary of what the lecture covers
3. **Key Concepts** - Major topics broken into sections with subheadings
4. **Definitions** - Important terms with clear definitions
5. **Important Ideas** - Key points explained clearly
6. **Summary** - A concise recap of the main takeaways

Format in clean Markdown with proper heading hierarchy.

## Section Summaries:
{combined}

"""

    if slide_text:
        final_prompt += f"\n## Additional Slide Content:\n{slide_text}\n"

    final_prompt += "\n\nNow create the final structured lecture notes:"

    response = model.generate_content(final_prompt)
    return response.text
