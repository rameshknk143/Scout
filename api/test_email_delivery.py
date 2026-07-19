import os
import sys

# Load .env file
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
if os.path.exists(env_path):
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key, val = key.strip(), val.strip()
            # Only load from .env if not already set in the environment
            if val and not os.environ.get(key):
                os.environ[key] = val

# Import auth
import auth

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_email_delivery.py <recipient_email>")
        sys.exit(1)
        
    to_email = sys.argv[1]
    code = "123456"
    purpose = "signup"
    
    print("--- ScoutVeda Email Delivery Test ---")
    print(f"To: {to_email}")
    print(f"EMAIL_FROM: {auth.EMAIL_FROM}")
    print(f"RESEND_API_KEY set: {bool(auth.RESEND_API_KEY)}")
    print(f"SMTP_HOST: {auth.SMTP_HOST}")
    print(f"SMTP_PORT: {auth.SMTP_PORT}")
    print(f"SMTP_USER: {auth.SMTP_USER}")
    print(f"SMTP_SECURE: {auth.SMTP_SECURE}")
    print("-------------------------------------")
    
    res = auth.send_otp_email(to_email, code, purpose)
    print(f"Result: {res}")
    
if __name__ == "__main__":
    main()
