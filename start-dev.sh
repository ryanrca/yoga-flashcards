#!/bin/bash

echo "🧘 Starting Yoga Flashcards Admin App..."
echo ""

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is required but not installed."
    echo "Please install Docker and Docker Compose to continue."
    exit 1
fi

# Stop any existing services
echo "🛑 Stopping any existing services..."
docker-compose down

# Build and start the services
echo "🐳 Building and starting Docker services..."
docker-compose up --build -d

echo ""
echo "⏳ Waiting for services to be ready..."

# Wait for backend to be ready
echo "Waiting for backend..."
timeout=60
counter=0
until docker-compose exec -T backend python -c "import django; django.setup(); from django.db import connection; connection.ensure_connection()" 2>/dev/null; do
    if [ $counter -ge $timeout ]; then
        echo "❌ Backend failed to start within ${timeout} seconds"
        echo "Check logs with: docker-compose logs backend"
        exit 1
    fi
    sleep 1
    counter=$((counter + 1))
done

# Wait for frontend to be ready
echo "Waiting for frontend..."
timeout=60
counter=0
until curl -s http://localhost:9000 > /dev/null 2>&1; do
    if [ $counter -ge $timeout ]; then
        echo "❌ Frontend failed to start within ${timeout} seconds"
        echo "Check logs with: docker-compose logs frontend"
        exit 1
    fi
    sleep 1
    counter=$((counter + 1))
done

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo ""
    echo "✅ Services are running!"
    echo ""
    echo "🌐 Access the application:"
    echo "  Frontend: http://localhost:9000"
    echo "  Backend API: http://localhost:8000"
    echo "  Django Admin: http://localhost:8000/admin"
    echo ""
    echo "🔑 Default login credentials:"
    echo "  Username: admin"
    echo "  Password: admin123"
    echo ""
    echo "📁 To import sample data:"
    echo "  docker-compose exec backend python manage.py import_cards sample-cards.csv"
    echo ""
    echo "📝 To stop the services, run:"
    echo "  docker-compose down"
    echo ""
    echo "📊 To view logs, run:"
    echo "  docker-compose logs -f"
else
    echo "❌ Services failed to start. Check the logs with:"
    echo "  docker-compose logs"
fi
