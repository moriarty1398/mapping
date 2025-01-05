from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Ride
import json
import requests
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict
import faiss
from django.views.decorators.csrf import ensure_csrf_cookie
import wikipediaapi
import arxiv
from bs4 import BeautifulSoup
import os
from pathlib import Path
from tqdm import tqdm

def index(request):
    context = {
        'title': 'Ride Booking System',
        'description': '''
        Welcome to our Ride Booking System! Set your pickup and drop-off locations,
        choose a vehicle type, and book your ride. Bikes cost ₹3/km and cars cost ₹8/km.
        '''
    }
    return render(request, 'rides/index.html', context)

@require_http_methods(["POST"])
def calculate_ride(request):
    try:
        data = json.loads(request.body)
        
        # Create new ride
        ride = Ride.objects.create(
            pickup_lat=data['pickup']['lat'],
            pickup_lng=data['pickup']['lng'],
            dropoff_lat=data['dropoff']['lat'],
            dropoff_lng=data['dropoff']['lng'],
            driver_lat=data['driver']['lat'],
            driver_lng=data['driver']['lng'],
            vehicle_type=data['vehicle_type']
        )

        # Calculate routes using OSRM
        pickup_route = get_route(
            (ride.driver_lat, ride.driver_lng),
            (ride.pickup_lat, ride.pickup_lng)
        )
        
        ride_route = get_route(
            (ride.pickup_lat, ride.pickup_lng),
            (ride.dropoff_lat, ride.dropoff_lng)
        )

        ride.distance = ride_route['distance']
        ride.cost = ride.calculate_cost()
        ride.save()

        return JsonResponse({
            'status': 'success',
            'data': {
                'ride_id': ride.id,
                'pickup_route': pickup_route,
                'ride_route': ride_route,
                'cost': float(ride.cost),
                'distance': ride.distance
            }
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

def get_route(start, end):
    """Calculate route using OSRM."""
    url = (f"https://router.project-osrm.org/route/v1/driving/"
           f"{start[1]},{start[0]};{end[1]},{end[0]}"
           "?overview=full&geometries=geojson")
    
    response = requests.get(url)
    data = response.json()
    
    if data['code'] != 'Ok':
        raise ValueError("Unable to calculate route")
        
    route = data['routes'][0]
    return {
        'distance': route['distance'] / 1000,  # Convert to kilometers
        'duration': route['duration'],
        'geometry': route['geometry']['coordinates']
    }

@require_http_methods(["POST"])
def complete_ride(request, ride_id):
    try:
        data = json.loads(request.body)
        ride = Ride.objects.get(id=ride_id)
        ride.rating = data.get('rating')
        ride.save()
        return JsonResponse({'status': 'success'})
    except Ride.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Ride not found'
        }, status=404)

def perimeter(request):
    return render(request, 'rides/perimeter.html')

class SimpleVectorDB:
    def __init__(self):
        self.model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
        self.documents = []
        self.embeddings = None
        self.index = None

    def add_documents(self, documents):
        self.documents = documents
        texts = [doc['content'] for doc in documents]
        embeddings = self.model.encode(texts)
        
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings.astype('float32'))

    def search(self, query: str, k: int = 3):
        query_embedding = self.model.encode([query])
        distances, indices = self.index.search(query_embedding.astype('float32'), k)
        return [self.documents[i] for i in indices[0]]

class LocalKnowledgeBase:
    def __init__(self):
        self.base_dir = Path('knowledge_base')
        self.base_dir.mkdir(exist_ok=True)
        
    def download_wikipedia_data(self, topics: list):
        """Download Wikipedia articles for given topics"""
        wiki = wikipediaapi.Wikipedia(
            language='en',
            extract_format=wikipediaapi.ExtractFormat.WIKI,
            user_agent='MyRAGSystem/1.0 (your@email.com)'
        )
        
        wiki_dir = self.base_dir / 'wikipedia'
        wiki_dir.mkdir(exist_ok=True)
        
        for topic in tqdm(topics, desc="Downloading Wikipedia articles"):
            try:
                page = wiki.page(topic)
                if page.exists():
                    topic_data = {
                        "title": page.title,
                        "summary": page.summary,
                        "sections": [
                            {
                                "title": section.title,
                                "content": section.text
                            } for section in page.sections
                        ]
                    }
                    
                    # Save to JSON file
                    with open(wiki_dir / f"{topic.replace(' ', '_')}.json", 'w') as f:
                        json.dump(topic_data, f, indent=2)
            except Exception as e:
                print(f"Error downloading {topic}: {e}")

    def download_arxiv_data(self, topics: list, max_results=10):
        """Download ArXiv papers for given topics"""
        arxiv_dir = self.base_dir / 'arxiv'
        arxiv_dir.mkdir(exist_ok=True)
        
        for topic in tqdm(topics, desc="Downloading ArXiv papers"):
            try:
                search = arxiv.Search(
                    query=topic,
                    max_results=max_results
                )
                papers = []
                
                for result in search.results():
                    paper = {
                        "title": result.title,
                        "summary": result.summary,
                        "authors": [author.name for author in result.authors],
                        "published": str(result.published),
                        "url": result.entry_id
                    }
                    papers.append(paper)
                
                # Save to JSON file
                with open(arxiv_dir / f"{topic.replace(' ', '_')}.json", 'w') as f:
                    json.dump(papers, f, indent=2)
            except Exception as e:
                print(f"Error downloading {topic}: {e}")

def download_knowledge_base():
    """Download all knowledge base data"""
    kb = LocalKnowledgeBase()
    
    # Define topics by category
    topics = {
        "technology": [
            "Artificial Intelligence",
            "Machine Learning",
            "Deep Learning",
            "Cybersecurity",
            "Cloud Computing",
            "Blockchain",
            "Internet of Things",
            "Data Science"
        ],
        "science": [
            "Physics",
            "Quantum Mechanics",
            "Chemistry",
            "Biology",
            "Astronomy",
            "Mathematics"
        ],
        "engineering": [
            "Mechanical Engineering",
            "Electrical Engineering",
            "Software Engineering",
            "Civil Engineering",
            "Chemical Engineering"
        ],
        "business": [
            "Economics",
            "Finance",
            "Marketing",
            "Management",
            "Entrepreneurship"
        ],
        "health": [
            "Medicine",
            "Healthcare",
            "Nutrition",
            "Mental Health",
            "Public Health"
        ]
    }
    
    # Download data for each category
    for category, topic_list in topics.items():
        print(f"\nDownloading {category} topics...")
        category_dir = kb.base_dir / category
        category_dir.mkdir(exist_ok=True)
        
        # Download Wikipedia articles
        kb.download_wikipedia_data(topic_list)
        
        # Download ArXiv papers
        kb.download_arxiv_data(topic_list)

# Update the RAG system to use local knowledge base
class LocalRAGSystem:
    def __init__(self):
        self.vector_db = SimpleVectorDB()
        self.knowledge_base_dir = Path('knowledge_base')
        self.load_knowledge_base()
    
    def load_knowledge_base(self):
        """Load documents from local knowledge base"""
        documents = []
        
        # Walk through all JSON files in knowledge base
        for json_file in self.knowledge_base_dir.rglob('*.json'):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    
                if 'wikipedia' in str(json_file):
                    # Process Wikipedia article
                    documents.append({
                        "content": data['summary'],
                        "source": f"wikipedia/{data['title']}",
                        "page": 1
                    })
                    
                    # Add sections
                    for section in data['sections']:
                        if section['content']:
                            documents.append({
                                "content": section['content'],
                                "source": f"wikipedia/{data['title']}/{section['title']}",
                                "page": 2
                            })
                
                elif 'arxiv' in str(json_file):
                    # Process ArXiv papers
                    for paper in data:
                        documents.append({
                            "content": paper['summary'],
                            "source": f"arxiv/{paper['title']}",
                            "page": 1
                        })
            
            except Exception as e:
                print(f"Error loading {json_file}: {e}")
        
        # Add documents to vector store
        self.vector_db.add_documents(documents)

    def process_content(self, content: str, word_limit: int = None) -> str:
        """Process and clean content"""
        # Skip bibliography and reference sections
        if any(keyword in content.lower() for keyword in ['bibliography', 'references', 'isbn']):
            return None
            
        # Clean up content
        content = content.replace('\n', ' ').strip()
        
        # Remove citations and ISBN numbers
        content = ' '.join([
            line for line in content.split()
            if not line.startswith('ISBN') 
            and not line.startswith('(') 
            and not line.endswith(')')
        ])
        
        if word_limit:
            words = content.split()
            if len(words) > word_limit:
                content = ' '.join(words[:word_limit]) + '.'
        
        return content

    def answer_question(self, question: str) -> dict:
        try:
            # Extract word limit
            word_limit = None
            if 'words' in question.lower():
                try:
                    word_limit = int(''.join(filter(str.isdigit, question)))
                except ValueError:
                    pass

            # Get relevant documents
            relevant_docs = self.vector_db.search(question, k=5)  # Get more docs initially
            
            # Filter and process content
            processed_docs = []
            for doc in relevant_docs:
                processed_content = self.process_content(doc['content'], word_limit)
                if processed_content:  # Only include if content is valid
                    processed_docs.append({
                        "content": processed_content,
                        "source": doc['source'],
                        "page": doc['page']
                    })
                
                if len(processed_docs) >= 2:  # Get 2 good documents
                    break
            
            if not processed_docs:
                return {
                    "answer": "I couldn't find relevant information about this topic.",
                    "sources": []
                }

            # Construct response
            main_content = processed_docs[0]['content']
            if len(processed_docs) > 1:
                main_content += "\n\nAdditional information: " + processed_docs[1]['content']

            return {
                "answer": main_content,
                "sources": [
                    {
                        "source": doc['source'],
                        "page": doc['page']
                    } for doc in processed_docs
                ]
            }
        except Exception as e:
            print(f"Error in answer_question: {e}")
            return {
                "answer": "An error occurred while processing your question.",
                "sources": []
            }

def main():
    # Initialize the RAG system
    rag_system = LocalRAGSystem()
    
    # Interactive question-answering loop
    print("Simple RAG System Demo (type 'quit' to exit)")
    print("Sample topics: Python, machine learning, data structures, neural networks, Git")
    
    while True:
        question = input("\nEnter your question: ")
        if question.lower() == 'quit':
            break
        
        result = rag_system.answer_question(question)
        
        print("\nAnswer:", result["answer"])
        print("\nSources:")
        for idx, source in enumerate(result["sources"], 1):
            print(f"{idx}. {source['source']} (page {source['page']})")

if __name__ == "__main__":
    main()

@ensure_csrf_cookie
def test_rag(request):
    if request.method == "GET":
        return render(request, 'rides/test_rag.html')
        
    elif request.method == "POST":
        try:
            data = json.loads(request.body)
            question = data.get('question', '')
            
            # Print question
            print("\n" + "="*50)
            print("Question:", question)
            print("="*50)
            
            # Use LocalRAGSystem
            rag_system = LocalRAGSystem()
            result = rag_system.answer_question(question)
            
            # Print response
            print("\nResponse:")
            print("-"*50)
            print("Answer:", result['answer'])
            print("\nSources:")
            for source in result['sources']:
                print(f"- {source['source']} (page {source['page']})")
            print("="*50 + "\n")
            
            return JsonResponse({
                'status': 'success',
                'answer': result['answer'],
                'sources': result['sources']
            })
        except Exception as e:
            print(f"Error: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Method not allowed'
    }, status=405)

def get_wikipedia_data(topics, max_articles=10):
    # Create a Wikipedia API object with a proper user agent
    wiki = wikipediaapi.Wikipedia(
        language='en',
        extract_format=wikipediaapi.ExtractFormat.WIKI,
        user_agent='MyRAGSystem/1.0 (contact@example.com)'  # Replace with your info
    )
    
    documents = []
    
    for topic in topics:
        page = wiki.page(topic)
        if page.exists():
            documents.append({
                "content": page.summary,
                "source": f"wikipedia/{topic}",
                "page": 1
            })
            
            # Add sections as separate documents
            for section in page.sections:
                documents.append({
                    "content": section.text,
                    "source": f"wikipedia/{topic}/section",
                    "page": 2
                })
                
    return documents[:max_articles]

def get_arxiv_data(search_query, max_results=10):
    documents = []
    search = arxiv.Search(
        query=search_query,
        max_results=max_results
    )
    
    for result in search.results():
        documents.append({
            "content": result.summary,
            "source": f"arxiv/{result.entry_id}",
            "page": 1
        })
    
    return documents

def get_gutenberg_data(book_ids):
    documents = []
    
    for book_id in book_ids:
        url = f"https://www.gutenberg.org/files/{book_id}/{book_id}-0.txt"
        try:
            response = requests.get(url)
            text = response.text
            
            # Split into chunks of reasonable size
            chunks = [text[i:i+1000] for i in range(0, len(text), 1000)]
            
            for i, chunk in enumerate(chunks):
                documents.append({
                    "content": chunk,
                    "source": f"gutenberg/book_{book_id}",
                    "page": i + 1
                })
        except:
            continue
            
    return documents

