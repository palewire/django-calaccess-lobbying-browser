from django.db import models
from django.core.urlresolvers import reverse
from django.utils.text import slugify


class Filer(models.Model):
    FILER_TYPE_OPTIONS = (
        ('c', 'Client'),
        ('e', 'Employer'),
        ('f', 'Firm'),
        ('l', 'Lobbyist'),
        ('p', 'Payment to Influence'),
    )
    # straight out of the filer table
    filer_id_raw = models.IntegerField()
    status = models.CharField(max_length=255, null=True)
    filer_type = models.CharField(max_length=10L, choices=FILER_TYPE_OPTIONS)
    effective_date = models.DateField(null=True)
    # fields updated by other tables
    xref_filer_id = models.CharField(max_length=32L, null=True)
    name = models.CharField(max_length=255L, null=True)

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('filer_detail', args=[str(self.pk)])

    def _create_slug(self):
        return slugify(self.name)

    slug = property(_create_slug)

    def links(self):
        d = {}
        from calaccess.models import FilerLinksCd, FilernameCd, LookupCode
        qs_links = FilerLinksCd.objects.filter(filer_id_a=self.filer_id_raw)
        for q in qs_links:
            qs_names = FilernameCd.objects.filter(
                filer_id=q.filer_id_b).order_by('-effect_dt').exclude(naml='')
            if qs_names.count() > 0:
                name_obj = qs_names[0]
                name = (name_obj.namt + ' ' + name_obj.namf + ' ' +
                        name_obj.naml + ' ' + name_obj.nams).strip()
                try:
                    description = LookupCode.objects.get(
                        code_id=q.link_type).code_desc
                except:
                    description = (
                        "failed to get a description for lookup code\
                         / link_type {0}"
                        .format(q.link_type)
                    )

                d[q.filer_id_b] = {
                    'link_type': description,
                    'filer_id_b': q.filer_id_b,
                    'filer_name': name,
                    'effective_date': q.effect_dt,
                }

        return d


class Filing(models.Model):
    filer = models.ForeignKey(Filer)
    filing_id_raw = models.IntegerField()
    amend_id = models.IntegerField()
    form_id = models.CharField(max_length=7)
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    session_id = models.IntegerField(null=True)
    dupe = models.BooleanField(default=False)

    def __unicode__(self):
        str_name = '%s (%s - %s)' % (self.filing_id_raw,
                                     self.start_date, self.end_date)
        return str_name

    def get_absolute_url(self):
        return reverse('filing_detail', args=[str(self.pk)])


class Summary(models.Model):  # comes from cover page
    pass


class Gift(models.Model):  # Activity Expenses in the parlance of the forms

    '''
    This model is the catchall for "activity expenses"
    reported on the various forms.
    I'm calling these "gifts" for short though they are not all presents.

    From the docs:
        Activity expenses include gifts, honoraria, consulting fees,
        salaries, and any other form of compensation, but do not include
        campaign contributions.

    '''
    filing = models.ForeignKey(Filing)
    recipient = models.CharField(max_length=255)
    recipient_position = models.CharField(max_length=255)
    recipient_amount = models.CharField(max_length=12)
    payee = models.CharField(max_length=255)
    payment_amount = models.DecimalField(max_digits=16, decimal_places=2)
    date = models.DateField(null=True)
    address1 = models.CharField(max_length=55L)
    address2 = models.CharField(max_length=55L)
    city = models.CharField(max_length=30L)
    state = models.CharField(max_length=2L)
    zip_code = models.CharField(max_length=10L)
    entity_code = models.CharField(max_length=3L)
    description = models.CharField(max_length=90L)
    # Back reference to the parent transaction id
    back_reference_id = models.CharField(max_length=20L)
    rec_type = models.CharField(max_length=4L)
    recsubtype = models.CharField(max_length=1L)
    transaction_id = models.CharField(max_length=20L)
    form_type = models.CharField(max_length=7L)
    line_item = models.IntegerField()
    # Field name made lowercase.
    memo_code = models.CharField(max_length=1L, null=True, blank=True)
    # Field name made lowercase.
    memo_refno = models.CharField(max_length=20L, null=True, blank=True)


class Contribution(models.Model):

    '''
    Campaign contributions that the lobbyist report giving
    '''
    filing = models.ForeignKey(Filing)
    acct_name = models.CharField(max_length=90L, blank=True)
    amount = models.DecimalField(max_digits=16, decimal_places=2)
    bakref_tid = models.CharField(max_length=20L, blank=True)
    ctrib_date = models.DateField(null=True)
    contributor_name = models.CharField(max_length=255, null=True, blank=True)
    entity_cd = models.CharField(max_length=3, blank=True)
    form_type = models.CharField(max_length=7L, blank=True)
    line_item = models.IntegerField()
    memo_code = models.CharField(max_length=1L, blank=True)
    memo_refno = models.CharField(max_length=20L, blank=True)
    rec_type = models.CharField(max_length=4L, blank=True)
    recipient = models.CharField(max_length=255, null=True, blank=True)
    recip_adr1 = models.CharField(max_length=55L, blank=True)
    recip_adr2 = models.CharField(max_length=55L, blank=True)
    recip_city = models.CharField(max_length=30L, blank=True)
    recip_id = models.CharField(max_length=9L, blank=True)
    recip_st = models.CharField(max_length=2L, blank=True)
    recip_zip4 = models.CharField(max_length=10L, blank=True)
    tran_id = models.CharField(max_length=20L, blank=True)


class Relationship(models.Model):

    '''
    Loops through each filer and records the
    filer's relationship to other filers
    '''
    filer = models.ForeignKey(Filer)
    # The CAL-ACCESS FILER_ID of the filer that's related to the ForeignKey
    # Filer in this model
    related_filer_id_raw = models.IntegerField()
    # The CAL-ACCESS name of the filer that's related to the ForeignKey Filer
    # in this model
    related_filer_name = models.CharField(max_length=255L, null=True)
    # Link type description
    related_link_type = models.CharField(max_length=255L, null=True)

    def __unicode__(self):
        return (
            '{0} -- {1} -- {2}'
            .format(
                self.filer.name,
                self.related_link_type,
                self.related_filer_name
            )
        )


class Client(models.Model):
    filer = models.ForeignKey(Filer)
    name = models.CharField(max_length=255)


class Firm(models.Model):
    filer = models.ForeignKey(Filer)
    name = models.CharField(max_length=255)


class Lobbyist(models.Model):
    filer = models.ForeignKey(Filer)
    name = models.CharField(max_length=255)
