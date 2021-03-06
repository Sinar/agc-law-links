__author__ = 'lowks'

import unittest
import json

import requests_mock
import agc_law
import sys
from agc_law import Law, LawPages
from mock import patch, Mock, call
from cStringIO import StringIO


class AGCTests(unittest.TestCase):

    def setUp(self):
        self.law = Law()
        self.input_html = """<div class="article-content">
<table><a href="hoho">hoho</a></table>
<table><a href="hehe">hehe</a></table></div>"""
        self.lp = LawPages(self.input_html)

    @patch("agc_law.requests")
    @patch("agc_law.LawPages")
    def test_find_laws(self, mock_law_pages, mock_requests):

        """Test for find_laws using mock 200 request"""

        mock_requests.get.return_value.status_code = 200
        mock_law_pages.return_value.give_pages.return_value = 'hulahoop'
        self.assertEqual(self.law.find_laws(), 'hulahoop')

    @patch("agc_law.requests")
    def test_find_laws_exception(self, mock_requests):

        """Test for find_laws exception using mock 400 status_code"""

        mock_requests.get.return_value.status_code = 400
        with self.assertRaises(SystemExit):
            self.law.find_laws()

    @patch("agc_law.Law.fetch")
    def test_dump_to_json(self, mock_fetch):

        """Test for dump_to_json using mock_fetch value"""

        mock_fetch.return_value = "mypage"
        self.assertTrue(self.law.dump_to_json(),
                        json.dumps({'lom': list("mypage")}))

    def test_lp_give_pages(self):
        self.assertListEqual(self.lp.give_pages(),
                             [(u'hehe', 'http://www.agc.gov.myhehe')])

    @patch("agc_law.LawPages.extract")
    def test_extract_to_json(self, mock_extract):

        """Test for extract_to_json using mock extract value"""

        mock_extract.return_value = "gula"
        data = self.lp.extract_to_json()
        self.assertEqual(data, '{\n    "lom": "gula"\n}')

    @patch("agc_law.requests")
    def test_private_fetch_law_exception(self, mock_requests):

        """Testing _fetch_law with mock 404 request to raise exception"""

        mock_requests.get.return_value.status_code = 404
        setattr(self.law, 'silent', True)
        with self.assertRaises(SystemExit):
            self.law._fetch_law(('test', 'test'), Mock())

    @patch("agc_law.LawPages.extract")
    def test_private_fetch_law(self, mock_law_pages):

        """Testing _fetch_law with mock requests and capturing stdout"""

        with requests_mock.mock() as mock_requests:
            test_text = (self.input_html.rstrip('</div>') +
                                               """><table><a href="gigi">gigi</table>
<table><tbody><a href="gogo">gogo</table></tbody></div>""")
            mock_requests.get(agc_law.FIRST_PAGE, text=test_text, status_code=200)
            mock_storage = Mock()
            mock_law_pages.return_value = "hulahoop"
            sys.stdout = captured = StringIO()
            self.law._fetch_law(('test', agc_law.FIRST_PAGE), mock_storage)
            self.assertEqual(captured.getvalue(),
                             'Requesting page test\n')
            self.assertIn(call('hulahoop'), mock_storage.extend.call_args_list)
            sys.stdout = sys.__stdout__

    @patch("agc_law.LawPages._get_rows")
    @patch("agc_law.LawPages._extract_row")
    def test_law_pages_extract(self, mock_extract_rows, mock_get_rows):

        """Test to verify extract method of LawPages"""

        mock_get_rows.return_value = ["row1", "row2", "row3"]
        mock_extract_rows.return_value = {'number': 'number1', 'docs': 'doc1'}
        result = self.lp.extract()
        self.assertEqual(result, [{'docs': 'doc1', 'number': 'number1'}])

    def test_law_pages_private_extract_row(self):

        """Test asserting correct calls are made in _extract_row"""

        input_html = """<div class="article-content">
<table>
<a href="hoho">
    <p>hoho</p>
</a>
</table>
<table>
    <a href="hehe">
        <p>hehe</p>
    </a>
</table>
<table>
    <a href="hoho">
        <tbody>
            <td>
                <p>hoho</p>
            </td>
        </tbody>
    </a>
</table>
<table>
    <a href="hoho">
        <tbody>
        <td>
            <p>
                <a href="www.harhar.com">harhar</a>
            </p>
        </td>
    <a href="hoho">
        <td>
            <p>
                <a href="www.herher.com">herher</a>
            </p>
        </td>
    </tbody>
</table>
</div>"""

        law_pages = LawPages(input_html)
        rows = law_pages._get_rows()

        real_value = agc_law.DOMAIN

        agc_law.DOMAIN = "http://abc.com"

        result = self.lp._extract_row(rows[0], rows[1])
        self.assertEqual(result, {'docs': [{'link': 'http://abc.comwww.herher.com',
                                            'name': u'herher'}],
                                  'number': u'harhar'})
        agc_law.DOMAIN = real_value

    @patch("agc_law.multiprocessing.Manager")
    @patch("agc_law.multiprocessing.Process.start")
    @patch("agc_law.multiprocessing.Process.join")
    @patch("agc_law.Law.find_laws")
    def test_fetch(self, mock_find_law, mock_process_join,
                   mock_process_start, mock_process_manager):

        """Test to verify fetch method of Law"""

        mock_find_law.return_value = [1, 2, 3]
        mock_process_manager.list.return_value = [3, 4, 5]
        self.law.fetch()
        self.assertEqual(mock_process_join.call_count, 3)
        self.assertEqual(mock_process_start.call_count, 3)
        self.assertEqual(mock_process_manager.call_count, 1)
