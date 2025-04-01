import streamlit as st
from model import Question, Choice, insert_question, get_all_questions, remove_question_from_db
from pydantic import BaseModel
from typing import List, Optional

# Define your Pydantic models (or import them if they're in a separate file)
class Choice(BaseModel):
    choice_text: str
    is_correct: int

class Question(BaseModel):
    id: Optional[int]  # Add id to the Question model
    text: str
    type: str
    choices: Optional[List[Choice]] = None

st.title("Create Questions")

# Input for a new question
st.text_input("Enter your question:", key="new_question")

# Dropdown for question type
question_types = ["", "Multiple Choice", "True/False", "Essay"]
st.selectbox("Select Question Type:", question_types, key="question_type")

# Initialize session state for MCQ choices
if "mcq_choices" not in st.session_state:
    st.session_state.mcq_choices = []

# Initialize session state for refresh flag
if "refresh_questions" not in st.session_state:
    st.session_state.refresh_questions = False

# Conditional Inputs Based on Question Type
if st.session_state.question_type == "True/False":
    st.radio("Select Correct Answer:", ["True", "False"], key="tf_answer")

elif st.session_state.question_type == "Multiple Choice":
    # Input field for adding a new choice
    new_choice = st.text_input("Enter a choice:")

    # Add choice button
    if st.button("Add Choice") and new_choice.strip():
        st.session_state.mcq_choices.append(new_choice.strip())

    # Display and allow deletion of added choices
    if st.session_state.mcq_choices:
        st.write("Choices:")
        for i, choice in enumerate(st.session_state.mcq_choices, 1):
            col1, col2 = st.columns([5, 1])  # Create two columns: one for the choice, one for the delete button
            with col1:
                st.write(f"{i}. {choice}")
            with col2:
                # Render X icon as a clickable button
                if st.button(f"❌", key=f"delete_choice_{i}"):
                    st.session_state.mcq_choices.pop(i - 1)  # Remove the choice
                    break  # Exit after popping to update the state correctly

        # Radio button to select the correct answer
        correct_choice = st.radio("Select the correct answer:", options=st.session_state.mcq_choices, key="correct_choice")

# Function to add a question to the database
def save_question():
    question_text = st.session_state.new_question.strip()
    question_type = st.session_state.question_type

    # Validation
    if not question_text:
        st.warning("⚠️ Please enter a question.")
        return
    if not question_type:
        st.warning("⚠️ Please select a question type.")
        return
    if question_type == "Multiple Choice" and not st.session_state.mcq_choices:
        st.warning("⚠️ Please add at least one choice for Multiple Choice questions.")
        return
    if question_type == "Multiple Choice" and 'correct_choice' not in st.session_state:
        st.warning("⚠️ Please select the correct answer for Multiple Choice questions.")
        return

    # Prepare question data using Pydantic models
    choices = []
    for choice in st.session_state.mcq_choices:
        is_correct = 1 if choice == st.session_state.correct_choice else 0
        choices.append(Choice(choice_text=choice, is_correct=is_correct))

    # Create a Question object without an id
    question_data = Question(
        id=None,  # Explicitly set to None
        text=question_text,
        type=question_type,
        choices=choices if question_type == "Multiple Choice" else None
    )

    # Insert into database
    insert_question(question_data)
    st.success("✅ Question added successfully!")

    # Reset fields
    st.session_state.new_question = ""
    st.session_state.mcq_choices = []

# Save question button
st.button("Add Question", on_click=save_question)

# Display all questions
if st.session_state.refresh_questions:
    st.session_state.questions = get_all_questions()  # Fetch questions again if the flag is set
    st.session_state.refresh_questions = False  # Reset the flag

if "questions" not in st.session_state:
    st.session_state.questions = get_all_questions()  # Initial fetch of questions

if st.session_state.questions:
    st.write("### Questions List:")
    for i, q in enumerate(st.session_state.questions, 1):
        st.write(f"{i}. {q.text} ({q.type})")

        if q.type == "Multiple Choice":
            st.write("Choices:")
            for j, choice in enumerate(q.choices, 1):
                st.write(f"- {choice.choice_text} (Correct: {choice.is_correct})")  # Use dot notation to access attributes

        # Add a delete button for each question
        if st.button(f"Delete Question {i}", key=f"delete_question_{q.id}"):  # Assuming each question has a unique id
            # Directly delete the question from the database
            remove_question_from_db(q.id)  # Call the function to delete the question from the database
            st.success(f"✅ Question {i} deleted successfully!")
            st.session_state.refresh_questions = True  # Set the flag to refresh questions
else:
    st.info("No questions added yet.")