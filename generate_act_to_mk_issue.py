#!/usr/bin/env python3
import re
import sys
from typing import List, Tuple, Any
from urllib import request
from html.parser import HTMLParser

URL_PATTERN = "http://www.kozlonyok.hu/nkonline/index.php?menuindex=200&pageindex=kozltart&ev={year}&szam={issue}"
ACT_ID_RE = re.compile(r'20..\. évi .* törvény')


class MkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tag_stack: Tuple[str, ...] = ()
        self.tags: List[Tuple[Tuple[str, ...], str]] = []

    def handle_starttag(self, tag: str, attrs: Any) -> None:
        self.tag_stack = self.tag_stack + (tag, )

    def handle_endtag(self, tag: str) -> None:
        while tag in self.tag_stack:
            self.tag_stack = self.tag_stack[:-1]

    def handle_data(self, data: str) -> None:
        data = data.strip()
        data = data.replace('\xa0', ' ')
        if data:
            self.tags.append((
                self.tag_stack,
                data
            ))

    def error(self, message: str) -> None:
        pass


def parse_single_issue(year: int, issue: int) -> None:
    url_to_download = URL_PATTERN.format(year=year, issue=issue)
    for _ in range(5):
        try:
            with request.urlopen(url_to_download) as downloaded_file:
                downloaded_data = downloaded_file.read()
            break
        except Exception as e:
            print("Problem downloading ", url_to_download, e, file=sys.stderr)
    else:
        raise ValueError("Could not download in 5 tries, stopping")

    parser = MkParser()
    parser.feed(downloaded_data.decode('utf-8'))
    parser.close()
    previous_id = None
    for _path, data in parser.tags:
        if ACT_ID_RE.match(data):
            previous_id = data
        elif previous_id is not None:
            if "," in data:
                data = '"{}"'.format(data)
            print('{}/{},{},{}'.format(year, issue, previous_id, data))
            previous_id = None


def parse_all() -> None:
    for year in range(2009, 2022):
        for issue in range(1, 360):
            parse_single_issue(year, issue)


print("This script will use the kozlonyok.hu server pretty heavily", file=sys.stderr)
print("Please be considearate and don't run it, but instead use the", file=sys.stderr)
print("already committed act_to_mk_issue.csv", file=sys.stderr)
print("Press enter to continue", file=sys.stderr)
sys.stdin.readline()

parse_all()
