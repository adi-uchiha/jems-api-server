from fastapi import FastAPI, Request
from jobspy import scrape_jobs
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine, String, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
import os
from dotenv import load_dotenv
import warnings
import numpy as np
import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel

warnings.filterwarnings("ignore", category=DeprecationWarning)

load_dotenv()

app = FastAPI()

# Define a Pydantic model for the request body
class ScrapeRequest(BaseModel):
    search_term: str = "software engineer"
    location: str = "India"
    results_wanted: int = 20

class Base(DeclarativeBase):
    pass

class EmbedRequest(BaseModel):
    text: str

class Job(Base):
    __tablename__ = "jobs"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=True)
    company: Mapped[str] = mapped_column(String, nullable=True)
    location: Mapped[str] = mapped_column(String, nullable=True)
    description: Mapped[str] = mapped_column(String, nullable=True)
    url: Mapped[str] = mapped_column(String, nullable=True)
    
    def __repr__(self):
        return f"Job(id={self.id!r}, title={self.title!r}, company={self.company!r})"

TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL", "libsql://jems-main-turso12686.turso.io")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN", "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3MzkzMzQyMDUsImlkIjoiNDhjOTExNTktN2U0My00OGQxLTgyNzEtNjMwMDU0ZWRkODNlIn0.pPkqWJppK3HZbikim1g0L6bien9sJS7wKXdHZAX5xbaeXP8LKY81xT-oOLdrMXLVroBJggrcMXyK7pt2RLFuCQ")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "pcsk_6aDtjC_4rYreRVVXzMabLfPX8uqjDCYJwxx48DeGbrQbPd48ynJ3kwfx4qMj2Rk9rXadTZ")

db_url = f"sqlite+{TURSO_DATABASE_URL}/?authToken={TURSO_AUTH_TOKEN}&secure=true"
print(f"Database URL: {db_url}")

engine = create_engine(db_url, connect_args={'check_same_thread': False}, echo=True)

pc = Pinecone(api_key=PINECONE_API_KEY)
index_name = "job-embeddings"

if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=384,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )

index = pc.Index(index_name)
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

def init_db():
    Base.metadata.create_all(engine)

def is_valid_embedding(embedding):
    return all(np.isfinite(x) for x in embedding)

def clean_value(value):
    if isinstance(value, float) and np.isnan(value):
        return None
    return str(value) if value is not None else None

def fetch_description(url, site):
    """Fetch job description from URL if missing, with site-specific handling."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        if site == "linkedin":
            desc = soup.find('div', class_='description__text')
        elif site == "glassdoor":
            desc = soup.find('div', class_='desc')
        elif site == "ziprecruiter":
            desc = soup.find('div', class_='job_description')
        elif site == "indeed":
            desc = soup.find('div', id='jobDescriptionText')
        else:
            desc = None
        
        return desc.get_text(strip=True) if desc else "Failed to extract description"
    except Exception as e:
        print(f"Failed to fetch description for {site} job at {url}: {str(e)}")
        return "Failed to fetch description"

@app.post("/embed")
async def generate_embedding(request: EmbedRequest):
    try:
        embedding = model.encode(request.text).tolist()
        return {"embedding": embedding}
    except Exception as e:
        return {"error": str(e)}

@app.post("/scrape")
async def scrape_and_process_jobs(request: ScrapeRequest):
    try:
        # Extract parameters from the request body
        search_term = request.search_term
        location = request.location
        results_wanted = request.results_wanted

        # Scrape jobs from multiple sites, handling failures individually
        site_names = ["indeed", "linkedin", "glassdoor", "ziprecruiter"]
        all_jobs = []
        
        for site in site_names:
            try:
                print(f"Scraping {site}...")
                jobs = scrape_jobs(
                    site_name=[site],
                    search_term=search_term,
                    location=location,
                    results_wanted=results_wanted if site != "ziprecruiter" else 10,  # Limit ZipRecruiter due to US focus
                    country_indeed="India" if site == "indeed" else None,
                    # Add proxies if needed: proxies="http://your_proxy:port"
                )
                all_jobs.extend(jobs.to_dict('records'))
                print(f"Successfully scraped {len(jobs)} jobs from {site}")
            except Exception as e:
                print(f"Failed to scrape {site}: {str(e)}")

        if not all_jobs:
            return {"status": "error", "message": "No jobs scraped from any site"}

        job_list = all_jobs
        pinecone_vectors = []
        successful_jobs = 0
        jobs_to_return = []

        # Debug: Print raw job data
        print("Raw job data from scrape_jobs:")
        for job in job_list:
            site = job.get('site', 'unknown')
            print(f"{site.capitalize()} Job: {job}")

        # Process jobs
        for job in job_list:
            site = job.get('site', 'unknown')
            job_id = str(job.get('id', '')) or f"unknown_{hash(str(job))}"
            title = clean_value(job.get('title', ''))
            company = clean_value(job.get('company', ''))
            location = clean_value(job.get('location', ''))
            description = clean_value(job.get('description', ''))
            url = clean_value(job.get('job_url', ''))
            
            if not description or description in ["No description available", "Failed to extract description"]:
                description = fetch_description(url, site)
            
            job_dict = {
                "id": job_id,
                "title": title or "Unknown Title",
                "company": company or "Unknown Company",
                "location": location or "Unknown Location",
                "description": description or "No description available",
                "url": url or "No URL available"
            }
            jobs_to_return.append(job_dict)
            
            db_job = Job(
                id=job_id,
                title=title or "Unknown Title",
                company=company or "Unknown Company",
                location=location or "Unknown Location",
                description=description or "No description available",
                url=url or "No URL available"
            )
            
            embedding_text = f"{title or ''} {company or ''} {location or ''} {description or ''}"
            embedding = model.encode(embedding_text).tolist()
            
            if is_valid_embedding(embedding):
                pinecone_vectors.append({
                    'id': job_id,
                    'values': embedding,
                    'metadata': {
                        'title': title or "Unknown Title",
                        'company': company or "Unknown Company",
                        'location': location or "Unknown Location",
                        'url': url or "No URL available"
                    }
                })
            else:
                print(f"Skipping job {job_id} due to invalid embedding: {embedding_text[:50]}...")
            
            successful_jobs += 1

        # Insert into database
        with Session(engine) as session:
            for job_dict in jobs_to_return:
                db_job = Job(
                    id=job_dict["id"],
                    title=job_dict["title"],
                    company=job_dict["company"],
                    location=job_dict["location"],
                    description=job_dict["description"],
                    url=job_dict["url"]
                )
                session.merge(db_job)
            session.commit()

        if pinecone_vectors:
            index.upsert(vectors=pinecone_vectors)
        else:
            print("Warning: No valid embeddings generated for Pinecone upsert")

        return {
            "status": "success",
            "message": f"Processed {successful_jobs} out of {len(job_list)} jobs, upserted {len(pinecone_vectors)} to Pinecone",
            "jobs_scraped": len(job_list),
            "jobs": jobs_to_return
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        }

if __name__ == "__main__":
    import uvicorn
    init_db()
    uvicorn.run(app, host="0.0.0.0", port=8000)