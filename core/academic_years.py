from core.models import AcademicYear


def get_academic_year_queryset():
    """Return academic years ordered with the active year first."""
    return AcademicYear.objects.order_by('-is_active', '-name')


def get_active_academic_year():
    """Return the currently active academic year, if any."""
    return get_academic_year_queryset().filter(is_active=True).first()


def get_default_academic_year():
    """Return the active academic year or the newest available year."""
    return get_active_academic_year() or get_academic_year_queryset().first()


def apply_default_academic_year_field(form, field_name):
    """Populate a year field queryset and default it on new/unbound forms."""

    field = form.fields.get(field_name)
    if not field:
        return

    years = get_academic_year_queryset()
    field.queryset = years

    if form.is_bound:
        return

    instance = getattr(form, 'instance', None)
    if instance is not None and getattr(instance, 'pk', None) and getattr(instance, f'{field_name}_id', None):
        return

    if form.initial.get(field_name) or field.initial:
        return

    default_year = get_default_academic_year()
    if default_year:
        field.initial = default_year
