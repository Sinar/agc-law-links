__author__ = 'lowks'

import unittest
import json

import requests_mock
import agc_law
from agc_law import Law, LawPages
from mock import patch, Mock, call


class AGCTest(unittest.TestCase):

    def setUp(self):
        self.law = Law()
        self.input_html = """<div class="article-content">
<table><a href="hoho">hoho</a></table>
<table><a href="hehe">hehe</a></table></div>"""
        self.lp = LawPages(self.input_html)

    @patch("agc_law.requests")
    @patch("agc_law.LawPages")
    def test_find_laws(self, mock_law_pages, mock_requests):
        mock_requests.get.return_value.status_code = 200
        mock_law_pages.return_value.give_pages.return_value = 'hulahoop'
        self.assertEqual(self.law.find_laws(), 'hulahoop')

    @patch("agc_law.requests")
    def test_find_laws_exception(self, mock_requests):
        mock_requests.get.return_value.status_code = 400
        with self.assertRaises(SystemExit):
            self.law.find_laws()

    @patch("agc_law.Law.fetch")
    def test_dump_to_json(self, mock_fetch):
        mock_fetch.return_value = "mypage"
        self.assertTrue(self.law.dump_to_json(),
                        json.dumps({'lom': list("mypage")}))

    def test_lp_give_pages(self):
        self.assertListEqual(self.lp.give_pages(),
                             [(u'hehe', 'http://www.agc.gov.myhehe')])

    @patch("agc_law.LawPages.extract")
    def test_extract_to_json(self, mock_extract):
        mock_extract.return_value = "gula"
        data = self.lp.extract_to_json()
        self.assertEqual(data, '{\n    "lom": "gula"\n}')

    @patch("agc_law.requests")
    def test_private_fetch_law_exception(self, mock_requests):
        mock_requests.get.return_value.status_code = 404
        with self.assertRaises(SystemExit):
            self.law._fetch_law(('test', 'test'), Mock())

    @patch("agc_law.LawPages.extract")
    def test_private_fetch_law(self, mock_law_pages):
        with requests_mock.mock() as mock_requests:
            test_text = (self.input_html.rstrip('</div>') +
                                               """><table><a href="gigi">gigi</table>
<table><tbody><a href="gogo">gogo</table></tbody></div>""")
            mock_requests.get(agc_law.FIRST_PAGE, text=test_text, status_code=200)
            mock_storage = Mock()
            mock_law_pages.return_value = "hulahoop"
            self.law._fetch_law(('test', agc_law.FIRST_PAGE), mock_storage)
            self.assertIn(call('hulahoop'), mock_storage.extend.call_args_list)

    @patch("agc_law.LawPages._get_rows")
    @patch("agc_law.LawPages._extract_row")
    def test_law_pages_extract(self, mock_extract_rows, mock_get_rows):
        mock_get_rows.return_value = ["row1", "row2", "row3"]
        mock_extract_rows.return_value = {'number': 'number1', 'docs': 'doc1'}
        result = self.lp.extract()
        self.assertEqual(result, [{'docs': 'doc1', 'number': 'number1'}])
