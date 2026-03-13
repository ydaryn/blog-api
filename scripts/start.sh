#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# start.sh — take a freshly cloned repo from zero to a running dev server.
# Usage: bash scripts/start.sh
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_DIR/settings/.env"
ENV_EXAMPLE="$PROJECT_DIR/settings/.env.example"
VENV_DIR="$PROJECT_DIR/.venv"
DJANGO_SETTINGS="settings.base"

SUPERUSER_EMAIL="admin@blog.local"
SUPERUSER_PASSWORD="admin1234"
SUPERUSER_FIRST="Admin"
SUPERUSER_LAST="User"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

step() { echo -e "\n${CYAN}${BOLD}▶ $1${NC}"; }
ok()   { echo -e "${GREEN}✓ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠ $1${NC}"; }
die()  { echo -e "${RED}✗ FAILED at step: $1${NC}" >&2; exit 1; }

# ── Step 1: Validate environment variables ───────────────────────────────────
step "1/8 Checking environment variables"

if [[ ! -f "$ENV_FILE" ]]; then
    if [[ -f "$ENV_EXAMPLE" ]]; then
        warn ".env not found — copying from .env.example. Edit $ENV_FILE before proceeding."
        cp "$ENV_EXAMPLE" "$ENV_FILE"
    else
        die "No .env file found at $ENV_FILE and no .env.example to copy from."
    fi
fi

REQUIRED_VARS=(
    BLOG_SECRET_KEY
    BLOG_DEBUG
    BLOG_REDIS_URL
    BLOG_REDIS_HOST
    BLOG_REDIS_PORT
    BLOG_DEFAULT_LANGUAGE
    EMAIL_BACKEND
)

missing=0
while IFS= read -r line || [[ -n "$line" ]]; do
    # Skip blank lines and comments
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
    # Split on first = only
    key="${line%%=*}"
    value="${line#*=}"
    key="${key// /}"
    [[ -z "$key" ]] && continue
    export "$key=$value" 2>/dev/null || true
done < "$ENV_FILE"

for var in "${REQUIRED_VARS[@]}"; do
    val="${!var:-}"
    if [[ -z "$val" ]]; then
        echo -e "${RED}  Missing required variable: $var${NC}" >&2
        missing=$((missing + 1))
    fi
done

if [[ $missing -gt 0 ]]; then
    die "Environment validation ($missing variable(s) missing or empty)"
fi
ok "All required environment variables are set"

cd "$PROJECT_DIR"

# ── Step 2: Virtual environment & dependencies ───────────────────────────────
step "2/8 Creating virtual environment and installing dependencies"

if [[ ! -d "$VENV_DIR" ]]; then
    python3 -m venv "$VENV_DIR" || die "Virtual environment creation"
    ok "Virtual environment created"
else
    ok "Virtual environment already exists — skipping creation"
fi

source "$VENV_DIR/bin/activate"
pip install --quiet --upgrade pip
pip install --quiet -r requirements/base.txt || die "pip install"
ok "Dependencies installed"

export DJANGO_SETTINGS_MODULE="$DJANGO_SETTINGS"

# ── Step 3: Run migrations ───────────────────────────────────────────────────
step "3/8 Running database migrations"
python manage.py migrate --no-input || die "Database migrations"
ok "Migrations complete"

# ── Step 4: Collect static files ─────────────────────────────────────────────
step "4/8 Collecting static files"
python manage.py collectstatic --no-input --clear 2>/dev/null || die "Collect static files"
ok "Static files collected"

# ── Step 5: Compile translation files ────────────────────────────────────────
step "5/8 Compiling translation files"
python manage.py compilemessages 2>/dev/null || warn "compilemessages failed — translations may not work (gettext not installed?)"
ok "Translations compiled"

# ── Step 6: Create superuser ─────────────────────────────────────────────────
step "6/8 Creating superuser"
python manage.py shell << PYEOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='$SUPERUSER_EMAIL').exists():
    User.objects.create_superuser(
        email='$SUPERUSER_EMAIL',
        password='$SUPERUSER_PASSWORD',
        first_name='$SUPERUSER_FIRST',
        last_name='$SUPERUSER_LAST',
    )
    print('Superuser created.')
else:
    print('Superuser already exists — skipping.')
PYEOF
ok "Superuser ready"

# ── Step 7: Seed database ─────────────────────────────────────────────────────
step "7/8 Seeding database with test data"
python manage.py seed_data || die "Database seeding"
ok "Test data seeded"

# ── Step 8: Start development server ─────────────────────────────────────────
step "8/8 Starting development server"

echo ""
echo -e "${BOLD}${GREEN}════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${GREEN}  Blog API is running!${NC}"
echo -e "${BOLD}${GREEN}════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BOLD}API root:${NC}       http://127.0.0.1:8000/api/"
echo -e "  ${BOLD}Swagger UI:${NC}     http://127.0.0.1:8000/api/docs/"
echo -e "  ${BOLD}ReDoc:${NC}          http://127.0.0.1:8000/api/redoc/"
echo -e "  ${BOLD}Admin panel:${NC}    http://127.0.0.1:8000/admin/"
echo ""
echo -e "  ${BOLD}Superuser email:${NC}    $SUPERUSER_EMAIL"
echo -e "  ${BOLD}Superuser password:${NC} $SUPERUSER_PASSWORD"
echo ""
echo -e "${YELLOW}  Press Ctrl+C to stop the server.${NC}"
echo ""

python manage.py runserver || die "Development server"
