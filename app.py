import os
import streamlit as st
from groq import Groq
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv

load_dotenv()

# Safely load API key for both local (.env) and cloud (st.secrets)
api_key = os.getenv("GROQ_API_KEY", "")
if not api_key:
    try:
        api_key = st.secrets.get("GROQ_API_KEY", "")
    except Exception:
        api_key = ""

client = Groq(api_key=api_key)

st.set_page_config(page_title="AI Expense Tracker", page_icon="💸", layout="wide")

st.title("💸 AI-Powered Expense Tracker & Insights")
st.markdown("Track your expenses naturally using **Groq** intelligence.")

# Initialize session state for expenses
if "expenses" not in st.session_state:
    st.session_state.expenses = pd.DataFrame(columns=["Date", "Description", "Category", "Amount"])

# Sidebar for adding expenses via AI text parsing
st.sidebar.header("➕ Add Expense via AI")
user_input = st.sidebar.text_area("Example: 'Spent $45 on groceries yesterday and $12 for lunch today'")

if st.sidebar.button("Process with Groq AI"):
    if not api_key:
        st.sidebar.error("Please configure your GROQ_API_KEY!")
    elif user_input:
        with st.spinner("Analyzing text with Groq..."):
            prompt = f"""
            Extract expense details from the following text into a structured JSON list format. 
            Fields required for each item: date (approximate or current if relative like 'today'), description, category (e.g., Food, Transport, Utilities, Entertainment, Shopping), amount (numeric only).
            Text: "{user_input}"
            Return ONLY a valid JSON array of objects with keys: "date", "description", "category", "amount". No extra text or markdown formatting except standard JSON.
            """
            try:
                chat_completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="openai/gpt-oss-20b",
                )
                content = chat_completion.choices[0].message.content.strip()
                # Clean markdown blocks if returned
                if content.startswith("```json"):
                    content = content[7:-3].strip()
                elif content.startswith("```"):
                    content = content[3:-3].strip()
                
                import json
                new_items = json.loads(content)
                new_df = pd.DataFrame(new_items)
                st.session_state.expenses = pd.concat([st.session_state.expenses, new_df], ignore_index=True)
                st.sidebar.success("Expenses added successfully!")
            except Exception as e:
                st.sidebar.error(f"Error parsing input: {e}")

# Main Dashboard
tab1, tab2 = st.tabs(["📊 Dashboard & Analytics", "🤖 AI Financial Advisor"])

with tab1:
    st.subheader("📋 Expense Records")
    if not st.session_state.expenses.empty:
        st.dataframe(st.session_state.expenses, use_container_width=True)
        
        # Metrics
        total_spent = st.session_state.expenses["Amount"].astype(float).sum()
        st.metric(label="Total Expenses", value=f"${total_spent:.2f}")
        
        # Charts
        col1, col2 = st.columns(2)
        with col1:
            fig_pie = px.pie(st.session_state.expenses, names="category", values="amount", title="Expenses by Category")
            st.plotly_chart(fig_pie, use_container_width=True)
        with col2:
            fig_bar = px.bar(st.session_state.expenses, x="description", y="amount", color="category", title="Expense Breakdown")
            st.plotly_chart(fig_bar, use_container_width=True)
            
        if st.button("Clear All Data"):
            st.session_state.expenses = pd.DataFrame(columns=["Date", "Description", "Category", "Amount"])
            st.rerun()
    else:
        st.info("No expenses recorded yet. Use the sidebar to add expenses using natural language!")

with tab2:
    st.subheader("💡 Smart Financial Recommendations")
    if not st.session_state.expenses.empty:
        if st.button("Generate AI Spending Analysis"):
            with st.spinner("Generating insights..."):
                summary_data = st.session_state.expenses.to_string()
                advisor_prompt = f"Analyze these expenses and give 3 practical budgeting tips to save money:\n{summary_data}"
                
                response = client.chat.completions.create(
                    messages=[{"role": "user", "content": advisor_prompt}],
                    model="openai/gpt-oss-20b"
                )
                st.write(response.choices[0].message.content)
    else:
        st.warning("Add some expenses first to get AI insights.")