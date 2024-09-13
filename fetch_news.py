import requests
from bs4 import BeautifulSoup
from langchain_community.document_loaders import WebBaseLoader
import pickle


# Function to get news links
def get_news_links():
	url = f"https://timesofindia.indiatimes.com/news"

	response = requests.get(url)

	soup = BeautifulSoup(response.content, "html.parser")

	links = []
	for a_tag in soup.find_all('a', class_='VeCXM KRbK2 JKnjg nmRcl'):
		links.append(a_tag['href'])

	# Save links to file
	try:
		with open('news.pkl', 'rb') as f:
			existing_data = pickle.load(f)
			for link in links:
				if link not in existing_data:
					existing_data.append(link)
				else:
					links.remove(link)
	except FileNotFoundError:
		existing_data = links

	with open('news.pkl', 'wb') as f:
		pickle.dump(existing_data, f)

	return links


# Function to load news
def load_news(links):
	loader = WebBaseLoader(links)
	return loader.load()


if __name__ == '__main__':
	links = get_news_links()
	docs = load_news(links)
	print('\n'.join(links))
	print(len(docs))
	print(docs[0])
