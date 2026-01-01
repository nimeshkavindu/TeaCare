# create_admin.py
from passlib.context import CryptContext

# 1. Setup Argon2 (Same as your project)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# 2. Admin Credentials
admin_email = "admin@teacare.com"
admin_pass = "admin123"
admin_hash = pwd_context.hash(admin_pass)

# 3. Print the SQL Command
print("\n--- RUN THIS SQL COMMAND ---")
print(f"INSERT INTO users (full_name, email, role, password_hash, phone_number) VALUES ('System Admin', '{admin_email}', 'admin', '{admin_hash}', '0000000000');")
print("----------------------------\n")