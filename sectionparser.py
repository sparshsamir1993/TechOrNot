from bs4 import Beautifulsoup
import requests
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from string import punctuation
from heapq import nlargest
from collections import defaultdict

def getwashingtonPost(url, token):
    try:
        page = requests.get(url).content
    except:
        return (None, None)
    soup = Beautifulsoup(page, 'html.parser')

    if soup is None:
        return(None, None)
    text = ""
    if soup.find_all(token) is not None:
        text = ' '.join(map(lambda p: p.text, soup.find_all(token)))
    return text, soup.title.text

def getNYTPost(url, token):
    try:
        page = requests.get(url).content
    except:
        return(None, None)
    soup = BeautifulSoup(page, 'html.parser')
    if soup is None:
        return(None, None)
    text= ""
    title = soup.title.text
    divs = soup.find_all("p", class_"story_content")
    if divs is not None:
        text = ' '.join(map(lambda p: p.text, divs))
    return text, title

def scrapeSource(url, magicFrag='2016', scrapperFunction=getNYTPost, token=None):
    urlBodies = {}
    response = requests.get(url).content
    soup = Beautifulsoup(response, 'html.parser')
    numErr = 0
    for a in soup.findAll('a'):
        try:
            url = a['href']
            if ((url not in urlBodies) and (magicFrag is not None and magicFrag in url) or magicFrag is None):
               body = scrapperFunction(url, token)
               if (body and len(body)>0):
                   urlBodies[url] = body
               print url
        except:
            numErr =+ 1
    return urlBodies





           
