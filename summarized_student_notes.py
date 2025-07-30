import streamlit as st
import pandas as pd
from io import BytesIO
import openai
import os

# 🔐 Set OpenAI API Key securely
openai.api_key = st.secrets["openai"]["api_key"]

# 🎯 Predefined Skill List
SKILL_SET = [
    "Communication Skills", "Leadership", "Resilience", "English Proficiency", "Discipline",
    "Diligence", "Task Management", "Adaptability", "Problem-solving", "Creativity",
    "Consistency", "Punctuality", "Respectfulness", "Self-motivation", "Maturity"
]

# 🤖 Function to get summary and skills from GPT
def generate_summary_and_skills(student_comments):
    prompt = f"""
You are an academic mentor assistant. You will receive a list of mentor comments about a student across several months.

Your tasks:
1. Write a concise summary (in 150-200 words) that reflects the student's progress, strengths, and areas of improvement, based on all the comments.
2. From the following list, identify **only those skills that are clearly evident** in the comments:
{", ".join(SKILL_SET)}.

- If no skill from the list is clearly reflected in the mentor comments, respond with: Student Skills: None
- Do not infer or guess skills unless they are mentioned or implied in the comments.

### Mentor Comments:
{student_comments}

### Output Format:
Summarized Note: <your 150-200 word summary>
Student Skills: <comma-separated list of matched skills from above, or 'None'>
"""

    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=1000
    )

    content = response.choices[0].message.content.strip()

    summary, skills = "", ""
    for line in content.splitlines():
        if line.startswith("Summarized Note:"):
            summary = line.replace("Summarized Note:", "").strip()
        elif line.startswith("Student Skills:"):
            skills = line.replace("Student Skills:", "").strip()
    return summary, skills

# 🖥️ Streamlit UI
st.set_page_config(page_title="Student Summary & Skills Generator", layout="wide")
st.title("🎓 AI-Generated Student Summary and Skill Extractor")

uploaded_file = st.file_uploader("📤 Upload Pivoted Mentor Comments Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Basic checks
    if not {"ADEK Application ID", "Student Full Name"}.issubset(df.columns):
        st.error("Excel file must contain 'ADEK Application ID' and 'Student Full Name' columns.")
    else:
        # Preview table
        st.write("✅ Uploaded Data Preview:")
        st.dataframe(df.head(), use_container_width=True)

        # Button to trigger summarization
        if st.button("🚀 Generate Result"):
            st.info("Running GPT model for summarization and skill extraction...")

            metadata_cols = {"ADEK Application ID", "Student Full Name"}
            comment_cols = [col for col in df.columns if col not in metadata_cols]

            # Combine all monthly comments into one string
            df["All Comments"] = df[comment_cols].astype(str).apply(lambda row: " ".join(row.dropna()), axis=1)

            # Run GPT for each student
            summaries = []
            skills_list = []

            for _, row in df.iterrows():
                summary, skills = generate_summary_and_skills(row["All Comments"])
                summaries.append(summary)
                skills_list.append(skills)

            df["Summarized Note"] = summaries
            df["Student Skills"] = skills_list

            df.drop(columns=["All Comments"], inplace=True)

            st.success("✅ Summarization completed!")
            st.write("### 🧾 Final Output Preview:")
            st.dataframe(df, use_container_width=True)

            # Export to Excel
            def to_excel(df):
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name="Student Summary")
                output.seek(0)
                return output

            excel_data = to_excel(df)

            st.download_button(
                label="📥 Download Excel with Summaries and Skills",
                data=excel_data,
                file_name="Student summary & skills.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
