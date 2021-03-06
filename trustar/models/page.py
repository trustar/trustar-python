# python 2 backwards compatibility
from __future__ import print_function

# package imports
from .base import ModelBase


class Page(ModelBase):
    """
    This is the base class used to define default methods and attributes for all classes which will be used for
    pagination of the TruSTAR public API.

    :ivar items: The list of items of the page; i.e. a list of indicators, reports, etc.
    """

    def __init__(self, items=None):
        self.items = items

    def __len__(self):
        return len(self.items)

    def __iter__(self):
        return self.items.__iter__()

    def __getitem__(self, item):
        return self.items[item]

    @classmethod
    def get_generator(cls, page_generator):
        """
        Gets a generator for retrieving all results from a paginated endpoint.  Pass exactly one of ``page_generator``
        or ``func``.  This method is intended for internal use.

        :param page_generator: A generator to be used to generate each successive |Page|.
        :return: A generator that generates each successive element.
        """

        # yield each item in the page one by one;
        # once it is out, generate the next page
        for page in page_generator:
            for item in page.items:
                yield item
