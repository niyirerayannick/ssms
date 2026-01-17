"""
Quick setup script for SIMS
Run: python setup.py
"""
import os
import sys
import subprocess

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"{'='*60}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return False

def main():
    print("SIMS - Setup Script")
    print("="*60)
    
    # Check if virtual environment is activated
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("\n⚠️  Warning: Virtual environment not detected.")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Please activate your virtual environment first.")
            sys.exit(1)
    
    # Install dependencies
    if not run_command("pip install -r requirements.txt", "Installing Python dependencies"):
        print("Failed to install dependencies. Please check requirements.txt")
        sys.exit(1)
    
    # Create migrations
    if not run_command("python manage.py makemigrations", "Creating database migrations"):
        print("Failed to create migrations.")
        sys.exit(1)
    
    # Run migrations
    if not run_command("python manage.py migrate", "Running database migrations"):
        print("Failed to run migrations. Please check your database configuration.")
        sys.exit(1)
    
    # Setup groups
    if not run_command("python manage.py setup_groups", "Setting up user groups and permissions"):
        print("Failed to setup groups.")
    
    # Setup Tailwind (optional)
    print("\n" + "="*60)
    print("Tailwind CSS Setup")
    print("="*60)
    response = input("Do you want to set up Tailwind CSS now? (y/n): ")
    if response.lower() == 'y':
        run_command("python manage.py tailwind install", "Installing Tailwind CSS")
        run_command("python manage.py tailwind build", "Building Tailwind CSS")
    
    print("\n" + "="*60)
    print("✅ Setup Complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Create a superuser: python manage.py createsuperuser")
    print("2. Run the development server: python manage.py runserver")
    print("3. Visit http://127.0.0.1:8000/ in your browser")
    print("\n" + "="*60)

if __name__ == "__main__":
    main()

