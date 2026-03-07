from django import template

register = template.Library()

@register.filter

def can_edit(post, user):
    """Return True if *user* may edit *post*.

    This just delegates to :meth:`Post.can_edit` so the logic stays on the model.
    """
    if user is None:
        return False
    try:
        return post.can_edit(user)
    except Exception:
        return False
