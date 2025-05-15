import streamlit as st
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright

visited_urls = set()

def get_links_playwright(url, base_domain):
    links = {}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(url, timeout=20000, wait_until="networkidle")
            page.wait_for_timeout(3000)  # Wait additional 3 seconds for JS rendering

            anchors = page.query_selector_all("a[href]")
            print(f"Found {len(anchors)} anchors on {url}")

            for anchor in anchors:
                href = anchor.get_attribute("href")
                text = anchor.inner_text().strip()[:100]
                if href:
                    full_url = urljoin(url, href)
                    if urlparse(full_url).netloc == base_domain and full_url not in visited_urls:
                        links[text or href] = full_url
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
            st.warning("No links found. This may be due to JavaScript rendering delay or DOM protection.")
            st.code("Try increasing wait time or checking if the page uses iframe / delayed JS.")
    else:
        st.warning("Please enter a valid URL.")
