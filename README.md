# SimpleCrawler
* This web crawler can be used to crawl a website from the command line or code

# Install
* Python required (3.6+) https://www.python.org/downloads/
* `pip install SimpleCrawler`

OR

* `git clone https://github.com/jackwardell/SimpleCrawler.git`
* `cd SimpleCrawler`
* `python3 -m venv venv`
* `source venv/bin/activate`
* `pip install --upgrade pip`
* `pip install -r requirements.txt`
* `pip install -e .`
* `pytest`
* `crawl https://www.example.com`

# Rules:
This crawler will:
* Only crawl text/html mime-types
* Only crawl pages that return 200 OK HTTP statuses
* Look at /robots.txt and obey by default (but can be overridden)
* Add User-Agent, default value = PyWebCrawler (but can be changed)
* Ignore ?query=strings and #fragments by default (but can be changed)
* Get links from ONLY href value in `<a href='/some-link'>click here</a>` tags

Todo:
* Nicer logging
* Crawl client errors and server error pages? (Most websites have 404 & 500 handlers which may have links)
* Parse more than just `<a>` tags and href attrs e.g. `src='/some-link'`
* Add a scheduler / wait frequency (Politeness)
* Request timeout


# Use
* just type `crawl <url>` into your command line e.g. `crawl https://www.google.com`

```
$ crawl --help
Usage: crawl [OPTIONS] URL

Options:
  -u, --user-agent TEXT
  -w, --max-workers INTEGER
  -t, --timeout INTEGER
  -h, --check-head
  -d, --disobey-robots
  -wq, --with-query
  -wf, --with-fragment
  --debug / --no-debug
  --help                     Show this message and exit.
```

optional params:

- "--user-agent" or "-u"
    - what the User-Agent header param is
    - default = 'PyWebCrawler'
- "--max-workers" or "-w"
    - max number of worker threads
    - default = 1
- "--timeout" or "-t"
    - how long to wait for new items from work queue before shutting down
    - default = 10
- "--check-head" or "-t"
    - whether to send HEAD request before sending GET request
    - why? some GET responses will be large (e.g. pdf) and sending HEAD request first will allow crawler to see MIME type before it makes a GET request, therefore averting the GET request altogether
    - default = False
- "--disobey-robots" or "-d"
    - whether to disobey robots.txt file
    - default = False
- "--with-query" or "-wq"
    - whether to allow query args e.g. https://www.example.com/?hello=world -> https://www.example.com/ if not --with-query
    - default = False
- "--with-fragment" or "-wf"
    - whether to allow fragments e.g. https://www.example.com/#helloworld -> https://www.example.com/ if not --with-fragment
    - default = False
- "--debug/--no-debug", default=False
    - whether to run the crawl, if debug on, then it wont crawl but will pump out crawler config
    - default = False


OR from code

```
from simple_crawler import Crawler

crawler = Crawler()
found_links = crawler.crawl('https://www.example.com/')
```
