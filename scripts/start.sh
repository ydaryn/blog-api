#!/bin/bash
set -euo pipefail

# ==========================================
# Colors & Helpers
# ==========================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()    { echo -e "${YELLOW}$*${NC}"; }
success() { echo -e "${GREEN}✓ $*${NC}"; }
error()   { echo -e "${RED}ERROR: $*${NC}" >&2; exit 1; }

# ==========================================
# Args
# ==========================================
SKIP_SEED=false
SKIP_STATIC=false
SKIP_SERVER=false

for arg in "$@"; do
  case $arg in
    --skip-seed)   SKIP_SEED=true ;;
    --skip-static) SKIP_STATIC=true ;;
    --no-server)   SKIP_SERVER=true ;;
    *) error "Unknown argument: $arg" ;;
  esac
done

# ==========================================
# Step 1: Check .env
# ==========================================
check_env() {
  info "Step 1: Checking environment variables..."

  [ -f ".env" ] || error ".env file not found!"

  set -a; source .env; set +a

  local required="SECRET_KEY BLOG_ENV_ID REDIS_HOST REDIS_PORT REDIS_DB
                  DJANGO_SUPERUSER_EMAIL DJANGO_SUPERUSER_PASSWORD"

  for var in $required; do
    [ -n "${!var:-}" ] || error "Missing required variable: $var"
  done

  success "Environment variables OK"
}

# ==========================================
# Step 2: Virtual environment
# ==========================================
setup_venv() {
  info "Step 2: Setting up virtual environment..."

  if [ ! -d "venv" ]; then
    python3 -m venv venv
    success "Virtual environment created"
  else
    success "Virtual environment already exists"
  fi

  # shellcheck source=/dev/null
  source venv/bin/activate
  pip install -r requirements/base.txt -q
  success "Dependencies installed"
}

# ==========================================
# Step 3: Django management commands
# ==========================================
setup_django() {
  cd backend

  info "Step 3: Running migrations..."
  python manage.py migrate --noinput
  success "Migrations done"

  if [ "$SKIP_STATIC" = false ]; then
    info "Step 4: Collecting static files..."
    python manage.py collectstatic --noinput
    success "Static files collected"
  fi

  info "Step 5: Compiling translations..."
  python manage.py compilemessages
  success "Translations compiled"

  info "Step 6: Creating superuser..."
  python manage.py shell -c "
from django.contrib.auth import get_user_model
import os
User = get_user_model()
email = os.environ['DJANGO_SUPERUSER_EMAIL']
if not User.objects.filter(email=email).exists():
    User.objects.create_superuser(
        email=email,
        first_name='Admin',
        last_name='User',
        password=os.environ['DJANGO_SUPERUSER_PASSWORD'],
    )
    print('Superuser created')
else:
    print('Superuser already exists')
"
  success "Superuser ready"

  if [ "$SKIP_SEED" = false ]; then
    info "Step 7: Seeding test data..."
    python manage.py seed_data
    success "Test data seeded"
  fi
}

# ==========================================
# Summary
# ==========================================
print_summary() {
  echo -e "${GREEN}"
  cat <<EOF
===========================================
  Blog API is ready!
===========================================
  API:      http://127.0.0.1:8000/api/
  Swagger:  http://127.0.0.1:8000/api/docs/
  ReDoc:    http://127.0.0.1:8000/api/redoc/
  Admin:    http://127.0.0.1:8000/admin/
-------------------------------------------
  Superuser: ${DJANGO_SUPERUSER_EMAIL}
===========================================
EOF
  echo -e "${NC}"
}

# ==========================================
# Main
# ==========================================
main() {
  echo -e "${GREEN}Starting Blog API setup...${NC}"
  check_env
  setup_venv
  setup_django
  print_summary

  if [ "$SKIP_SERVER" = false ]; then
    info "Step 8: Starting development server..."
    python manage.py runserver
  fi
}

main "$@"