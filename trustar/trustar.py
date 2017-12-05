from __future__ import print_function

from .report import Report, DISTRIBUTION_TYPE_ENCLAVE
from .page import Page
from .utils import normalize_timestamp

import logging
import json
from datetime import datetime
import configparser
import requests
import requests.auth
from requests import HTTPError
from builtins import object
from future import standard_library

standard_library.install_aliases()

logger = logging.getLogger(__name__)


CLIENT_VERSION = "0.3.0"


class TruStar(object):
    """
    This class is used to interact with the TruStar API.
    """

    REQUIRED_KEYS = ['auth', 'base', 'api_key', 'api_secret']
    DEFAULTS = {
        'client_type': 'PYTHON_SDK',
        'client_version': CLIENT_VERSION,
        'client_metatag': None,
        'verify': True
    }

    def __init__(self, config_file="../examples/trustar.conf", config_role="trustar", config=None):
        """
        Constructs and configures the instance.  Attempts to use 'config' to configure.  If it is None,
        then attempts to use 'config_file' instead.
        :param config_file: Path to configuration file.
        :param config_role: The section in the configuration file to use.
        :param config: A dictionary of configuration options.
        """

        # attempt to use configuration file if one exists
        if config is None:

            if config is not None:
                raise Exception("Cannot use 'config' parameter if also using 'config_file' parameter.")

            config_parser = configparser.RawConfigParser()
            config_parser.read(config_file)

            try:
                # parse enclaves
                if config_parser.has_option(config_role, 'enclave_ids'):
                    enclave_ids = config_parser.get(config_role, 'enclave_ids').split(',')
                else:
                    enclave_ids = []

                # use config file to create config dict
                config = {
                    'auth': config_parser.get(config_role, 'auth_endpoint'),
                    'base': config_parser.get(config_role, 'api_endpoint'),
                    'api_key': config_parser.get(config_role, 'user_api_key'),
                    'api_secret': config_parser.get(config_role, 'user_api_secret'),
                    'client_type': config_parser.get(config_role, 'client_type', fallback=None),
                    'client_version': config_parser.get(config_role, 'client_version', fallback=None),
                    'client_metatag': config_parser.get(config_role, 'client_metatag', fallback=None),
                    'verify': config_parser.get(config_role, 'verify', fallback=None),
                    'enclave_ids': [x.strip() for x in enclave_ids if x is not None]
                }

            except Exception as e:
                raise KeyError("Problem reading config file: %s" % e)

        # set properties from config dict
        for key, val in config.items():
            if val is None:
                # ensure required properties are present
                if val in TruStar.REQUIRED_KEYS:
                    raise Exception("Missing config value for %s" % key)
                elif val in TruStar.DEFAULTS:
                    config[key] = TruStar.DEFAULTS[key]

        # set properties
        self.auth = config['auth']
        self.base = config['base']
        self.api_key = config['api_key']
        self.api_secret = config['api_secret']
        self.client_type = config['client_type']
        self.client_version = config['client_version']
        self.client_metatag = config['client_metatag']
        self.verify = config['verify']
        self.enclave_ids = config['enclave_ids']

    @staticmethod
    def normalize_timestamp(date_time):
        return normalize_timestamp(date_time)

    def __get_token(self):
        """
        Retrieves the OAUTH token generated by your API key and API secret.
        this function has to be called before any API calls can be made
        """
        client_auth = requests.auth.HTTPBasicAuth(self.api_key, self.api_secret)
        post_data = {"grant_type": "client_credentials"}
        response = requests.post(self.auth, auth=client_auth, data=post_data)

        # raise exception if status code indicates an error
        if 400 <= response.status_code < 600:
            message = "{} {} Error: {}".format(response.status_code,
                                               "Client" if response.status_code < 500 else "Server",
                                               "unable to get token")
            raise HTTPError(message=message, response=response)
        return response.json()["access_token"]

    def __get_headers(self, is_json=False):
        """
        Create headers dictionary for a request.
        :param is_json: Whether the request body is a json.
        :return: The headers dictionary.
        """
        headers = {"Authorization": "Bearer " + self.__get_token()}

        if self.client_type is not None:
            headers["Client-Type"] = self.client_type

        if self.client_version is not None:
            headers["Client-Version"] = self.client_version

        if self.client_metatag is not None:
            headers["Client-Metatag"] = self.client_metatag

        if is_json:
            headers['Content-Type'] = 'application/json'

        return headers

    def __request(self, method, path, headers=None, **kwargs):
        """
        A wrapper around requests.request that handles boilerplate code specific to TruStar's API.
        :param method: The method of the request ("GET", "PUT", "POST", or "DELETE")
        :param path: The path of the request, i.e. the piece of the URL after the base URL
        :param headers: A dictionary of headers that will be merged with the base headers for the SDK
        :param kwargs: Any extra keyword arguments.  These will be forwarded to requests.request.
        :return: The response object.
        """

        # get headers and merge with headers from method parameter if it exists
        base_headers = self.__get_headers(is_json=method in ["POST", "PUT"])
        if headers is not None:
            base_headers.update(headers)

        # make request
        response = requests.request(method=method,
                                    url="{}/{}".format(self.base, path),
                                    headers=base_headers,
                                    verify=self.verify,
                                    **kwargs)

        # raise exception if status code indicates an error
        if 400 <= response.status_code < 600:
            if 'message' in response.json():
                reason = response.json()['message']
            else:
                reason = "unknown cause"
            message = "{} {} Error: {}".format(response.status_code,
                                               "Client" if response.status_code < 500 else "Server",
                                               reason)
            raise HTTPError(message, response=response)
        return response

    def __get(self, path, **kwargs):
        """
        Convenience method for making GET calls.
        :param path: The path of the request, i.e. the piece of the URL after the base URL
        :param kwargs: Any extra keyword arguments.  These will be forwarded to requests.request.
        """
        return self.__request("GET", path, **kwargs)

    def __put(self, path, **kwargs):
        """
        Convenience method for making PUT calls.
        :param path: The path of the request, i.e. the piece of the URL after the base URL
        :param kwargs: Any extra keyword arguments.  These will be forwarded to requests.request.
        """
        return self.__request("PUT", path, **kwargs)

    def __post(self, path, **kwargs):
        """
        Convenience method for making POST calls.
        :param path: The path of the request, i.e. the piece of the URL after the base URL
        :param kwargs: Any extra keyword arguments.  These will be forwarded to requests.request.
        """
        return self.__request("POST", path, **kwargs)

    def __delete(self, path, **kwargs):
        """
        Convenience method for making DELETE calls.
        :param path: The path of the request, i.e. the piece of the URL after the base URL
        :param kwargs: Any extra keyword arguments.  These will be forwarded to requests.request.
        """
        return self.__request("DELETE", path, **kwargs)

    def get_report_url(self, report_id):
        """
        Build direct URL to report from its ID
        :param report_id: Incident Report (IR) ID, e.g., as returned from `submit_report`
        :return URL
        """

        # Check environment for URL
        base_url = 'https://station.trustar.co' if ('https://api.trustar.co' in self.base) else \
            self.base.split('/api/')[0]

        return "%s/constellation/reports/%s" % (base_url, report_id)


    #####################
    ### API Endpoints ###
    #####################

    def ping(self, **kwargs):
        """
        Ping the API.
        :param kwargs: Any extra keyword arguments.  These will be forwarded to requests.request.
        """
        return self.__get("ping", **kwargs).content.decode('utf-8').strip('\n')

    def get_version(self, **kwargs):
        """
        Ping the API.
        :param kwargs: Any extra keyword arguments.  These will be forwarded to requests.request.
        """
        return self.__get("version", **kwargs).content.decode('utf-8').strip('\n')


    ########################
    ### Report Endpoints ###
    ########################

    def get_report_details(self, report_id, id_type=None, **kwargs):
        """
        Retrieves the report details dictionary
        :param report_id: Incident Report ID
        :param id_type: indicates if ID is internal report guid or external ID provided by the user
        :param kwargs: Any extra keyword arguments.  These will be forwarded to requests.request.
        :return Incident report dictionary if found, else exception.
        """
        params = {'idType': id_type}
        resp = self.__get("report/%s" % report_id, params=params, **kwargs)
        return json.loads(resp.content.decode('utf8'))

    def get_reports(self, distribution_type=DISTRIBUTION_TYPE_ENCLAVE, enclave_ids=None,
                    from_time=None, to_time=None, page_number=None, page_size=None, **kwargs):
        """
        Retrieves reports filtering by time window, distribution type, and enclave association.

        :param distribution_type: Optional, restrict reports to specific distribution type
        (by default all accessible reports are returned). Possible values are: 'COMMUNITY' and 'ENCLAVE'
        :param enclave_ids: Optional comma separated list of enclave ids, restrict reports to specific enclaves
        (by default reports from all enclaves are returned)
        :param from_time: Optional start of time window (Unix timestamp - milliseconds since epoch)
        :param to_time: Optional end of time window (Unix timestamp - milliseconds since epoch)
        :param page_number: The page number to get.
        :param page_size: The size of the page to be returned.
        :param kwargs: Any extra keyword arguments.  These will be forwarded to requests.request.
        """

        # make enclave_ids default to configured list of enclave IDs
        if enclave_ids is None and distribution_type is not None and distribution_type.upper() == DISTRIBUTION_TYPE_ENCLAVE:
            enclave_ids = self.enclave_ids

        params = {
            'from': from_time,
            'to': to_time,
            'distributionType': distribution_type,
            'enclaveIds': enclave_ids,
            'pageNumber': page_number,
            'pageSize': page_size
        }
        resp = self.__get("reports", params=params, **kwargs)
        body = resp.json()

        # replace each dict in 'items' with a Report object
        body['items'] = [Report.from_dict(report) for report in body['items']]

        # create a Page object from the dict
        return Page.from_dict(body)


    def submit_report(self, report_body=None, title=None, external_id=None, external_url=None, time_began=datetime.now(),
                      enclave=False, enclave_ids=None, report=None, **kwargs):
        """
        Wraps supplied text as a JSON-formatted TruSTAR Incident Report and submits it to TruSTAR Station
        By default, this submits to the TruSTAR community. To submit to your enclave(s), set enclave parameter to True,
        and ensure that the target enclaves' ids are specified in the config file field enclave_ids.
        :param report_body: body of report
        :param title: title of report
        :param external_id: external tracking id of report, optional if user doesn't have their own tracking id that they want associated with this report
        :param external_url: external url of report, optional and is associated with the original source of this report
        :param time_began: time report began
        :param enclave: boolean - whether or not to submit report to user's enclaves (see 'enclave_ids' config property)
        :param enclave_ids: the IDs of the enclaves to submit the report to
        :param report: a Report object.  If present, other parameters will be ignored.
        :param kwargs: Any extra keyword arguments.  These will be forwarded to requests.request.
        """

        # if no Report object was passed, construct one from the other parameters
        if report is None:

            # use configured enclave_ids by default
            if enclave_ids is None:
                enclave_ids = self.enclave_ids

            report = Report(title=title,
                            body=report_body,
                            time_began=time_began,
                            external_id=external_id,
                            external_url=external_url,
                            is_enclave=enclave,
                            enclave_ids=enclave_ids)

        payload = {
            'incidentReport': report.to_dict(),
            'enclaveIds': report.enclave_ids
        }

        resp = self.__post("report", data=json.dumps(payload), timeout=60, **kwargs)
        return resp.json()

    def update_report(self, report_id=None, id_type=None, title=None, report_body=None, time_began=None,
                      external_url=None, distribution=None, enclave_ids=None, report=None, **kwargs):
        """
        Updates report with the given id, overwrites any fields that are provided
        :param report_id: Incident Report ID
        :param id_type: indicates if ID is internal report guid or external ID provided by the user
        :param title: new title for report
        :param report_body: new body for report
        :param time_began: new time_began for report
        :param external_url: external url of report, optional and is associated with the original source of this report
        :param distribution: new distribution type for report
        :param enclave_ids: new list of enclave ids that the report will belong to (python list or comma-separated list)
        :param report: a Report object.  If present, other parameters will be ignored.
        :param kwargs: Any extra keyword arguments.  These will be forwarded to requests.request.
        """

        # if no Report object was passed, construct one from the other parameters
        if report is None:

            # use configured enclave_ids by default
            if enclave_ids is None:
                enclave_ids = self.enclave_ids

            report = Report(id=report_id,
                            title=title,
                            body=report_body,
                            time_began=time_began,
                            external_url=external_url,
                            is_enclave=distribution is None or distribution.upper() == DISTRIBUTION_TYPE_ENCLAVE,
                            enclave_ids=enclave_ids)

        # make id_type default to "internal"
        id_type = id_type or Report.ID_TYPE_INTERNAL

        # determine which ID to use based on id_type
        if id_type.upper() == Report.ID_TYPE_EXTERNAL:
            report_id = report.external_id
        else:
            report_id = report.id

        # not allowed to update value of 'externalTrackingId', so remove it
        report_dict = {k: v for k, v in report.to_dict() if k != 'externalTrackingId'}

        params = {'idType': id_type}
        payload = {
            'incidentReport': report_dict,
            'enclaveIds': report.enclave_ids
        }

        resp = self.__put("report/%s" % report_id, data=json.dumps(payload), params=params, **kwargs)
        return resp.json()

    def delete_report(self, report_id, id_type=None, **kwargs):
        """
        Deletes the report for the given id
        :param report_id: Incident Report ID
        :param id_type: indicates if ID is internal report guid or external ID provided by the user
        :param kwargs: Any extra keyword arguments.  These will be forwarded to requests.request.
        """
        params = {'idType': id_type}
        resp = self.__delete("report/%s" % report_id, params=params, **kwargs)
        return resp

    def get_correlated_reports(self, indicators, **kwargs):
        """
        Retrieves all TruSTAR reports that contain the searched indicator. You can specify multiple indicators
        separated by commas
        :param indicators: The list of indicators to retrieve correlated reports for.
        :param kwargs: Any extra keyword arguments.  These will be forwarded to requests.request.
        """
        params = {'indicators': indicators}
        resp = self.__get("reports/correlate", params=params, **kwargs)
        return resp.json()


    ###########################
    ### Indicator Endpoints ###
    ###########################

    def get_community_trends(self, indicator_type=None, from_time=None, to_time=None, page_size=None, page_number=None, **kwargs):
        """
        Find community trending indicators.
        :param indicator_type: the type of indicators.  If None, will get all types of indicators except for MALWARE and CVEs.
        :param from_time: Optional start of time window (Unix timestamp - milliseconds since epoch)
        :param to_time: Optional end of time window (Unix timestamp - milliseconds since epoch)
        :param page_size: # of results on returned page
        :param page_number: page to start returning results on
        :param kwargs: Any extra keyword arguments.  These will be forwarded to requests.request.
        :return: json response of the result
        """

        params = {
            'type': indicator_type,
            'from': from_time,
            'to': to_time,
            'pageSize': page_size,
            'pageNumber': page_number
        }
        resp = self.__get("indicators/community-trending", params=params, **kwargs)
        return Page.from_dict(resp.json())

    def get_related_indicators(self, indicators=None, sources=None, page_size=None, page_number=None, **kwargs):
        """
        Finds all reports that contain the indicators and returns correlated indicators from those reports.
        :param indicators: list of indicators to search for
        :param sources: list of sources to search.  Options are: INCIDENT_REPORT, EXTERNAL_INTELLIGENCE, and ORION_FEED.
        :param page_size: # of results on returned page
        :param page_number: page to start returning results on
        :param kwargs: Any extra keyword arguments.  These will be forwarded to requests.request.
        :return: json response of the result
        """

        params = {
            'indicators': indicators,
            'sources': sources,
            'pageNumber': page_number,
            'pageSize': page_size
        }
        resp = self.__get("indicators/related", params=params, **kwargs)
        return Page.from_dict(resp.json())

    def get_related_external_indicators(self, indicators=None, sources=None, **kwargs):
        """
        Finds all reports that contain the indicators and returns correlated indicators from those reports.
        :param indicators: list of indicators to search for
        :param sources: list of sources to search
        :param kwargs: Any extra keyword arguments.  These will be forwarded to requests.request.
        """

        params = {
            'indicators': indicators,
            'sources': sources
        }
        resp = self.__get("indicators/external/related", params=params, **kwargs)
        return resp.json()


    #####################
    ### Tag Endpoints ###
    #####################

    def get_enclave_tags(self, report_id, id_type=None, **kwargs):
        """
        Retrieves the enclave tags present in a specific report
        :param report_id: Incident Report ID
        :param id_type: Optional, indicates if ID is internal report guid or external ID provided by the user
        (default Internal)
        :param kwargs: Any extra keyword arguments.  These will be forwarded to requests.request.
        """
        params = {'idType': id_type}
        resp = self.__get("reports/%s/enclave-tags" % report_id, params=params, **kwargs)
        return resp.json()

    def add_enclave_tag(self, report_id, name, enclave_id, id_type=None, **kwargs):
        """
        Adds a tag to a specific report, in a specific enclave
        :param report_id: Incident Report ID
        :param name: name of the tag to be added
        :param enclave_id: id of the enclave where the tag will be added
        :param id_type: Optional, indicates if ID is internal report guid or external ID provided by the user
        (default Internal)
        :param kwargs: Any extra keyword arguments.  These will be forwarded to requests.request.
        """
        params = {
            'idType': id_type,
            'name': name,
            'enclaveId': enclave_id
        }
        resp = self.__post("reports/%s/enclave-tags" % report_id, params=params, **kwargs)
        return resp.json()

    def delete_enclave_tag(self, report_id, name, enclave_id, id_type=None, **kwargs):
        """
        Deletes a tag from a specific report, in a specific enclave
        :param report_id: Incident Report ID
        :param name: name of the tag to be deleted
        :param enclave_id: id of the enclave where the tag will be deleted
        :param id_type: Optional, indicates if ID is internal report guid or external ID provided by the user
        (default Internal)
        :param kwargs: Any extra keyword arguments.  These will be forwarded to requests.request.
        """
        params = {
            'idType': id_type,
            'name': name,
            'enclaveId': enclave_id
        }
        resp = self.__delete("reports/%s/enclave-tags" % report_id, params=params, **kwargs)
        return resp.content.decode('utf8')


    #################
    ### Iterators ###
    #################

    @staticmethod
    def get_page_generator(func, start_page=0, page_size=None):
        """
        Gets a generator for retrieving pages from a paginated endpoint.
        :param func: Should take parameters 'page_number' and 'page_size' and return the corresponding Page object.
        :param start_page: The page to start on.
        :param page_size: The size of each page.
        :return: The generator.
        """
        page_number = start_page
        more_pages = True
        while more_pages:
            page = func(page_number=page_number, page_size=page_size)
            yield page
            more_pages = page.has_more_pages()
            page_number += 1

    @classmethod
    def get_generator(cls, func=None, page_iterator=None):
        """
        Gets a generator for retrieving all results from a paginated endpoint.  Pass exactly one of 'page_iterator'
        or 'func'.
        :param func: Should take parameters 'page_number' and 'page_size' and return the corresponding Page object.
        If page_iterator is None, this will be used to create one.
        :param page_iterator: A page_iterator to be used to generate each successive page.
        :return: The generator.
        """

        # if page_iterator is None, use func to create one
        if page_iterator is None:
            if func is None:
                raise Exception("To use 'get_iterator', must provide either a page iterator or a method.")
            else:
                page_iterator = cls.get_page_generator(func)

        for page in page_iterator:
            for item in page.items:
                yield item

    def get_report_page_iterator(self, start_page=0, page_size=None, **kwargs):
        """
        Creates a generator from the 'get_reports' method that returns each successive page.
        :param start_page: The page to start on.
        :param page_size: The size of each page.
        :param kwargs: Any extra keyword arguments.  These will be forwarded to the 'get_reports' method.
        :return: The generator.
        """
        def func(page_number, page_size):
            return self.get_reports(page_number=page_number, page_size=page_size, **kwargs)

        return self.get_page_generator(func, start_page, page_size)

    def get_report_iterator(self, **kwargs):
        """
        Creates a generator from the 'get_reports' method that returns each successive report.
        :param kwargs: Any extra keyword arguments.  These will be forwarded to the 'get_reports' method.
        :return: The generator.
        """
        return self.get_generator(page_iterator=self.get_report_page_iterator(**kwargs))

    def get_community_trends_page_iterator(self, start_page=0, page_size=None, **kwargs):
        """
        Creates a generator from the 'get_community_trends' method that returns each successive page.
        :param start_page: The page to start on.
        :param page_size: The size of each page.
        :param kwargs: Any extra keyword arguments.  These will be forwarded to the 'get_community_trends' method.
        :return: The generator.
        """
        def func(page_number, page_size):
            return self.get_community_trends(page_number=page_number, page_size=page_size, **kwargs)

        return self.get_page_generator(func, start_page, page_size)

    def get_community_trends_iterator(self, **kwargs):
        """
        Creates a generator from the 'get_community_trends_iterator' method that returns each successive report.
        :param kwargs: Any extra keyword arguments.  These will be forwarded to the 'get_community_trends_iterator' method.
        :return: The generator.
        """
        return self.get_generator(page_iterator=self.get_community_trends_page_iterator(**kwargs))

    def get_related_indicators_page_iterator(self, start_page=0, page_size=None, **kwargs):
        """
        Creates a generator from the 'get_related_indicators' method that returns each successive page.
        :param start_page: The page to start on.
        :param page_size: The size of each page.
        :param kwargs: Any extra keyword arguments.  These will be forwarded to the 'get_related_indicators' method.
        :return: The generator.
        """
        def func(page_number, page_size):
            return self.get_related_indicators(page_number=page_number, page_size=page_size, **kwargs)

        return self.get_page_generator(func, start_page, page_size)

    def get_related_indicators_iterator(self, **kwargs):
        """
        Creates a generator from the 'get_generator' method that returns each successive report.
        :param kwargs: Any extra keyword arguments.  These will be forwarded to the 'get_generator' method.
        :return: The generator.
        """
        return self.get_generator(page_iterator=self.get_related_indicators_page_iterator(**kwargs))
