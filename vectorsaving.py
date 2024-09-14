from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
import fetch_news


# Function to vectorize the news
def vectorize_papers(news):
	text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
	splits = text_splitter.split_documents(news)
	if splits:
		embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
		db = FAISS.from_documents(splits, embeddings)

		# Load existing data
		try:
			dbe = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
			db.merge_from(dbe)
		except:
			pass
		db.save_local("faiss_index")

def get_vectors():
	embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
	db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
	return db


if __name__ == '__main__':
	links = fetch_news.get_news_links()
	news = fetch_news.load_news(links)
	vectorize_papers(news)
