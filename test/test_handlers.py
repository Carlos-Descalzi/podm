# vim:ts=4:sw=4:expandtab
import unittest
from podm import JsonObject, ListStringHandler, Property


class Company:
    def __init__(self, string):
        self.string = string

    def __str__(self):
        return self.string


class Companies(JsonObject):
    company_list = Property("companies", default=[], handler=ListStringHandler(Company))


class TestHandlers(unittest.TestCase):
    def test_ListStringHandler_encoding(self):
        reference_list = ["company1", "company2", "company3"]
        data = {"companies": reference_list }
        companies = Companies.from_dict(data)

        self.assertTrue(all(isinstance(company, Company) for company in companies.company_list))
        self.assertCountEqual([str(c) for c in companies.company_list], reference_list)

    def test_ListStringHandler_decoding(self):
        reference_list = ["company1", "company2", "company3"]
        companies = Companies()
        companies.company_list = [Company(c) for c in reference_list]
        data = companies.to_dict()

        self.assertCountEqual(data["companies"], reference_list)

