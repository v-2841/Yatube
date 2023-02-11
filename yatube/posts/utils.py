from django.core.paginator import Paginator
from django.conf import settings


def paginator_func(request, post):
    paginator = Paginator(post, settings.POSTS_VIEW_NUM)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
