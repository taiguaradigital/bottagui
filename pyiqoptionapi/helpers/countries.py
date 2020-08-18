from threading import RLock
import logging
import time

__all__ = ['Countries', ]


class Countries(object):

    def __init__(self, api):
        super(Countries, self).__init__()
        self.api = api
        self._countries = {
             'Worldwide': {'id': 0, 'name': 'Worldwide'},
             'AF': {'id': 1, 'name': 'Afghanistan'},
             'AL': {'id': 2, 'name': 'Albania'},
             'DZ': {'id': 3, 'name': 'Algeria'},
             'AD': {'id': 5, 'name': 'Andorra'},
             'AO': {'id': 6, 'name': 'Angola'},
             'AI': {'id': 7, 'name': 'Anguilla'},
             'AG': {'id': 9, 'name': 'Antigua and Barbuda'},
             'AR': {'id': 10, 'name': 'Argentina'},
             'AM': {'id': 11, 'name': 'Armenia'},
             'AW': {'id': 12, 'name': 'Aruba'},
             'AT': {'id': 14, 'name': 'Austria'},
             'AZ': {'id': 15, 'name': 'Azerbaijan'},
             'BS': {'id': 16, 'name': 'Bahamas'},
             'BH': {'id': 17, 'name': 'Bahrain'},
             'BD': {'id': 18, 'name': 'Bangladesh'},
             'BB': {'id': 19, 'name': 'Barbados'},
             'BY': {'id': 20, 'name': 'Belarus'},
             'BZ': {'id': 22, 'name': 'Belize'},
             'BJ': {'id': 23, 'name': 'Benin'},
             'BM': {'id': 24, 'name': 'Bermuda'},
             'BO': {'id': 26, 'name': 'Bolivia'},
             'BA': {'id': 27, 'name': 'Bosnia and Herzegowina'},
             'BW': {'id': 28, 'name': 'Botswana'},
             'BV': {'id': 29, 'name': 'Bouvet Island'},
             'BR': {'id': 30, 'name': 'Brazil'},
             'BN': {'id': 31, 'name': 'Brunei Darussalam'},
             'BG': {'id': 32, 'name': 'Bulgaria'},
             'BF': {'id': 33, 'name': 'Burkina Faso'},
             'BI': {'id': 34, 'name': 'Burundi'},
             'KH': {'id': 35, 'name': 'Cambodia'},
             'CM': {'id': 36, 'name': 'Cameroon'},
             'CV': {'id': 38, 'name': 'Cape Verde'},
             'KY': {'id': 39, 'name': 'Cayman Islands'},
             'TD': {'id': 41, 'name': 'Chad'},
             'CL': {'id': 42, 'name': 'Chile'},
             'CN': {'id': 43, 'name': 'China'},
             'CC': {'id': 45, 'name': 'Cocos Islands'},
             'CO': {'id': 46, 'name': 'Colombia'},
             'KM': {'id': 47, 'name': 'Comoros'},
             'CG': {'id': 48, 'name': 'Congo'},
             'CK': {'id': 49, 'name': 'Cook Islands'},
             'CR': {'id': 50, 'name': 'Costa Rica'},
             'CI': {'id': 51, 'name': "Côte d'Ivoire"},
             'HR': {'id': 52, 'name': 'Croatia'},
             'CU': {'id': 53, 'name': 'Cuba'},
             'CY': {'id': 54, 'name': 'Cyprus'},
             'CZ': {'id': 55, 'name': 'Czech Republic'},
             'DK': {'id': 56, 'name': 'Denmark'},
             'DJ': {'id': 57, 'name': 'Djibouti'},
             'DM': {'id': 58, 'name': 'Dominica'},
             'DO': {'id': 59, 'name': 'Dominican Republic'},
             'TL': {'id': 60, 'name': 'East Timor'},
             'EC': {'id': 61, 'name': 'Ecuador'},
             'EG': {'id': 62, 'name': 'Egypt'},
             'SV': {'id': 63, 'name': 'El Salvador'},
             'EE': {'id': 66, 'name': 'Estonia'},
             'ET': {'id': 67, 'name': 'Ethiopia'},
             'FO': {'id': 69, 'name': 'Faroe Islands'},
             'FJ': {'id': 70, 'name': 'Fiji'},
             'FI': {'id': 71, 'name': 'Finland'},
             'FR': {'id': 72, 'name': 'France'},
             'GF': {'id': 73, 'name': 'French Guiana'},
             'PF': {'id': 74, 'name': 'French Polynesia'},
             'GA': {'id': 75, 'name': 'Gabon'},
             'GM': {'id': 76, 'name': 'Gambia'},
             'GE': {'id': 77, 'name': 'Georgia'},
             'DE': {'id': 78, 'name': 'Germany'},
             'GH': {'id': 79, 'name': 'Ghana'},
             'GR': {'id': 81, 'name': 'Greece'},
             'GD': {'id': 83, 'name': 'Grenada'},
             'GP': {'id': 84, 'name': 'Guadeloupe'},
             'GT': {'id': 86, 'name': 'Guatemala'},
             'GN': {'id': 87, 'name': 'Guinea'},
             'GY': {'id': 88, 'name': 'Guyana'},
             'HT': {'id': 89, 'name': 'Haiti'},
             'HN': {'id': 90, 'name': 'Honduras'},
             'HK': {'id': 91, 'name': 'Hong Kong'},
             'HU': {'id': 92, 'name': 'Hungary'},
             'IS': {'id': 93, 'name': 'Iceland'},
             'ID': {'id': 94, 'name': 'Indonesia'},
             'IQ': {'id': 95, 'name': 'Iraq'},
             'IE': {'id': 96, 'name': 'Ireland'},
             'IT': {'id': 97, 'name': 'Italy'},
             'JM': {'id': 98, 'name': 'Jamaica'},
             'JO': {'id': 100, 'name': 'Jordan'},
             'KZ': {'id': 101, 'name': 'Kazakhstan'},
             'KE': {'id': 102, 'name': 'Kenya'},
             'KI': {'id': 103, 'name': 'Kiribati'},
             'KW': {'id': 104, 'name': 'Kuwait'},
             'KG': {'id': 105, 'name': 'Kyrgyzstan'},
             'LA': {'id': 106, 'name': 'Laos'},
             'LV': {'id': 107, 'name': 'Latvia'},
             'LB': {'id': 108, 'name': 'Lebanon'},
             'LS': {'id': 109, 'name': 'Lesotho'},
             'LR': {'id': 110, 'name': 'Liberia'},
             'LY': {'id': 111, 'name': 'Libya'},
             'LT': {'id': 113, 'name': 'Lithuania'},
             'LU': {'id': 114, 'name': 'Luxembourg'},
             'MO': {'id': 115, 'name': 'Macau'},
             'MK': {'id': 116, 'name': 'Macedonia'},
             'MG': {'id': 117, 'name': 'Madagascar'},
             'MW': {'id': 118, 'name': 'Malawi'},
             'MY': {'id': 119, 'name': 'Malaysia'},
             'MV': {'id': 120, 'name': 'Maldives'},
             'ML': {'id': 121, 'name': 'Mali'},
             'MT': {'id': 122, 'name': 'Malta'},
             'MQ': {'id': 124, 'name': ''},
             'MR': {'id': 125, 'name': 'Mauritania'},
             'MU': {'id': 126, 'name': 'Mauritius'},
             'MX': {'id': 128, 'name': 'Mexico'},
             'FM': {'id': 129, 'name': 'Micronesia'},
             'MD': {'id': 130, 'name': 'Moldova'},
             'MC': {'id': 131, 'name': 'Monaco'},
             'MN': {'id': 132, 'name': 'Mongolia'},
             'MA': {'id': 134, 'name': 'Morocco'},
             'MZ': {'id': 135, 'name': 'Mozambique'},
             'MM': {'id': 136, 'name': 'Myanmar'},
             'NA': {'id': 137, 'name': 'Namibia'},
             'NP': {'id': 139, 'name': 'Nepal'},
             'NL': {'id': 140, 'name': 'Netherlands'},
             'AN': {'id': 141, 'name': 'Netherlands Antilles'},
             'NC': {'id': 142, 'name': 'New Caledonia'},
             'NZ': {'id': 143, 'name': 'New Zealand'},
             'NI': {'id': 144, 'name': 'Nicaragua'},
             'NE': {'id': 145, 'name': 'Niger'},
             'NG': {'id': 146, 'name': 'Nigeria'},
             'NO': {'id': 149, 'name': 'Norway'},
             'OM': {'id': 150, 'name': 'Oman'},
             'PK': {'id': 151, 'name': 'Pakistan'},
             'PW': {'id': 152, 'name': 'Palau'},
             'PA': {'id': 153, 'name': 'Panama'},
             'PG': {'id': 154, 'name': 'Papua New Guinea'},
             'PY': {'id': 155, 'name': 'Paraguay'},
             'PE': {'id': 156, 'name': 'Peru'},
             'PH': {'id': 157, 'name': 'Philippines'},
             'PL': {'id': 159, 'name': 'Poland'},
             'PT': {'id': 160, 'name': 'Portugal'},
             'QA': {'id': 162, 'name': 'Qatar'},
             'RE': {'id': 163, 'name': 'Reunion Island'},
             'RO': {'id': 164, 'name': 'Romania'},
             'RW': {'id': 166, 'name': 'Rwanda'},
             'KN': {'id': 167, 'name': 'Saint Kitts and Nevis'},
             'LC': {'id': 168, 'name': 'Saint Lucia'},
             'SA': {'id': 171, 'name': 'Saudi Arabia'},
             'SN': {'id': 172, 'name': 'Senegal'},
             'SC': {'id': 173, 'name': 'Seychelles'},
             'SG': {'id': 175, 'name': 'Singapore'},
             'SK': {'id': 176, 'name': 'Slovakia'},
             'SI': {'id': 177, 'name': 'Slovenia'},
             'SO': {'id': 179, 'name': 'Somalia'},
             'ZA': {'id': 180, 'name': 'South Africa'},
             'KR': {'id': 181, 'name': 'South Korea'},
             'ES': {'id': 182, 'name': 'Spain'},
             'LK': {'id': 183, 'name': 'Sri Lanka'},
             'SH': {'id': 184, 'name': 'ST. Helena'},
             'SR': {'id': 186, 'name': 'Suriname'},
             'SZ': {'id': 187, 'name': 'Swaziland'},
             'SE': {'id': 188, 'name': 'Sweden'},
             'CH': {'id': 189, 'name': 'Switzerland'},
             'TW': {'id': 191, 'name': 'Taiwan'},
             'TJ': {'id': 192, 'name': 'Tajikistan'},
             'TZ': {'id': 193, 'name': 'Tanzania'},
             'TH': {'id': 194, 'name': 'Thailand'},
             'TG': {'id': 195, 'name': 'Togo'},
             'TT': {'id': 198, 'name': 'Trinidad and Tobago'},
             'TN': {'id': 199, 'name': 'Tunisia'},
             'TR': {'id': 200, 'name': 'Turkey'},
             'TM': {'id': 201, 'name': 'Turkmenistan'},
             'UG': {'id': 203, 'name': 'Uganda'},
             'UA': {'id': 204, 'name': 'Ukraine'},
             'AE': {'id': 205, 'name': 'United Arab Emirates'},
             'GB': {'id': 206, 'name': 'United Kingdom'},
             'UY': {'id': 207, 'name': 'Uruguay'},
             'UZ': {'id': 208, 'name': 'Uzbekistan'},
             'VE': {'id': 211, 'name': 'Venezuela'},
             'VN': {'id': 212, 'name': 'Vietnam'},
             'VG': {'id': 213, 'name': 'Virgin Islands UK'},
             'YE': {'id': 216, 'name': 'Yemen'},
             'ZM': {'id': 218, 'name': 'Zambia'},
             'ZW': {'id': 219, 'name': 'Zimbabwe'},
             'RS': {'id': 220, 'name': 'Serbia'},
             'ME': {'id': 221, 'name': 'Montenegro'},
             'IN': {'id': 225, 'name': 'India'},
             'TC': {'id': 234, 'name': 'Turks and Caicos Islands'},
             'CD': {'id': 235, 'name': 'Democratic Republic of Congo'},
             'GG': {'id': 236, 'name': 'Guernsey'},
             'IM': {'id': 237, 'name': 'Isle of Man'},
             'JE': {'id': 239, 'name': 'Jersey'},
             'CW': {'id': 246, 'name': 'Curaçao'}
             }
        self._lock = RLock()

    def get_countries_names(self):
        with self._lock:
            return list([v['name'] for v in self._countries.values()])
    
    def get_country_name(self, name_short):
        with self._lock:
            return self._countries.get(name_short).get('name')
        
    def get_top_countries(self, country='Worldwide'):
         """ return dict {country_id, name_short, profit}  """
         try:
             return self.api.get_leader_board(country, 1, 1, 0)['result']['top_countries']
         except TimeoutError:
             logging.error('timeout response. retry new get response in 1 seconds.')
             retries = 0
             response = None
             while not response:
                retries += 1
                time.sleep(1)
                response = self.get_top_countries(country)
                if retries >= 3:
                     logging.error('all attempts have failed')
                     return False
                return response
                 
         except Exception as e:
             logging.error('get-top-countries -> {}'.format(e))

    def get_country_id(self, country):
        try:
             if len(country) == 2:
                  with self._lock:
                       return self._countries[country]['id']
             else:
                  with self._lock:
                       return list(filter(lambda value: value['name'] == country, self._countries.values()))[0]['id']
        except:
            return None
