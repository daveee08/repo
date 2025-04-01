import streamlit as st
from model import get_all_questions, insert_user_response, UserResponse, UserAnswers  # Import UserAnswers
from typing import List
import requests
import json

st.title("Take the Quiz")


def evaluate_learner_level(score: int, total_questions: int) -> str:
    if total_questions == 0:
        return "No questions answered"
    
    percentage = (score / total_questions) * 100
    
    if percentage < 50:
        return "Slow Learner"
    elif 50 <= percentage < 80:
        return "Average Learner"
    else:
        return "Advanced Learner"


def clean_response(response):
    cleaned_response = response.strip()
    cleaned_response = cleaned_response.replace('*', '')
    cleaned_response = cleaned_response.replace('`', '')
    return cleaned_response


def get_chatbot_response(messages):
    api_key = "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"
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Use messages directly since they are already dictionaries
    data = {
        "model": "deepseek/deepseek-chat-v3-0324:free",
        "messages": messages,
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        response_data = response.json()
        return clean_response(response_data['choices'][0]['message']['content'])
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None


# Fetch all questions from the database
questions = get_all_questions()

if questions:
    st.write("### Questions List:")
    
    # Initialize a session state to store user answers
    if "user_answers" not in st.session_state:
        st.session_state.user_answers = UserAnswers(user_id=1)  # Replace with actual user ID logic

    # Display each question and its choices
    for i, q in enumerate(questions, 1):
        st.write(f"**{i}. {q.text}** ({q.type})")

        if q.type == "Multiple Choice":
            choices = [choice.choice_text for choice in q.choices]
            user_answer = st.radio(f"Select your answer for question {i}:", options=choices, key=f"question_{i}")
            st.session_state.user_answers.add_response(q.id, user_answer)  # Store the user's answer

        elif q.type == "True/False":
            user_answer = st.radio(f"Select your answer for question {i}:", options=["True", "False"], key=f"question_{i}")
            st.session_state.user_answers.add_response(q.id, user_answer)  # Store the user's answer

        elif q.type == "Essay":
            user_answer = st.text_area(f"Your answer for question {i}:", key=f"question_{i}")
            st.session_state.user_answers.add_response(q.id, user_answer)  # Store the user's answer

    # Submit button to check answers
    if st.button("Submit Answers"):
        score = 0
        total_questions = len(questions)

        # Check answers and store responses
        for i, q in enumerate(questions, 1):
            user_response = st.session_state.user_answers.responses.get(q.id)
            # Store user response in the database
            insert_user_response(UserResponse(user_id=st.session_state.user_answers.user_id, question_id=q.id, response=user_response), questions)

            if q.type == "Multiple Choice":
                correct_answer = next(choice.choice_text for choice in q.choices if choice.is_correct == 1)
                if user_response == correct_answer:
                    score += 1

            elif q.type == "True/False":
                correct_answer = "True" if any(choice.is_correct == 1 for choice in q.choices) else "False"
                if user_response == correct_answer:
                    score += 1

        # Evaluate wrong answers
        wrong_questions = st.session_state.user_answers.evaluate(questions)

        st.success(f"You scored {score} out of {total_questions}!")

        # Determine learner level
        learner_level = evaluate_learner_level(score, total_questions)

        st.write(f"Your learner level is: {learner_level}")

        if wrong_questions:
            st.write("You got the following questions wrong:")
            for question_text, user_response, correct_answer in wrong_questions:
                st.write(f"**Question:** {question_text}")
                st.write(f"**Your Answer:** {user_response}")
                st.write(f"**Correct Answer:** {correct_answer}")

                # Prepare messages for AI to explain the wrong answers
                explanation_messages = [
                    {"role": "user", "content": f"I answered '{user_response}' for the question '{question_text}', but the correct answer is '{correct_answer}'. As a {learner_level}, can you explain why I got this wrong?"}
                ]
                
                # Get AI explanation
                explanation_response = get_chatbot_response(explanation_messages)
                if explanation_response:

                    cleaned_explanation = clean_response(explanation_response)
                    st.markdown(f"""
                        <div style="background-color: #7a7d8e; padding: 10px; border-radius: 5px; color: white;">
                            Explanation: {explanation_response}
                        </div>
                    """, unsafe_allow_html=True)

        else:
            st.write("Congratulations! You answered all questions correctly.")

        st.session_state.user_answers = UserAnswers(user_id=1)

else:
    st.info("No questions available.")