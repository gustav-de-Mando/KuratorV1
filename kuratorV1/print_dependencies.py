def print_requirements():
    """
    Prints the required packages for the Empire IV Discord bot.
    """
    requirements = [
        "discord.py==2.5.2",
        "email-validator==2.2.0",
        "flask==3.1.0",
        "flask-sqlalchemy==3.1.1", 
        "google-api-python-client==2.166.0",
        "google-auth-httplib2==0.2.0",
        "google-auth-oauthlib==1.2.1",
        "gunicorn==23.0.0",
        "pillow==11.1.0",
        "psycopg2-binary==2.9.10",
        "python-dotenv==1.1.0",
        "python-magic==0.4.27"
    ]
    
    print("# Package Dependencies for Empire IV Discord Bot")
    print()
    for requirement in requirements:
        print(requirement)

if __name__ == "__main__":
    print_requirements()