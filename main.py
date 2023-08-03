import json
import os
import re

import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 "
}


def getcookies_decode_to_dict():
    cookies_dict = {}
    with open('cookies.json', 'r') as f:
        cookies = json.loads(f.read())
        for cookie in cookies:
            cookies_dict[cookie['name']] = cookie['value']
    return cookies_dict


def get_title_and_sumpage(session, post_url):
    response = session.get(post_url, headers=headers)
    soup = BeautifulSoup(response.text, 'lxml')
    # print(soup.title)
    title = soup.title.text
    title = title.replace("【图片】", "").replace("_百度贴吧", "")
    page_info = soup.find('li', class_='l_reply_num').text
    author = soup.find('div', class_='louzhubiaoshi')['author']
    sumpage = (re.search(r'共(\d+)页', page_info)).group(1)

    return title, author, int(sumpage)


# 获取该页面内的所有楼层内容
def get_text(soup) -> list:
    items_with_class = soup.find_all(class_="d_post_content j_d_post_content")
    text_list = []
    # print(items_with_class)
    for item in items_with_class:
        # 去除首尾空格
        text_list.append(item.get_text().strip() + "\n")
    return text_list


# 获取该页面内的所有楼层数和发帖时间
def get_floor_info(soup):
    items_with_class = soup.find_all(class_="post-tail-wrap")
    floor_info_list = []
    for item in items_with_class:
        info_soup = BeautifulSoup(str(item), 'lxml')
        tail_info_elements = info_soup.find_all(class_='tail-info')
        tail_info_texts = [element.get_text() for element in tail_info_elements]
        floor_info_list.append([tail_info_texts[2], tail_info_texts[3]])
    return floor_info_list


if __name__ == '__main__':
    tid = "8528911427"
    post_url = rf"https://tieba.baidu.com/p/{tid}?see_lz=1"
    session = requests.session()
    cookies_dict = getcookies_decode_to_dict()
    session.cookies.update(cookies_dict)

    title, author, sumpage = get_title_and_sumpage(session, post_url)
    print(title, sumpage)

    # 创建以标题为名的文件夹
    if not os.path.exists(title):
        os.mkdir(title)

    os.chdir(title)
    text_list = []

    # eg.[['1楼', '2023-07-31 02:10'], ['2楼', '2023-07-31 02:12']]
    floor_info_list = []
    content_str = f"## {title}\n\n原文地址：{post_url}\n\n作者：{author}\n\n"

    for i in range(1, sumpage + 1):
        print(f"共{sumpage}页，正在下载第{i}页")
        page_url = rf"https://tieba.baidu.com/p/{tid}?see_lz=1&pn={i}"
        response = session.get(page_url, headers=headers)
        soup = BeautifulSoup(response.text, 'lxml')
        floor_info_list.append(get_floor_info(soup))
        text_list.append(get_text(soup))
        # print(text_list)
        break

    # print(len(floor_info_list[0]), len(text_list[0]))
    # print(floor_info_list[0])
    # print(text_list[0])

    for i in range(sumpage):
        for floor in zip(floor_info_list[i], text_list[i]):
            content_str += f'##### <span id="{floor[i][0]}">{floor[i][0]} 发表于{floor[i][1]}</span>\n'
            content_str += floor[1] + "\n"
        break

    print(content_str)
    with open('content.md', 'w', encoding='utf-8') as f:
        f.write(content_str)
