# Multiple Choice Question Generator (MCQGEN)

This project consists of three Python scripts that work together to classify, generate, and write out multiple choice questions based on a set of input documents and learning goals. The scripts use the GPT-3.5-turbo model from the OpenAI API for natural language processing tasks.

![Overview Diagram](https://github.com/lmlearning/LLMMultiChoiceCreator/blob/main/mcqgen.png)


## Requirements

* Python 3.6 or higher
* An OpenAI API key (sign up [here](https://beta.openai.com/signup/))
* The following Python packages:
  * openai
  * dotenv
  * tiktoken
  * reportlab

To install the required packages, run:

```bash
pip install openai python-dotenv tiktoken reportlab
```

## Usage

1. Create a `.env` file in the project directory with the following content:

```ini
OPENAI_API_KEY=your_openai_api_key_here
```

Replace `your_openai_api_key_here` with your actual OpenAI API key.

2. Prepare the input data:

* Create a directory containing one or more plain text files (`.txt`). Each file should contain a document with paragraphs separated by two newline characters (`\n\n`).
* Create a plain text file (`.txt`) containing the learning goals. Each goal should be on a separate line and have a unique number in square brackets at the beginning (e.g., `[1] Goal 1`).

3. Run the scripts in the following order:

### classify_document_paragraphs.py

```bash
python classify_document_paragraphs.py path_to_document_directory path_to_learning_goals_file path_to_sqlite_database_file
```

This script classifies the paragraphs in the input documents based on their related learning goals and stores the results in an SQLite database.

### generate_questions.py

```bash
python generate_questions.py path_to_document_directory path_to_learning_goals_file path_to_question_format_file path_to_sqlite_database_file
```

This script generates multiple choice questions for each related paragraph and stores them in the SQLite database. The question format should be provided in a separate plain text file (`.txt`).

### write_questions.py

```bash
python write_questions.py path_to_sqlite_database_file output_file_format path_to_output_file
```

This script writes the generated multiple choice questions to an output file in the specified format (`txt`, `csv`, or `pdf`).

## Example

Suppose we have the following files:

* `data/`: A directory containing plain text files with the input documents.
* `learning_goals.txt`: A file containing the learning goals.
* `question_format.txt`: A file containing the question format.

To generate multiple choice questions, run the following commands:

```bash
python classify_document_paragraphs.py data learning_goals.txt database.db
python generate_questions.py data learning_goals.txt question_format.txt database.db
python write_questions.py database.db pdf questions.pdf
```

This will generate a PDF file (`questions.pdf`) containing the multiple choice questions.
