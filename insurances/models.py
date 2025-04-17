from django.db import models
from django.core.validators import EmailValidator, RegexValidator
from django.utils.translation import gettext_lazy as _


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))

    class Meta:
        abstract = True


class Insured(TimestampedModel):
    first_name = models.CharField(max_length=100, verbose_name=_('First Name'))
    last_name = models.CharField(max_length=100, verbose_name=_('Last Name'))
    email = models.EmailField(
        validators=[EmailValidator(message=_('Enter a valid email address.'))],
        blank=True,
        null=True,
        verbose_name=_('Email')
    )
    phone_number = models.CharField(
        max_length=11,
        validators=[RegexValidator(r'^09\d{9}$', message=_('Enter a valid Iranian mobile number.'))],
        verbose_name=_('Mobile Number')
    )
    national_id = models.CharField(max_length=10, unique=True, verbose_name=_('National ID'))
    birth_date = models.DateField(verbose_name=_('Birth Date'))
    father_name = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('Father Name'))
    place_of_issue = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('Place of Issue'))

    class Meta:
        verbose_name = _('Insured Personal Details')
        verbose_name_plural = _('Insured Personal Details')

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Insurer(TimestampedModel):
    name = models.CharField(max_length=100, verbose_name=_('Insurer Name'))
    unique_id = models.CharField(max_length=50, unique=True, verbose_name=_('Insurer Unique ID'))

    class Meta:
        verbose_name = _('Insurer')
        verbose_name_plural = _('Insurers')

    def __str__(self):
        return self.name


class Policyholder(TimestampedModel):
    name = models.CharField(max_length=100, verbose_name=_('Policyholder Name'))
    unique_id = models.CharField(max_length=50, unique=True, verbose_name=_('Policyholder Unique ID'))

    class Meta:
        verbose_name = _('Policyholder')
        verbose_name_plural = _('Policyholders')

    def __str__(self):
        return self.name


class Policy(TimestampedModel):
    unique_id = models.CharField(max_length=50, primary_key=True, verbose_name=_('Policy Unique ID'))
    insured = models.ForeignKey(
        Insured,
        on_delete=models.CASCADE,
        related_name='policies',
        verbose_name=_('Insured Person'))
    insurer = models.ForeignKey(Insurer, on_delete=models.PROTECT, related_name='policies', verbose_name=_('Insurer'))
    policyholder = models.ForeignKey(
        Policyholder,
        on_delete=models.PROTECT,
        related_name='policies',
        verbose_name=_('Policyholder'))
    start_date = models.DateField(verbose_name=_('Start Date'))
    end_date = models.DateField(verbose_name=_('End Date'))
    confirmation_date = models.DateField(blank=True, null=True, verbose_name=_('Confirmation Date'))

    class Meta:
        verbose_name = _('Policy')
        verbose_name_plural = _('Policies')
        unique_together = (('insured', 'insurer', 'policyholder', 'start_date'),)

    def __str__(self):
        return f"Policy {self.unique_id} for {self.insured}"


class Plan(TimestampedModel):
    policy = models.ForeignKey(Policy, on_delete=models.CASCADE, related_name='plans', verbose_name=_('Policy'))
    name = models.CharField(max_length=100, verbose_name=_('Plan Name'))
    unique_id = models.CharField(max_length=50, unique=True, verbose_name=_('Plan Unique ID'))

    class Meta:
        verbose_name = _('Plan')
        verbose_name_plural = _('Plans')

    def __str__(self):
        return self.name


class InsuredStatus(TimestampedModel):
    policy = models.ForeignKey(
        Policy,
        on_delete=models.CASCADE,
        related_name='insured_statuses',
        verbose_name=_('Policy'))
    unique_id = models.CharField(max_length=50, unique=True, verbose_name=_('Insured Unique ID'))

    class Meta:
        verbose_name = _('Insured Status')
        verbose_name_plural = _('Insured Statuses')

    def __str__(self):
        return f"Insured {self.unique_id}"
