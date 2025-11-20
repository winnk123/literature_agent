"""
Utility Tools for Scientific Literature Management

This module provides a comprehensive suite of utility functions and classes for managing
scientific literature, including:
- Paper metadata structures (PaperMetadata dataclass)
- Multi-source paper search (Semantic Scholar, arXiv, PubMed)
- PDF downloading and text extraction
- Paper filtering and deduplication
- Citation formatting (APA, BibTeX)
- Query parsing and execution
- DOI resolution and publisher page scraping

These utilities support the literature search and survey capabilities of the InternAgent system.
"""

import logging
import re
import os
import time
import requests
import httpx
import subprocess
from pathlib import Path
import pdfplumber
from urllib.parse import urljoin
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import random
from datetime import datetime

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Define the paper search endpoint URL
search_url = 'https://api.semanticscholar.org/graph/v1/paper/search/'
graph_url = 'https://api.semanticscholar.org/graph/v1/paper/'
rec_url = "https://api.semanticscholar.org/recommendations/v1/papers/forpaper/"

@dataclass
class PaperMetadata:
    """Data class for paper metadata."""
    
    title: str
    authors: List[str]
    abstract: str
    year: Optional[int] = None
    doi: Optional[str] = None
    journal: Optional[str] = None
    url: Optional[str] = None
    citations: Optional[int] = None
    references: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    full_text: Optional[str] = None
    source: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "authors": self.authors,
            "abstract": self.abstract,
            "year": self.year,
            "doi": self.doi,
            "journal": self.journal,
            "url": self.url,
            "citations": self.citations,
            "references": self.references,
            "keywords": self.keywords,
            "source": self.source
        }
    
    def to_citation(self, format_type: str = "apa") -> str:
        """
        Generate a formatted citation.
        
        Args:
            format_type: Citation format ("apa", "mla", "chicago", "harvard", "bibtex")
            
        Returns:
            Formatted citation string
        """
        if format_type == "apa":
            # APA format
            author_text = ""
            if self.authors:
                if len(self.authors) == 1:
                    author_text = f"{self.authors[0]}."
                elif len(self.authors) == 2:
                    author_text = f"{self.authors[0]} & {self.authors[1]}."
                else:
                    author_text = f"{self.authors[0]} et al."
            
            year_text = f" ({self.year})." if self.year else ""
            journal_text = f" {self.journal}," if self.journal else ""
            doi_text = f" doi:{self.doi}" if self.doi else ""
            
            return f"{author_text}{year_text} {self.title}.{journal_text}{doi_text}"
            
        elif format_type == "bibtex":
            # BibTeX format
            first_author = self.authors[0].split(" ")[-1] if self.authors else "Unknown"
            year = self.year or "Unknown"
            key = f"{first_author}{year}"
            
            authors = " and ".join(self.authors) if self.authors else "Unknown"
            
            return (
                f"@article{{{key},\n"
                f"  author = {{{authors}}},\n"
                f"  title = {{{self.title}}},\n"
                f"  journal = {{{self.journal or 'Unknown'}}},\n"
                f"  year = {{{self.year or 'Unknown'}}},\n"
                f"  doi = {{{self.doi or ''}}}\n"
                f"}}"
            )
            
        # Default to a basic citation
        authors = ", ".join(self.authors) if self.authors else "Unknown"
        year = f"({self.year})" if self.year else ""
        journal = f"{self.journal}" if self.journal else ""
        
        return f"{authors} {year}. {self.title}. {journal}"
    
# Search tools
def fetch_semantic_papers(keyword, max_results=20, sort="relevance", min_citation_count: int = 0, min_year: Optional[int] = None):
    search_url = "https://api.semanticscholar.org/graph/v1/paper/search"
    query_params = {
        'query': keyword,
        'limit': max_results,
        'fields': 'title,year,citationCount,venue,journal,authors,abstract,tldr,isOpenAccess,openAccessPdf'
    }
    if sort:
        query_params['sort'] = sort
    headers = {'x-api-key': os.environ['S2_API_KEY']}  # Ensure you have the API key set
    response = requests.get(search_url, params=query_params, headers=headers)

    if response.status_code == 200:
        searched_data = response.json().get('data', [])
        papers = []
        for paper_data in searched_data:
            author_list = [author.get("name", "") for author in paper_data.get("authors", [])]
            
            paper_obj = PaperMetadata(
                title=paper_data.get("title", ""),
                authors=author_list,
                abstract=paper_data.get("abstract", ""),
                year=paper_data.get("year"),
                doi=paper_data.get("doi"),
                journal=(paper_data.get("journal", {}).get("name") if isinstance(paper_data.get("journal"), dict) else paper_data.get("venue")),
                url=paper_data.get("url"),
                citations=paper_data.get("citationCount"),
                source='semantic_scholar'
            )
            paper_dict = paper_obj.to_dict()
            paper_dict["citationCount"] = paper_data.get("citationCount")
            if min_citation_count and (paper_dict.get("citationCount") or 0) < min_citation_count:
                continue
            if min_year and paper_dict.get("year") and paper_dict["year"] < min_year:
                continue
            papers.append(paper_dict)
            
        return papers
    else:
        logger.info(f"KeywordQuery: {response.status_code}")
        return []   
    
def fetch_pubmed_papers(query: str, max_results: int = 20, sort: str = "relevance", **kwargs) -> list:
    """
    Fetch papers from PubMed based on the query.
    
    Args:
        query: Search query
        max_results: Maximum number of results (default: 20)
        sort: Sort order ("relevance" or "date")
    
    Returns:
        List of paper metadata in JSON format
    """
    logger.info(f"Searching PubMed for: {query}")
    
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    search_url = f"{base_url}/esearch.fcgi"
    fetch_url = f"{base_url}/efetch.fcgi"
    
    sort_param = "relevance" if sort == "relevance" else "pub+date"
    search_params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "sort": sort_param
    }
    
    try:
        response = requests.get(search_url, params=search_params)
        if response.status_code != 200:
            logger.error(f"PubMed search error: {response.status_code}")
            return []
        
        search_data = response.text
        soup = BeautifulSoup(search_data, "xml")
        pmids = [item.text for item in soup.find_all("Id")]
        
        if not pmids:
            logger.info(f"No PubMed results found for query: {query}")
            return []
        
        # 发起获取详细信息的请求
        fetch_params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml"
        }
        
        fetch_response = requests.get(fetch_url, params=fetch_params)
        if fetch_response.status_code != 200:
            logger.error(f"PubMed fetch error: {fetch_response.status_code}")
            return []
        
        xml_data = fetch_response.text
        papers = parse_pubmed_xml(xml_data)  # 假设你有一个解析函数
        return papers
    
    except Exception as e:
        logger.error(f"Error searching PubMed: {str(e)}")
        return []


def fetch_arxiv_papers(query: str, max_results: int = 20, sort: str = "relevance", categories: list = None, **kwargs) -> list:
    """
    Fetch papers from arXiv based on the query.
    
    Args:
        query: Search query
        max_results: Maximum number of results (default: 20)
        sort: Sort order ("relevance" or "date")
        categories: List of arXiv categories to search (default: None)
    
    Returns:
        List of paper metadata in JSON format
    """
    logger.info(f"Searching arXiv for: {query}")
    
    # arXiv API URL
    search_url = "http://export.arxiv.org/api/query"
    
    # Sort parameter
    sort_param = "relevance" if sort == "relevance" else "submittedDate"
    
    # Category filter
    cat_filter = ""
    if categories:
        cat_filter = " AND (" + " OR ".join([f"cat:{cat}" for cat in categories]) + ")"
    
    # Search parameters
    search_query = f"all:{query}{cat_filter}"
    
    min_year = kwargs.get("min_year")
    max_year = kwargs.get("max_year")
    if min_year or max_year:
        try:
            min_year_int = int(min_year) if min_year else None
        except (ValueError, TypeError):
            min_year_int = None
        try:
            max_year_int = int(max_year) if max_year else None
        except (ValueError, TypeError):
            max_year_int = None
        
        start_date = f"{min_year_int:04d}0101" if min_year_int else "19000101"
        end_year = max_year_int if max_year_int else datetime.utcnow().year + 5
        end_date = f"{end_year:04d}1231"
        search_query += f" AND submittedDate:[{start_date} TO {end_date}]"
    
    search_params = {
        "search_query": search_query,
        "max_results": max_results,
        "sortBy": sort_param,
        "sortOrder": "descending"
    }
    
    try:
        response = requests.get(search_url, params=search_params)
        if response.status_code != 200:
            logger.error(f"arXiv search error: {response.status_code}")
            return []
        
        xml_data = response.text
        papers = parse_arxiv_xml(xml_data)  # 假设你有一个解析函数
        
        logger.info(f"Get {len(papers)} papers from arXiv")

        return papers
    
    except Exception as e:
        logger.error(f"Error searching arXiv: {e}")
        return []

def select_papers(paper_bank, max_papers, rag_read_depth):
    selected_for_deep_read = []
    count = 0
    for paper in sorted(paper_bank, key=lambda x: x.get('score', 0), reverse=True):
        if count >= rag_read_depth:
            break
        url = None
        if paper['source'] in ['arXiv', 'pubmed']:
            # For arXiv and pubmed, check if 'url' or 'doi' exists
            if 'url' in paper:
                url = paper['url']
            elif 'doi' in paper:
                url = paper['doi']
        elif paper['source'] == 'semantic_scholar':
            # For semantic_scholar, check if 'isOpenAccess' is True
            if paper.get('isOpenAccess', False):
                if 'openAccessPdf' in paper and 'url' in paper['openAccessPdf']:
                    url = paper['openAccessPdf']['url']
        
        if url:
            selected_for_deep_read.append(paper)
            count += 1

    selected_for_deep_read = selected_for_deep_read[:max_papers]
    return selected_for_deep_read

def parse_arxiv_xml(xml_data: str) -> list:
    
    papers = []
    soup = BeautifulSoup(xml_data, "xml")
    
    for entry in soup.find_all("entry"):
        try:
            # Title
            title_elem = entry.find("title")
            title_text = title_elem.text.strip() if title_elem else ""
            
            # Abstract
            summary_elem = entry.find("summary")
            abstract_text = summary_elem.text.strip() if summary_elem else ""
            
            # Authors
            authors = []
            for author in entry.find_all("author"):
                name_elem = author.find("name")
                if name_elem:
                    authors.append(name_elem.text.strip())
            
            # Publication year
            published_elem = entry.find("published")
            year = None
            if published_elem:
                try:
                    pub_date = published_elem.text.strip()
                    match = re.search(r"(\d{4})", pub_date)
                    if match:
                        year = int(match.group(1))
                except ValueError:
                    pass
            
            # DOI and URL
            doi = None
            url = None
            for link in entry.find_all("link"):
                href = link.get("href", "")
                if link.get("title") == "doi":
                    doi = href.replace("http://dx.doi.org/", "")
                elif link.get("rel") == "alternate":
                    url = href.replace("abs", "pdf")
            
            paper = PaperMetadata(
                    title=title_text,
                    authors=authors,
                    abstract=abstract_text,
                    year=year,
                    doi=doi,
                    journal="arXiv",
                    url=url,
                    source='arXiv'
                )
            papers.append(paper.to_dict())# NOTE: placeholder for paper metadata 
            
        except Exception as e:
            logger.error(f"Error parsing arXiv entry: {str(e)}")
    
    return papers


def parse_pubmed_xml(xml_data: str) -> list:

    papers = []
    soup = BeautifulSoup(xml_data, "xml")
    
    for article in soup.find_all("PubmedArticle"):
        try:
            article_data = article.find("Article")
            if not article_data:
                continue
            
            # Title
            title = article_data.find("ArticleTitle")
            title_text = title.text if title else ""
            
            # Abstract
            abstract_elem = article_data.find("Abstract")
            abstract_text = ""
            if abstract_elem:
                abstract_parts = abstract_elem.find_all("AbstractText")
                if abstract_parts:
                    abstract_text = " ".join(part.text for part in abstract_parts)
            
            # Authors
            authors = []
            author_list = article_data.find("AuthorList")
            if author_list:
                for author in author_list.find_all("Author"):
                    last_name = author.find("LastName")
                    fore_name = author.find("ForeName")
                    
                    if last_name and fore_name:
                        authors.append(f"{fore_name.text} {last_name.text}")
                    elif last_name:
                        authors.append(last_name.text)
            
            # Journal
            journal_elem = article_data.find("Journal")
            journal_name = ""
            if journal_elem:
                journal_title = journal_elem.find("Title")
                if journal_title:
                    journal_name = journal_title.text
            
            # Publication Date
            pub_date_elem = journal_elem.find("PubDate") if journal_elem else None
            year = None
            if pub_date_elem:
                year_elem = pub_date_elem.find("Year")
                if year_elem:
                    try:
                        year = int(year_elem.text)
                    except ValueError:
                        pass
            
            # DOI
            doi = None
            article_id_list = article.find("ArticleIdList")
            if article_id_list:
                for article_id in article_id_list.find_all("ArticleId"):
                    if article_id.get("IdType") == "doi":
                        doi = article_id.text
                        break
            
            # Create paper metadata
            paper = PaperMetadata(
                title=title_text,
                authors=authors,
                abstract=abstract_text,
                year=year,
                doi=doi,
                journal=journal_name + "@Pubmed",
                source='pubmed'
            )
            papers.append(paper.to_dict()) # NOTE: placeholder for paper metadata
            
        except Exception as e:
            logger.error(f"Error parsing PubMed article: {str(e)}")
    
    return papers

# IO tools

def parse_io_description(output):
    match_input = re.match(r'Input\("([^"]+)"\)', output)
    input_description = match_input.group(1) if match_input else None
    match_output = re.match(r'.*Output\("([^"]+)"\)', output)
    output_description = match_output.group(1) if match_output else None
    return input_description, output_description


def format_papers_for_printing(paper_lst, include_abstract=True, include_score=True, include_id=True):
    """
    Convert a list of papers to a string for printing or as part of a prompt.
    """
    output_str = ""
    for idx, paper in enumerate(paper_lst):
        # if include_id and "paperId" in paper:
        #     output_str += "paperId: " + paper["paperId"].strip() + "\n"
        if include_id:
            output_str += "paperId: " + str(idx) + "\n" 
        elif include_id and "title" in paper:
            output_str += "paperId: " + paper["title"].strip() + "\n"
        
        output_str += "title: " + paper.get("title", "").strip() + "\n"
        
        if include_abstract:
            if "abstract" in paper and paper["abstract"]:
                output_str += "abstract: " + paper["abstract"].strip() + "\n"
            elif "tldr" in paper and paper["tldr"] and paper["tldr"].get("text"):
                output_str += "tldr: " + paper["tldr"]["text"].strip() + "\n"
        
        if "year" in paper:
            output_str += "year: " + str(paper["year"]) + "\n"
        
        if "score" in paper and include_score:
            output_str += "relevance score: " + str(paper["score"]) + "\n"
        
        output_str += "\n"
    
    return output_str

def format_papers_for_printing_next_query(paper_lst, include_abstract=True, include_score=True, include_id=True):
    """
    Convert a list of papers to a string for printing or as part of a prompt.
    """
    output_str = ""
    for idx, paper in enumerate(paper_lst):
        if include_id:
            output_str += "paperId: " + str(idx) + "\n" 
        elif include_id and "title" in paper:
            output_str += "paperId: " + paper["title"].strip() + "\n"
        
        output_str += "title: " + paper.get("title", "").strip() + "\n"
        
        output_str += "\n"
    
    return output_str

def print_top_papers_from_paper_bank(paper_bank, top_k=10):
    data_list = [{'id': id, **info} for id, info in paper_bank.items()]
    top_papers = sorted(data_list, key=lambda x: x['score'], reverse=True)[: top_k]
    logger.debug(format_papers_for_printing(top_papers, include_abstract=False))


def dedup_paper_bank(sorted_paper_bank):
    idx_to_remove = []

    for i in reversed(range(len(sorted_paper_bank))):
        for j in range(i):
            if sorted_paper_bank[i]["paperId"].strip() == sorted_paper_bank[j]["paperId"].strip():
                idx_to_remove.append(i)
                break
            if ''.join(sorted_paper_bank[i]["title"].lower().split()) == ''.join(
                    sorted_paper_bank[j]["title"].lower().split()):
                idx_to_remove.append(i)
                break
            if sorted_paper_bank[i]["abstract"] == sorted_paper_bank[j]["abstract"]:
                idx_to_remove.append(i)
                break

    deduped_paper_bank = [paper for i, paper in enumerate(sorted_paper_bank) if i not in idx_to_remove]
    return deduped_paper_bank


def download_pdf(pdf_url, save_folder="pdfs"):
    logger.info(f"downloading pdf from {pdf_url}")
    
    if not pdf_url:
        return None
    
    os.makedirs(save_folder, exist_ok=True)
    
    file_name = pdf_url.split("/")[-1]
    if not file_name.endswith('.pdf'):
        file_name = file_name + '.pdf'
    save_path = os.path.join(save_folder, file_name)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
    }
    try:
        response = httpx.get(url=pdf_url,headers=headers, timeout=10, verify=False)
        if response.status_code == 200:
            with open(save_path, "wb") as file:
                file.write(response.content)
            return save_path
        else:
            logger.error(f"Failed to download PDF from {pdf_url}: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error downloading PDF from {pdf_url}: {e}")
        return None
    
def download_pdf_pubmed(url, save_folder="pdfs"):
    os.makedirs(save_folder, exist_ok=True)
    
    # 构造 scihub-cn 命令
    command = f'scihub-cn -d {url} -o "{save_folder}"'
    
    logger.info(f"downloading pdf from {url} via {command}")
    
    try:
        # 执行命令
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
                downloaded_files = [f for f in os.listdir(save_folder) if f.endswith('.pdf')]
                if downloaded_files:
                    latest_file = max(downloaded_files, key=lambda x: os.path.getctime(Path(save_folder) / x))
                    downloaded_pdf_path = Path(save_folder) / latest_file
                    logger.info(f"name of the file being downloaded: {downloaded_pdf_path}")
                    return str(downloaded_pdf_path)
                else:
                    logger.info("The downloaded PDF file was not found")
                    return None
        else:
            logger.error(f"Failed download: {result.stderr.decode('utf-8')}")
            return None
    except Exception as e:
        logger.error(f"Failed download: {e}")
        return None
    
    
def download_pdf_by_doi(doi: str, download_dir: str = "downloaded_papers"):

    doi = doi.strip()
    if doi.lower().startswith('doi:'):
        doi = doi[4:].strip()
    if doi.lower().startswith('https://doi.org/'):
        doi = doi[16:].strip()
    
    doi_url = f"https://doi.org/{doi}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(doi_url, headers=headers, allow_redirects=True)
    publisher_url = response.url
    logger.info(f"Redirected to the publisher page: {publisher_url}")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    pdf_links = []
    
    for link in soup.find_all('a', href=True):
        href = link['href']
        link_text = link.get_text().lower()
        if ('pdf' in href.lower() or 
            'pdf' in link_text or 
            'download' in link_text and ('full' in link_text or 'article' in link_text) or
            'full text' in link_text):
            pdf_links.append(urljoin(publisher_url, href))
    
    if pdf_links:
        print(f"找到 {len(pdf_links)} 个可能的 PDF 链接")
        pdf_url = pdf_links[0]
        print(f"尝试下载: {pdf_url}")
        
        pdf_response = requests.get(pdf_url, headers=headers, stream=True)
        if pdf_response.status_code == 200 and 'application/pdf' in pdf_response.headers.get('Content-Type', ''):
            # 创建下载目录
            os.makedirs(download_dir, exist_ok=True)
            
            # 自动生成文件名（仅使用 DOI）
            filename = f"{doi.replace('/', '_')}.pdf"
            filepath = os.path.join(download_dir, filename)
            
            # 保存 PDF 文件
            with open(filepath, 'wb') as f:
                for chunk in pdf_response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            print(f"PDF已下载到: {filepath}")
            return filepath
        else:
            print("下载失败：无法获取有效的 PDF 文件。")
    else:
        print("未找到 PDF 链接。")
    
    return None

def extract_text_from_pdf(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text()
            return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None
    
    
def get_pdf_url(paper_id, max_retries=5):

    base_url = "https://api.semanticscholar.org/graph/v1/paper/"
    url = f"{base_url}{paper_id}"
    params = {"fields": "openAccessPdf"}  

    headers = {'x-api-key': os.environ['S2_API_KEY']}
    response = requests.get(url, params=params, headers=headers)

    if response.status_code == 200:
        data = response.json()
        return data.get("openAccessPdf", {}).get("url")

    elif response.status_code == 429:
        attempt = 0
        while attempt < max_retries:
            print("Rate limit exceeded. Sleeping for 10 seconds...")
            time.sleep(10) 
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                return data.get("openAccessPdf", {}).get("url")
            attempt += 1
        print("Max retries exceeded. Could not retrieve PDF URL.")
        return None

    else:
        print(f"Failed to retrieve PDF URL. Status code: {response.status_code}")
        return None

        
def PaperQuery(paper_id):
    query_params = {
        'paperId': paper_id,
        'limit': 20,
        'fields': 'title,year,citationCount,abstract'
    }
    headers = {'x-api-key': os.environ['S2_API_KEY']}
    response = requests.get(url=rec_url + paper_id, params=query_params, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None


def PaperDetails(paper_id, fields='title,year,abstract,authors,citationCount,venue,citations,references,tldr'):

    ## get paper details based on paper id
    paper_data_query_params = {'fields': fields}
    headers = {'x-api-key': os.environ['S2_API_KEY']}
    response = requests.get(url=graph_url + paper_id, params=paper_data_query_params, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None


def GetAbstract(paper_id):
    ## get the abstract of a paper based on paper id
    paper_details = PaperDetails(paper_id)

    if paper_details is not None:
        return paper_details["abstract"]
    else:
        return None


def GetCitationCount(paper_id):
    ## get the citation count of a paper based on paper id
    paper_details = PaperDetails(paper_id)

    if paper_details is not None:
        return int(paper_details["citationCount"])
    else:
        return None


def GetCitations(paper_id):
    ## get the citation list of a paper based on paper id
    paper_details = PaperDetails(paper_id)

    if paper_details is not None:
        return paper_details["citations"]
    else:
        return None


def GetReferences(paper_id):
    ## get the reference list of a paper based on paper id
    paper_details = PaperDetails(paper_id)
    references = paper_details["references"][: 100]

    ## get details of each reference, keep first 20 to save costs
    detailed_references = [PaperDetails(ref["paperId"], fields='title,year,abstract,citationCount') for ref in
                           references if ref["paperId"]]
    detailed_references = paper_filter(detailed_references)[: 20]

    if paper_details is not None:
        return detailed_references
    else:
        return None


def is_valid_paper(paper):
    paper = paper
    # Check for specific keywords indicating non-research papers
    title = paper.get("title", "").lower() if paper.get("title") else ""
    abstract = paper.get("abstract", "").lower() if paper.get("abstract") else ""
    if ("survey" in title or "survey" in abstract or
        "review" in title or "review" in abstract or
        "position paper" in title or "position paper" in abstract):
        return False
    
    # Check abstract length (new rule)
    if len(abstract.split()) <= 50:
        return False
    
    return True

def paper_filter(paper_lst):
    """
    Filter out papers based on some basic heuristics.
    Args:
        paper_lst (dict): A dictionary where keys are sources (e.g., 'pubmed', 'arxiv') and values are lists of papers.
    Returns:
        dict: A dictionary with the same structure as input, but with filtered papers.
    """
    filtered_paper_lst = {}
    
    # Iterate through each source and filter papers
    for source, papers in paper_lst.items():
        if isinstance(papers, list):  # Ensure the value is a list
            filtered_papers = [paper for paper in papers if is_valid_paper(paper)]
            filtered_paper_lst[source] = filtered_papers
        else:
            # If the value is not a list, skip or handle differently
            filtered_paper_lst[source] = papers  # Keep the original structure
    
    # print("Filtered paper list: ", filtered_paper_lst)
    return filtered_paper_lst

def multi_source_search(query: str, sources: list[str] = None, max_results: int = 10, **kwargs) -> dict[str, list[dict]]:
    
    if not sources:
        sources = ["pubmed", "arxiv", "semantic_scholar"]
    
    combined_results = {}
    
    for source in sources:
        if source == "pubmed":
            combined_results[source] = fetch_pubmed_papers(query, max_results)
        elif source == "arxiv":
            combined_results[source] = fetch_arxiv_papers(query, max_results)
        elif source == "semantic_scholar":
            combined_results[source] = fetch_semantic_papers(
                query,
                max_results,
                sort=kwargs.get("sort", "relevance"),
                min_citation_count=kwargs.get("min_citation_count", 0),
                min_year=kwargs.get("min_year")
            )
        else:
            logger.warning(f"Unknown source: {source}. Skipping.")
    
    return combined_results

def parse_and_execute(output, max_results, **kwargs):
    ## parse gpt4 output and execute corresponding functions
    if output.startswith("KeywordQuery"):
        match = re.match(r'KeywordQuery\("([^"]+)"\)', output)
        keyword = match.group(1) if match else None
        if keyword:
            response = multi_source_search(keyword, max_results=max_results, **kwargs)
            if response is not None:
                paper_lst = response
            # print("paper_lst: ",paper_lst)
            return paper_filter(paper_lst)
        else:
            return None
    elif output.startswith("PaperQuery"):
        match = re.match(r'PaperQuery\("([^"]+)"\)', output)
        paper_id = match.group(1) if match else None
        if paper_id:
            response = PaperQuery(paper_id)
            if response is not None and response["recommendedPapers"]:
                paper_lst = response["recommendedPapers"]
                return paper_filter(paper_lst)
    elif output.startswith("GetAbstract"):
        match = re.match(r'GetAbstract\("([^"]+)"\)', output)
        paper_id = match.group(1) if match else None
        if paper_id:
            return GetAbstract(paper_id)
    elif output.startswith("GetCitationCount"):
        match = re.match(r'GetCitationCount\("([^"]+)"\)', output)
        paper_id = match.group(1) if match else None
        if paper_id:
            return GetCitationCount(paper_id)
    elif output.startswith("GetCitations"):
        match = re.match(r'GetCitations\("([^"]+)"\)', output)
        paper_id = match.group(1) if match else None
        if paper_id:
            return GetCitations(paper_id)
    elif output.startswith("GetReferences"):
        match = re.match(r'GetReferences\("([^"]+)"\)', output)
        paper_id = match.group(1) if match else None
        if paper_id:
            return GetReferences(paper_id)
    return None

def replace_and_with_or(query, max_keep=1):
    parts = query.split(" AND ")
    
    if len(parts) <= max_keep + 1:
        return query
    
    if max_keep > 0:
        keep_positions = random.sample(range(len(parts) - 1), max_keep)
    else:
        keep_positions = []
    
    result = parts[0]
    for i in range(len(parts) - 1):
        if i in keep_positions:
            result += " AND " + parts[i + 1]  # 保留 AND
        else:
            result += " OR " + parts[i + 1]  # 将 AND 替换为 OR
    
    return result
