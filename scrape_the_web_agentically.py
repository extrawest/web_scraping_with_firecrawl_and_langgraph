"""Agentic web scraping example using Firecrawl and LangGraph."""

import logging
from operator import or_
from typing import Any, Dict, List, Optional, TypedDict

from firecrawl import FirecrawlApp
from langgraph.graph import END, START, StateGraph, Graph
from pydantic_settings import BaseSettings
from typing_extensions import Annotated

class Settings(BaseSettings):
    firecrawl_url: str = "http://localhost:3002"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = 'ignore'

def load_settings() -> Settings:
    """Load settings from environment variables or .env file."""
    try:
        return Settings()
    except ValueError as e:
        logging.error(f"Configuration error: {e}. Ensure FIRECRAWL_API_KEY is set in your environment or .env file.")
        raise

def setup_logging(level: int = logging.INFO) -> None:
    """Configure the root logger with a consistent format."""
    logger = logging.getLogger()
    if logger.hasHandlers():
        logger.handlers.clear()

    logger.setLevel(level)
    handler = logging.StreamHandler()
    handler.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def first_non_null(a: Any, b: Any) -> Any:
    """Return the first non-null value between two values."""
    return a if a is not None else b

class InputState(TypedDict):
    """Input schema for the graph."""
    url: str
    keyword: str

class OverallState(TypedDict):
    """Overall state schema for the LangGraph agent."""
    urls: List[str]
    current_url_index: int
    total_urls: int
    urls_to_scrape: List[str]
    extracted_info: Annotated[Optional[str], first_non_null]
    extracted_from_url: Annotated[Optional[str], first_non_null]
    is_information_found: Annotated[Optional[bool], or_]
    keyword: str

def initialize_state(state: Dict[str, Any], config: Dict[str, Any]) -> OverallState:
    """Initialize the agent's state from the input parameters."""
    logging.info("Executing node: initialize_state")

    configurable = config.get("configurable", {})
    url = configurable.get("url")
    keyword = configurable.get("keyword")
    
    return {
        "urls": [url],
        "current_url_index": 0,
        "total_urls": 0,
        "urls_to_scrape": [],
        "keyword": keyword,
        "extracted_info": None,
        "extracted_from_url": None,
        "is_information_found": False
    }

def get_sitemap(state: OverallState, config: Dict[str, Any]) -> OverallState:
    """Fetch the sitemap for the initial URL and update the state with the list of URLs to process."""
    logging.info("Executing node: get_sitemap")

    settings: Settings = config.get("settings", Settings())
    app = FirecrawlApp(api_url=settings.firecrawl_url)
    logging.info(f"Using Firecrawl server at {settings.firecrawl_url}")

    initial_url = state["urls"][0]
    if not initial_url:
        logging.error("No initial URL provided")
        state["urls"] = []
        state["total_urls"] = 0
        return state
        
    logging.info(f"Fetching sitemap for: {initial_url}")

    try:
        sitemap = [initial_url]
        
        try:
            map_result = app.map_url(initial_url)
            if hasattr(map_result, 'links') and isinstance(map_result.links, list) and map_result.links:
                sitemap = map_result.links
                logging.info(f"Found {len(sitemap)} links in sitemap")
            else:
                logging.info("No sitemap links found. Using only the initial URL.")
        except Exception as e:
            logging.warning(f"Error fetching sitemap, using initial URL only: {e}")

        if not sitemap:
            logging.warning(f"No sitemap links found for {initial_url}. Proceeding with only the initial URL.")
            sitemap = [initial_url]

        valid_urls = [url for url in sitemap if url and isinstance(url, str)]
        if len(valid_urls) < len(sitemap):
            logging.warning(f"Filtered out {len(sitemap) - len(valid_urls)} invalid URLs from sitemap.")
        
        if not valid_urls:
            logging.warning("No valid URLs found in sitemap. Using initial URL as fallback.")
            valid_urls = [initial_url]
            
        state["urls"] = valid_urls
        state["total_urls"] = len(valid_urls)
        logging.info(f"Found {len(valid_urls)} URLs to process.")

    except Exception as e:
        logging.error(f"Error fetching sitemap for {initial_url}: {e}")
        logging.warning("Proceeding with only the initial URL due to sitemap error.")
        state["urls"] = [initial_url]
        state["total_urls"] = 1

    return state


def scrape_manager(state: OverallState) -> OverallState:
    """Manage the batching of URLs for scraping."""
    logging.info("Executing node: scrape_manager")

    total_urls = state.get("total_urls", 0)
    current_index = state.get("current_url_index", 0)
    urls = state.get("urls", [])

    if not urls or current_index >= total_urls:
        if not urls:
            logging.warning("No URLs available for scraping.")
        else:
            logging.info("All URLs have been processed.")
            
        state["urls_to_scrape"] = []
        return state

    url_to_scrape = urls[current_index]
    state["current_url_index"] = current_index + 1
    state["urls_to_scrape"] = [url_to_scrape]

    progress_percentage = (current_index / total_urls) * 100 if total_urls > 0 else 0
    logging.info(f"Processing URL {current_index + 1}/{total_urls}: {url_to_scrape} (Progress: {progress_percentage:.2f}%)")

    return state


def send_to_scraper(state: OverallState) -> List[Dict[str, Any]]:
    """Prepare individual URL scraping tasks."""
    urls_to_scrape = state.get("urls_to_scrape", [])
    keyword = state.get("keyword", "")

    if not urls_to_scrape:
        return []

    logging.info(f"Processing {len(urls_to_scrape)} URLs in scraper node.")

    return [{"url": url, "keyword": keyword} for url in urls_to_scrape]


def scraper(state: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """Scrape a single URL for content relevant to the keyword."""
    urls = state.get("urls_to_scrape", [])
    if urls:
        url = urls[0]
        keyword = state.get("keyword", "")
        logging.info(f"Using URL from urls_to_scrape: {url}")
    else:
        logging.error("Empty urls_to_scrape list")
        return {
            "extracted_info": None,
            "extracted_from_url": None,
            "is_information_found": False
        }

    if not url:
        logging.error("No URL found in state")
        return {
            "extracted_info": None,
            "extracted_from_url": None,
            "is_information_found": False
        }

    settings: Settings = config.get("settings", Settings())

    app = FirecrawlApp(api_url=settings.firecrawl_url)
    logging.info(f"Using Firecrawl server at {settings.firecrawl_url}")

    extracted_info: Optional[str] = None
    information_found: bool = False

    try:
        logging.info(f"Starting scrape for: {url}")

        scrape_result = app.scrape_url(url)
        logging.info(f"Successfully scraped: {url}")

        logging.info(f"Processing API response of type: {type(scrape_result)}")

        extracted_metadata = ""
        extracted_html = ""
        extracted_markdown = ""
        extracted_text = ""

        if hasattr(scrape_result, 'metadata') and scrape_result.metadata:
            extracted_html = str(scrape_result.metadata)

        if hasattr(scrape_result, 'html') and scrape_result.html:
            extracted_html = str(scrape_result.html)

        if hasattr(scrape_result, 'markdown') and scrape_result.markdown:
            extracted_markdown = str(scrape_result.markdown)

        if hasattr(scrape_result, 'text') and scrape_result.text:
            extracted_text = str(scrape_result.text)

        extracted_info = extracted_metadata + extracted_html + extracted_markdown + extracted_text

        if extracted_info and keyword.lower() in extracted_info.lower():
            information_found = True
            logging.info(f"Found keyword '{keyword}' in extracted content")

        if not extracted_info:
            logging.warning(f"Failed to extract content from {url}")

    except Exception as e:
        logging.error(f"Error scraping {url}: {e}")

    return {
        "extracted_info": extracted_info,
        "extracted_from_url": url,
        "is_information_found": information_found,
    }

def evaluate(state: OverallState) -> Dict[str, Any]:
    """Evaluate if the required information has been found."""
    logging.info("Executing node: evaluate")
    keyword = state.get("keyword", "unknown keyword")
    extracted_from_url = state.get("extracted_from_url")
    extracted_info = state.get("extracted_info")

    if state.get("is_information_found"):
        logging.info(f"Information found for keyword '{keyword}' from URL: {extracted_from_url}")
        return {
            "is_information_found": True,
            "extracted_info": extracted_info,
            "extracted_from_url": extracted_from_url,
            "keyword": keyword
        }
    else:
        logging.info(f"Information not yet found for keyword '{keyword}'")
        return {"is_information_found": False}

def should_continue_scraping(state: OverallState) -> str:
    """Determine the next step after evaluation."""
    logging.info("Executing node: should_continue_scraping (conditional edge)")

    is_information_found = state.get("is_information_found", False)
    current_index = state.get("current_url_index", 0)
    total_urls = state.get("total_urls", 0)

    if is_information_found:
        batch_number = current_index // 1
        logging.info(f"Information found in batch {batch_number}")
        return "end_process"

    if current_index >= total_urls:
        logging.info(f"All {total_urls} URLs processed without finding information. Ending process.")
        return "end_process"

    logging.info(f"Information not found in URL {current_index}/{total_urls}. Continuing to next URL.")
    return "continue_scraping"

def create_graph(settings: Settings) -> Graph:
    """Create the LangGraph workflow for web scraping."""
    logging.info("Creating LangGraph workflow for web scraping")

    builder = StateGraph(OverallState)

    builder.add_node("initialize_state", initialize_state)
    builder.add_node("get_sitemap", get_sitemap)
    builder.add_node("scrape_manager", scrape_manager)
    builder.add_node("scraper", scraper)
    builder.add_node("evaluate", evaluate)

    builder.add_edge(START, "initialize_state")
    builder.add_edge("initialize_state", "get_sitemap")
    builder.add_edge("get_sitemap", "scrape_manager")
    builder.add_edge("scrape_manager", "scraper")
    builder.add_edge("scraper", "evaluate")

    builder.add_conditional_edges(
        "evaluate",
        should_continue_scraping,
        {
            "continue_scraping": "scrape_manager",
            "end_process": END
        }
    )

    try:
        graph = builder.compile()
        logging.info("Graph compiled successfully.")
        return graph
    except Exception as e:
        logging.error(f"Failed to compile graph: {e}")
        raise RuntimeError(f"Graph compilation failed: {e}") from e

def main(url: str = "", keyword: str = "") -> None:
    """Run the web scraping agent with local Firecrawl."""
    setup_logging()

    logging.info("Starting web scraping agent")
    logging.info(f"Target URL: {url}")
    logging.info(f"Search keyword: {keyword}")

    settings = load_settings()

    if not url:
        logging.error("No target URL provided")
        return

    graph = create_graph(settings)

    config = {
        "configurable": {
            "url": url,
            "keyword": keyword
        },
        "settings": settings,
        "recursion_limit": 2000
    }

    logging.info("\nStarting processing...")

    try:
        state = {}
        processed_count = 0
        max_batches = 100

        for batch in range(max_batches):
            state = graph.invoke(state, config=config)

            if state.get("is_information_found", False):
                logging.info(f"Information found in batch {batch + 1}")
                break

            current_index = state.get("current_url_index", 0)
            total_urls = state.get("total_urls", 0)
            processed_count = current_index

            if current_index >= total_urls:
                logging.info("All URLs processed")
                break

            progress = (current_index / total_urls) * 100 if total_urls > 0 else 0
            logging.info(f"Progress: {current_index}/{total_urls} URLs ({progress:.2f}%)")

            if batch > 10 and batch % 10 == 0:
                logging.info(f"Processed {batch} batches without finding information. Continuing...")

    except Exception as e:
        logging.error(f"Error during graph execution: {e}")
        state = None

    logging.info("\n--- Final Results ---")
    if state:
        if state.get("is_information_found", False):
            found_url = state.get("extracted_from_url", "unknown")
            extracted_info = state.get("extracted_info", "")
            logging.info(f"\n✅ Information for '{keyword}' found at {found_url}")

            if extracted_info:
                info_preview = extracted_info[:500] + "..." if len(extracted_info) > 500 else extracted_info
                logging.info(f"\nExtracted information preview:\n{info_preview}")
        else:
            processed = state.get("current_url_index", processed_count)
            logging.info(f"\n❌ Information for '{keyword}' could not be found after checking {processed} URLs.")
    else:
        logging.warning("No state was returned from the graph execution.")

if __name__ == "__main__":
    target_url = "https://python.langchain.com"
    search_keyword = "How to track token usage for LLMs"

    if not target_url or not search_keyword:
        print("Please set the target_url and search_keyword variables.")
    else:
        main(target_url, search_keyword)
