import os
import openai
import sqlite3
import logging
import contextlib
import argparse
from dotenv import load_dotenv
import regex as re

load_dotenv()  # Load environment variables from .env file

# Set up OpenAI API credentials
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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

def main(doc_dir, learning_goals_file, db_path):
    # Load the learning goals from a separate file
    with open(learning_goals_file, encoding="utf-8") as f:
        learning_goals = [line.strip() for line in f.readlines()]
        learning_goals_text = '\n'.join(learning_goals)

    # Create the SQLite table
    with sqlite_connection(db_path) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS paragraphs (
                     id INTEGER PRIMARY KEY,
                     doc_name TEXT,
                     para_num INTEGER,
                     text TEXT,
                     related_goals TEXT
                     )""")

    # Iterate through the text files in the directory
    for filename in os.listdir(doc_dir):
        if filename.endswith(".txt"):
            # Read the contents of the text file
            with open(os.path.join(doc_dir, filename), encoding="utf-8") as f:
                file_text = f.read()
            
            # Split the text into paragraphs
            paragraphs = file_text.split("\n\n")
            
            # Iterate through the paragraphs and determine related learning goals
            for i, paragraph in enumerate(paragraphs):
                # Use the OpenAI API to determine related learning goals
                try:
                    system_prompt = f"Act as an expert writer for a certification exam."
                    user_prompt = f"Which of the following learning goals if any does this paragraph relate to? Interpret the goals broadly. Answer with the number in square brackets.\n\nLearning goals:\n\"\"\"\n{learning_goals_text}\n\"\"\"\n\nParagraph:\n\"\"\"{paragraph}\n\"\"\""
                    completions = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ]
                    )
        
                    message = completions.choices[0]['message']['content']
                    # Extract the related learning goals from the response
                    related_goals = [re.search(r'\[(\d+)\]', goal).group(1) for goal in learning_goals if re.search(r'\[(\d+)\]', goal).group(1) in message]
                except Exception as e:
                    logger.error(f"Error: {e}")
                    related_goals = []

                # Store the results in the SQLite table
                with sqlite_connection(db_path) as c:
                    c.execute("INSERT INTO paragraphs (doc_name, para_num, text, related_goals) VALUES (?, ?, ?, ?)", (filename, i, paragraph, ", ".join(related_goals)))

                # Log the result for debugging purposes
                logger.info(f"Processed paragraph {i} in {filename}: {paragraph.strip()}")
                if related_goals:
                    logger.info(f"Related goals: {', '.join(related_goals)}")
                else:
                    logger.info("No related goals found")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("doc_dir", help="path to document directory")
    parser.add_argument("learning_goals_file", help="path to file containing learning goals")
    parser.add_argument("db_path", help="path to SQLite database file")
    args = parser.parse_args()
    main(args.doc_dir, args.learning_goals_file,args.db_path)