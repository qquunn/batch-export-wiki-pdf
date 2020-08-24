# -*- coding: utf-8 -*-

import logging
import requests
import os
import time
# import urlparse
from urllib.parse import urlparse
from urllib.parse import urlsplit
from urllib import parse
from pyquery import PyQuery as pq
import re


def generateHeaders():
    headersBrower = '''
Accept:application/json, text/javascript, */*; q=0.01
Accept-Encoding:gzip, deflate, sdch
Accept-Language:en-US,en;q=0.8
Connection:keep-alive
User-Agent:Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36 OPR/44.0.2510.857
    '''

    headersMap = dict()
    for item in headersBrower.splitlines():
        item = str.strip(item)
        if item and ":" in item:
            (key, value) = item.split(":", 1)
            headersMap[str.strip(key)] = str.strip(value)

    return headersMap

# 如果wiki需要登录验证,先用浏览器访问wiki,登录以后,获取该用户的cookie信息. cookie信息一般包含JSESSIONID
def genereateCookies():
    cookieString = "_ga=G;"
    cookieMap1 = {}
    for item in cookieString.split(";"):
        item = str.strip(item)
        if item and "=" in item:
            (key, value) = item.split("=", 1)
            cookieMap1[str.strip(key)] = str.strip(value)

    return cookieMap1



def save_file(url, path):
    if os.path.exists(path):
        logging.debug("exist path=" + path)
        return

    logging.debug("将 %s 保存到 %s" % (url, path))

    logging.debug("start get " + url)

    resp = requests.get(url, timeout=1000, headers=generateHeaders(), cookies=genereateCookies(), stream=True,verify=False)

    if resp.status_code  == 200:

        with open(path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    f.flush()
            f.close()

        logging.debug("save file " + path)

        time.sleep(3)

    else:
        print("error ", resp.status_code)

def parse_host_pageId_fromurl(url):
    # r = urlsplit(url)

    # # print(type(r.scheme),type(r.netloc),type(r.port))

    # # if r.port == None :
    # host = r.scheme + "://" + r.netloc
    # # else :
    #     # host = r.scheme + "://" + r.netloc + ":" + str(r.port)

    # params=parse.parse_qs(r.query,True)
    # print(params)
    # pageId = params["pageId"]

    # return (host, pageId[0])

    print("!!!parse:",url)
    r = urlsplit(url)
    host = r.scheme + "://" + r.netloc
    resp = requests.get(url, timeout=1000, headers=generateHeaders(), cookies=genereateCookies(), stream=True,verify=False)
    if resp.status_code == 200:
        reg=re.compile(r"(?<=pdfpageexport.action\?pageId=)\d+")
        match=reg.search(resp.text)
        if match:
            print("ID:",match.group(0))
            return (host,match.group(0))
            

    print("error ", "cannot find pageID for download in url:", url )
    return 



def get_sub_pages_url(parentUrl):
    print("!!!parentUrl",parentUrl)

    url = "%s/plugins/pagetree/naturalchildren.action?decorator=none&excerpt=false&sort=position&reverse=false&disableLinks=false&expandCurrent=false&hasRoot=true&pageId=%s&treeId=0&startDepth=0" % parse_host_pageId_fromurl(parentUrl)
    print("!!!get_sub_pages_url",url)
    resp = requests.get(url, timeout=1000, headers=generateHeaders(), cookies=genereateCookies(), stream=True,verify=False)

    if resp.status_code == 200:
        doc = pq(resp.text)
        links = []

        for a in doc.find("a").items():
            text = a.text().strip()
            if a.attr("href") and text:
                links.append({
                    "title" : text.encode("utf-8"),
                    "href" : parse.urljoin(parentUrl, a.attr("href"))
                })
        print("links:",links)
        return links

    else :
        logging.error("failed get url %s status_code=%d " % (url, resp.status_code))

    return []

def validateTitle(title):
    rstr = r"[\/\\\:\*\?\"\<\>\|]"  # '/ \ : * ? " < > |'
    new_title = re.sub(rstr, "_", title)  # 替换为下划线
    return new_title

def export_wiki(wiki_title, wiki_page_url, dir):
    if not os.path.exists(dir):
        os.makedirs(dir)

    print("!!!Export:",wiki_page_url)
    export_url = "%s/spaces/flyingpdf/pdfpageexport.action?pageId=%s" % parse_host_pageId_fromurl(wiki_page_url)
    print(dir,'',wiki_title)
    wiki_title=validateTitle(wiki_title)
    save_file(export_url, dir + "/" + wiki_title + ".pdf")

    subpages = get_sub_pages_url(wiki_page_url)
    if subpages :
        parentdir = dir + "/" + wiki_title
        for subpage in subpages :
            export_wiki(str(subpage["title"],encoding = "utf8"), subpage["href"], parentdir)


logging.basicConfig(level=logging.DEBUG)

# 请先修改generateHeaders和genereateCookies方法的配置
wiki_page_url = "https://confluence.cis.unimelb.edu.au:8443/display/SWEN900132019IC/05+Product+Manuals"
wiki_title = "555"
dir = "."
export_wiki(wiki_title, wiki_page_url, dir)
