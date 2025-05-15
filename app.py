import time
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import undetected_chromedriver as uc

visited = set()

def get_links_uc(url, base_domain):
    links = {}
    try:
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-blink-features=AutomationControlled")

        driver = uc.Chrome(options=options)
        driver.get(url)
        time.sleep(10)  # Let JavaScript load content

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        anchors = soup.find_all("a", href=True)

        print(f"Found {len(anchors)} links on {url}")

        for a in anchors:
            href = a['href']
            text = a.get_text(strip=True)[:100]
            full_url = urljoin(url, href)
            if urlparse(full_url).netloc == base_domain and full_url not in visited:
                links[text or href] = full_url

        driver.quit()
    except Exception as e:
        print(f"[ERROR] {e}")
    return links

# === Run the script ===
if __name__ == "__main__":
    start_url = "https://www.lawmatrix.ai"
    domain = urlparse(start_url).netloc
    visited.clear()

    found_links = get_links_uc(start_url, domain)

    print("\n📄 Extracted Links:")
    for text, href in found_links.items():
        print(f"- {text}: {href}")

