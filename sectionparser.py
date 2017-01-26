from bs4 import BeautifulSoup
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
    soup = BeautifulSoup(page, 'html.parser')

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
    divs = soup.find_all("p", class_="story_content")
    if divs is not None:
        text = ' '.join(map(lambda p: p.text, divs))
    return text, title

def scrapeSource(url, magicFrag='2016', scrapperFunction=getNYTPost, token=None):
    urlBodies = {}
    response = requests.get(url).content
    soup = BeautifulSoup(response, 'html.parser')
    numErr = 0
    for a in soup.findAll('a'):
        try:
            url = a['href']
            if ((url not in urlBodies) and (magicFrag is not None and magicFrag in url) or magicFrag is None):
               body = scrapperFunction(url, token)
               if (body and len(body)>0):
                   urlBodies[url] = body
               """print (url)"""
        except:
            numErr =+ 1
    return urlBodies


class FrequencySummarizer:
    def __init__(self,min_cut=0.1,max_cut=0.9):
        self._min_cut = min_cut
        self._max_cut = max_cut
        self._stopwords = set(stopwords.words('english') +
                              list(punctuation) +
                              [u"'s",'"'])
    
    def _compute_frequencies(self,word_sent):
        freq = defaultdict(int)
     
        for sentence in word_sent:
            for word in sentence:
                if word not in self._stopwords:
                    freq[word] += 1
        try:
            m = float(max(freq.values()))
        except:
            m = 1
        print (m)
        for word in list(freq.keys()):
            freq[word] = freq[word]/m
            if freq[word] > self._max_cut or freq[word] < self._min_cut:
                del freq[word]
        return freq
    
    def extractFeatures(self,article,n,customStopWords=None):
        text = article[0]
        title = article[1]
        sentences = sent_tokenize(text)
        word_sent = [word_tokenize(s.lower()) for s in sentences]
        self._freq = self._compute_frequencies(word_sent)
        if n < 0:
            return nlargest(len(self._freq.keys()),self._freq,key=self._freq.get)
        else:
            return nlargest(n,self._freq,key=self._freq.get)
    
    def extractRawFrequencies(self, article):
        text = article[0]
        title = article[1]
        sentences = sent_tokenize(text)
        word_sent = [word_tokenize(s.lower()) for s in sentences]
        freq = defaultdict(int)
        for s in word_sent:
            for word in s:
                if word not in self._stopwords:
                    freq[word] += 1
        return freq
    
    def summarize(self, article,n):
        text = article[0]
        title = article[1]
        sentences = sent_tokenize(text)
        word_sent = [word_tokenize(s.lower()) for s in sentences]
        self._freq = self._compute_frequencies(word_sent)
        ranking = defaultdict(int)
        for i,sentence in enumerate(word_sent):
            for word in sentence:
                if word in self._freq:
                    ranking[i] += self._freq[word]
        sentences_index = nlargest(n,ranking,key=ranking.get)

        return [sentences[j] for j in sentences_index]



urlWashingtonPostNonTech = "https://www.washingtonpost.com/sports"
urlNewYorkTimesNonTech = "https://www.nytimes.com/pages/sports/index.html"
urlWashingtonPostTech = "https://www.washingtonpost.com/business/technology"
urlNewYorkTimesTech = "http://www.nytimes.com/pages/technology/index.html"

washingtonPostTechArticles = scrapeSource(urlWashingtonPostTech,
                                          '2017',
                                         getwashingtonPost,
                                         'article') 
washingtonPostNonTechArticles = scrapeSource(urlWashingtonPostNonTech,
                                          '2017',
                                         getwashingtonPost,
                                         'article')
                
                
newYorkTimesTechArticles = scrapeSource(urlNewYorkTimesTech,
                                       '2017',
                                       getNYTPost,
                                       None)
newYorkTimesNonTechArticles = scrapeSource(urlNewYorkTimesNonTech,
                                       '2017',
                                       getNYTPost,
                                       None)


articleSummaries = {}

for techUrlDict in [washingtonPostTechArticles, newYorkTimesTechArticles]:
    for articleUrl in techUrlDict:
        if techUrlDict[articleUrl][1] is not None:
            if len(techUrlDict[articleUrl][1])>0:
                fs = FrequencySummarizer()
                summary = fs.extractFeatures(techUrlDict[articleUrl], 25)
                articleSummaries[articleUrl] = {'feature-vector': summary, 'label':'tech'}
            
            
for nonTechUrlDict in [washingtonPostNonTechArticles, newYorkTimesNonTechArticles]:
    for articleUrl in nonTechUrlDict:
        if nonTechUrlDict[articleUrl][1] is not None:
            if len(nonTechUrlDict[articleUrl][1])>0:
                fs = FrequencySummarizer()
                summary = fs.extractFeatures(nonTechUrlDict[articleUrl], 25)
                articleSummaries[articleUrl] = {'feature-vector': summary, 'label':'non-tech'}
            
def getDoxeyDonkey(url, token):
    response = requests.get(url).content
    soup = BeautifulSoup(response, 'html.parser')
    title = soup.title.text
    divs = soup.findAll('div', class_=token)
    text = ' '.join(map(lambda p: p.text, divs))
    return text, title

testUrl = "http://doxydonkey.blogspot.in"
testArticle = getDoxeyDonkey(testUrl, 'post-body')
fs = FrequencySummarizer()
testArticleSummary = fs.extractFeatures(testArticle, 25)

similarities = {}
for articleUrl in articleSummaries:
    oneArticleSummary = articleSummaries[articleUrl]['feature-vector']
    similarities[articleUrl] = len((set(testArticleSummary)).intersection(set(oneArticleSummary)))

labels = defaultdict(int)
knn = nlargest(5, similarities, key=similarities.get)
for oneNeighbour in knn:
    labels[articleSummaries[oneNeighbour]['label']] += 1

final = nlargest(1, labels, key=labels.get)
print (final)
