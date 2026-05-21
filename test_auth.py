import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoquestbackend.settings')
django.setup()

from django.contrib.auth import get_user_model, authenticate
User = get_user_model()

print("Testing Authentication:")
for email in ["student@test.com", "teacher@test.com", "admin@admin.com"]:
    user = User.objects.filter(email=email).first()
    if user:
        print(f"\nUser: {email}")
        print(f"Is Active: {user.is_active}")
        print(f"Is Teacher: {user.is_teacher}")
        print(f"Is Student: {user.is_student}")
        
        # Test common passwords
        for pwd in ["admin123", "password123", "test1234", "password", "123456"]:
            if user.check_password(pwd):
                print(f"[!] Password is: {pwd}")
                # test authenticate()
                auth_user = authenticate(email=email, password=pwd)
                print(f"authenticate() returned: {auth_user}")
                break
        else:
            print("[?] Unknown password, cannot test authenticate().")
    else:
        print(f"User {email} not found.")
