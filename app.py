
import streamlit as st
import pandas as pd
import tempfile
import mailbox
import requests

# Hugging Face Inference API settings
API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
headers = {"Authorization": "Bearer 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"}

# Function to call Hugging Face API for summarization
def summarize_text(text):
    payload = {
    "inputs": f'''
You are an advanced assistant specialized in analyzing professional email inboxes across various industries.

Your task is to review a batch of email messages and organize the information in a clear, useful, and structured way. These messages may relate to various clients, projects, tasks, teams, or internal discussions.

Your output should include the following sections:

---

1. 📚 **Topics Identified**
   - List the main topics, subjects, and threads covered in the emails.
   - Group emails under each topic.

2. 👥 **People and Roles**
   - Identify who participated in which conversations.
   - If roles are mentioned (e.g., manager, technician, supplier), include them.

3. 🏢 **Companies and Customers Mentioned**
   - List all external companies, partners, or customers referenced.
   - Group relevant emails under each customer if possible.

4. 📨 **Conversation Threads (Grouped by Topic)**
   For each major topic, provide:
   - A summary of the conversation
   - Notable decisions or agreements
   - Questions or unresolved issues

5. ✅ **Action Items**
   - Extract clear tasks or requests made in the emails
   - Include:
     - Who is responsible (if known)
     - What needs to be done
     - By when (if a date or urgency is mentioned)

6. ⏳ **Pending or Follow-Up Items**
   - Highlight emails where a reply or action was requested but not confirmed
   - List who needs to follow up, and on what

7. 🗓️ **Deadlines and Time-sensitive Info**
   - Summarize any mentioned dates, events, or due times

---

Be concise but informative. Maintain structure so the information is easy to navigate.

Here are the emails to analyze:
{text}
'''
}
    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()[0]['summary_text']
    else:
        return f"Error: {response.text}"

# Read .mbox file and extract email bodies
def read_emails_from_mbox(file_path):
    mbox = mailbox.mbox(file_path)
    emails = []
    for message in mbox:
        subject = message['subject'] or "(No subject)"
        body = message.get_payload(decode=True)
        if body:
            try:
                body = body.decode()
            except:
                body = str(body)
        else:
            body = "(No content)"
        emails.append(f"Subject: {subject}\n{body}")
    return emails

# Streamlit UI
st.title("📧 Email Summarizer (MBOX Format)")
uploaded_file = st.file_uploader("Upload a .mbox file", type=["mbox"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mbox") as tmp:
        tmp.write(uploaded_file.getvalue())
        file_path = tmp.name

    emails = read_emails_from_mbox(file_path)
    st.success(f"Loaded {len(emails)} emails")

    if emails:
        # Limit the content to a manageable size for summarization
        full_text = "\n\n".join(emails[:5])  # summarizing first 5 emails
        st.subheader("📝 Summary")
        with st.spinner("Summarizing..."):
            summary = summarize_text(full_text)
        st.write(summary)

        # Optionally save
        if st.button("💾 Save Summary"):
            with open("summaries.csv", "a", encoding="utf-8") as f:
                f.write(f"{uploaded_file.name}|{summary}\n")
            st.success("Summary saved to summaries.csv")
