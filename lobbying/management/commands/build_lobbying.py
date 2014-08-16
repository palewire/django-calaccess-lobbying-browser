import gc

from django.core.management.base import BaseCommand

try:
    from calaccess.models import (
        CvrLobbyDisclosureCd,
        FilernameCd,
        FilerFilingsCd,
        LccmCd,
        LexpCd,
    )
except:
    print "you need to load the raw calaccess data\
            using the django-calaccess-parser app in \
            order to populate this one"

from lobbying.models import (
    Client,
    Contribution,
    Filer,
    Filing,
    Gift,
    Relationship,
    LegislativeSession,
    Report
)


# I should be using the Django bulk_create method.
# In the campaign finance app too.
# see self.load_gifts below. something like that
# https://docs.djangoproject.com/en/dev/ref/models/querysets/#bulk-create
def queryset_iterator(queryset, chunksize=1000):
    '''
    Iterate over a Django Queryset ordered by the primary key

    This method loads a maximum of chunksize (default: 1000) rows in it's
    memory at the same time while django normally would load all rows in it's
    memory. Using the iterator() method only causes it to not preload all the
    classes.

    Note that the implementation of the iterator does not support
    ordered query sets.

    https://djangosnippets.org/snippets/1949/
    '''
    pk = 0
    last_pk = queryset.order_by('-pk')[0].pk
    queryset = queryset.order_by('pk')
    while pk < last_pk:
        for row in queryset.filter(pk__gt=pk)[:chunksize]:
            pk = row.pk
            yield row
        gc.collect()


class Command(BaseCommand):
    help = "Break out the recipient committee campaign finance data\
            from the CAL-ACCESS dump"

    def handle(self, *args, **options):
        # self.load_filers()
        # self.load_filings()
        # self.load_relationships()
        # self.load_gifts()
        # self.load_contributions()
        # # self.load_summary()
        # self.load_client()
        self.load_reports()

    def load_filers(self):
        '''
        Load up all the filer types associated with lobbying reports
        '''
        self.stdout.write('Loading lobbyist filers ...')
        i = 0
        bulk_records = []
        filer_id_list = list(
            FilernameCd
            .objects
            .filter(
                filer_type__in=['CLIENT', 'LOBBYIST',
                                'FIRM', 'EMPLOYER', 'PAYMENT TO INFLUENCE'])
            .values_list('filer_id', flat=True)
            .distinct()
        )

        for filer_id in filer_id_list:
            obj = FilernameCd.objects.filter(
                filer_id=filer_id).order_by('-effect_dt')[0]

            if obj.filer_type == 'CLIENT':
                f_type = 'c'
            elif obj.filer_type == 'LOBBYIST':
                f_type = 'l'
            elif obj.filer_type == 'FIRM':
                f_type = 'f'
            # organizations the employ in-house lobbyists i think
            elif obj.filer_type == 'EMPLOYER':
                f_type = 'e'

            insert = Filer()
            insert.filer_id_raw = filer_id
            insert.status = obj.status
            insert.filer_type = f_type
            insert.effective_date = obj.effect_dt
            insert.xref_filer_id = obj.xref_filer_id
            insert.name = (
                "{0} {1} {2} {3}"
                .format(
                    obj.namt,
                    obj.namf,
                    obj.naml,
                    obj.nams
                )
                .strip()
            )
            # insert.save()
            i += 1
            bulk_records.append(insert)
            if i % 5000 == 0:
                Filer.objects.bulk_create(bulk_records)
                print '%s records created ...' % i
                bulk_records = []
        if len(bulk_records) > 0:
            Filer.objects.bulk_create(bulk_records)
            bulk_records = []
            print '%s records created ...' % i

    def load_filings(self):
        '''
        Load up all the filings, using only
        the most recent amendment of a particular filing
        And before loading the filngs, make sure there is
        actually data associated with them
        '''
        self.stdout.write('Loading lobbyist filings ...')
        i = 0
        bulk_records = []
        for filer in Filer.objects.all():
            # get a list of all the filings on record
            all_filing_list = list(
                FilerFilingsCd
                .objects
                .filter(filer_id=filer.filer_id_raw)
                .values_list('filing_id', flat=True)
                .distinct()
            )

            # but just import the filings that we have data for. There are lots
            # of orphan filing records. they exist in the filngs table, but
            # have to data associated with them in the other tables.
            filing_list = list(
                CvrLobbyDisclosureCd
                .objects
                .filter(filing_id__in=all_filing_list)
                .values_list('filing_id', flat=True)
                .distinct()
            )
            # print 'filer_id_raw\tname\tall_filings\tfilings_with_data'
            # print '%s\t%s\t%s\t%s' % (filer.filer_id_raw, filer.name,
            # len(all_filing_list), len(filing_list))
            for filing_id in filing_list:
                filing = (
                    FilerFilingsCd
                    .objects
                    .filter(filing_id=filing_id)
                    .order_by('-filing_sequence')[0]
                )
                insert = Filing()
                insert.filer = filer
                insert.filing_id_raw = filing.filing_id
                insert.amend_id = filing.filing_sequence
                insert.form_id = filing.form_id
                insert.start_date = filing.rpt_start
                insert.end_date = filing.rpt_end
                insert.session_id = filing.session_id
                # insert.save()
                i += 1
                bulk_records.append(insert)
                if i % 5000 == 0:
                    Filing.objects.bulk_create(bulk_records)
                    print '%s records created ...' % i
                    bulk_records = []
        if len(bulk_records) > 0:
            Filing.objects.bulk_create(bulk_records)
            bulk_records = []
            print '%s records created ...' % i

    def load_relationships(self):
        '''
        For each Filer, decipher all the links tied
        to them inside the FilerLinksCd table
        '''
        self.stdout.write('Loading lobbyist relationships ...')
        i = 0
        bulk_records = []
        for f in Filer.objects.all():
            link_dict = f.links()
            for d in link_dict.values():
                insert = Relationship()
                insert.filer = f
                insert.related_filer_id_raw = d['filer_id_b']
                insert.related_filer_name = d['filer_name']
                insert.related_link_type = d['link_type']
                # insert.save()
                i += 1
                bulk_records.append(insert)
                if i % 5000 == 0:
                    Relationship.objects.bulk_create(bulk_records)
                    print '%s records created ...' % i
                    bulk_records = []
        if len(bulk_records) > 0:
            Relationship.objects.bulk_create(bulk_records)
            bulk_records = []
            print '%s records created ...' % i

    def load_gifts(self):
        '''
        The LexpCd table is full of what are called "Activity Expenses"
        I'm calling these "gifts" for short though they are not all presents.
        From the docs:
            Activity expenses include gifts, honoraria,
            consulting fees, salaries, and
            any other form of compensation, but do not include
            campaign contributions.
        '''
        self.stdout.write('Loading lobbyist gifts ...')
        i = 0  # Loop counter to trigger bulk saves
        bulk_records = []
        filing_id_list = list(
            LexpCd.objects.values_list('filing_id', flat=True).distinct())
        qs_filers = Filer.objects.filter(
            filing__filing_id_raw__in=filing_id_list).distinct()
        for filer_obj in qs_filers:
            for f in filer_obj.filing_set.all():
                qs = LexpCd.objects.filter(
                    filing_id=f.filing_id_raw, amend_id=f.amend_id)
                for q in qs:
                    insert = Gift()
                    insert.filing = f
                    insert.line_item = q.line_item
                    insert.rec_type = q.rec_type
                    insert.city = q.payee_city
                    insert.date = q.expn_date
                    insert.recsubtype = q.recsubtype
                    insert.entity_code = q.entity_cd
                    insert.memo_refno = q.memo_refno
                    insert.state = q.payee_st
                    insert.payment_amount = q.amount
                    insert.transaction_id = q.tran_id
                    insert.zip_code = q.payee_zip4
                    insert.recipient_position = q.bene_posit
                    insert.recipient_amount = q.bene_amt
                    insert.description = q.expn_dscr
                    insert.address1 = q.payee_adr1
                    insert.address2 = q.payee_adr2
                    insert.form_type = q.form_type
                    insert.recipient = q.bene_name

                    insert.payee = (
                        "{0} {1} {2} {3}"
                        .format(
                            q.payee_namt.encode('utf-8'),
                            q.payee_namf.encode('utf-8'),
                            q.payee_naml.encode('utf-8'),
                            q.payee_nams.encode('utf-8')
                        )
                        .strip()
                    )

                    insert.memo_code = q.memo_code
                    insert.back_reference_id = q.bakref_tid
                    # insert.save()
                    i += 1
                    bulk_records.append(insert)
                    if i % 5000 == 0:
                        Gift.objects.bulk_create(bulk_records)
                        print '%s records created ...' % i
                        bulk_records = []
        if i > 0:
            Gift.objects.bulk_create(bulk_records)
            print '%s records created ...' % i
            bulk_records = []

    def load_contributions(self):
        '''
        These are the campaign contributions that
        the lobbyists and firms reported donating
        '''
        self.stdout.write('Loading lobbyist contributions ...')
        i = 0
        bulk_records = []
        for f in Filing.objects.filter(
            form_id__in=[
                'F635', 'F615', 'F625', 'F645']):

            qs = LccmCd.objects.filter(
                filing_id=f.filing_id_raw, amend_id=f.amend_id)
            for q in qs:
                insert = Contribution()
                insert.filing = f
                insert.acct_name = q.acct_name
                insert.ctrib_date = q.ctrib_date

                insert.contributor_name = (
                    "{0} {1} {2} {3}"
                    .format(
                        q.ctrib_namt.encode('utf-8'),
                        q.ctrib_namf.encode('utf-8'),
                        q.ctrib_naml.encode('utf-8'),
                        q.ctrib_nams.encode('utf-8')
                    )
                    .strip()
                )

                insert.recip_adr2 = q.recip_adr2
                insert.bakref_tid = q.bakref_tid
                insert.line_item = q.line_item
                insert.entity_cd = q.entity_cd
                insert.tran_id = q.tran_id
                insert.recip_id = q.recip_id
                insert.memo_refno = q.memo_refno
                insert.rec_type = q.rec_type
                insert.amount = q.amount
                insert.memo_code = q.memo_code
                insert.recip_st = q.recip_st
                insert.recip_zip4 = q.recip_zip4
                insert.form_type = q.form_type
                insert.recip_adr1 = q.recip_adr1
                insert.recip_city = q.recip_city
                insert.recipient = (
                    "{0} {1} {2} {3}"
                    .format(
                        q.recip_namt.encode('utf-8'),
                        q.recip_namf.encode('utf-8'),
                        q.recip_naml.encode('utf-8'),
                        q.recip_nams.encode('utf-8')
                    )
                    .strip()
                )
                # insert.save()
                i += 1
                bulk_records.append(insert)
                if i % 5000 == 0:
                    Contribution.objects.bulk_create(bulk_records)
                    print '%s records created ...' % i
                    bulk_records = []
        if len(bulk_records) > 0:
            Contribution.objects.bulk_create(bulk_records)
            bulk_records = []
            print '%s records created ...' % i

    def load_summary(self):
        '''

        '''
        filing_list = list(
            CvrLobbyDisclosureCd
            .object
            .values_list('filing_id', flat=True)
            .distinct()
        )

        return filing_list

    def load_client(self):
        self.stdout.write('Loading clients ...')
        i = 0
        bulk_records = []

        # CLIENT (WHO IS AN EMPLOYER) OF A FIRM
        client_id_list = (
            Relationship
            .objects
            .filter(related_link_type='CLIENT OF A FIRM')
            .values_list('filer__filer_id_raw', flat=True)
            .distinct()
        )

        for client_id in client_id_list:
            obj = Filer.objects.get(filer_id_raw=client_id)
            insert = Client()
            insert.filer = obj
            insert.name = obj.name
            # insert.save()
            i += 1
            bulk_records.append(insert)
            if i % 5000 == 0:
                Client.objects.bulk_create(bulk_records)
                print '%s records created ...' % i
                bulk_records = []
        if len(bulk_records) > 0:
            Client.objects.bulk_create(bulk_records)
            bulk_records = []
            print '%s records created ...' % i

    def load_reports(self):  # Experimental
        self.stdout.write('Loading lobbyist periodic reports ...')
        i = 0
        bulk_records = []

        filing_id_amendment_pairs = Filing.objects.all().values('filing_id_raw', 'amend_id', 'filer__pk')

        filing_filers = {}
        amend_combos = {}
        for f in filing_id_amendment_pairs:

            if f['amend_id'] not in amend_combos:
                amend_combos[f['amend_id']] = []
            amend_combos[f['amend_id']].append(f['filing_id_raw'])

            filing_filers[f['filing_id_raw']] = f['filer__pk']

        print amend_combos.keys()

        for ak, av in amend_combos.iteritems():
            matchset = list(CvrLobbyDisclosureCd.objects.filter(
                filing_id__in=av,
                amend_id=ak
            ).values(
                'filing_id',
                'filer_naml',
                'filer_namf',
                'lby_actvty',
                'rpt_date',
                'from_date',
                'thru_date',
                'amend_id',
            ))

            for m in matchset:
                # try:
                insert = Report()
                insert.filer_id = filing_filers[m['filing_id']]
                insert.filing_id = m['filing_id']
                insert.amend_id = m['amend_id']
                insert.filer_lname = m['filer_naml']
                insert.filer_fname = m['filer_namf']
                insert.lobbying_description = m['lby_actvty']
                insert.report_date = m['rpt_date']
                insert.report_period_start = m['from_date']
                insert.report_period_end = m['thru_date']
                #insert.legislative_session = filing['']

                i += 1
                bulk_records.append(insert)
                if i % 5000 == 0:
                    print 'About to create %s ...' % i
                    Report.objects.bulk_create(bulk_records)
                    print '%s records created ...' % i
                    bulk_records = []
                # except:
                #     pass

        if len(bulk_records) > 0:
            print 'About to create %s ...' % i
            Report.objects.bulk_create(bulk_records)
            bulk_records = []
            print '%s records created ...' % i

        # for fa in filing_id_amendment_pairs:
        #     try:
        #         match = CvrLobbyDisclosureCd.objects.get(
        #             filing_id=fa['filing_id_raw'],
        #             amend_id=fa['amend_id']
        #         ).values(
        #             'filing_id',
        #             'filer_naml',
        #             'filer_namf',
        #             'lby_actvty',
        #             'rpt_date',
        #             'from_date',
        #             'thru_date',
        #             'amend_id',
        #         )

        #         insert = Report()
        #         insert.filer_id = filing_id_amendment_pairs['filer__pk']
        #         insert.filing_id = match['filing_id']
        #         insert.amend_id = match['amend_id']
        #         insert.filer_lname = match['filer_naml']
        #         insert.filer_fname = match['filer_namf']
        #         insert.lobbying_description = match['lby_actvty']
        #         insert.report_date = match['rpt_date']
        #         insert.report_period_start = match['from_date']
        #         insert.report_period_end = match['thru_date']
        #         #insert.legislative_session = filing['']

        #         i += 1
        #         bulk_records.append(insert)
        #         if i % 5000 == 0:
        #             Report.objects.bulk_create(bulk_records)
        #             print '%s records created ...' % i
        #             bulk_records = []
        #     except:
        #         pass

        # if len(bulk_records) > 0:
        #     Report.objects.bulk_create(bulk_records)
        #     bulk_records = []
        #     print '%s records created ...' % i


        #     report_matches.append()
        # # Find matching combinations in the raw cd
        # filing_list = list(
        #         CvrLobbyDisclosureCd
        #         .objects
        #         .filter(filing_id__in=all_filing_list)
        #         .values(
        #             'filing_id',
        #             'filer_naml',
        #             'filer_namf',
        #             'lby_actvty',
        #             'rpt_date',
        #             'from_date',
        #             'thru_date',
        #             'amend_id',
        #         )
        #     )

        # for filer in Filer.objects.all():
        #     # get a list of all the filings on record
        #     all_filing_list = list(
        #         FilerFilingsCd
        #         .objects
        #         .filter(filer_id=filer.filer_id_raw)
        #         .values_list('filing_id', flat=True)
        #         .distinct()
        #     )

        #     # but just import the filings that we have data for. There are lots
        #     # of orphan filing records. they exist in the filngs table, but
        #     # have to data associated with them in the other tables.
        #     filing_list = list(
        #         CvrLobbyDisclosureCd
        #         .objects
        #         .filter(filing_id__in=all_filing_list)
        #         .values(
        #             'filing_id',
        #             'filer_naml',
        #             'filer_namf',
        #             'lby_actvty',
        #             'rpt_date',
        #             'from_date',
        #             'thru_date',
        #             'amend_id',
        #         )
        #         .distinct()
        #     )

        #     #Speed this up by doing one query to get all the pks rather than running a new select for each row.
        #     filing_pairs = Filing.objects.filter(filing_id_raw__in=[f['filing_id'] for f in filing_list], amend_id__in=[f['amend_id'] for f in filing_list]).values('pk', 'filing_id_raw', 'amend_id')
            # Now make a lookup dictionary so you can get the filing pk by raw id
            # filing_lookup = {}
            # for f in filing_pairs:
            #     filing_lookup[f['filing_id_raw']] = f['pk']

            
