from collections import namedtuple
from datetime import datetime, timedelta

from django.db import models, connection
from dateutil.rrule import rrule, MONTHLY
from django.conf import settings
from django.utils.translation import ugettext as _

from camp_fin.templatetags.helpers import format_money
from camp_fin.decorators import check_date_params

class Candidate(models.Model):
    entity = models.ForeignKey("Entity", db_constraint=False)
    prefix = models.CharField(max_length=10, null=True)
    first_name = models.CharField(max_length=50, null=True)
    middle_name = models.CharField(max_length=50, null=True)
    last_name = models.CharField(max_length=50, null=True)
    suffix = models.CharField(max_length=10, null=True)
    business_phone = models.CharField(max_length=50, null=True)
    home_phone = models.CharField(max_length=50, null=True)
    address = models.ForeignKey("Address", null=True, db_constraint=False)
    status = models.ForeignKey("Status", null=True, db_constraint=False)
    date_added = models.DateTimeField(null=True)
    contact = models.ForeignKey("Contact", null=True, db_constraint=False)
    email = models.CharField(max_length=50, null=True)
    date_updated = models.DateTimeField(null=True)
    qual_candidate_id = models.IntegerField(null=True)
    deceased = models.CharField(max_length=3)
    
    full_name = models.CharField(max_length=500, null=True)
    
    slug = models.CharField(max_length=500, null=True)

    def __str__(self):
        return self.full_name
    
class PAC(models.Model):
    entity = models.ForeignKey("Entity", db_constraint=False)
    name = models.CharField(max_length=100)
    acronym = models.CharField(max_length=15, null=True)
    business_phone = models.CharField(max_length=20, null=True)
    home_phone = models.CharField(max_length=20, null=True)
    email = models.CharField(max_length=50, null=True)
    address = models.ForeignKey("Address", related_name="address", db_constraint=False, null=True)
    treasurer = models.ForeignKey("Treasurer", db_constraint=False, null=True)
    date_added = models.DateTimeField()
    status = models.ForeignKey("Status", db_constraint=False, null=True)
    contact = models.ForeignKey("Contact", db_constraint=False, null=True)
    date_updated = models.DateTimeField(null=True)
    bank_name = models.CharField(max_length=100, null=True)
    bank_phone = models.CharField(max_length=50, null=True)
    fax_number = models.CharField(max_length=50, null=True)
    bank_address = models.ForeignKey("Address", related_name="pac_bank_address", null=True, db_constraint=False)
    initial_balance = models.FloatField(null=True)
    initial_balance_from_self = models.NullBooleanField(null=True)
    initial_debt = models.FloatField(null=True)
    initial_debt_from_self = models.NullBooleanField(null=True)
    
    slug = models.CharField(max_length=500, null=True)

    def __str__(self):
        return self.name
    
    @property
    def full_name(self):
        # This is here so we can treat pacs and candidates the same in
        # templates
        return self.name

class Campaign(models.Model):
    status_choices = (
        ('active', _('Active')),
        ('dropout', _('Dropped out')),
        ('lost_primary', _('Lost primary'))
    )

    olddb_id = models.IntegerField(null=True)
    candidate = models.ForeignKey('Candidate', db_constraint=False, null=True)
    election_season = models.ForeignKey('ElectionSeason', db_constraint=False)
    office = models.ForeignKey('Office', db_constraint=False)
    division = models.ForeignKey('Division', db_constraint=False, null=True)
    district = models.ForeignKey('District', db_constraint=False, null=True)
    treasurer = models.ForeignKey('Treasurer', db_constraint=False, null=True)
    status = models.ForeignKey('CampaignStatus', db_constraint=False, null=True)
    date_added = models.DateTimeField()
    county = models.ForeignKey('County', db_constraint=False, null=True)
    political_party = models.ForeignKey('PoliticalParty', db_constraint=False)
    last_updated = models.DateTimeField(null=True)
    primary_election_winner_status = models.IntegerField(null=True)
    general_election_winner_status = models.IntegerField(null=True)
    bank_name = models.CharField(max_length=100, null=True)
    bank_phone = models.CharField(max_length=50, null=True)
    bank_address = models.ForeignKey("Address", related_name="campaign_bank_address", null=True, db_constraint=False)
    committee_name = models.CharField(max_length=100, null=True)
    committee_phone_1 = models.CharField(max_length=25, null=True)
    committee_phone_2 = models.CharField(max_length=25, null=True)
    committee_fax_number = models.CharField(max_length=25, null=True)
    committee_email = models.CharField(max_length=50, null=True)
    committee_address = models.ForeignKey('Address', related_name='committee_address', db_constraint=False, null=True)
    initial_balance = models.FloatField(null=True)
    initial_balance_from_self = models.NullBooleanField()
    initial_debt = models.FloatField(null=True)
    initial_debt_from_self = models.NullBooleanField()
    qual_campaign_id = models.IntegerField(null=True)
    biannual = models.NullBooleanField()
    from_campaign = models.ForeignKey('Campaign', db_constraint=False, null=True)
    active_race = models.ForeignKey('Race', db_constraint=False, null=True)
    race_status = models.CharField(max_length=25, default='active', choices=status_choices)

    def __str__(self):
        office = self.office.description

        if self.candidate:
            candidate_name = '{0} {1}'.format(self.candidate.first_name,
                                            self.candidate.last_name)
            return '{0} ({1})'.format(candidate_name, office)
        else:
            party = self.political_party.name
            return '{0} ({1})'.format(party, office)

    @check_date_params
    def filings(self, since=None):
        '''
        Return a queryset representing all filings in a given filing period.

        Accepts an optional filter argument, `since`, as a string representing a year
        (e.g. '2017'). If `since` is present, the method will restrict contributions
        to filings starting January 1st of that year. If `since` is not specified,
        the method will return all contributions ever recorded for this campaign.
        '''
        filings = self.candidate.entity.filing_set.all()

        if since:
            date = '{year}-01-01'.format(year=since)
            filings = filings.filter(filing_period__filing_date__gte=date)

        return filings

    @check_date_params
    def funds_raised(self, since=None):
        '''
        Total funds raised in a given filing period.

        Accepts optional filter argument `since` with the same requirements as
        all other methods on this class.
        '''
        entity_id = self.candidate.entity.id

        sum_contributions = '''
            SELECT COALESCE(SUM(amount), 0)
            FROM contributions_by_month
            WHERE entity_id = %s
        '''

        if since:
            sum_contributions += '''
                AND month >= '{year}-01-01'::date
            '''.format(year=since)

        cursor = connection.cursor()
        cursor.execute(sum_contributions, [entity_id])
        amount = cursor.fetchone()[0]

        return amount

    @check_date_params
    def expenditures(self, since=None):
        '''
        Total expenditures in a given filing period.

        Accepts optional filter argument `since` with the same requirements as
        all other methods on this class.
        '''
        entity_id = self.candidate.entity.id

        sum_expenditures = '''
            SELECT COALESCE(SUM(amount), 0)
            FROM expenditures_by_month
            WHERE entity_id = %s
        '''

        if since:
            sum_expenditures += '''
                AND month >= '{year}-01-01'::date
            '''.format(year=since)

        cursor = connection.cursor()
        cursor.execute(sum_expenditures, [entity_id])
        amount = cursor.fetchone()[0]

        return amount

    def share_of_funds(self, total=None):
        '''
        This campaign's share of some portion of total funds. Defaults to the
        portion of total funds raised in this campaign's active race.
        '''
        has_race = self.active_race is not None and self.active_race.total_funds > 0

        if not total:
            if has_race:
                total = self.active_race.total_funds
            else:
                return 0

        if has_race:
            percent = round(self.funds_raised(since=self.active_race.funding_period) /
                            total, 2)

            return round(percent * 100)
        else:
            return 0

    @property
    def cash_on_hand(self):
        '''
        Total amount of cash that a campaign has on hand at any given point in time.
        '''
        last_filing = self.filing_set.order_by('-date_closed').first()

        if last_filing:
            return last_filing.closing_balance
        else:
            return 0

    @property
    def is_winner(self):
        if getattr(self, 'race', False):
            # Since the `winner` relationship is OneToOne, the ability
            # to reverse access a `race` (distinct from `active_race`)
            # means that this campaign must be the winner
            return True
        else:
            return False

    @property
    def party_identifier(self):
        '''
        Return a shortened version of the Campaign's party.
        '''
        if self.political_party.name:
            if self.political_party.name == 'Democrat':
                return 'D'
            elif self.political_party.name == 'Republican':
                return 'R'
            else:
                return 'I'
        else:
            return None

    def get_status(self):
        '''
        Return the status for this campaign.
        '''
        return self.race_status

    def display_status(self):
        '''
        Show a verbose version of the status for this campaign, e.g. in a template.
        '''
        return dict(self.status_choices)[self.race_status]


class Race(models.Model):
    group = models.ForeignKey('RaceGroup', db_constraint=False, blank=True, null=True)
    office = models.ForeignKey('Office', db_constraint=False)
    division = models.ForeignKey('Division', db_constraint=False, blank=True, null=True)
    district = models.ForeignKey('District', db_constraint=False, blank=True, null=True)
    office_type = models.ForeignKey('OfficeType', db_constraint=False, blank=True, null=True)
    county = models.ForeignKey('County', db_constraint=False, blank=True, null=True)
    election_season = models.ForeignKey('ElectionSeason', db_constraint=False)
    winner = models.OneToOneField('Campaign', blank=True, null=True)

    class Meta:
        unique_together = ('district', 'division', 'office_type', 'county',
                           'office', 'election_season')

    def __str__(self):
        if self.year:
            default = '{year} Race for {office}'.format(year=self.year,
                                                        office=self.office)
            specific = '%s Race for {specifier} {office}' % str(self.year)
        else:
            default = 'Race for {office}'.format(office=self.office)
            specific = 'Race for {specifier} {office}'

        if self.office_type:
            if self.office_type.description in ('Statewide', 'Judicial'):
                return default

            elif (self.office_type.description in ('Legislative', 'Public Regulation Commission')
                and self.district is not None):

                return specific.format(specifier=self.district,
                                    office=self.office)

            elif self.office_type.description == 'County Offices' and self.county is not None:
                return specific.format(specifier=self.county,
                                    office=self.office)

            else:
                return default
        else:
            return default

    @property
    def campaigns(self):
        '''
        Return all campaigns involved in this race.
        '''
        return self.campaign_set.all()

    @property
    def sorted_campaigns(self):
        '''
        Return all campaigns involved in this race, in reverse order of how much
        money they've raised.
        '''
        return sorted([camp for camp in self.campaigns],
                      key=lambda camp: camp.funds_raised(since=self.funding_period),
                      reverse=True)

    @property
    def active_campaigns(self):
        '''
        Campaigns that are still active in this race.
        '''
        return sorted([camp for camp in self.campaigns if camp.get_status() == 'active'],
                      key=lambda camp: camp.funds_raised(since=self.funding_period),
                      reverse=True)

    @property
    def sorted_dropouts(self):
        '''
        Campaigns that have dropped out of this race, sorted by funds raised.
        '''
        return sorted([camp for camp in self.campaigns if camp.get_status() != 'active'],
                      key=lambda camp: camp.funds_raised(since=self.funding_period),
                      reverse=True)

    @property
    def num_candidates(self):
        '''
        Return the number of candidates involved in this race.
        '''
        return self.campaigns.count()

    @property
    def largest_contribution(self):
        '''
        Return the amount of funds raised for the largest campaign in this race.
        '''
        if self.num_candidates > 0:
            return self.sorted_campaigns[0].funds_raised(since=self.funding_period)
        else:
            return 0

    @property
    def year(self):
        '''
        If this race has an ElectionSeason, return the year of the race.
        Otherwise, return None.
        '''
        return getattr(self.election_season, 'year', None)

    @property
    def funding_period(self):
        '''
        If this race has an ElectionSeason, return the year that the funding
        period started. Otherwise, return None.
        '''
        if self.year:
            return str(int(self.year) - 1)
        else:
            return None

    @property
    def total_funds(self):
        '''
        Return the total amount of money raised in this race, aggreggated from
        the total contributions to each campaign during the election season.
        '''
        return sum(campaign.funds_raised(since=self.funding_period) for campaign in self.campaigns)

    @property
    def campaigns_by_party(self):
        '''
        Return a list of campaigns in this race, organized by party.
        '''
        campaigns = [
            ('democrat', self.campaign_set.filter(political_party__name='Democrat')),
            ('republican', self.campaign_set.filter(political_party__name='Republican')),
            ('other', self.campaign_set.exclude(political_party__name__in=['Democrat', 'Republican']))
        ]

        biggest_party = max(queryset.count() for party, queryset in campaigns)

        campaign_list = []
        for party, queryset in campaigns:
            if queryset.count() > 0:
                # Sort campaigns by funds raised
                formatted_campaigns = sorted([campaign for campaign in queryset],
                                             key=lambda camp: camp.funds_raised(since=self.year),
                                             reverse=True)
                if queryset.count() < biggest_party:
                    # Add empty campaigns so that the table rows will line up
                    formatted_campaigns += [{} for missing in range(biggest_party - queryset.count())]

                campaign_list.append((party, formatted_campaigns))

        return campaign_list


class RaceGroup(models.Model):
    short_title = models.CharField(max_length=50)
    full_title = models.CharField(max_length=50)
    description = models.CharField(max_length=250)

    def __str__(self):
        return self.full_title


class OfficeType(models.Model):
    description = models.CharField(max_length=50)

    def __str__(self):
        return self.description

class Office(models.Model):
    description = models.CharField(max_length=100)
    status = models.ForeignKey('Status', db_constraint=False)
    office_type = models.ForeignKey('OfficeType', db_constraint=False, null=True)
    
    def __str__(self):
        return self.description

class District(models.Model):
    office = models.ForeignKey('Office', db_constraint=False)
    name = models.CharField(max_length=25)
    status = models.ForeignKey('Status', db_constraint=False)

    def __str__(self):
        return self.name

class County(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class PoliticalParty(models.Model):
    name = models.CharField(max_length=25)

    def __str__(self):
        return self.name

class Transaction(models.Model):
    contact = models.ForeignKey('Contact', db_constraint=False, null=True)
    amount = models.FloatField(db_index=True)
    received_date = models.DateTimeField(db_index=True)
    date_added = models.DateTimeField()
    check_number = models.CharField(max_length=100, null=True)
    memo = models.TextField(null=True)
    description = models.CharField(max_length=75, null=True)
    transaction_type = models.ForeignKey('TransactionType', db_constraint=False)
    filing = models.ForeignKey('Filing', db_constraint=False)
    olddb_id = models.IntegerField(null=True)
    name_prefix = models.CharField(max_length=25, null=True)
    first_name = models.CharField(max_length=255, null=True)
    middle_name = models.CharField(max_length=255, null=True)
    last_name = models.CharField(max_length=255, null=True)
    suffix = models.CharField(max_length=15, null=True)
    company_name = models.CharField(max_length=255, null=True, db_index=True)
    address = models.CharField(max_length=255, null=True)
    city = models.CharField(max_length=100, null=True)
    state = models.CharField(max_length=25, null=True)
    zipcode = models.CharField(max_length=10, null=True)
    county = models.ForeignKey('County', db_constraint=False, null=True)
    country = models.CharField(max_length=100, null=True)
    contact_type = models.ForeignKey('ContactType', db_constraint=False, null=True)
    transaction_status = models.ForeignKey('Status', db_constraint=False, null=True)
    from_file_id = models.IntegerField(null=True)
    contact_type_other = models.CharField(max_length=25, null=True)
    occupation = models.CharField(max_length=255, null=True)
    expenditure_for_certified_candidate = models.NullBooleanField()
    
    full_name = models.CharField(max_length=500, null=True)

    def __str__(self):
        return self.full_name
    
    @property
    def transaction_subject(self):
        # This is here so that the API key makes a little more sense
        return self.filing

    @property
    def full_address(self):
        full_address = ''
        
        if self.address:
            full_address = '{}'.format(self.address)
        
        if self.city:
            full_address = '{0} {1}'.format(full_address, self.city)

        if self.state:
            full_address = '{0}, {1}'.format(full_address, self.state)

        if self.zipcode:
            full_address = '{0} {1}'.format(full_address, self.zipcode)

        return full_address.strip()

class TransactionType(models.Model):
    description = models.CharField(max_length=50)
    contribution = models.BooleanField()
    anonymous = models.BooleanField()
    
    def __str__(self):
        return self.description

class Loan(models.Model):
    contact = models.ForeignKey('Contact', db_constraint=False, null=True)
    status = models.ForeignKey('Status', db_constraint=False)
    date_added = models.DateTimeField()
    amount = models.FloatField()
    check_number = models.CharField(max_length=30, null=True)
    memo = models.CharField(max_length=500, null=True)
    received_date = models.DateTimeField()
    interest_rate = models.FloatField(null=True)
    due_date = models.DateTimeField(null=True)
    payment_schedule_id = models.IntegerField(null=True)
    filing = models.ForeignKey('Filing', db_constraint=False, null=True)
    olddb_id = models.IntegerField(null=True)
    name_prefix = models.CharField(max_length=25, null=True)
    first_name = models.CharField(max_length=255, null=True)
    middle_name = models.CharField(max_length=255, null=True)
    last_name = models.CharField(max_length=255, null=True)
    suffix = models.CharField(max_length=15, null=True)
    company_name = models.CharField(max_length=255, null=True)
    address = models.CharField(max_length=255, null=True)
    city = models.CharField(max_length=50, null=True)
    state = models.CharField(max_length=25, null=True)
    zipcode = models.CharField(max_length=10, null=True)
    county = models.ForeignKey('County', db_constraint=False, null=True)
    country = models.CharField(max_length=50, null=True)
    contact_type = models.ForeignKey('ContactType', db_constraint=False, null=True)
    from_file_id = models.IntegerField(null=True)
    contact_type_other = models.CharField(max_length=25, null=True)
    occupation = models.CharField(max_length=255, null=True)
    loan_transfer_date = models.DateTimeField(null=True)
    from_file_id = models.IntegerField(null=True)
    
    full_name = models.CharField(max_length=500, null=True)

    def __str__(self):
        return self.full_name
    
    @property
    def full_address(self):
        full_address = ''
        
        if self.address:
            full_address = '{}'.format(self.address)
        
        if self.city:
            full_address = '{0} {1}'.format(full_address, self.city)

        if self.state:
            full_address = '{0}, {1}'.format(full_address, self.state)

        if self.zipcode:
            full_address = '{0} {1}'.format(full_address, self.zipcode)

        if self.country:
            full_address = '{0} {1}'.format(full_address, self.country)

        return full_address.strip()

class LoanTransaction(models.Model):
    loan = models.ForeignKey('Loan', db_constraint=False)
    amount = models.FloatField()
    interest_paid = models.FloatField(null=True)
    transaction_date = models.DateTimeField()
    date_added = models.DateTimeField()
    check_number = models.CharField(max_length=50, null=True)
    memo = models.TextField(null=True)
    transaction_type = models.ForeignKey('LoanTransactionType', db_constraint=False)
    transaction_status = models.ForeignKey('Status', db_constraint=False)
    filing = models.ForeignKey('Filing', db_constraint=False)
    from_file_id = models.IntegerField(null=True)

    def __str__(self):
        return '{0} {1}'.format(self.transaction_type, 
                                format_money(self.amount))

class LoanTransactionType(models.Model):
    description = models.CharField(max_length=25)

    def __str__(self):
        return self.description

class SpecialEvent(models.Model):
    event_name = models.CharField(max_length=255, null=True)
    transaction_status = models.ForeignKey('Status', db_constraint=False)
    date_added = models.DateTimeField()
    event_date = models.DateField()
    admission_price = models.FloatField()
    attendance = models.IntegerField()
    location = models.CharField(max_length=255, null=True)
    description = models.TextField(null=True)
    sponsors = models.TextField(null=True)
    total_admissions = models.FloatField()
    anonymous_contributions = models.FloatField()
    total_expenditures = models.FloatField()
    filing = models.ForeignKey('Filing', db_constraint=False)
    olddb_id = models.IntegerField(null=True)
    address = models.CharField(max_length=255, null=True)
    city = models.CharField(max_length=100, null=True)
    zipcode = models.CharField(max_length=10, null=True)
    county = models.ForeignKey('County', db_constraint=False, null=True)
    country = models.CharField(max_length=50, null=True)
    from_file_id = models.IntegerField(null=True)

    def __str__(self):
        if self.event_name:
            return self.event_name
        else:
            return 'Event sponsored by {0} on {1}'.format(self.sponsors, 
                                                          self.event_date)

class Filing(models.Model):
    entity = models.ForeignKey('Entity', db_constraint=False)
    olddb_campaign_id = models.IntegerField(null=True)
    olddb_profile_id = models.IntegerField(null=True)
    filing_period = models.ForeignKey('FilingPeriod', db_constraint=False)
    status = models.ForeignKey('Status', db_constraint=False, null=True)
    date_added = models.DateTimeField()
    olddb_ethics_report_id = models.IntegerField(null=True)
    campaign = models.ForeignKey('Campaign', db_constraint=False, null=True)
    date_closed = models.DateTimeField()
    date_last_amended = models.DateTimeField(null=True)
    opening_balance = models.FloatField()
    total_contributions = models.FloatField()
    total_expenditures = models.FloatField()
    total_loans = models.FloatField(null=True)
    total_inkind = models.FloatField(null=True)
    total_unpaid_debts = models.FloatField(null=True)
    closing_balance = models.FloatField()
    total_debt_carried_forward = models.FloatField(null=True)
    total_debt_paid = models.FloatField(null=True)
    total_loans_forgiven = models.FloatField(null=True)
    pdf_report = models.CharField(max_length=1000, null=True)
    final = models.BooleanField()
    no_activity = models.BooleanField()
    supplement_count = models.IntegerField(null=True)
    total_supplemental_contributions = models.FloatField(null=True)
    edited = models.CharField(max_length=3)
    regenerate = models.NullBooleanField()

    def __str__(self):
        if self.campaign:
            return '{0} {1} {2}'.format(self.campaign.candidate.first_name,
                                        self.campaign.candidate.last_name,
                                        self.filing_period)
        else:
            return self.entity.pac_set.first().name

    @check_date_params
    def contributions(self, since=None):
        '''
        Return the contributions (as Transaction objects) represented by this filing,
        filtered by an optional year (the `since` parameter).

        We need this method because filing periods can span multiple years, so
        the `total_contributions` can't reliably disaggregate contributions that
        occurred in one year but were reported in the next.
        '''
        contributions = self.transaction_set.filter(transaction_type__contribution=True)

        if since:
            date = '{year}-01-01'.format(year=since)
            contributions = contributions.filter(received_date__gte=date)

        return contributions

    @check_date_params
    def loans(self, since=None):
        '''
        Return the loans (as LoanTransaction objects) represented by this filing.
        Same params and reasoning as the `contributions` method.
        '''
        desc = 'Payment'
        loans = self.loantransaction_set.filter(transaction_type__description=desc)

        if since:
            date = '{year}-01-01'.format(year=since)
            loans = loans.filter(transaction_date__gte=date)

        return loans

    @check_date_params
    def expenditures(self, since=None):
        '''
        Return the expenditures (as Transaction objects) represented by this filing.
        Same params and reasoning as the `contributions` method.
        '''
        desc = 'Monetary Expenditure'
        expenditures = self.transaction_set.filter(transaction_type__description=desc)

        if since:
            date = '{year}-01-01'.format(year=since)
            expenditures = expenditures.filter(received_date__gte=date)

        return expenditures


class FilingPeriod(models.Model):
    filing_date = models.DateTimeField()
    due_date = models.DateTimeField()
    olddb_id = models.IntegerField(null=True)
    description = models.CharField(max_length=255, null=True)
    allow_no_activity = models.BooleanField()
    filing_period_type = models.ForeignKey('FilingType', db_constraint=False)
    exclude_from_cascading = models.BooleanField()
    supplemental_init_date = models.DateTimeField(null=True)
    regular_filing_period = models.ForeignKey('RegularFilingPeriod', db_constraint=False, null=True)
    initial_date = models.DateField()
    email_sent_status = models.IntegerField()
    reminder_sent_status = models.IntegerField()
    
    def __str__(self):
        return '{0}/{1} ({2})'.format(self.filing_date.month, 
                                      self.filing_date.year,
                                      self.filing_period_type.description)

class Address(models.Model):
    street = models.CharField(null=True, max_length=255)
    city = models.CharField(null=True, max_length=255)
    state = models.ForeignKey('State', null=True, db_constraint=False)
    zipcode = models.CharField(null=True, max_length=10)
    county = models.ForeignKey('County', null=True, db_constraint=False)
    country = models.CharField(max_length=50, null=True)
    address_type = models.ForeignKey('AddressType', null=True, db_constraint=False)
    olddb_id = models.IntegerField(null=True)
    date_added = models.DateTimeField(null=True)
    from_file_id = models.IntegerField(null=True)

    def __str__(self):
        if self.street:
            street = self.street.strip()
            city = self.city.strip()
            state = str(self.state).strip()
            zipcode = self.zipcode.strip()

            address = '{0} {1}, {2} {3}'.format(street,
                                                city,
                                                state,
                                                zipcode)
        else:
            address = 'No address found'

        return address

class CampaignStatus(models.Model):
    description = models.CharField(max_length=10)

    def __str__(self):
        return self.description

class Division(models.Model):
    name = models.CharField(max_length=25)
    district = models.ForeignKey('District', db_constraint=False)
    status = models.ForeignKey('Status', db_constraint=False)

    def __str__(self):
        return self.name

class ElectionSeason(models.Model):
    year = models.CharField(max_length=5)
    special = models.BooleanField()
    status = models.ForeignKey('Status', db_constraint=False)

    def __str__(self):
        return 'Election year {}'.format(self.year)

class Entity(models.Model):
    user_id = models.IntegerField(null=True)
    entity_type = models.ForeignKey('EntityType', db_constraint=False, null=True)
    olddb_id = models.IntegerField(null=True)

    def __str__(self):
        return 'Entity {}'.format(self.entity_type)

    @check_date_params
    def trends(self, since='2010'):
        '''
        Generate a dict of filing trends for use in contribution/expenditure charts
        for this Entity.
        '''
        def stack_trends(trend):
            '''
            Private helper method for compiling trends.
            '''
            stacked_trend = []
            for begin, end, rate in trend:
                if not stacked_trend:
                    stacked_trend.append((rate, begin))
                    stacked_trend.append((rate, end))

                elif begin == stacked_trend[-1][1]:
                    stacked_trend.append((rate, begin))
                    stacked_trend.append((rate, end))

                elif begin > stacked_trend[-1][1]:
                    previous_rate, previous_end = stacked_trend[-1]
                    stacked_trend.append((previous_rate, begin))
                    stacked_trend.append((rate, begin))
                    stacked_trend.append((rate, end))

                elif begin < stacked_trend[-1][1]:
                    previous_rate, previous_end = stacked_trend.pop()
                    stacked_trend.append((previous_rate, begin))
                    stacked_trend.append((rate + previous_rate, begin))

                    if end < previous_end:
                        stacked_trend.append((rate + previous_rate, end))
                        stacked_trend.append((previous_rate, end))
                        stacked_trend.append((previous_rate, previous_end))

                    elif end > previous_end:
                        stacked_trend.append((rate + previous_rate, previous_end))
                        stacked_trend.append((rate, previous_end))
                        stacked_trend.append((rate, end))
                    else:
                        stacked_trend.append((rate + previous_rate, end))

            flattened_trend = []

            for i, point in enumerate(stacked_trend):
                rate, date = point
                flattened_trend.append([rate, *date])

            return flattened_trend

        # Balances and debts
        summed_filings = '''
            SELECT
              SUM(f.total_contributions) + \
                SUM(COALESCE(f.total_supplemental_contributions, 0)) AS total_contributions,
              SUM(f.total_expenditures) AS total_expenditures,
              SUM(COALESCE(f.total_loans, 0)) AS total_loans,
              SUM(COALESCE(f.total_unpaid_debts, 0)) AS total_unpaid_debts,
              SUM(f.closing_balance) AS closing_balance,
              SUM(f.opening_balance) AS opening_balance,
              SUM(f.total_debt_carried_forward) AS debt_carried_forward,
              fp.filing_date,
              MIN(fp.initial_date) AS initial_date
            FROM camp_fin_filing AS f
            JOIN camp_fin_filingperiod AS fp
              ON f.filing_period_id = fp.id
            WHERE f.entity_id = %s
              AND fp.exclude_from_cascading = FALSE
              AND fp.regular_filing_period_id IS NULL
              AND fp.filing_date >= '{year}-01-01'
            GROUP BY fp.filing_date
            ORDER BY fp.filing_date
        '''.format(year=since)

        cursor = connection.cursor()

        cursor.execute(summed_filings, [self.id])

        columns = [c[0] for c in cursor.description]
        filing_tuple = namedtuple('Filings', columns)

        summed_filings = [filing_tuple(*r) for r in cursor]

        balance_trend, debt_trend = [], []

        if summed_filings:

            for filing in summed_filings:
                filing_date = filing.filing_date
                date_array = [filing_date.year, filing_date.month, filing_date.day]
                debts = (-1 * filing.total_unpaid_debts)
                balance_trend.append([filing.closing_balance, *date_array])
                debt_trend.append([debts, *date_array])

            if summed_filings[0].opening_balance:
                first_opening_balance = summed_filings[0].opening_balance
            else:
                first_opening_balance = 0

            if summed_filings[0].debt_carried_forward:
                first_debt = summed_filings[0].debt_carried_forward
            else:
                first_debt = 0

            init_date = summed_filings[0].initial_date

            first_initial_date = [int(since), 1, 1]

            # If the first available filing date is on or before the start date
            # passed into this method, use that as the first date in the trendline
            if init_date:
                init_date_parts = [init_date.year, init_date.month, init_date.day]
                if datetime(*init_date_parts) <= datetime(*first_initial_date):
                    first_initial_date = init_date_parts

            debt_trend.insert(0, [first_debt, *first_initial_date])
            balance_trend.insert(0, [first_opening_balance, *first_initial_date])

        output_trends = {
            'balance_trend': balance_trend,
            'debt_trend': debt_trend
        }

        # Donations and expenditures
        monthly_query = '''
            SELECT
              {table}.amount AS amount,
              {table}.month AS month
            FROM {table}_by_month AS {table}
            WHERE {table}.entity_id = %s
              AND {table}.month >= '{year}-01-01'::date
            ORDER BY month
        '''

        contributions_query = monthly_query.format(table='contributions', year=since)
        expenditures_query = monthly_query.format(table='expenditures', year=since)

        cursor.execute(contributions_query, [self.id])

        columns = [c[0] for c in cursor.description]
        amount_tuple = namedtuple('Amount', columns)

        contributions = [amount_tuple(*r) for r in cursor]

        cursor.execute(expenditures_query, [self.id])

        columns = [c[0] for c in cursor.description]
        amount_tuple = namedtuple('Amount', columns)

        expenditures = [amount_tuple(*r) for r in cursor]

        donation_trend, expend_trend = [], []

        if contributions or expenditures:

            contributions_lookup = {r.month.date(): r.amount for r in contributions}
            expenditures_lookup = {r.month.date(): r.amount for r in expenditures}

            all_months = list(contributions_lookup.keys()) + list(expenditures_lookup.keys())

            start_month = datetime(int(since), 1, 1)
            end_month = settings.LAST_FILING_DATE

            for month in rrule(freq=MONTHLY, dtstart=start_month, until=end_month):

                replacements = {'month': month.month - 1}

                if replacements['month'] < 1:
                    replacements['month'] = 12
                    replacements['year'] = month.year - 1

                begin_date = month.replace(**replacements)

                begin_date_array = [begin_date.year,
                                    begin_date.month,
                                    begin_date.day]

                end_date_array = [month.year,
                                  month.month,
                                  month.day]

                contribution_amount = contributions_lookup.get(month.date(), 0)
                expenditure_amount = expenditures_lookup.get(month.date(), 0)

                donation_trend.append([begin_date_array, end_date_array, contribution_amount])
                expend_trend.append([begin_date_array, end_date_array, (-1 * expenditure_amount)])

            donation_trend = stack_trends(donation_trend)
            expend_trend = stack_trends(expend_trend)

        output_trends['donation_trend'] = donation_trend
        output_trends['expend_trend'] = expend_trend

        return output_trends


class EntityType(models.Model):
    description = models.CharField(max_length=25)

    def __str__(self):
        return self.description

class FilingType(models.Model):
    description = models.CharField(max_length=25)
    
    def __str__(self):
        return self.description

class Treasurer(models.Model):
    prefix = models.CharField(max_length=10, null=True)
    first_name = models.CharField(max_length=50, null=True)
    middle_name = models.CharField(max_length=50, null=True)
    last_name = models.CharField(max_length=50, null=True)
    suffix = models.CharField(max_length=10, null=True)
    business_phone = models.CharField(max_length=50, null=True)
    alt_phone = models.CharField(max_length=50, null=True)
    email = models.CharField(max_length=255, null=True)
    address = models.ForeignKey('Address', db_constraint=False)
    date_added = models.DateTimeField()
    status = models.ForeignKey('Status', db_constraint=False)
    olddb_entity_id = models.IntegerField(null=True)

    full_name = models.CharField(max_length=500, null=True)
    
    def __str__(self):
        return self.full_name

class Contact(models.Model):
    prefix = models.CharField(max_length=10, null=True)
    first_name = models.CharField(max_length=50, null=True)
    middle_name = models.CharField(max_length=50, null=True)
    last_name = models.CharField(max_length=50, null=True)
    suffix = models.CharField(max_length=10, null=True)
    occupation = models.CharField(max_length=100, null=True)
    address = models.ForeignKey('Address', db_constraint=False)
    phone = models.CharField(max_length=30, null=True)
    email = models.CharField(max_length=100, null=True)
    memo = models.TextField(null=True)
    company_name = models.CharField(max_length=255, null=True)
    contact_type = models.ForeignKey('ContactType', db_constraint=False)
    status = models.ForeignKey('Status', db_constraint=False)
    olddb_id = models.IntegerField(null=True)
    date_added = models.DateTimeField(null=True)
    entity = models.ForeignKey('Entity', db_constraint=False)
    from_file_id = models.IntegerField(null=True)

    full_name = models.CharField(max_length=500, null=True)
    
    def __str__(self):
        return self.full_name

class ContactType(models.Model):
    description = models.CharField(max_length=100)
    
    def __str__(self):
        return self.description

class State(models.Model):
    postal_code = models.CharField(max_length=2, null=True)
    
    def __str__(self):
        if self.postal_code:
            return self.postal_code
        return ''

class Story(models.Model):
    '''
    NMID stories that accompany candidates, campaigns, and races.
    '''

    class Meta:
        verbose_name_plural = 'stories'

    link = models.URLField()
    title = models.CharField(max_length=500)
    candidate = models.ManyToManyField('Candidate', blank=True)
    race = models.ManyToManyField('Race', blank=True)

class Lobbyist(models.Model):
    entity = models.ForeignKey("Entity", db_constraint=False)
    status = models.ForeignKey("Status", null=True, db_constraint=False)
    date_added = models.DateTimeField(null=True)
    prefix = models.CharField(max_length=10, null=True)
    first_name = models.CharField(max_length=50, null=True)
    middle_name = models.CharField(max_length=50, null=True)
    last_name = models.CharField(max_length=50, null=True)
    suffix = models.CharField(max_length=10, null=True)
    email = models.CharField(max_length=100, null=True)
    registration_date = models.DateTimeField(null=True)
    termination_date = models.DateTimeField(null=True)
    filing_period = models.ForeignKey("LobbyistFilingPeriod",
                                      db_constraint=False,
                                      null=True)
    permanent_address = models.ForeignKey("Address",
                                          related_name="lobbyist_permanent_address",
                                          null=True,
                                          db_constraint=False)
    lobbying_address = models.ForeignKey("Address",
                                         related_name="lobbyist_lobbying_address",
                                         null=True,
                                         db_constraint=False)
    contact = models.ForeignKey("Contact", db_constraint=False, null=True)
    phone = models.CharField(max_length=30, null=True)
    date_updated = models.DateTimeField(null=True)
    slug = models.CharField(max_length=500, null=True)

    @property
    def full_name(self):
        '''
        Return the full name of this lobbyist.
        '''
        name_parts = [self.prefix, self.first_name, self.middle_name,
                      self.last_name, self.suffix]

        return ' '.join(name for name in name_parts if name is not None)

    def __str__(self):
        return self.full_name

class LobbyistRegistration(models.Model):
    lobbyist = models.ForeignKey("Lobbyist", db_constraint=False)
    date_added = models.DateTimeField(null=True)
    year = models.CharField(max_length=5)
    is_registered = models.NullBooleanField(null=True)

class LobbyistEmployer(models.Model):
    lobbyist = models.ForeignKey("Lobbyist", db_constraint=False)
    organization = models.ForeignKey("Organization", db_constraint=False)
    date_added = models.DateTimeField(null=True)
    year = models.CharField(max_length=5)

class Organization(models.Model):
    entity = models.ForeignKey("Entity", db_constraint=False)
    date_added = models.DateTimeField(null=True)
    status = models.ForeignKey("Status", null=True, db_constraint=False)
    name = models.CharField(max_length=100)
    email = models.CharField(max_length=100, null=True)
    permanent_address = models.ForeignKey("Address",
                                          related_name="organization_permanent_address",
                                          null=True,
                                          db_constraint=False)
    contact = models.ForeignKey("Contact", db_constraint=False)
    date_updated = models.DateTimeField(null=True)
    phone = models.CharField(max_length=30, null=True)

class LobbyistFilingPeriod(models.Model):
    filing_date = models.DateTimeField(null=True)
    due_date = models.DateTimeField(null=True)
    description = models.CharField(max_length=100)
    allow_statement_of_no_activity = models.NullBooleanField(null=True)
    initial_date = models.DateTimeField(null=True)
    lobbyist_filing_period_type = models.ForeignKey("LobbyistFilingPeriodType", null=True, db_constraint=False)
    regular_filing_period =  models.ForeignKey("FilingPeriod", null=True, db_constraint=False)

class LobbyistTransaction(models.Model):
    lobbyist_report = models.ForeignKey("LobbyistReport", null=True, db_constraint=False)
    name = models.CharField(max_length=250, null=True)
    beneficiary = models.CharField(max_length=250, null=True)
    expenditure_purpose = models.CharField(max_length=250, null=True)
    lobbyist_transaction_type = models.ForeignKey("LobbyistTransactionType", null=True, db_constraint=False)
    received_date = models.DateTimeField(null=True)
    amount = models.FloatField()
    date_added = models.DateTimeField(null=True)
    transaction_status = models.ForeignKey("LobbyistTransactionStatus", null=True, db_constraint=False)

class LobbyistTransactionType(models.Model):
    description = models.CharField(max_length=100)
    group = models.ForeignKey("LobbyistTransactionGroup", null=True, db_constraint=False)

class LobbyistReport(models.Model):
    entity = models.ForeignKey("Entity", db_constraint=False)
    lobbyist_filing_period = models.ForeignKey("LobbyistFilingPeriod", null=True, db_constraint=False)
    status = models.ForeignKey("Status", null=True, db_constraint=False)
    date_added = models.DateTimeField(null=True)
    date_closed = models.DateTimeField(null=True)
    date_updated = models.DateTimeField(null=True)
    pdf_report = models.CharField(max_length=50)
    meal_beverage_expenses = models.FloatField()
    entertainment_expenses = models.FloatField()
    gift_expenses = models.FloatField()
    other_expenses = models.FloatField()
    special_event_expenses = models.FloatField()
    expenditures = models.FloatField()
    political_contributions = models.FloatField()

class LobbyistSpecialEvent(models.Model):
    lobbyist_report = models.ForeignKey("LobbyistReport", db_constraint=False)
    event_type = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    received_date = models.DateTimeField(null=True)
    amount = models.FloatField()
    groups_invited = models.CharField(max_length=2000, null=True)
    date_added = models.DateTimeField(null=True)
    transaction_status = models.ForeignKey("LobbyistTransactionStatus", null=True, db_constraint=False)

class LobbyistBundlingDisclosure(models.Model):
    destinatary_name = models.CharField(max_length=100)
    lobbyist_report = models.ForeignKey("LobbyistReport", db_constraint=False)
    date_added = models.DateTimeField(null=True)
    transaction_status = models.ForeignKey("LobbyistTransactionStatus", null=True, db_constraint=False)

class LobbyistBundlingDisclosureContributor(models.Model):
    bundling_disclosure = models.ForeignKey("LobbyistBundlingDisclosure", db_constraint=False)
    name = models.CharField(max_length=100)
    address = models.ForeignKey("Address",
                                related_name="lobbyist_bundling_disclosure_contributor_address",
                                null=True,
                                db_constraint=False)
    amount = models.FloatField()
    occupation = models.CharField(max_length=250, null=True)
    lobbyist_report = models.ForeignKey("LobbyistReport", null=True, db_constraint=False)

######################################################################
### Below here are normalized tables that we may or may not end up ###
### getting. Just stubbing them out in case we do                  ###
######################################################################

class RegularFilingPeriod(models.Model):
    pass

class Status(models.Model):
    pass

class AddressType(models.Model):
    pass

class LobbyistFilingPeriodType(models.Model):
    pass

class LobbyistTransactionStatus(models.Model):
    pass

class LobbyistTransactionGroup(models.Model):
    pass
