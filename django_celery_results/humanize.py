"""Some helpers to humanize values."""

from datetime import datetime

from django.utils.timezone import now
from django.utils.translation import ugettext as _
from django.utils.translation import ungettext


def pluralize_year(n):
    """Return a string with the number of yeargs ago."""
    return ungettext(_('{num} year ago'), _('{num} years ago'), n)


def pluralize_month(n):
    """Return a string with the number of months ago."""
    return ungettext(_('{num} month ago'), _('{num} months ago'), n)


def pluralize_week(n):
    """Return a string with the number of weeks ago."""
    return ungettext(_('{num} week ago'), _('{num} weeks ago'), n)


def pluralize_day(n):
    """Return a string with the number of days ago."""
    return ungettext(_('{num} day ago'), _('{num} days ago'), n)


OLDER_CHUNKS = (
    (365.0, pluralize_year),
    (30.0, pluralize_month),
    (7.0, pluralize_week),
    (1.0, pluralize_day),
)


def naturaldate(date, include_seconds=False):
    """Convert datetime into a human natural date string."""
    if not date:
        return ''

    right_now = now()
    today = datetime(right_now.year, right_now.month,
                     right_now.day, tzinfo=right_now.tzinfo)
    delta = right_now - date
    delta_midnight = today - date

    days = delta.days
    hours = delta.seconds // 3600
    minutes = delta.seconds // 60
    seconds = delta.seconds

    if days < 0:
        return _('just now')

    if days == 0:
        if hours == 0:
            if minutes > 0:
                return ungettext(
                    _('{minutes} minute ago'),
                    _('{minutes} minutes ago'), minutes
                ).format(minutes=minutes)
            else:
                if include_seconds and seconds:
                    return ungettext(
                        _('{seconds} second ago'),
                        _('{seconds} seconds ago'), seconds
                    ).format(seconds=seconds)
                return _('just now')
        else:
            return ungettext(
                _('{hours} hour ago'), _('{hours} hours ago'), hours
            ).format(hours=hours)

    if delta_midnight.days == 0:
        return _('yesterday at {time}').format(time=date.strftime('%H:%M'))

    count = 0
    for chunk, pluralizefun in OLDER_CHUNKS:
        if days >= chunk:
            count = int(round((delta_midnight.days + 1) / chunk, 0))
            fmt = pluralizefun(count)
            return fmt.format(num=count)
