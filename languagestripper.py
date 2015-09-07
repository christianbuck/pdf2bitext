import re
import urlparse
import urllib

class LanguageStripper(object):

    def __init__(self, languages=None):
        self.code_to_language = {}
        for code in ["arabic", "ara", "ar"]:
            self.code_to_language[code] = "ar"
        for code in ["bulgarian", "bul", "bg"]:
            self.code_to_language[code] = "bg"
        for code in ["czech", "cze", "cz", "cs"]:
            self.code_to_language[code] = "cs"
        for code in ["deutsch", "german", "ger", "deu", "de"]:
            self.code_to_language[code] = "de"
        for code in ["english", "eng", "en"]:
            self.code_to_language[code] = "en"
        for code in ["espanol", "spanish", "spa", "esp", "es"]:
            self.code_to_language[code] = "es"
        for code in ["french", "francais", "fran", "fra", "fre", "fr"]:
            self.code_to_language[code] = "fr"
        for code in ["chinese", "chi", "zh"]:
            self.code_to_language[code] = "zh"
        for code in ["russian", "russky", "russki", "russkij", "rus", "ru"]:
            self.code_to_language[code] = "ru"
        # new, not in "Dirt-Cheap"-paper
        for code in ["tedesco", "de-de", "de-ch", "de-at", "de-li", 'de-lu',
                     'allemand']:
            self.code_to_language[code] = "de"
        for code in ["fr-be", "fr-ca", "fr-fr", "fr-lu", "fr-ch"]:
            self.code_to_language[code] = "fr"
        for code in ["italian", "italiano", "ital", 'ita', 'it-it', 'it-ch',
                     'it']:
            self.code_to_language[code] = "it"
        for code in ["en-en", "en-us", "en-uk", 'en-ca', 'en-bz', 'en-ab',
                     'en-in', 'en-ie', 'en-jm', 'en-nz', 'en-ph', 'en-za',
                     'en-tt', 'inglese']:
            self.code_to_language[code] = "en"

        if languages is not None:
            kv_pairs = [(k, v) for k, v in self.code_to_language.items()
                        if v in languages]
            self.code_to_language = dict(kv_pairs)

        for code, lang in self.code_to_language.items():
            # add de_de from de-de
            self.code_to_language[code.replace('-', '_')] = lang

        keys = self.code_to_language.keys()
        keys.sort(key=len, reverse=True)
        regexp_string = "(?<![a-zA-Z0-9])(?:%s)(?![a-zA-Z0-9])" % (
            "|".join(keys))
        self.re_code = re.compile(regexp_string, re.IGNORECASE)

        # remove "-eng" including the hyphen but not -fr from fr-fr
        keys = [key for key in keys if '-' not in key and '_' not in key]
        regexp_string = "[-_](?:%s)(?![a-zA-Z0-9])" % (
            "|".join(keys))
        self.re_strip = re.compile(regexp_string, re.IGNORECASE)

    def strip_path(self, path):
        components = []
        for c in path.split('/'):
            c = self.re_strip.sub('', c)
            components.append(self.re_code.sub('', c))
        return '/'.join(components)

    def strip_query(self, query):
        result = []
        for k, v in urlparse.parse_qsl(query):
            v = self.re_code.sub('', v)
            result.append((k, v))
        return urllib.urlencode(result.encode('utf-8'))

    def stripn(self, uri):
        return self.re_code.subn('', uri)

    def strip(self, uri):
        return self.re_code.sub('', uri)

    def match(self, uri):
        for match in self.re_code.findall(uri):
            match = match.lower()
            assert match in self.code_to_language, \
                "Unknown match: %s\n" % match
            return self.code_to_language[match]
        return ""
