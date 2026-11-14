from .models import AdminActionLog


def get_client_ip(request):
    """So'rov yuborgan mijozning IP manzilini aniqlash."""
    if not request:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def log_admin_action(request_or_user, action: str, target_obj, details: str = ""):
    """Moderator va Admin harakatini jurnalga qayd qilish."""
    user = None
    ip_address = None

    if hasattr(request_or_user, 'user'):
        user = request_or_user.user
        ip_address = get_client_ip(request_or_user)
    else:
        user = request_or_user

    AdminActionLog.objects.create(
        user=user if getattr(user, 'is_authenticated', False) else None,
        action=action,
        target_model=target_obj.__class__.__name__,
        target_id=getattr(target_obj, 'id', None),
        target_repr=str(target_obj)[:250],
        details=details,
        ip_address=ip_address,
    )

