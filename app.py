"""
TalentScout — Hiring Assistant (app.py)

Features implemented (high-level):
- Sidebar for candidate inputs (Full name, email, phone, years exp, desired role, location, tech stack)
- Option to choose 3-5 questions PER TECHNOLOGY (assignment asks 3-5 per tech)
- Adaptive prompts based on years of experience (fresher / junior / mid-level)
- Per-tech question generation (LLM call per tech) with parsing and fallback templates
- Chat UI in main page: ask one question at a time, accept candidate answer, produce LLM feedback
- Context handling (session_state stores conversation, questions, answers)
- Fallback mechanism when LLM fails or returns unparsable results
- Graceful conversation end & simulated candidate saving
- Docstrings and comments for maintainability
"""

import streamlit as st
import time
import re
from typing import List, Dict
from openRouter_client import OpenRouterClient

st.set_page_config(page_title="TalentScout Hiring Assistant", layout="wide")

# ---------------------------
# Simulated persistent storage (in-memory for this demo)
# ---------------------------
class SimulatedStorage:
    def __init__(self):
        self._last_candidate = None

    def save_candidate(self, candidate: dict):
        """Simulates saving candidate info (in-memory only)."""
        self._last_candidate = {k: v for k, v in candidate.items() if k != "greeted"}

    def last_saved(self):
        return self._last_candidate

# ---------------------------
# Utility functions
# ---------------------------
def is_exit_command(text: str) -> bool:
    return text.lower().strip() in ["exit", "quit", "bye", "goodbye"]

def validate_email(email: str) -> bool:
    return "@" in email and "." in email

def validate_phone(phone: str) -> bool:
    digits = "".join([c for c in phone if c.isdigit()])
    return len(digits) >= 8

# ---------------------------
# Session-state initialization
# ---------------------------
if "conversation" not in st.session_state:
    st.session_state.conversation = []
if "candidate" not in st.session_state:
    st.session_state.candidate = {}
if "finished" not in st.session_state:
    st.session_state.finished = False
if "chat_started" not in st.session_state:
    st.session_state.chat_started = False
if "llm" not in st.session_state:
    st.session_state.llm = OpenRouterClient()
if "storage" not in st.session_state:
    st.session_state.storage = SimulatedStorage()


# ---------------------------
# Helpers
# ---------------------------


def append(role: str, text: str):
    """Append a message to conversation and print a console log for debugging."""
    st.session_state.conversation.append({"role": role, "text": text})


def reset():
    """Reset the whole interview session (clears conversation and candidate)."""
    st.session_state.conversation = []
    st.session_state.candidate = {}
    st.session_state.finished = False
    st.session_state.chat_started = False


def safe_generate(prompt: str, retries: int = 3, backoff: float = 1.5) -> str:
    """
    Call the LLM generate method with retries and exponential backoff.
    Raises the final exception if all retries fail.
    """
    last_exc = None
    for attempt in range(retries):
        try:
            return st.session_state.llm.generate(prompt)
        except Exception as e:
            last_exc = e
            # backoff sleep except before last attempt
            if attempt < retries - 1:
                time.sleep(backoff * (attempt + 1))
                continue
            else:
                # re-raise after final attempt
                raise last_exc
    raise last_exc


def parse_grouped_questions(raw_text: str) -> List[Dict[str, str]]:
    """
    Parse LLM output that may be grouped by headings (e.g., "Python:") and numbered lists.
    Returns a list of dicts: {"tech": <tech-or-None>, "question": <text>}
    """
    questions = []
    current_tech = None
    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue
        # heading e.g., "Python:" or "Python -"
        head_match = re.match(r'^([A-Za-z0-9 _\-\+\.\#]+)\s*[:\-]\s*$', line)
        if head_match:
            current_tech = head_match.group(1).strip()
            continue

        # numbered question like "1. What is ...?"
        num_match = re.match(r'^\d+\.\s*(.+)$', line)
        if num_match:
            q = num_match.group(1).strip().rstrip('.')
            questions.append({"tech": current_tech, "question": q})
            continue

        # plain question line fallback (if it looks like a question)
        if line.endswith('?') or line.lower().startswith(("what", "how", "explain", "describe", "why", "when", "give")):
            questions.append({"tech": current_tech, "question": line.rstrip('.')})
            continue

        # otherwise ignore noise lines
    return questions


def fallback_questions_for_tech(tech: str, n: int, years_exp: float) -> List[Dict[str, str]]:
    """
    Provide safe fallback questions if LLM can't produce them.
    These are intentionally simple and cover basics appropriate to candidate level.
    Returns list of dicts {"tech": tech, "question": ...}
    """
    level = "fresher" if years_exp < 1 else "junior" if years_exp < 3 else "mid-level"
    tech_lower = tech.lower()
    templates = []

    # Generic base templates
    templates.append(f"What is {tech} and where is it commonly used?")
    templates.append(f"Name one common task you would perform using {tech}. How would you start?")
    templates.append(f"Explain a basic concept or term related to {tech} that a beginner should know.")
    templates.append(f"Describe a simple example or use-case of {tech}.")
    templates.append(f"What are common tools or libraries used with {tech}?")

    # Tech-specific mild customization for common techs
    if "python" in tech_lower:
        templates[1] = "How do you write a function in Python? Give a short example."
        templates[2] = "What is a list in Python and how is it different from a tuple?"
    elif "react" in tech_lower:
        templates[0] = "What is a component in React?"
        templates[1] = "How do you pass data from parent to child component in React?"
    elif "sql" in tech_lower or "postgres" in tech_lower or "mysql" in tech_lower:
        templates[0] = "What is a database table and a row?"
        templates[1] = "What is a primary key and why is it important?"
    elif "django" in tech_lower or "fastapi" in tech_lower or "flask" in tech_lower:
        templates[0] = f"What is a web framework like {tech}, and when would you use it?"
        templates[1] = "How do you handle incoming HTTP requests in a simple route?"
    elif "javascript" in tech_lower or tech_lower == "js":
        templates[0] = "What is JavaScript and how is it used in web development?"
        templates[1] = "What's the difference between var/let/const in JavaScript?"
    elif "node" in tech_lower:
        templates[0] = "What is Node.js used for?"
        templates[1] = "How would you create a simple HTTP server in Node?"

    # pick first n templates
    picked = templates[:n]
    return [{"tech": tech, "question": q} for q in picked]


def build_per_tech_prompt(tech: str, years_exp: float, n: int = 3) -> str:
    """
    Build a prompt requesting n beginner/junior/mid-level questions for a single technology.
    The prompt is explicit about candidate experience so the LLM tailors difficulty.
    """
    if years_exp <= 1:
        level = "entry-level (fresher)"
    elif years_exp <= 3:
        level = "junior-level"
    else:
        level = "mid-level (practical, not deep system design)"

    return (
        f"You are an interviewer preparing questions for a {level} candidate.\n"
        f"Generate {n} open-ended, beginner-friendly technical interview questions about this technology: {tech}.\n"
        f"Focus on core concepts and practical basics that a {level} candidate should know.\n"
        f"Output as a numbered list (1., 2., ...). Do NOT provide answers or extra commentary."
    )


def generate_questions_for_stack(tech_stack: List[str], years_exp: float, per_tech_n: int) -> List[Dict[str, str]]:
    """
    Generate questions for each tech in tech_stack using the LLM. If LLM fails or parsing
    returns nothing for a particular tech, fallback to built-in templates.
    Returns flattened list of {tech, question}.
    """
    all_questions = []
    for tech in tech_stack:
        prompt = build_per_tech_prompt(tech, years_exp, per_tech_n)
        try:
            raw = safe_generate(prompt)
            parsed = parse_grouped_questions(raw)
            # if parsed contains tech=None (because model didn't include heading), set tech
            for q in parsed:
                if q["tech"] is None:
                    q["tech"] = tech
            if not parsed:
                # try quick fallback parsing if model returned unnumbered list
                # fallback to built-in templates
                parsed = []
            if parsed:
                all_questions.extend(parsed)
            else:
                fallback = fallback_questions_for_tech(tech, per_tech_n, years_exp)
                all_questions.extend(fallback)
                print(f"[WARN] Used fallback questions for {tech}")
        except Exception as e:
            print(f"[ERROR] Question generation failed for {tech}: {e}")
            fallback = fallback_questions_for_tech(tech, per_tech_n, years_exp)
            all_questions.extend(fallback)
    return all_questions


# ---------------------------
# Sidebar: Candidate Info Form
# ---------------------------
with st.sidebar.form("candidate_form", clear_on_submit=False):
    st.header("Candidate Info (required)")
    full_name = st.text_input("Full Name", placeholder="e.g., Arpit Patel")
    email = st.text_input("Email", placeholder="e.g., arpit@example.com")
    phone = st.text_input("Phone (with country code)", placeholder="e.g., +91 9876543210")
    years_exp = st.number_input("Years of Experience", min_value=0.0, step=0.5, value=0.0, format="%.1f")
    desired_positions = st.text_input("Desired Position(s)", placeholder="e.g., Software Engineer")
    location = st.text_input("Current Location", placeholder="e.g., Bangalore, India")
    tech_stack_text = st.text_input("Tech Stack (comma-separated)", placeholder="e.g., Python, React, SQL")
    per_tech_n = st.slider("Questions per technology (3–5)", min_value=3, max_value=5, value=3)

    start_chat = st.form_submit_button("Start Chat")

    if start_chat:
        # basic validation
        if not full_name.strip():
            st.sidebar.warning("Please enter your full name.")
        elif not validate_email(email):
            st.sidebar.warning("Please enter a valid email.")
        elif not validate_phone(phone):
            st.sidebar.warning("Please enter a valid phone number with country code.")
        elif not tech_stack_text.strip():
            st.sidebar.warning("Please enter at least one technology in tech stack.")
        else:
            # Save candidate info
            tech_list = [t.strip() for t in tech_stack_text.split(",") if t.strip()]
            st.session_state.candidate = {
                "full_name": full_name.strip(),
                "email": email.strip(),
                "phone": phone.strip(),
                "years_experience": years_exp,
                "desired_positions": desired_positions.strip(),
                "location": location.strip(),
                "tech_stack": tech_list,
                "questions": [],
                "answers": [],  # store candidate answers
            }
            st.session_state.chat_started = True
            append("assistant", f"Welcome {full_name}! I will ask you questions based on your tech stack: {', '.join(tech_list)}.")
            # Generate questions per tech
            questions = generate_questions_for_stack(tech_list, years_exp, per_tech_n)
            # Save questions in session_state; each entry is {"tech":..., "question":...}
            st.session_state.candidate["questions"] = questions
            st.session_state.candidate["q_index"] = 0
            # Ask first question
            if questions:
                first = questions[0]
                append("assistant", f"({first['tech']}) {first['question']}")
            else:
                append("assistant", "Could not generate any questions. Please try again later.")
            # Rerun to show chat on main page
            st.rerun()


# ---------------------------
# Main: Chat interface
# ---------------------------
st.title("TalentScout — Interview Chat")

# Display conversation history (main page is just chat + final feedback)
for msg in st.session_state.conversation:
    with st.chat_message(msg["role"]):
        st.markdown(msg["text"])

# If chat not started
if not st.session_state.chat_started:
    st.info("Fill candidate details on the left and click **Start Chat**. The interview will appear here.")
    st.stop()

# If interview finished
if st.session_state.finished:
    st.success("Interview complete. Candidate saved (simulated).")
    # Show last saved candidate object (simulated storage)
    try:
        st.json(st.session_state.storage.last_saved())
    except Exception:
        st.write("Saved candidate (simulated) is not available.")
    if st.button("Start New Interview"):
        reset()
        st.rerun()
    st.stop()

# Chat input (active interview)
user_input = st.chat_input("Type your answer here... (type 'exit' to finish early)")
if user_input:
    text = user_input.strip()
    append("user", text)

    # Exit immediately if requested
    if is_exit_command(text):
        append("assistant", "Thanks! We've received your responses. We'll review and get back to you.")
        # Save candidate (simulated) and finish
        st.session_state.storage.save_candidate(st.session_state.candidate)
        st.session_state.finished = True
        st.rerun()

    # Otherwise handle Q/A
    c = st.session_state.candidate
    q_idx = c.get("q_index")

    if q_idx is None:
        append("assistant", "No more questions. Type `exit` to finish or click 'Start New Interview' in the sidebar.")
        st.rerun()

    # Get current question
    if "questions" not in c or q_idx >= len(c["questions"]):
        append("assistant", "No more questions available.")
        c["q_index"] = None
        st.rerun()

    current_q = c["questions"][q_idx]

    # Save the answer
    c.setdefault("answers", []).append({"question": current_q["question"], "tech": current_q["tech"], "answer": text})

    # Build evaluation prompt (ask model to evaluate candidate answer for appropriateness to their experience level)
    years_exp = c.get("years_experience", 0.0)
    level = "entry-level (fresher)" if years_exp < 1 else "junior-level" if years_exp < 3 else "mid-level"

    eval_prompt = (
        f"You are an interviewer/evaluator. The candidate is {level} with {years_exp} years experience.\n"
        f"Question (technology: {current_q['tech']}): {current_q['question']}\n"
        f"Candidate's answer: {text}\n\n"
        "Provide a short evaluation focusing on:\n"
        "- Correctness (was the core idea addressed?)\n"
        "- Clarity (is it explained clearly?)\n"
        "- Depth (is it appropriate for the candidate's experience?)\n"
        "Then give 2-3 concrete suggestions the candidate could study to improve.\n"
        "Keep the feedback concise (2-4 sentences) and friendly."
    )

    # Ask LLM for feedback (safe_generate with fallback)
    try:
        feedback = safe_generate(eval_prompt)
        if not feedback or not feedback.strip():
            feedback = "No feedback generated by the model."
    except Exception as e:
        feedback = "Could not generate feedback at this time."

    # Append feedback
    append("assistant", f"📝 Feedback ({current_q['tech']}):\n> {feedback}")

    # Move to next question
    next_idx = q_idx + 1
    if next_idx < len(c["questions"]):
        c["q_index"] = next_idx
        next_q = c["questions"][next_idx]
        append("assistant", f"({next_q['tech']}) {next_q['question']}")
    else:
        # All questions done: save candidate (simulated), thank and finish
        append("assistant", "That’s all the questions I had. Thank you — we’ve saved your responses and will review them shortly.")
        st.session_state.storage.save_candidate(st.session_state.candidate)
        c["q_index"] = None
        st.session_state.finished = True

    # Force rerun to reflect new conversation messages
    st.rerun()