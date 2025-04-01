import mysql.connector
from mysql.connector import Error
from pydantic import BaseModel
from typing import List, Optional

# Define your Pydantic models
class Choice(BaseModel):
    choice_text: str
    is_correct: int  # You can change this to bool if you prefer

class Question(BaseModel):
    id: Optional[int]  # Add id to the Question model
    text: str
    type: str
    choices: Optional[List[Choice]] = None

class UserResponse(BaseModel):
    user_id: int
    question_id: int
    response: str

class UserAnswers:
    def __init__(self, user_id):
        self.user_id = user_id
        self.responses = {}

    def add_response(self, question_id, response):
        self.responses[question_id] = response

    def evaluate(self, questions):
        wrong_questions = []
        for q in questions:
            user_response = self.responses.get(q.id)
            if user_response is not None:
                if q.type == "Multiple Choice":
                    correct_answer = next(choice.choice_text for choice in q.choices if choice.is_correct == 1)
                elif q.type == "True/False":
                    correct_answer = "True" if any(choice.is_correct == 1 for choice in q.choices) else "False"
                else:
                    continue  # Skip essay questions for evaluation

                if user_response != correct_answer:
                    wrong_questions.append((q.text, user_response, correct_answer))
        return wrong_questions

def insert_user_response(user_response: UserResponse, questions: List[Question]):
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",  # Use your database password here
            database="data"  # Make sure the database is named correctly
        )
        cursor = connection.cursor()

        # Determine if the user's response is correct
        correct_answer = None
        for question in questions:
            if question.id == user_response.question_id:
                if question.type == "Multiple Choice":
                    correct_answer = next(choice.choice_text for choice in question.choices if choice.is_correct == 1)
                elif question.type == "True/False":
                    correct_answer = "True" if any(choice.is_correct == 1 for choice in question.choices) else "False"
                break

        # Set is_correct to 1 if the user's response matches the correct answer, otherwise 0
        is_correct = 1 if user_response.response == correct_answer else 0

        # Insert user response into the user_response table
        cursor.execute("INSERT INTO user_response (user_id, question_id, response, is_correct) VALUES (%s, %s, %s, %s)", 
                       (user_response.user_id, user_response.question_id, user_response.response, is_correct))

        connection.commit()
    except Error as e:
        print(f"Error occurred: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def remove_question_from_db(question_id: int):
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",  # Use your database password here
            database="data"  # Make sure the database is named correctly
        )
        cursor = connection.cursor()

        # Delete choices associated with the question
        cursor.execute("DELETE FROM choices WHERE question_id = %s", (question_id,))
        
        # Delete the question itself
        cursor.execute("DELETE FROM questions WHERE id = %s", (question_id,))

        connection.commit()
    except Error as e:
        print(f"Error occurred: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def insert_question(question: Question):
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",  # Use your database password here
            database="data"  # Make sure the database is named correctly
        )
        cursor = connection.cursor()

        # Insert question into the database
        cursor.execute("INSERT INTO questions (text, type) VALUES (%s, %s)", 
                       (question.text, question.type))
        question_id = cursor.lastrowid  # Get the ID of the inserted question

        # Insert choices into the database (if any)
        if question.choices:
            for choice in question.choices:
                cursor.execute("INSERT INTO choices (question_id, choice_text, is_correct) VALUES (%s, %s, %s)", 
                               (question_id, choice.choice_text, choice.is_correct))

        connection.commit()
    except Error as e:
        print(f"Error occurred: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def get_all_questions():
    questions = []
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",  # Use your database password here
            database="data"  # Make sure the database is named correctly
        )
        cursor = connection.cursor()

        # Fetch all questions and their choices
        cursor.execute("""
        SELECT q.id, q.text, q.type, c.choice_text, c.is_correct
        FROM questions q
        LEFT JOIN choices c ON q.id = c.question_id
        ORDER BY q.id, c.id
        """)

        results = cursor.fetchall()

        # Process the results into a list of Question objects
        current_question = None
        for row in results:
            if current_question is None or current_question.id != row[0]:
                if current_question:
                    questions.append(current_question)
                # Initialize a new Question object
                current_question = Question(id=row[0], text=row[1], type=row[2], choices=[])
            # Add choices to the current question
            if row[3]:  # Check if choice _text is not NULL
                current_question.choices.append(Choice(choice_text=row[3], is_correct=row[4]))

        # Append the last question
        if current_question:
            questions.append(current_question)

    except Error as e:
        print(f"Error occurred: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return questions
