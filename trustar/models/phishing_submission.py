# python 2 backwards compatibility
from __future__ import print_function
from builtins import super

# package imports
from .base import ModelBase


class PhishingSubmission(ModelBase):
    """
    Models a |PhishingSubmission_resource|

    ``context`` is a dictionary containing these fields:
    indicatorType, indicatorValue, sourceKey, normalizedIndicatorScore

    :ivar submission_id: The id of the email submission
    :ivar title: The title of the email submission (email subject)
    :ivar priority_event_score: The score of the email submission
    :ivar status: The current triage status of a submission ("UNRESOLVED", "CONFIRMED", or "IGNORED")
    :ivar context: A list containing dicts which represent IOCs, sources, and scores
                    that contributed to to the triage score.
    """

    def __init__(self,
                 submission_id=None,
                 title=None,
                 priority_event_score=None,
                 status=None,
                 context=None):
        """
        Constructs a |PhishingSubmission| object.
        """
        self.submission_id = submission_id
        self.title = title
        self.priority_event_score = priority_event_score
        self.status = status
        self.context = context

    @classmethod
    def from_dict(cls, phishing_submission):
        """
        Creates a phishing submission object from a dictionary.

        :param phishing_submission: The phishing submission dictionary.
        :return: The |PhishingSubmission| object.
        """

        return PhishingSubmission(submission_id=phishing_submission.get('submissionId'),
                                  title=phishing_submission.get('title'),
                                  priority_event_score=phishing_submission.get('priorityEventScore'),
                                  status=phishing_submission.get('status'),
                                  context=phishing_submission.get('context'))

    def to_dict(self, remove_nones=False):
        """
        Creates a dictionary representation of a phishing submission.

        :param remove_nones: Whether ``None`` values should be filtered out of the dictionary.  Defaults to ``False``.
        :return: A |PhishingSubmission| object.
        """

        if remove_nones:
            return super(PhishingSubmission, self).to_dict(remove_nones=True)

        return {
            'submissionId': self.submission_id,
            'title': self.title,
            'priorityEventScore': self.priority_event_score,
            'status': self.status,
            'context': self.context,
        }


class PhishingIndicator(ModelBase):
    """
    Models a |PhishingIndicator_resource|.

    :ivar indicator_type: The type of the extracted entity (e.g. URL, IP, ...)
    :ivar value: The value of an extracted entity (e.g. www.badsite.com, etc.)
    :ivar source_key: A string that is associated with the closed source providing context
                       (e.g. 'virustotal', 'crowdstrike_indicator')
    :ivar normalized_indicator_score: The normalized score associated with a context entity
    :ivar original_indicator_score: A score given to the indicator by its original source
    """

    def __init__(self,
                 indicator_type=None,
                 value=None,
                 source_key=None,
                 normalized_indicator_score=None,
                 original_indicator_score=None):
        """
        Constructs a |PhishingIndicator| object.
        """
        self.indicator_type = indicator_type
        self.value = value
        self.source_key = source_key
        self.normalized_indicator_score = normalized_indicator_score
        self.original_indicator_score = original_indicator_score

    @classmethod
    def from_dict(cls, phishing_indicator):
        """
        Creates a phishing indicator object from a dictionary.

        :param phishing_indicator: The phishing indicator dictionary.
        """

        return PhishingIndicator(indicator_type=phishing_indicator.get('indicatorType'),
                                 value=phishing_indicator.get('value'),
                                 source_key=phishing_indicator.get('sourceKey'),
                                 normalized_indicator_score=phishing_indicator.get('normalizedIndicatorScore'),
                                 original_indicator_score=phishing_indicator.get('originalIndicatorScore'))

    def to_dict(self, remove_nones=False):
        """
        Creates a dictionary representation of a phishing indicator.

        :param remove_nones: Whether ``None`` values should be filtered out of the dictionary.  Defaults to ``False``.
        :return: A |PhishingIndicator| object.
        """

        if remove_nones:
            return super(PhishingIndicator, self).to_dict(remove_nones=True)

        return {
            'indicatorType': self.indicator_type,
            'value': self.value,
            'sourceKey': self.source_key,
            'normalizedIndicatorScore': self.normalized_indicator_score,
            'originalIndicatorScore': self.original_indicator_score
        }
