# app/management/commands/seed_django_tutorials.py
import json
from django.core.management.base import BaseCommand
from app.models import Tutorial, TutorialStep


class Command(BaseCommand):
    help = 'Seeds Django-specific tutorials for testing code validation'

    def handle(self, *args, **options):
        self.stdout.write('Seeding Django tutorials...')

        # ─── Find the next available order number ────────────────────────
        max_order = Tutorial.objects.aggregate(
            max_order=__import__('django.db.models', fromlist=['Max']).Max('order')
        )['max_order'] or 0

        # ═══════════════════════════════════════════════════════════════════
        #  TUTORIAL 1: Django Basics — Project Setup
        # ═══════════════════════════════════════════════════════════════════
        tutorial1, created = Tutorial.objects.get_or_create(
            title='Django Basics — Project Setup',
            defaults={
                'description': 'Learn how to set up a Django project from scratch: virtual environments, installing Django, and creating your first project.',
                'order': max_order + 1,
                'is_active': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'  Created tutorial: {tutorial1.title}'))
        else:
            self.stdout.write(f'  Tutorial already exists: {tutorial1.title}')

        # Step 1: Virtual Environments
        TutorialStep.objects.get_or_create(
            tutorial=tutorial1,
            order=1,
            defaults={
                'title': 'Create a Virtual Environment',
                'content': '''
                    <h3>🛡️ Virtual Environments</h3>
                    <p>Before installing Django, you need to create an <strong>isolated environment</strong> for your project.</p>
                    <p>A <strong>virtual environment (venv)</strong> keeps your project's packages separate from your system's global Python packages.</p>
                    <h4>Your Task:</h4>
                    <p>Type the command to create a virtual environment called <code>venv</code> using Python's built-in module.</p>
                    <p><strong>Hint:</strong> The command uses <code>python -m venv</code> followed by the name.</p>
                ''',
                'file_type': 'python',
                'initial_code': '# Create a virtual environment called "venv"\n# Type the command below:\n',
                'solution_code': '# Create a virtual environment called "venv"\n# Type the command below:\npython -m venv venv',
                'expected_elements': json.dumps([
                    'python -m venv venv'
                ]),
                'checkpoint_xp': 10,
                'trivia': 'The venv module was added to Python 3.3. Before that, developers used a third-party tool called virtualenv!',
            }
        )

        # Step 2: Install Django
        TutorialStep.objects.get_or_create(
            tutorial=tutorial1,
            order=2,
            defaults={
                'title': 'Install Django',
                'content': '''
                    <h3>📦 Installing Django</h3>
                    <p><strong>pip</strong> is Python's package manager — like an app store for Python libraries.</p>
                    <p>Always install Django <strong>inside your activated virtual environment</strong>, never globally.</p>
                    <h4>Your Task:</h4>
                    <p>Type the pip command to install Django.</p>
                ''',
                'file_type': 'python',
                'initial_code': '# Install the Django framework using pip\n# Type the command below:\n',
                'solution_code': '# Install the Django framework using pip\n# Type the command below:\npip install django',
                'expected_elements': json.dumps([
                    'pip install django'
                ]),
                'checkpoint_xp': 10,
                'trivia': 'Django was named after the jazz guitarist Django Reinhardt. It was created in 2003 at a newspaper in Kansas!',
            }
        )

        # Step 3: Start a Project
        TutorialStep.objects.get_or_create(
            tutorial=tutorial1,
            order=3,
            defaults={
                'title': 'Create a Django Project',
                'content': '''
                    <h3>🏗️ Starting a Django Project</h3>
                    <p>A <strong>Project</strong> is the entire web application system. An <strong>App</strong> is a feature module inside it.</p>
                    <p><code>django-admin startproject</code> creates the project skeleton with:</p>
                    <ul>
                        <li><code>manage.py</code> — your project's command center</li>
                        <li><code>settings.py</code> — project configuration</li>
                        <li><code>urls.py</code> — URL routing</li>
                    </ul>
                    <h4>Your Task:</h4>
                    <p>Type the command to create a new Django project called <code>mysite</code>.</p>
                ''',
                'file_type': 'python',
                'initial_code': '# Create a new Django project called "mysite"\n# Type the command below:\n',
                'solution_code': '# Create a new Django project called "mysite"\n# Type the command below:\ndjango-admin startproject mysite',
                'expected_elements': json.dumps([
                    'django-admin startproject mysite'
                ]),
                'checkpoint_xp': 15,
                'trivia': 'django-admin is the command-line utility that comes with Django. After creating a project, you use manage.py instead!',
            }
        )

        # Step 4: Create an App
        TutorialStep.objects.get_or_create(
            tutorial=tutorial1,
            order=4,
            defaults={
                'title': 'Create a Django App',
                'content': '''
                    <h3>🧩 Creating an App</h3>
                    <p>An app is a feature module inside your project. One project can have <strong>many apps</strong> (blog, users, api…).</p>
                    <p>After creating an app, you must <strong>register it</strong> in <code>INSTALLED_APPS</code> inside <code>settings.py</code>.</p>
                    <h4>Your Task:</h4>
                    <p>Type the command to create a new app called <code>blog</code> using <code>manage.py</code>.</p>
                ''',
                'file_type': 'python',
                'initial_code': '# Create a new Django app called "blog"\n# Type the command below:\n',
                'solution_code': '# Create a new Django app called "blog"\n# Type the command below:\npython manage.py startapp blog',
                'expected_elements': json.dumps([
                    'python manage.py startapp blog'
                ]),
                'checkpoint_xp': 15,
                'trivia': 'A single Django project at Instagram handles over 2 billion users — all powered by the same Project → App architecture you just learned!',
            }
        )

        # ═══════════════════════════════════════════════════════════════════
        #  TUTORIAL 2: Django Templates & Generic Views
        # ═══════════════════════════════════════════════════════════════════
        tutorial2, created = Tutorial.objects.get_or_create(
            title='Django Templates & Generic Views',
            defaults={
                'description': 'Master Django Template Language (DTL) tags like {% load static %}, {{ variables }}, and learn to use Generic Views like ListView and DetailView.',
                'order': max_order + 2,
                'prerequisite': tutorial1,
                'is_active': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'  Created tutorial: {tutorial2.title}'))
        else:
            self.stdout.write(f'  Tutorial already exists: {tutorial2.title}')

        # Step 1: Load Static & Block Tags
        TutorialStep.objects.get_or_create(
            tutorial=tutorial2,
            order=1,
            defaults={
                'title': 'Template Tags — Static Files & Blocks',
                'content': '''
                    <h3>🏷️ Django Template Tags</h3>
                    <p>Django templates use special tags to add logic to HTML:</p>
                    <ul>
                        <li><code>{%&nbsp;load static %}</code> — loads the static file system (CSS, JS, images)</li>
                        <li><code>{%&nbsp;block content %}</code> — defines an overridable section for template inheritance</li>
                        <li><code>{%&nbsp;endblock %}</code> — closes the block</li>
                    </ul>
                    <h4>Your Task:</h4>
                    <p>Complete the Django template below by adding <code>{%&nbsp;load static %}</code> at the top and wrapping the content in a <code>{%&nbsp;block content %}</code> / <code>{%&nbsp;endblock %}</code> pair.</p>
                ''',
                'file_type': 'django',
                'initial_code': '<!-- Add the load static tag here -->\n\n<!DOCTYPE html>\n<html>\n<head>\n    <title>My Blog</title>\n</head>\n<body>\n    <!-- Wrap this content in a block called "content" -->\n    <h1>Welcome to My Blog</h1>\n    <p>This is my first Django template.</p>\n    <!-- End the block here -->\n</body>\n</html>',
                'solution_code': '{% load static %}\n\n<!DOCTYPE html>\n<html>\n<head>\n    <title>My Blog</title>\n</head>\n<body>\n    {% block content %}\n    <h1>Welcome to My Blog</h1>\n    <p>This is my first Django template.</p>\n    {% endblock %}\n</body>\n</html>',
                'expected_elements': json.dumps([
                    '{% load static %}',
                    '{% block content %}',
                    '{% endblock %}'
                ]),
                'checkpoint_xp': 15,
                'trivia': 'Django\'s template language was designed to be used by designers, not just programmers. That\'s why it uses {% %} instead of Python code directly!',
            }
        )

        # Step 2: Template Variables & For Loop
        TutorialStep.objects.get_or_create(
            tutorial=tutorial2,
            order=2,
            defaults={
                'title': 'Template Variables & Loops',
                'content': '''
                    <h3>🔄 Variables & Loops in Templates</h3>
                    <p>Django templates can display data from views:</p>
                    <ul>
                        <li><code>{{&nbsp;variable }}</code> — outputs a variable's value</li>
                        <li><code>{%&nbsp;for item in items %}</code> — loops through a list</li>
                        <li><code>{%&nbsp;endfor %}</code> — ends the loop</li>
                    </ul>
                    <h4>Your Task:</h4>
                    <p>Complete the template to display a page title using <code>{{&nbsp;title }}</code> and list all blog posts using a <code>{%&nbsp;for %}</code> loop. Display each post's title with <code>{{&nbsp;post.title }}</code>.</p>
                ''',
                'file_type': 'django',
                'initial_code': '{% extends "base.html" %}\n\n{% block content %}\n<h1><!-- Display the title variable here --></h1>\n\n<div class="posts">\n    <!-- Loop through posts here -->\n        <article>\n            <h2><!-- Display post.title here --></h2>\n        </article>\n    <!-- End the loop here -->\n</div>\n{% endblock %}',
                'solution_code': '{% extends "base.html" %}\n\n{% block content %}\n<h1>{{ title }}</h1>\n\n<div class="posts">\n    {% for post in posts %}\n        <article>\n            <h2>{{ post.title }}</h2>\n        </article>\n    {% endfor %}\n</div>\n{% endblock %}',
                'expected_elements': json.dumps([
                    '{{ title }}',
                    '{% for',
                    '{{ post.title }}',
                    '{% endfor %}'
                ]),
                'checkpoint_xp': 15,
                'trivia': 'Django templates are sandboxed — you cannot execute arbitrary Python code in them. This is a security feature by design!',
            }
        )

        # Step 3: Generic Views — ListView
        TutorialStep.objects.get_or_create(
            tutorial=tutorial2,
            order=3,
            defaults={
                'title': 'Generic Views — ListView',
                'content': '''
                    <h3>📋 Generic Views: ListView</h3>
                    <p>Instead of writing view functions from scratch, Django provides <strong>Generic Views</strong> — pre-built classes that handle common patterns.</p>
                    <p><strong>ListView</strong> automatically:</p>
                    <ul>
                        <li>Fetches all objects from a model</li>
                        <li>Passes them to a template</li>
                        <li>Handles pagination</li>
                    </ul>
                    <h4>Your Task:</h4>
                    <p>Create a <code>BlogListView</code> class that inherits from <code>ListView</code>, sets the model to <code>Blog</code>, uses a custom template, and sets the context object name.</p>
                ''',
                'file_type': 'python',
                'initial_code': 'from django.views.generic import ListView\nfrom .models import Blog\n\n# Create a class-based view that lists all Blog posts\n# It should:\n# 1. Inherit from ListView\n# 2. Set model = Blog\n# 3. Set template_name = "blog/blog_list.html"\n# 4. Set context_object_name = "posts"\n\n',
                'solution_code': 'from django.views.generic import ListView\nfrom .models import Blog\n\n# Create a class-based view that lists all Blog posts\n# It should:\n# 1. Inherit from ListView\n# 2. Set model = Blog\n# 3. Set template_name = "blog/blog_list.html"\n# 4. Set context_object_name = "posts"\n\nclass BlogListView(ListView):\n    model = Blog\n    template_name = "blog/blog_list.html"\n    context_object_name = "posts"',
                'expected_elements': json.dumps([
                    'class BlogListView',
                    'ListView',
                    'model = Blog',
                    'template_name',
                    'context_object_name'
                ]),
                'checkpoint_xp': 20,
                'trivia': 'Generic Views were inspired by Ruby on Rails\' scaffolding. They can reduce a 20-line function view to just 4 lines!',
            }
        )

        # Step 4: Generic Views — DetailView
        TutorialStep.objects.get_or_create(
            tutorial=tutorial2,
            order=4,
            defaults={
                'title': 'Generic Views — DetailView',
                'content': '''
                    <h3>🔍 Generic Views: DetailView</h3>
                    <p><strong>DetailView</strong> displays a single object. It automatically:</p>
                    <ul>
                        <li>Looks up the object by primary key or slug</li>
                        <li>Returns a 404 if not found</li>
                        <li>Passes the object to the template</li>
                    </ul>
                    <h4>Your Task:</h4>
                    <p>Create a <code>BlogDetailView</code> that inherits from <code>DetailView</code>, sets the model to <code>Blog</code>, and uses a custom template.</p>
                ''',
                'file_type': 'python',
                'initial_code': 'from django.views.generic import DetailView\nfrom .models import Blog\n\n# Create a class-based view that shows a single Blog post\n# It should:\n# 1. Inherit from DetailView\n# 2. Set model = Blog\n# 3. Set template_name = "blog/blog_detail.html"\n\n',
                'solution_code': 'from django.views.generic import DetailView\nfrom .models import Blog\n\n# Create a class-based view that shows a single Blog post\n# It should:\n# 1. Inherit from DetailView\n# 2. Set model = Blog\n# 3. Set template_name = "blog/blog_detail.html"\n\nclass BlogDetailView(DetailView):\n    model = Blog\n    template_name = "blog/blog_detail.html"',
                'expected_elements': json.dumps([
                    'class BlogDetailView',
                    'DetailView',
                    'model = Blog',
                    'template_name'
                ]),
                'checkpoint_xp': 20,
                'trivia': 'DetailView automatically names the template variable "object" or the lowercase model name (e.g., "blog"). Use context_object_name to customize it!',
            }
        )

        # Step 5: URL Patterns for Generic Views
        TutorialStep.objects.get_or_create(
            tutorial=tutorial2,
            order=5,
            defaults={
                'title': 'URL Routing for Generic Views',
                'content': '''
                    <h3>🔗 Connecting Views to URLs</h3>
                    <p>Generic views must be connected to URL patterns using <code>.as_view()</code>.</p>
                    <p>The URL pattern for a DetailView typically uses <code>&lt;int:pk&gt;</code> to capture the post ID.</p>
                    <h4>Your Task:</h4>
                    <p>Complete the URL patterns to connect:</p>
                    <ul>
                        <li><code>''</code> (empty path) → <code>BlogListView</code></li>
                        <li><code>'post/&lt;int:pk&gt;/'</code> → <code>BlogDetailView</code></li>
                    </ul>
                ''',
                'file_type': 'python',
                'initial_code': 'from django.urls import path\nfrom .views import BlogListView, BlogDetailView\n\nurlpatterns = [\n    # Add the URL pattern for BlogListView at the root path\n    # Add the URL pattern for BlogDetailView at post/<int:pk>/\n]\n',
                'solution_code': "from django.urls import path\nfrom .views import BlogListView, BlogDetailView\n\nurlpatterns = [\n    path('', BlogListView.as_view(), name='blog_list'),\n    path('post/<int:pk>/', BlogDetailView.as_view(), name='blog_detail'),\n]\n",
                'expected_elements': json.dumps([
                    'BlogListView.as_view()',
                    'BlogDetailView.as_view()',
                    '<int:pk>'
                ]),
                'checkpoint_xp': 20,
                'trivia': 'The .as_view() method converts a class-based view into a callable function that Django\'s URL router can use. It\'s the bridge between classes and URL patterns!',
            }
        )

        self.stdout.write(self.style.SUCCESS('\n✅ Django tutorials seeded successfully!'))
        self.stdout.write(f'  Tutorial 1: {tutorial1.title} ({tutorial1.steps.count()} steps)')
        self.stdout.write(f'  Tutorial 2: {tutorial2.title} ({tutorial2.steps.count()} steps)')
