import sys
from gensim.models.keyedvectors import KeyedVectors
import mysql.connector
from nltk.corpus import stopwords
from bs4 import BeautifulSoup
import nltk
from nltk.stem import WordNetLemmatizer 
import re
import time
import operator
from sshtunnel import SSHTunnelForwarder
from dotenv import load_dotenv
import os

load_dotenv()


#use ssh to connect to the remote database
server = SSHTunnelForwarder(
    os.getenv("SSH_HOST"),
    ssh_username=os.getenv("SSH_hostname"),
    ssh_password=os.getenv("SSH_pass"),
    remote_bind_address=("127.0.0.1", 3306)
)
server.start()

sotorrent = mysql.connector.connect(
  host="127.0.0.1",
  port=server.local_bind_port,
  user=os.getenv("sotor_user"),
  passwd=os.getenv("sotor_password"),
  database=os.getenv("sotor_db"))

cursor_issues = sotorrent.cursor()
lemmatizer = WordNetLemmatizer() 
cursor_issues.execute("SELECT Id, body, title FROM sotorrent24_01.Posts WHERE PostTypeId=1 AND score>0 AND answercount>0 AND LastActivityDate > '2019-06-01 00:00:00' AND Tags LIKE '%python%'")
posts = cursor_issues.fetchmany(1000)

REPLACE_BY_SPACE_RE = re.compile('[/(){}\[\]\|@,;]')
BAD_SYMBOLS_RE = re.compile('[^0-9a-z #+_]')
STOPWORDS = set(stopwords.words('english'))

def clean_text(text):
    soup = BeautifulSoup(text, "lxml")
    codeblocks = soup.findAll('code')
    for match in codeblocks:
        match.decompose()
    text = str(soup)
    text = BeautifulSoup(text, "lxml").text # HTML decoding
    text = text.lower() # lowercase text
    text = REPLACE_BY_SPACE_RE.sub(' ', text) # replace REPLACE_BY_SPACE_RE symbols by space in text
    text = BAD_SYMBOLS_RE.sub('', text) # delete symbols which are in BAD_SYMBOLS_RE from text
    text = ' '.join(word for word in text.split() if word not in STOPWORDS) # delete stopwors from text
    text = ' '.join(word for word in text.split() if word in word_vect.vocab) # delete non embedded words
    return text

#word embeddings from Efstathiou, V., Chatzilenas, C., Spinellis, D., 2018. "Word Embeddings for the Software Engineering Domain". In Proceedings of the 15th International Conference on Mining Software Repositories. ACM.
word_vect = KeyedVectors.load_word2vec_format("SO_vectors_200.bin", binary=True)
initial_sentence = clean_text(sys.argv[1])


bestmatching = {}

while posts:
  for post in posts:
      new_text=post[1] + " " + post[2]
      new_text=clean_text(new_text)
      cossim = 0
      if(len(new_text) != 0):
        cossim = word_vect.n_similarity(initial_sentence.split(), new_text.split())
      if(len(bestmatching) <5):
        bestmatching[post[0]] = cossim
      elif(min(bestmatching.items(), key=operator.itemgetter(1))[1] < cossim):
         del bestmatching[min(bestmatching.items(), key=operator.itemgetter(1))[0]]     
         bestmatching[post[0]] = cossim
  posts = cursor_issues.fetchmany(1000)

bestmatching = sorted(bestmatching.items(), key=lambda x: x[1], reverse=True)

for item in bestmatching:
  cursor_issues.execute("SELECT title FROM sotorrent24_01.Posts WHERE Id=" + str(item[0]) +";")
  title = cursor_issues.fetchone()
  print(str(item[0]) + " " + title[0])

mydb_issues.close()
server.stop()

sys.stdout.flush()