import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import re

# API Key from file
with open('api_key.txt', 'r') as f:
    API_KEY = f.read().strip()

# Configure Cerebras (OpenAI-compatible)
client = OpenAI(
    api_key='csk_chm8ecccc54dfhmn38t8jdpwy3erf44pnmctydecnepy9xrt',
    base_url="https://api.cerebras.ai/v1"
)

# URL to fetch
URL = 'https://en.wikipedia.org/wiki/Artificial_intelligence'

def fetch_and_clean_webpage(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Remove scripts, styles, nav, header, footer, aside, etc.
    for tag in soup(["script", "style", "nav", "header", "footer", "aside", "noscript", "meta", "link"]):
        tag.decompose()

    # Remove specific footer or irrelevant divs if present
    footer = soup.find('div', {'id': 'footer'})
    if footer:
        footer.decompose()

    # Extract main content (for Wikipedia)
    content_div = soup.find('div', {'id': 'mw-content-text'})
    if content_div:
        text = content_div.get_text(separator=' ', strip=True)
    else:
        # Fallback: get text from body or all
        body = soup.find('body')
        if body:
            text = body.get_text(separator=' ', strip=True)
        else:
            text = soup.get_text(separator=' ', strip=True)

    # Clean further: remove excessive whitespace and non-content text
    text = re.sub(r'\s+', ' ', text).strip()
    # Remove common irrelevant phrases
    text = re.sub(r'Wikipedia.*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'From Wikipedia.*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Jump to.*', '', text, flags=re.IGNORECASE)
    return text[:5000]  # Limit to first 5000 chars to avoid token limits

def summarize_with_cerebras(text):
    prompt = f"""
    Analyze the following webpage content about Artificial Intelligence and summarize it into 3-5 concise bullet points focusing on key aspects, trends, and implications. Then, provide one short insight that interprets the overall theme or trend in a single line.

    Content:
    {text}

    Output format:
    Summary:
    • <point 1>
    • <point 2>
    • <point 3>
    • <point 4>
    • <point 5>

    Insight:
    <single-line insight>
    """

    response = client.chat.completions.create(
        model="llama3.1-8b",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def main():
    cleaned_text = fetch_and_clean_webpage(URL)
    result = summarize_with_cerebras(cleaned_text)

    # Print to console
    print(result)

    # Save to file
    with open('summary_output.txt', 'w') as f:
        f.write(result)

if __name__ == '__main__':
    main()
