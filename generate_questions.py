import os
import openai
import sqlite3
import logging
import contextlib
import argparse
from dotenv import load_dotenv
import tiktoken
import regex as re

load_dotenv()  # Load environment variables from .env file

# Set up OpenAI API credentials
openai.api_key = os.environ.get("OPENAI_API_KEY")

#constant for chunk size
CHUNK_SIZE = 1024

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# Define the SQLite connection context manager
@contextlib.contextmanager
def sqlite_connection(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        yield cursor
    except Exception as e:
        logger.error(f"Error: {e}")
        conn.rollback()
    else:
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def main(doc_dir, learning_goals_file, question_format_file, db_file):
    # Load the learning goals from a file
    with open(learning_goals_file) as f:
        learning_goals = [line.strip() for line in f.readlines()]

    # Load the question format from a file
    with open(question_format_file) as f:
        question_format = f.read()

    # Create the certification questions table if it doesn't already exist
    with sqlite_connection(db_file) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS certification_questions (
                     id INTEGER PRIMARY KEY,
                     goal TEXT,
                     paragraph TEXT,
                     question TEXT
                     )""")

    # Iterate over the learning goals
    last_goal_id = None
    for goal in learning_goals:
        goal_id = re.search(r'\[(\d+)\]', goal).group(1) 

        # Query the related paragraphs from the SQLite database
        with sqlite_connection(db_file) as c:
            c.execute("SELECT text FROM paragraphs WHERE related_goals LIKE ?", ('%' + goal_id + '%',))
            paragraphs = c.fetchall()
        
        running_text = ""
        
        # Generate a certification question for each paragraph
        for paragraph in paragraphs:

            if len(paragraph[0].strip()) == 0: # TODO: needs a better solution
                continue

            running_text += paragraph[0]
            enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
            prompt_len = len(enc.encode(running_text))
            
            if prompt_len > CHUNK_SIZE or last_goal_id != goal_id and last_goal_id != None:
                try:
                    system_prompt = f"Act as an expert writer for a certification exam."
                    user_prompt = f' I will provide to with a format and some content and you should write a new exam question using the specified format but based on the content provided. Provide answers and an explanation for the question. Do not number the question.\nFormat:\n"""\n{question_format}\n"""\n\nContent:\n"""\n{running_text}\n"""'
                    completions = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ]
                    )
        
                    message = completions.choices[0]['message']['content']

                    # Store the question in the SQLite database
                    with sqlite_connection(db_file) as c:
                        c.execute("INSERT INTO certification_questions (goal, paragraph, question) VALUES (?, ?, ?)", (goal_id, paragraph[0], message))
                except Exception as e:
                    logger.error(f"Error: {e}")
                    logger.error(f"Failed to generate question for goal '{goal}' and paragraph '{paragraph[0]}'")

                # Log the result for debugging purposes
                logger.info(f"Generated question for goal '{goal_id}' and paragraph '{paragraph[0]}'")
                logger.info(f"Question: {message.strip()}")
                running_text = ""
        last_goal_id = goal_id
    # Log a message indicating that the script has finished
    logger.info("Finished generating certification questions")

if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Generate certification questions from paragraphs")
    parser.add_argument("doc_dir", help="the path to the directory containing the document files")
    parser.add_argument("learning_goals_file", help="the path to the file containing the learning goals")
    parser.add_argument("question_format_file", help="the path to the file containing the question format")
    parser.add_argument("db_file", help="the path to the SQLite database file")
    args = parser.parse_args()
    main(args.doc_dir,args.learning_goals_file,args.question_format_file, args.db_file)