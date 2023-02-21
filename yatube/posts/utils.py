import datetime
import os
import IP2Location

from django.shortcuts import render
from django.core.paginator import Paginator
from django.conf import settings


TZ_OFFSET_TO_NAME = {
    '+14:00': 'Etc/GMT-14',
    '+13:00': 'Etc/GMT-13',
    '+12:00': 'Etc/GMT-12',
    '+11:00': 'Etc/GMT-11',
    '+10:00': 'Etc/GMT-10',
    '+09:00': 'Etc/GMT-9',
    '+08:00': 'Etc/GMT-8',
    '+07:00': 'Etc/GMT-7',
    '+06:00': 'Etc/GMT-6',
    '+05:00': 'Etc/GMT-5',
    '+04:00': 'Etc/GMT-4',
    '+03:00': 'Etc/GMT-3',
    '+02:00': 'Etc/GMT-2',
    '+01:00': 'Etc/GMT-1',
    '+00:00': 'Etc/GMT',
    '-01:00': 'Etc/GMT+1',
    '-02:00': 'Etc/GMT+2',
    '-03:00': 'Etc/GMT+3',
    '-04:00': 'Etc/GMT+4',
    '-05:00': 'Etc/GMT+5',
    '-06:00': 'Etc/GMT+6',
    '-07:00': 'Etc/GMT+7',
    '-08:00': 'Etc/GMT+8',
    '-09:00': 'Etc/GMT+9',
    '-10:00': 'Etc/GMT+10',
    '-11:00': 'Etc/GMT+11',
    '-12:00': 'Etc/GMT+12',
}


def paginator_func(request, post):
    paginator = Paginator(post, settings.POSTS_VIEW_NUM)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


def set_cookie(response, key, value, days_expire=7):
    if days_expire is None:
        max_age = 365 * 24 * 60 * 60  # one year
    else:
        max_age = days_expire * 24 * 60 * 60
    expires = datetime.datetime.strftime(
        datetime.datetime.utcnow() + datetime.timedelta(seconds=max_age),
        "%a, %d-%b-%Y %H:%M:%S GMT",
    )
    response.set_cookie(
        key,
        value,
        max_age=max_age,
        expires=expires,
        domain=settings.SESSION_COOKIE_DOMAIN,
        secure=settings.SESSION_COOKIE_SECURE or None,
    )
    return response


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def ip_timezone_cookie(request, template, context):
    database = IP2Location.IP2Location(os.path.join(
        settings.BASE_DIR, "ip_db", "IP2LOCATION-LITE-DB11.IPV6.BIN"))
    try:
        offset = database.get_timezone(get_client_ip(request))
    except Exception:
        offset = '+00:00'
    try:
        timezone = TZ_OFFSET_TO_NAME[offset]
    except Exception:
        timezone = 'Etc/GMT'
    context['timezone'] = timezone
    response = render(request, template, context)
    return set_cookie(response, 'timezone', timezone)
