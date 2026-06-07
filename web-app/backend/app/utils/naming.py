"""Naming helpers for auto-generated organization names and slugs."""
from slugify import slugify


def get_personal_org_name(display_name: str | None, email: str) -> str:
    """Generate a personal workspace name from user info.

    Examples:
        ('Ali Mert Ozdemir',  'foo@bar.com')  --> "Ali's Workspace"
        ('Acme GmbH',         'x@y.com')      --> "Acme's Workspace"
        (None,                'foo@bar.com')  --> "Foo's Workspace"
        ('',                  'foo@bar.com')  --> "Foo's Workspace"
    """
    source = (display_name or "").strip() or email.split("@")[0]
    parts = source.split()
    first_word = parts[0] if parts else "My"
    # Capitalize first letter, preserve rest (keeps accents intact).
    first_word = first_word[0].upper() + first_word[1:] if first_word else "My"
    return f"{first_word}'s Workspace"


def slugify_org_name(name: str) -> str:
    """Convert an org name into a URL-safe slug (matches organizations.slug VARCHAR(80)).

    Examples:
        "Ali's Workspace"            --> "ali-s-workspace"
        "Acme Property Mgmt GmbH"    --> "acme-property-mgmt-gmbh"
        "Izmir Yasar Muhendislik"    --> "izmir-yasar-muhendislik"
        "Foo & Bar, Inc."            --> "foo-and-bar-inc"
    """
    return slugify(name, max_length=80)
