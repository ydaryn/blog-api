import pytz
from django.conf import settings
from django.utils import translation, timezone


SUPPORTED_LANGUAGES = ['en', 'ru', 'kk']


def _resolve_language(request):
    """
    Determine active language using priority order:
    1. Authenticated user's saved preferred_language
    2. ?lang= query parameter
    3. Accept-Language HTTP header
    4. DEFAULT_LANGUAGE from settings (fallback)
    """
    # 1. Authenticated user preference
    if hasattr(request, 'user') and request.user.is_authenticated:
        lang = getattr(request.user, 'preferred_language', None)
        if lang and lang in SUPPORTED_LANGUAGES:
            return lang

    # 2. ?lang= query param
    lang = request.GET.get('lang', '').lower()[:2]
    if lang in SUPPORTED_LANGUAGES:
        return lang

    # 3. Accept-Language header (take first preferred language)
    accept = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
    for token in accept.split(','):
        code = token.strip().split(';')[0].strip().lower()[:2]
        if code in SUPPORTED_LANGUAGES:
            return code

    # 4. Default
    return getattr(settings, 'DEFAULT_LANGUAGE', 'en')


class LanguageMiddleware:
    """
    Detect the correct language for each request using a 4-source priority chain
    and activate it so all gettext translations use the right language.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        lang = _resolve_language(request)
        translation.activate(lang)
        request.LANGUAGE_CODE = lang
        response = self.get_response(request)
        translation.deactivate()
        return response


class TimezoneMiddleware:
    """
    Activate the authenticated user's IANA timezone for each request
    so datetime rendering uses the correct local time.
    Anonymous requests use UTC.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tz_name = 'UTC'
        if hasattr(request, 'user') and request.user.is_authenticated:
            tz_name = getattr(request.user, 'timezone', 'UTC') or 'UTC'
        try:
            timezone.activate(pytz.timezone(tz_name))
        except Exception:
            timezone.activate(pytz.utc)
        response = self.get_response(request)
        timezone.deactivate()
        return response
