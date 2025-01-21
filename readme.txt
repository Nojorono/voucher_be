# Project Setup

This project is built using Python and Django. Follow the steps below to set up the project.

## Prerequisites

- Python 3.x
- pip (Python package installer)
- virtualenv (optional but recommended)

## Setup Instructions

1. **Clone the repository:**

    ```sh
    git clone <repository_url>
    cd <repository_name>
    ```

2. **Create a virtual environment (optional but recommended):**

    ```sh
    python -m venv env
    source env/bin/activate  # On Windows use `env\Scripts\activate`
    ```

3. **Install the required packages:**

    ```sh
    pip install -r requirements.txt
    ```

4. **Apply migrations:**

    ```sh
    python manage.py migrate
    ```

5. **Run the development server:**

    ```sh
    python manage.py runserver
    ```

6. **Access the application:**

    Open your web browser and go to `http://127.0.0.1:8000/`.

## Folder Structure
