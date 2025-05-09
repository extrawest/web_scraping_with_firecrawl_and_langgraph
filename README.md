# 🕸️ Agentic Web Scraping with Firecrawl and LangGraph

[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)]()
[![Maintainer](https://img.shields.io/static/v1?label=Yevhen%20Ruban&message=Maintainer&color=red)](mailto:yevhen.ruban@extrawest.com)
[![Ask Me Anything !](https://img.shields.io/badge/Ask%20me-anything-1abc9c.svg)]()
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
![GitHub release](https://img.shields.io/badge/release-v1.0.0-blue)


This repository contains an intelligent web scraping solution that uses Firecrawl for content extraction and LangGraph for orchestrating the scraping workflow. 
The system can automatically crawl websites, extract content, and search for specific keywords or information.




https://github.com/user-attachments/assets/e67ce230-d2da-47f8-9ff2-007849dd1d08




## 🚀 Features

- **Automated Sitemap Extraction**: Automatically discovers all pages on a website
- **Intelligent Content Extraction**: Extracts markdown, HTML, or text content from web pages
- **Keyword Search**: Searches for specific keywords or phrases across all pages
- **Progress Tracking**: Real-time progress updates during scraping
- **Error Handling**: Robust error handling for network issues and parsing errors
- **Configurable**: Easy to configure for different websites and search terms
- **LangGraph Workflow**: Uses LangGraph for structured, maintainable scraping workflows

## 📋 Requirements

The code requires the following dependencies:
- Python 3.8+
- firecrawl-py
- langgraph
- pydantic-settings
- python-dotenv

## 🛠️ Installation

```bash
# Clone the repository
git clone https://github.com/extrawest/web_scraping_with_firecrawl_and_langgraph.git
cd web_scraping_with_firecrawl_and_langgraph

# Install required packages
pip install -r requirements.txt

# Create a .env file with your configuration
echo "FIRECRAWL_URL=http://localhost:3002" > .env
```

## 📝 Usage

### Basic Usage

```python
from scrape_the_web_agentically import main

# Run the scraper with a target URL and keyword
main(url="https://example.com", keyword="specific information")
```

### Command Line Usage

```bash
# Run the script directly
python scrape_the_web_agentically.py
```

### Configuration

You can modify the target URL and search keyword by editing the script:

```python
if __name__ == "__main__":
    target_url = "https://python.langchain.com"
    search_keyword = "LLMs"
    
    if not target_url or not search_keyword:
        print("Please set the target_url and search_keyword variables.")
    else:
        main(target_url, search_keyword)
```

## 🧠 How It Works

The script uses a LangGraph workflow to orchestrate the web scraping process:

1. **Initialization**: Sets up the initial state with the target URL and keyword
2. **Sitemap Extraction**: Fetches the sitemap to discover all pages on the website
3. **Batch Processing**: Processes URLs in batches for efficient scraping
4. **Content Extraction**: Extracts content from each page using Firecrawl
5. **Keyword Search**: Searches for the specified keyword in the extracted content
6. **Result Evaluation**: Determines if the information was found or if more URLs need to be processed

The workflow is visualized and saved as a PNG file for easy understanding of the process.

## 🔄 LangGraph Workflow

![firecrawl_langgraph_visualization](https://github.com/user-attachments/assets/0182b399-cb9d-40ef-bf10-02045f92c370)


The script uses LangGraph to create a structured workflow with the following nodes:

- `initialize_state`: Sets up the initial state with URL and keyword
- `get_sitemap`: Fetches the sitemap for the target URL
- `scrape_manager`: Manages batches of URLs for processing
- `scraper`: Extracts content from individual URLs
- `evaluate`: Checks if the keyword was found in the content

The workflow continues until either the keyword is found or all URLs have been processed.

## 🔧 Customization

### Firecrawl Server

By default, the script connects to a local Firecrawl server at `http://localhost:3002`. You can change this by:

1. Setting the `FIRECRAWL_URL` environment variable
2. Creating a `.env` file with `FIRECRAWL_URL=your-server-url`
3. Modifying the `firecrawl_url` parameter in the `Settings` class
