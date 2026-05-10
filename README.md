# DjangoQuest Backend

This is the Django REST Framework backend for the DjangoQuest platform. It handles user authentication, cloud saves, achievements, video tutorials, and admin management.

## How the Projects Connect
This platform has three main parts that work together:
1. **Backend (This Repository)**: The core database and server. It controls the logins, saves, and data.
2. **[Frontend Web Portal](https://github.com/7uisu/DjangoQuest-Frontend.git)**: The website where students can see their progress and teachers can manage classes.
3. **[Godot Game Client](https://github.com/7uisu/djangoquest_capstone_godot_project_revision.git)**: The 3D game. Players download this to actually play the coding game.

## Prerequisites
- Python 3.10+
- Git

## Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/7uisu/DjangoQuest-Backend.git
   cd DjangoQuest-Backend
   ```

2. **Create and Activate a Virtual Environment**
   ```bash
   # On macOS / Linux
   python3 -m venv venv
   source venv/bin/activate

   # On Windows
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Setup (.env file)**
   You need to create a special file called `.env` to hold secret passwords and keys. Create this file in the main folder (next to `manage.py`) and paste this inside:
   ```env
   SECRET_KEY=put_any_random_text_here
   DEBUG=True
   ```
   *(Note: This keeps the app safe. Never upload this file to GitHub!)*

5. **Run Migrations**
   Initialize the database (by default it uses SQLite for local development):
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create a Superuser (Optional but Recommended)**
   To access the Django Admin panel:
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the Development Server**
   ```bash
   python manage.py runserver
   ```
   The backend will now be available at `http://localhost:8000/`. Keep this terminal running!
