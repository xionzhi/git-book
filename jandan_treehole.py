#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：test_dev 
@File    ：jandan_treehole.py
@Author  ：xionzhi
@Date    ：2023/6/6 16:48
"""

import asyncio
from base64 import b64encode
from datetime import datetime

try:
    import aiohttp
    import click
    from lxml import etree
except ImportError as e:
    msg = f"""
    {e.msg}
    pip install click==8.1.3 aiohttp==3.8.4 lxml==4.9.2
    """
    raise ImportError(msg)


class JanDanTreeHole:
    def __init__(self):
        self.base_url = 'https://jandan.net/treehole'
        self.datetime_now = datetime.now().strftime('%Y%m%d')

    @staticmethod
    async def fetch(client, url: str) -> str:
        async with client.get(url) as resp:
            assert resp.status == 200
            return await resp.text()

    @staticmethod
    def parse_page_number(resp: str) -> int:
        elem = etree.HTML(resp)
        page_number = elem.xpath('//*[@id="comments"]/div[2]/div/span/text()')[0]
        return int(page_number[1:-1])

    def parse_post_info(self, resp: str):
        elem = etree.HTML(resp)
        elem_post_list = elem.xpath('//ol[@class="commentlist"]/li')
        for elem_post in elem_post_list:
            author = elem_post.xpath('.//div[@class="author"]/strong/text()')
            small = elem_post.xpath('.//div[@class="author"]//a/text()')
            text = elem_post.xpath('.//div[@class="text"]//p/text()')
            oo = elem_post.xpath('.//span[@class="tucao-like-container"]/span/text()')
            xx = elem_post.xpath('.//span[@class="tucao-unlike-container"]/span/text()')
            tc = elem_post.xpath('.//a[@class="tucao-btn"]/text()')
            index = elem_post.xpath('.//span[@class="righttext"]/a/text()')
            post_dict = {
                'author': author[0] if author else '',
                'small': small[0] if small else '',
                'text': text[0] if text else '',
                'oo': f'OO [{oo[0] if oo else ""}]',
                'xx': f'XX [{xx[0] if xx else ""}]',
                'tc': tc[0] if tc else '',
                'index': index[0] if index else '',
            }
            self.format_print(post_dict)

    @staticmethod
    def format_print(post_dict: dict):
        def _new_line(text):
            _text, _size = '', 20
            if len(text) < _size:
                _text = text
            else:
                while True:
                    if len(text) < _size:
                        _text += text
                        break
                    _text += f'{text[0:_size]}\n{" " * 8}'
                    text = text[_size:]
            return _text

        # {(textwrap.wrap(post_dict['text'], width=20))}
        click.echo(f"""
        {post_dict['author']}{" " * 15}{post_dict['small']}
        https://jandan.net/t/{post_dict['index']}
        
        {_new_line(post_dict['text'])}
        
        {post_dict['oo']}{" " * 4}{post_dict['xx']}{" " * 4}{post_dict['tc']}
        {'-' * 40}""")

    async def max_page_number(self):
        async with aiohttp.ClientSession() as client:
            page_number = self.parse_page_number(await self.fetch(client, self.base_url))
        click.echo(f'max page size is: {page_number}')

    async def get_page_info(self, page: int):
        async with aiohttp.ClientSession() as client:
            page_base64 = b64encode(f'{self.datetime_now}-{page}'.encode('utf-8')).decode('utf-8')
            page_url = f'{self.base_url}/{page_base64}#comments'
            page_html = await self.fetch(client, page_url)
            self.parse_post_info(page_html)

    async def run(self, count=None):
        async with aiohttp.ClientSession() as client:
            page_number = self.parse_page_number(await self.fetch(client, self.base_url))
            for page in range(page_number, 0, -1):
                page_base64 = b64encode(f'{self.datetime_now}-{page}'.encode('utf-8')).decode('utf-8')
                page_url = f'{self.base_url}/{page_base64}#comments'
                page_html = await self.fetch(client, page_url)
                self.parse_post_info(page_html)

                if count:
                    if count == 1:
                        break
                    count -= 1


@click.command()
@click.option('--count', default=5, type=click.INT, help='Number of pages to view.')
@click.option('--page', default=0, type=click.INT, help='Page number to be viewed.')
@click.option('--max_page', default=False, type=click.BOOL, help='Max Page number.')
def main(count: int, page: int, max_page: bool):
    jd_treehole = JanDanTreeHole()
    loop = asyncio.get_event_loop()

    if max_page is True:
        loop.run_until_complete(jd_treehole.max_page_number())
        return 1

    if page > 0:
        loop.run_until_complete(jd_treehole.get_page_info(page))
        return 1

    loop.run_until_complete(jd_treehole.run(count=count if count else None))


if __name__ == '__main__':
    main()
