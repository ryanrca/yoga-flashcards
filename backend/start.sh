#!/bin/bash

# Wait for MySQL to be ready and responsive
wait_for_mysql() {
    echo "Checking if MySQL is ready..."
    
    # First, wait for MySQL port to be available
    echo "⏳ Waiting for MySQL port..."
    while ! nc -z db 3306; do
        sleep 1
    done
    echo "✅ MySQL port is available"
    
    # Then wait for MySQL to accept connections with our credentials
    echo "⏳ Waiting for MySQL authentication..."
    for i in {1..60}; do
        if mysql -h db -u django_user -pdjango_password -e "SELECT 1;" > /dev/null 2>&1; then
            echo "✅ MySQL is ready and accepting connections!"
            return 0
        else
            echo "⏳ Waiting for MySQL authentication... (attempt $i/60)"
            sleep 2
        fi
    done
    
    echo "❌ MySQL failed to become ready within 120 seconds"
    return 1
}

# Start the backend services
echo "🧘 Starting Yoga Flashcards Backend..."

# Wait for database
wait_for_mysql || exit 1

# Run Django setup commands
echo "📚 Running migrations..."
python manage.py migrate

echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

echo "🌱 Seeding initial data..."
python manage.py seed_initial_data || echo "Warning: Initial data seeding failed or already exists"

echo "🚀 Starting Django development server..."
python manage.py runserver 0.0.0.0:8000
