#!/usr/bin/env python
# easy_install -U simplejson beautifulsoup4 requests lxml
import sys
import json
import bs4
import requests
import multiprocessing
import simplejson

DOMAIN = 'http://www.agc.gov.my'

FIRST_PAGE = 'http://www.agc.gov.my/index.php?option=com_content&view=article&id=1406&Itemid=259'


class Law(object):
    def __init__(self, silent = False):
        self.headers = {}
        self.headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64; rv:18.0) Gecko/20100101 Firefox/18.0)'
        self.silent = silent

    def find_laws(self):
        r = requests.get(FIRST_PAGE, headers=self.headers)
        if r.status_code != 200:
            sys.exit('YOU FAILED!!! HTTP ERROR %d' % r.status_code)
        vs = LawPages(r.text)
        return vs.give_pages()

    def fetch(self):
        suppliers = self.find_laws()

        manager = multiprocessing.Manager()
        laws = manager.list()

        stores = []
        for s in suppliers:
            process = multiprocessing.Process(target=self._fetch_law,
                                              args=(s, laws))
            stores.append(process)
            process.start()

        for store in stores:
            store.join()
        return laws

    def dump_to_json(self):
        laws = self.fetch()
        data = {'lom': list(laws)}
        return json.dumps(data)

    def _fetch_law(self, task, storage):
        number, link = task
        if not self.silent:
            print 'Requesting page %s' % number
        r = requests.get(link, headers=self.headers)
        
        if r.status_code != 200:
            sys.exit('CONNECTION ERROR!!! HTTP ERROR %d' % r.status_code)
        vs = LawPages(r.text)
        storage.extend(vs.extract())
        

class LawPages(object):
    def __init__(self, html):
        self.html = bs4.BeautifulSoup(html, 'lxml')
        self.content = self.html.find('div', {'class': 'article-content'})
        self.tables = self.content.find_all('table') if self.content else []

    def give_pages(self):
        links = self.tables[1].find_all('a')
        return map(lambda link: (link.text.strip(), DOMAIN + link['href']), links)
            
    def _get_rows(self):
        return self.tables[3].find('tbody').find_all('td')
        
    def _extract_row(self, rnumber, rcontent):
        number = rnumber.find('p').text.strip()
        p = rcontent.find('p')
        dloms = p.find_all('a')

        docs = {}
        for d in dloms:
            docs[d.text.strip()] = DOMAIN + d['href']

        ems = p.find_all('em')
        for e in ems:
            name = e.text.strip()
            if not docs.get(name):
                docs[name] = None

        ldocs = []
        for name, link in docs.iteritems():
            ldocs.append({'name': name,
                          'link': link})

        return {'number': number,
                'docs': ldocs}
        
    def extract(self):
        number, content = 0, 1
        loms = []
        rows = self._get_rows()
        while content < len(rows):
            loms.append(self._extract_row(rows[number],
                                             rows[content]))
            number, content = content +1, content + 2
        return loms

    def extract_to_json(self):
        data = {'lom': self.extract()}
        return simplejson.dumps(data,sort_keys=True, indent=4, separators=(',', ': '))
        
if __name__ == '__main__':
    scraper = Law(True)
    print scraper.dump_to_json()
