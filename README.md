# DjangoQuest Backend

This is the Django REST Framework backend for the DjangoQuest platform. It handles user authentication, cloud saves, achievements, video tutorials, and admin management.

## Prerequisites
- Python 3.10+
- Git

## Getting Started

1. **Clone the repository**
   ```bash
   git clone <repository_url>
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

4. **Environment Setup**
   Create a `.env` file in the root directory (where `manage.py` is located) with the following basic configuration. You may need to add additional API keys depending on your feature usage (like AI keys):
   ```env
   SECRET_KEY=your_secret_key_here
   DEBUG=True
   ```

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
