import sqlite3
import argparse
import csv
import contextlib
import logging
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from reportlab.lib.styles import getSampleStyleSheet

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

def add_question_to_pdf(pdf, question, style):
    paragraph = Paragraph(question.replace('\n', '<br/>'), style)
    pdf.append(paragraph)
    pdf.append(Spacer(0, 20))

def write_questions_to_file(db_file, file_format, output_file):
    # Define the SQL query to retrieve the questions
    query = "SELECT id, question FROM certification_questions"

    # Open the output file
    if file_format == "txt":
        file = open(output_file, "w")
    elif file_format == "csv":
        file = open(output_file, "w", newline="")
        writer = csv.writer(file)
        writer.writerow(["id", "question"])
    elif file_format == "pdf":
        pdf = SimpleDocTemplate(output_file, pagesize=landscape(letter))
        story = []
        style = getSampleStyleSheet()['BodyText']
        style.fontSize = 14
        style.leading = 20
    else:
        raise ValueError("Invalid file format")

    # Iterate over the questions and write them to the output file
    with sqlite_connection(db_file) as c:
        rows = c.execute(query)
        for row in rows:
            id = row[0]
            question = row[1]

            if file_format == "txt":
                file.write(f"{question}\n\n")
            elif file_format == "csv":
                writer.writerow([id,question])
            elif file_format == "pdf":
                add_question_to_pdf(story, question, style)

    # Close the output file
    if file_format == "pdf":
        pdf.build(story)
    else:
        file.close()

if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Export certification questions")
    parser.add_argument("db_file", help="the path to the SQLite database file")
    parser.add_argument("file_format", help="the format of the output file", choices=["txt", "csv", "pdf"])
    parser.add_argument("output_file", help="the path to the output file")
    args = parser.parse_args()

    # Write the questions to the output file
    write_questions_to_file(args.db_file, args.file_format, args.output_file)