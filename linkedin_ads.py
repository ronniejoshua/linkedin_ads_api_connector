import requests
import re
import datetime as dt


class LinkedInReporting(object):

    def __init__(self, access_token):
        """
        """
        self.access_token = access_token
        self.headers = {'Connection': 'Keep-Alive',
                        'Authorization': 'Bearer {}'.format(self.access_token)}
        self.BASE = 'https://api.linkedin.com/v2/'
        self._insert_time = dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    def get_account_ids(self, accounts_req: list) -> dict:
        """
        :param accounts_req:
        :return:
        """
        PATH = 'adAccountsV2'
        URI = self.BASE + PATH
        payload = {
            'q': 'search',
            'sort.field': 'ID',
            'sort.order': 'DESCENDING'
        }

        search_status_values = ['CANCELED', 'ACTIVE']
        for idx, val in enumerate(search_status_values):
            payload['search.status.values[{}]'.format(idx)] = str(val)

        search_type_values = ['BUSINESS', 'ENTERPRISE']
        for idx, val in enumerate(search_type_values):
            payload['search.type.values[{}]'.format(idx)] = str(val)

        r = requests.get(URI, params=payload,
                         headers=self.headers)

        acc_dict = {}
        for idx in range(0, len(r.json()['elements'])):
            acc_dict[r.json()['elements'][idx]['id']] = r.json()['elements'][idx]['name']

        return {a_num: a_name for (a_num, a_name) in acc_dict.items() if a_num in accounts_req}

    def get_campaign_ids(self, accounts_req: list) -> list:
        """
        :param accounts_req:
        :return:
        """
        PATH = 'adCampaignsV2'
        URI = self.BASE + PATH
        payload = {
            'q': 'search',
            'sort.field': 'ID',
            'sort.order': 'DESCENDING'
        }
        linkedin_accs = self.get_account_ids(accounts_req)
        for idx, acc in enumerate(list(linkedin_accs)):
            payload['search.account.values[{}]'.format(
                idx)] = 'urn:li:sponsoredAccount:{}'.format(acc)

        r = requests.get(URI, params=payload, headers=self.headers)
        json_obj = r.json()
        return [json_obj['elements'][i]['id'] for i in range(len(json_obj['elements']))]

    def get_campaign_dictionary(self, accounts_req: list) -> list:
        campaign_dictionary = list()
        total_paging, start_paging, count_paging = 0, 0, 100
        PAGING = True
        while PAGING:
            PATH = 'adCampaignsV2'
            URI = self.BASE + PATH
            payload = {
                'q': 'search',
                'sort.field': 'ID',
                'sort.order': 'DESCENDING',
                'start': start_paging,
                'count': count_paging
            }
            linkedin_accs = self.get_account_ids(accounts_req)
            for idx, acc in enumerate(list(linkedin_accs)):
                payload['search.account.values[{}]'.format(
                    idx)] = 'urn:li:sponsoredAccount:{}'.format(acc)
            r = requests.get(URI, params=payload, headers=self.headers)
            for dd in r.json()['elements']:
                req_dd = {
                    '_insert_time': self._insert_time,
                    'account_id': int(re.findall(r'\d+', dd.get('account'))[0]),
                    'account_name': linkedin_accs.get(int(re.findall(r'\d+', dd.get('account'))[0])),
                    'campaign_id': dd.get('id'),
                    'campaign_name': dd.get('name'),
                    'format': dd.get('format'),
                    'servingStatuses': str(dd.get('servingStatuses')),
                    'type': dd.get('type'),
                    'objectiveType': dd.get('objectiveType'),
                    'optimizationTargetType': dd.get('optimizationTargetType'),
                    'campaignGroup_id': int(re.findall(r'\d+', dd.get('campaignGroup'))[0]),
                    'dailyBudget': int(dd.get('dailyBudget').get('amount')) if dd.get(
                        'dailyBudget') is not None else None,
                    'costType': dd.get('costType'),
                    'creativeSelection': dd.get('creativeSelection'),
                    'offsiteDeliveryEnabled': dd.get('offsiteDeliveryEnabled'),
                    'audienceExpansionEnabled': dd.get('audienceExpansionEnabled'),
                    'status': dd.get('status')
                }
                campaign_dictionary.append(req_dd)
            total_paging = r.json()['paging']['total']
            start_paging = r.json()['paging']['start']
            count_paging = r.json()['paging']['count']
            print(total_paging, start_paging, count_paging)
            if total_paging <= count_paging:
                PAGING = False
            else:
                start_paging, count_paging = count_paging, count_paging + 10
        return campaign_dictionary

    def get_creative_dictionary(self, accounts_req: list) -> list:
        creative_dictionary = list()
        total_paging, start_paging, count_paging = 0, 0, 100
        PAGING = True
        while PAGING:
            PATH = 'adCreativesV2'
            URI = self.BASE + PATH
            list_campaigns = self.get_campaign_ids(accounts_req)
            payload = {
                'q': 'search',
                'sort.field': 'ID',
                'sort.order': 'DESCENDING',
                'start': start_paging,
                'count': count_paging
            }
            for idx, cmpgns in enumerate(list_campaigns):
                payload['search.campaign.values[{}]'.format(idx)] = 'urn:li:sponsoredCampaign:{}'.format(cmpgns)
            r = requests.get(URI, params=payload, headers=self.headers)

            for dd in r.json()['elements']:
                row = {
                    '_insert_time': self._insert_time,
                    'campaign_id': int(re.findall(r'\d+', dd['campaign'])[0]),
                    'creative_id': dd['id'],
                    'Status': dd['status'],
                    'ReviewStatus': dd['review']['reviewStatus'],
                    'Type': dd['type'],
                    'servingStatuses': dd['servingStatuses'][0],
                    'data': str(dd['variables']['data']) if isinstance(dd.get('variables', None), dict) else None
                }
                creative_dictionary.append(row)
            total_paging = r.json()['paging']['total']
            start_paging = r.json()['paging']['start']
            count_paging = r.json()['paging']['count']
            print(total_paging, start_paging, count_paging)
            if total_paging <= count_paging:
                PAGING = False
            else:
                start_paging, count_paging = count_paging, count_paging + 100
        return creative_dictionary

    def get_campaign_creative_perf_stats(self, accounts_req: list, start_date, end_date):
        start_day = start_date.day
        start_month = start_date.month
        start_year = start_date.year
        end_day = end_date.day
        end_month = end_date.month
        end_year = end_date.year
        creative_performance_stats = list()
        for cmpgn_id in self.get_campaign_ids(accounts_req):
            start_paging, count_paging = 0, 200
            PATH = 'adAnalyticsV2'
            URI = self.BASE + PATH
            payload = {
                'q': 'statistics',
                'start': start_paging,
                'count': count_paging,
                'pivots[0]': 'CAMPAIGN',
                'pivots[1]': 'CREATIVE',
                'dateRange.end.day': end_day,
                'dateRange.end.month': end_month,
                'dateRange.end.year': end_year,
                'dateRange.start.day': start_day,
                'dateRange.start.month': start_month,
                'dateRange.start.year': start_year,
                'timeGranularity': 'DAILY',
                'campaigns[0]': 'urn:li:sponsoredCampaign:{}'.format(cmpgn_id)
            }
            r = requests.get(URI, params=payload, headers=self.headers)
            if r.json()['elements']:
                for dd in r.json()['elements']:
                    row = {
                        '_insert_time': self._insert_time,
                        'start_date': self.extract_date(dd)[0],
                        'end_date': self.extract_date(dd)[1],
                        'campaign_id': int(re.findall(r'\d+', str(dd.get('pivotValues')))[0]),
                        'creative_id': int(re.findall(r'\d+', str(dd.get('pivotValues')))[1]),
                        'externalWebsitePostClickConversions': dd.get('externalWebsitePostClickConversions'),
                        'adUnitClicks': dd.get('adUnitClicks'),
                        'companyPageClicks': dd.get('companyPageClicks'),
                        'viralOneClickLeads': dd.get('viralOneClickLeads'),
                        'textUrlClicks': dd.get('textUrlClicks'),
                        'viralCommentLikes': dd.get('viralCommentLikes'),
                        'viralExternalWebsiteConversions': dd.get('viralExternalWebsiteConversions'),
                        'cardClicks': dd.get('cardClicks'),
                        'likes': dd.get('likes'),
                        'viralComments': dd.get('viralComments'),
                        'oneClickLeads': dd.get('oneClickLeads'),
                        'viralCardImpressions': dd.get('viralCardImpressions'),
                        'follows': dd.get('follows'),
                        'viralOneClickLeadFormOpens': dd.get('viralOneClickLeadFormOpens'),
                        'conversionValueInLocalCurrency': float(dd.get('conversionValueInLocalCurrency')),
                        'viralFollows': dd.get('viralFollows'),
                        'otherEngagements': dd.get('otherEngagements'),
                        'viralImpressions': dd.get('viralImpressions'),
                        'viralReactions': dd.get('viralReactions'),
                        'totalEngagements': dd.get('totalEngagements'),
                        'opens': dd.get('opens'),
                        'leadGenerationMailInterestedClicks': dd.get('leadGenerationMailInterestedClicks'),
                        'cardImpressions': dd.get('cardImpressions'),
                        'costInLocalCurrency': float(dd.get('costInLocalCurrency')),
                        'viralLikes': dd.get('viralLikes'),
                        'viralOtherEngagements': dd.get('viralOtherEngagements'),
                        'shares': dd.get('shares'),
                        'viralCardClicks': dd.get('viralCardClicks'),
                        'viralExternalWebsitePostViewConversions': dd.get('viralExternalWebsitePostViewConversions'),
                        'viralTotalEngagements': dd.get('viralTotalEngagements'),
                        'viralCompanyPageClicks': dd.get('viralCompanyPageClicks'),
                        'actionClicks': dd.get('actionClicks'),
                        'viralShares': dd.get('viralShares'),
                        'comments': dd.get('comments'),
                        'externalWebsitePostViewConversions': dd.get('externalWebsitePostViewConversions'),
                        'costInUsd': float(dd.get('costInUsd')),
                        'landingPageClicks': dd.get('landingPageClicks'),
                        'oneClickLeadFormOpens': dd.get('oneClickLeadFormOpens'),
                        'impressions': dd.get('impressions'),
                        'sends': dd.get('sends'),
                        'leadGenerationMailContactInfoShares': dd.get('leadGenerationMailContactInfoShares'),
                        'externalWebsiteConversions': dd.get('externalWebsiteConversions'),
                        'viralExternalWebsitePostClickConversions': dd.get('viralExternalWebsitePostClickConversions'),
                        'viralLandingPageClicks': dd.get('viralLandingPageClicks'),
                        'clicks': dd.get('clicks'),
                        'reactions': dd.get('reactions'),
                        'viralClicks': dd.get('viralClicks')
                    }
                    creative_performance_stats.append(row)
        return creative_performance_stats

    @staticmethod
    def extract_date(date_dict):
        start_date_dd = date_dict.get('dateRange').get('start')
        end_date_dd = date_dict.get('dateRange').get('end')

        start_date = dt.datetime(start_date_dd['year'], start_date_dd['month'], start_date_dd['day'])
        start_date = start_date.strftime("%Y-%m-%d")

        end_date = dt.datetime(end_date_dd['year'], end_date_dd['month'], end_date_dd['day'])
        end_date = end_date.strftime("%Y-%m-%d")

        return [start_date, end_date]
