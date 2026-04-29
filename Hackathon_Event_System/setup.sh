#!/bin/bash
# EventHub — Automated Setup Script
set -e

echo "======================================"
echo "  EventHub Setup Script"
echo "======================================"

# Create virtual environment
echo ""
echo "[1/6] Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "[2/6] Installing dependencies..."
pip install -q -r requirements.txt

# Run migrations
echo "[3/6] Running database migrations..."
cd event_system
python manage.py makemigrations
python manage.py migrate

# Create superuser (non-interactive)
echo "[4/6] Creating admin superuser (admin / admin123)..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@eventhub.com', 'admin123')
    print('  Superuser created.')
else:
    print('  Superuser already exists.')
"

# Seed sample events
echo "[5/6] Seeding sample events..."
python manage.py shell -c "
from core.models import Event
events = ['Hackathon', 'Tech Quiz', 'Coding Contest', 'Debugging Challenge']
for name in events:
    obj, created = Event.objects.get_or_create(name=name)
    if created:
        print(f'  Created event: {name}')
    else:
        print(f'  Already exists: {name}')
"

echo "[6/6] Setup complete!"
echo ""
echo "======================================"
echo "  Start the server:"
echo "  cd event_system"
echo "  python manage.py runserver"
echo ""
echo "  Admin: http://127.0.0.1:8000/admin"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo "  App:   http://127.0.0.1:8000/"
echo "======================================"
