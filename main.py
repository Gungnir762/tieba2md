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
def get_text(soup, img_dir) -> list:
    items_with_class = soup.find_all(class_="d_post_content j_d_post_content")
    text_list = []
    # print(items_with_class)
    for item in items_with_class:
        # 去除首尾空格
        text = item.get_text().strip() + "\n"
        # 保存可能存在的图片
        soup_img = BeautifulSoup(str(item), "lxml")
        try:
            img_src = soup_img.find('img')['src']
            # print(img_src)
            img_name = (img_src.split("/")[-1]).split("?")[0]
            # print(img_name)
            img_path = os.path.join(img_dir, img_name)
            img_text = f"![{img_name.split('.')[0]}]({img_path})"
            text += img_text + "\n"
            with open(img_path, "wb") as f:
                f.write(requests.get(img_src).content)
        except:
            # print("没有图片")
            pass
        text_list.append(text)
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

    img_dir = "./images"

    session = requests.session()
    cookies_dict = getcookies_decode_to_dict()
    session.cookies.update(cookies_dict)

    title, author, sumpage = get_title_and_sumpage(session, post_url)
    print(title, sumpage)

    # 创建以标题为名的文件夹
    if not os.path.exists(title):
        os.mkdir(title)
    os.chdir(title)
    if not os.path.exists(img_dir):
        os.mkdir(img_dir)

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
        text_list.append(get_text(soup, img_dir))

    # with open('floor_info_list.json', 'w', encoding='utf-8') as f:
    #     f.write(json.dumps(floor_info_list, ensure_ascii=False))
    #
    # with open('text_list.json', 'w', encoding='utf-8') as f:
    #     f.write(json.dumps(text_list, ensure_ascii=False))

    # 共8页就是range(7)
    for i in range(sumpage):
        print(f"正在写入第{i + 1}页")
        for floor, text in zip(floor_info_list[i], text_list[i]):
            content_str += f'##### <span id="{floor[0]}">{floor[0]} 发表于{floor[1]}</span>\n'
            content_str += text + "\n"

    # print(content_str)
    with open('content.md', 'w', encoding='utf-8') as f:
        f.write(content_str)
