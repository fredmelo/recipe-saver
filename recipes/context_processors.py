from .models import Tag


def sidebar_tags(request):
    if request.user.is_authenticated:
        return {'sidebar_tags': Tag.objects.filter(user=request.user).order_by('name')}
    return {'sidebar_tags': []}
