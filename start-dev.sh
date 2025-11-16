#!/bin/bash

# Yoga Flashcards Development Setup Script

echo "Setting up Yoga Flashcards development environment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if Docker Compose is available
if ! docker compose version &> /dev/null; then
    echo "Docker Compose is not installed. Please install Docker Compose and try again."
    exit 1
fi

echo "Docker is running"

# Build and start the services
echo "Building and starting services..."
docker compose up --build -d

echo "Waiting for services to be ready..."
sleep 30

# Check if services are running
if docker compose ps | grep -q "Up"; then
    echo "  Services are running!"
    echo ""
    echo "  Application URLs:"
    echo "   Frontend: http://localhost:9000"
    echo "   Backend API: http://localhost:8000"
    echo "   Django Admin: http://localhost:8000/admin"
    echo ""
    echo "  Default admin credentials:"
    echo "   Username: admin"
    echo "   Password: admin123"
    echo ""
    echo "  Showing logs (Ctrl+C to exit)..."
    echo "  To stop services: docker compose down"
    echo ""
    docker compose logs -f frontend backend
else
    echo "  Services failed to start. Check logs with: docker compose logs"
    exit 1
fi
