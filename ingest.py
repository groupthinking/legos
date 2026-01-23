#!/usr/bin/env python3
"""
Google OSS License Page Scraper using Playwright

This script scrapes license information from Google's OSS license page,
handling authentication and outputting structured JSONL data.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext


def setup_browser(headless: bool = False) -> tuple[Browser, BrowserContext, Page]:
    """
    Initialize Playwright browser with proper configuration.
    
    Args:
        headless: Whether to run browser in headless mode
        
    Returns:
        Tuple of (browser, context, page)
    """
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=headless)
    context = browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    )
    page = context.new_page()
    return browser, context, page


def wait_for_authentication(page: Page, url: str) -> None:
    """
    Navigate to URL and pause for manual authentication if needed.
    
    Args:
        page: Playwright page object
        url: Target URL to navigate to
    """
    print(f"[INFO] Navigating to: {url}")
    page.goto(url, wait_until='domcontentloaded')
    
    # Check if authentication is required
    # Look for common auth indicators
    if any(keyword in page.url.lower() for keyword in ['login', 'signin', 'auth']):
        print("\n" + "="*60)
        print("[AUTH] Authentication required!")
        print("[AUTH] Please log in manually in the browser window.")
        print("[AUTH] Press Enter in this terminal when done...")
        print("="*60 + "\n")
        input()
        print("[INFO] Continuing after authentication...")


def scrape_license_list(page: Page) -> List[Dict[str, Any]]:
    """
    Scrape license list items from the page.
    
    This function extracts license information including:
    - Package/library name
    - License type
    - License text content
    - Any additional metadata
    
    Args:
        page: Playwright page object
        
    Returns:
        List of dictionaries containing license information
    """
    licenses = []
    
    try:
        # Wait for content to load
        # Common selectors for OSS license pages
        page.wait_for_load_state('networkidle', timeout=10000)
        
        # Try multiple common patterns for OSS license pages
        selectors = [
            'li',  # Generic list items
            '.license-item',
            '[data-license]',
            'article',
            '.library-item',
            '.package-item'
        ]
        
        # Find which selector works
        working_selector = None
        for selector in selectors:
            elements = page.query_selector_all(selector)
            if elements and len(elements) > 0:
                working_selector = selector
                print(f"[INFO] Found {len(elements)} items using selector: {selector}")
                break
        
        if not working_selector:
            print("[WARN] No standard license list found, trying to extract all text content")
            # Fallback: extract all text content
            body_text = page.inner_text('body')
            licenses.append({
                'type': 'full_page',
                'content': body_text,
                'source': page.url
            })
            return licenses
        
        # Extract license information from elements
        elements = page.query_selector_all(working_selector)
        
        for idx, element in enumerate(elements):
            try:
                # Extract text content
                text = element.inner_text().strip()
                
                # Skip empty elements
                if not text or len(text) < 10:
                    continue
                
                # Try to extract structured data
                license_data = {
                    'id': idx,
                    'content': text,
                    'html': element.inner_html(),
                }
                
                # Try to find package name (usually in heading or strong tag)
                name_element = element.query_selector('h1, h2, h3, h4, strong, .name, .package-name')
                if name_element:
                    license_data['name'] = name_element.inner_text().strip()
                
                # Try to find license type
                license_type_element = element.query_selector('.license-type, .type, [class*="license"]')
                if license_type_element:
                    license_data['license_type'] = license_type_element.inner_text().strip()
                
                # Try to find links
                links = element.query_selector_all('a')
                if links:
                    license_data['links'] = [link.get_attribute('href') for link in links if link.get_attribute('href')]
                
                licenses.append(license_data)
                
            except Exception as e:
                print(f"[WARN] Error processing element {idx}: {e}")
                continue
        
        print(f"[INFO] Successfully extracted {len(licenses)} licenses")
        
    except Exception as e:
        print(f"[ERROR] Error during scraping: {e}")
        raise
    
    return licenses


def save_to_jsonl(data: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save scraped data to JSONL (JSON Lines) format.
    
    Args:
        data: List of dictionaries to save
        output_path: Path to output JSONL file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in data:
            json.dump(item, f, ensure_ascii=False)
            f.write('\n')
    
    print(f"[SUCCESS] Saved {len(data)} items to {output_path}")


def main():
    """Main execution function."""
    # Configuration
    # Default to Google's open source page - modify as needed
    target_url = sys.argv[1] if len(sys.argv) > 1 else "https://opensource.google/projects"
    output_file = Path(sys.argv[2] if len(sys.argv) > 2 else "licenses.jsonl")
    headless = "--headless" in sys.argv
    
    print(f"[INFO] Starting Google OSS License Scraper")
    print(f"[INFO] Target URL: {target_url}")
    print(f"[INFO] Output file: {output_file}")
    print(f"[INFO] Headless mode: {headless}")
    
    playwright_instance = None
    browser = None
    
    try:
        # Setup browser
        playwright_instance = sync_playwright().start()
        browser = playwright_instance.chromium.launch(headless=headless)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = context.new_page()
        
        # Handle authentication
        wait_for_authentication(page, target_url)
        
        # Scrape licenses
        licenses = scrape_license_list(page)
        
        # Validate we got data
        if not licenses:
            print("[ERROR] No licenses were extracted!")
            return 1
        
        # Save to JSONL
        save_to_jsonl(licenses, output_file)
        
        print("\n[SUCCESS] Scraping completed successfully!")
        return 0
        
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user")
        return 130
        
    except Exception as e:
        print(f"\n[ERROR] Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        # Cleanup
        if browser:
            browser.close()
        if playwright_instance:
            playwright_instance.stop()


if __name__ == "__main__":
    sys.exit(main())
