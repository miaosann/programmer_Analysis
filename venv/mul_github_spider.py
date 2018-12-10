# -*- coding: utf-8 -*-
from multiprocessing import Pool, cpu_count, Manager
import threading
import pandas as pd
import csv
import requests
from bs4 import BeautifulSoup
try:
    from functools import namedtuple
except ImportError:
    from collections import namedtuple

HEADER = {
    'User-Agent': "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1"
}
COLUMNS = ['user', 'name', 'position', 'repositories', 'stars', 'followers', 'following', 'contributions']
PROFILE = namedtuple('PROFILE', COLUMNS)

DF = pd.DataFrame(columns=COLUMNS, index=["0"])
lock = threading.Lock()  # 全局资源锁


def _str_2_int(stri):
    if 'k' in stri:
        return int(float(stri[:-1]) * 1000)
    if ',' in stri:
        return int(stri.replace(',', ''))
    else:
        return int(stri)


def user_crawler(user,Result):
    url = 'https://github.com/{}'.format(user)
    values = [None] * len(COLUMNS)
    values[COLUMNS.index('user')] = user
    try:
        html = requests.get(url, headers=HEADER, timeout=10).text
        soup = BeautifulSoup(html, 'lxml')

        tag_name = soup.find_all('span', class_='p-name vcard-fullname d-block')
        if len(tag_name) > 0:
            name = tag_name[0].text
            if len(name) > 0:
                values[COLUMNS.index('name')] = name

        tag_position = soup.find_all('span', class_='p-label')
        if len(tag_position) > 0:
            position = tag_position[0].text
            values[COLUMNS.index('position')] = position

        tags_overview = soup.find_all('span', class_='Counter')
        repositories = _str_2_int(tags_overview[0].text.replace('\n', '').replace(' ', ''))
        stars = _str_2_int(tags_overview[1].text.replace('\n', '').replace(' ', ''))
        followers = _str_2_int(tags_overview[2].text.replace('\n', '').replace(' ', ''))
        following = _str_2_int(tags_overview[3].text.replace('\n', '').replace(' ', ''))
        values[COLUMNS.index('repositories')] = repositories
        values[COLUMNS.index('stars')] = stars
        values[COLUMNS.index('followers')] = followers
        values[COLUMNS.index('following')] = following

        tag_contributions = soup.find_all('h2', class_='f4 text-normal mb-2')
        try:
            contributions = _str_2_int(
                tag_contributions[0].text.replace('\n', '').replace(' ', '').replace('contributionsinthelastyear', ''))
        except Exception as err:
            contributions = _str_2_int(
                tag_contributions[0].text.replace('\n', '').replace(' ', '').replace('contributioninthelastyear', ''))
        values[COLUMNS.index('contributions')] = contributions

        print(values)
        Result.append(values)
    except Exception as e:
        print(e)


def get_all_followers(user):
    followers_list = []
    idx = 0
    url = "https://github.com/{}?tab=followers"
    while True:
        idx += 1
        if idx > 1:
            page_url = url
        else:
            page_url = url.format(user)

        print("PAGE_URL："+page_url)
        try:
            html = requests.get(page_url, headers=HEADER, timeout=10).text
            #print("HTML："+html)
            if '<span class="disabled">Next</span>' in html:
                break
            soup = BeautifulSoup(html, 'lxml')
            tag_names = soup.find_all('span', class_='link-gray pl-1')
            for name in tag_names:
                followers_list.append(name.text)
            if '<div class="paginate-container">' not in html:
                break
            nextUrl = soup.find('div', class_='pagination').children
            for urlItem in nextUrl:
                if urlItem.string == "Next":
                    #print(urlItem.attrs['href'])
                    url = urlItem.attrs['href']
                    #print("hh："+url)

        except Exception as e:
            print(e)
    return followers_list


def save():
    with open("result.csv", "w+" ,encoding='utf-8-sig' ,newline='') as f:
        f_csv = csv.writer(f)
        f_csv.writerow(COLUMNS)
        f_csv.writerows(Result)
        print('data saved')


if __name__ == '__main__':

    Result = Manager().list()
    main_user = ''
    print('Let us begin ...')
    followers_list = get_all_followers(main_user)
    pool = Pool(processes=cpu_count())
    for user in followers_list:
        pool.apply_async(user_crawler, args=(user,Result,))

    pool.close()

    pool.join()
    print("总数为："+str(len(Result)))
    print(Result)
    save()