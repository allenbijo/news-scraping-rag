import requests
from bs4 import BeautifulSoup
from langchain_community.document_loaders import WebBaseLoader


def get_news_links():
	url = f"https://timesofindia.indiatimes.com/news"

	response = requests.get(url)

	soup = BeautifulSoup(response.content, "html.parser")

	links = []
	for a_tag in soup.find_all('a', class_='VeCXM KRbK2 JKnjg nmRcl'):
		links.append(a_tag['href'])
	return links


def load_news(links):
	loader = WebBaseLoader(links)
	return loader.load()


if __name__ == '__main__':
	links = get_news_links()
	print('\n'.join(links))
	docs = load_news(links)
	print(len(docs))
	print(docs[0])
