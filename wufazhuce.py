#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：test_dev 
@File    ：wufazhuce.py
@Author  ：xionzhi
@Date    ：2023/6/30 15:55 
"""
import asyncio
import os

import aiohttp
from aiofile import async_open
from lxml import etree


class WuFaZhuCeSpider:
    def __init__(self):
        self.headers = {'Referer': 'http://wufazhuce.com/'}

    async def read_image_save(self, file_name):
        async with async_open(file_name) as afp:
            url_txt = await afp.read()
        async with aiohttp.ClientSession() as session:
            for url_item in url_txt.split('\n'):
                idx, img_url = url_item.split(',')
                async with session.request(method='GET', url=img_url, headers=self.headers) as response:
                    if response.status == 200:
                        file_stream = await response.read()
                    else:
                        continue

                async with async_open(f'images/{idx}_{img_url.split("/")[-1]}', 'wb') as afp:
                    await afp.write(file_stream)

    """页面处理"""

    @staticmethod
    async def request(session, method, url, **kwargs):
        async with session.request(method=method, url=url, **kwargs) as response:
            print('[request] --> text', url, response.status)
            if response.status == 200:
                return await response.text()

    @staticmethod
    async def write_url(file_name, text):
        print('[write] --> url', text)
        async with async_open(file_name, 'a') as afp:
            await afp.write(text + '\n')

    @staticmethod
    async def save_html(file_name, html):
        print('[save] --> html', file_name)
        async with async_open(file_name, 'a') as afp:
            await afp.write(html)

    async def xpath_image_url(self, path_key, idx, html):
        img_url_xpath = {
            'one': '//div[@class="one-imagen"]/img/@src',
            'article': '//div[@class="articulo-contenido"]/div/img/@src',
            'question': '//div[@class="cuestion-contenido"]/div/img/@src'
        }
        html_tree = etree.HTML(html)
        img_url = html_tree.xpath(img_url_xpath[path_key])
        if img_url:
            await self.write_url(f'{path_key}/image_url.txt', f'{idx},{img_url[0]}')

    async def loop_post_run(self, path_key, max_id, min_id):
        async with aiohttp.ClientSession() as session:
            for idx in range(max_id, min_id, -1):
                url = f'http://wufazhuce.com/{path_key}/{idx}'
                html = await self.request(session, method='GET', url=url, headers=self.headers)
                if html:
                    # 储存html
                    await self.save_html(f'{path_key}/html/{idx}.html', html)

                    # 寻找 储存 封面
                    await self.xpath_image_url(path_key, idx, html)

    async def find_max_ids(self):
        async with aiohttp.ClientSession() as session:
            async with session.request(method='GET', url='http://wufazhuce.com', headers=self.headers) as response:
                html = await response.text()
        html_tree = etree.HTML(html)

        one_url = html_tree.xpath('//div[@id="carousel-one"]/div/div[1]/a/@href')
        article_url = html_tree.xpath('//p[@class="one-articulo-titulo"]/a/@href')
        question_url = html_tree.xpath('//div[@class="fp-one-cita"]/a/@href')

        _slice_id = lambda x: x[0].split('/')[-1]

        one_id, article_id, question_id = _slice_id(one_url), _slice_id(article_url), _slice_id(question_url)
        return {
            'one': int(one_id),
            'article': int(article_id),
            'question': int(question_id),
        }

    async def run(self):
        tasks_setting = [
            {'path_key': 'one', 'max_id': 0, 'min_id': 0},
            {'path_key': 'article', 'max_id': 0, 'min_id': 0},
            {'path_key': 'question', 'max_id': 0, 'min_id': 0},
        ]

        max_id_dict = await self.find_max_ids()
        tasks = []
        for task in tasks_setting:
            task['max_id'] = max_id_dict[task['path_key']]
            os.makedirs(f"{task['path_key']}/html", exist_ok=True)
            print(task)
            tasks.append(self.loop_post_run(**task))

        await asyncio.gather(*tasks)


if __name__ == '__main__':
    ws = WuFaZhuCeSpider()
    asyncio.run(ws.run())
