import streamlit as st
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

visited_urls = set()

def get_links_playwright(url, base_domain):
    links = {}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)  # Run in headed mode to mimic real user
            context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36")
            page = context.new_page()
            page.goto(url, timeout=30000, wait_until="networkidle")
            page.wait_for_timeout(15000)  # Wait 15 seconds for complete JS rendering

            # Screenshot for debug
            page.screenshot(path="debug.png", full_page=True)

            # First, parse the main page content
            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')
            anchors = soup.find_all('a', href=True)
            print(f"Found {len(anchors)} anchors on main page of {url}")

            for a in anchors:
                href = a['href']
                text = a.get_text(strip=True)[:100]
                full_url = urljoin(url, href)
                if urlparse(full_url).netloc == base_domain and full_url not in visited_urls:
                    links[text or href] = full_url

            # Then, check iframes and scrape their links too
            for frame in page.frames:
                if frame.url != page.url:
                    try:
                        frame_html = frame.content()
                        frame_soup = BeautifulSoup(frame_html, 'html.parser')
                        frame_anchors = frame_soup.find_all('a', href=True)
                        print(f"Found {len(frame_anchors)} anchors in iframe: {frame.url}")
                        for a in frame_anchors:
                            href = a['href']
                            text = a.get_text(strip=True)[:100]
                            full_url = urljoin(frame.url, href)
                            if urlparse(full_url).netloc == base_domain and full_url not in visited_urls:
                                links[text or href] = full_url
                    except Exception as e:
                        print(f"[Iframe ERROR] {e}")

            browser.close()
    except Exception as e:
        print(f"[ERROR] {e}")
    return links

def crawl_site_recursive_playwright(url, base_domain, depth):
    if depth == 0 or url in visited_urls:
        return {}
    visited_urls.add(url)
    all_links = get_links_playwright(url, base_domain)
    for _, link_href in all_links.items():
        if link_href not in visited_urls:
            deeper_links = crawl_site_recursive_playwright(link_href, base_domain, depth - 1)
            all_links.update(deeper_links)
    return all_links

# Streamlit UI
st.title("AI-Powered Web Crawler using Playwright")

url_input = st.text_input("Enter a website URL:", "https://www.lawmatrix.ai")
max_depth = st.slider("Crawl depth:", 1, 3, 2)

if st.button("Start Crawling"):
    if url_input:
        st.write(f"Crawling with Playwright: {url_input} | Depth = {max_depth}")
        parsed = urlparse(url_input)
        domain = parsed.netloc
        visited_urls.clear()

        with st.spinner("Crawling with browser rendering..."):
            links = crawl_site_recursive_playwright(url_input, domain, max_depth)

        if links:
            st.success(f"Found {len(links)} links.")
            for text, href in links.items():
                st.markdown(f"- [{text}]({href})")
        else:
            st.warning("No links found. This may be due to JavaScript rendering delay, iframe use, or bot protection.")
            st.code("Try increasing wait time, inspecting screenshot (debug.png), or reviewing page structure.")
    else:
        st.warning("Please enter a valid URL.")
