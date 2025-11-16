#!/bin/bash

# Wait for MySQL to be ready and responsive
wait_for_mysql() {
    echo "Checking if MySQL is ready..."
    
    # Wait for MySQL to accept connections with our credentials
    echo "Waiting for MySQL to be ready..."
    for i in {1..30}; do
        if python -c "import MySQLdb; MySQLdb.connect(host='db', user='django_user', passwd='django_password', db='yoga_flashcards')" 2>/dev/null; then
            echo "MySQL is ready and accepting connections!"
            return 0
        else
            echo "Waiting for MySQL... (attempt $i/30)"
            sleep 2
        fi
    done
    
    echo "MySQL failed to become ready within 60 seconds"
    return 1
}

# Start the backend services
echo "Starting Yoga Flashcards Backend..."

# Wait for database
wait_for_mysql || exit 1

# Run Django setup commands
echo "Running migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Seeding initial data..."
python manage.py seed_initial_data || echo "Warning: Initial data seeding failed or already exists"

echo "Starting Django development server..."
python manage.py runserver 0.0.0.0:8000
