from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe", headless=True)
    page = browser.new_page()
    page.goto("http://localhost:8501")
    page.locator('label:has-text("Document processing")').click()
    page.wait_for_timeout(2000)
    page.locator('input[type="file"]').set_input_files("sample_data/synthetic_003_mismatch.png")
    page.wait_for_timeout(2000)
    page.locator('button:has-text("Extract fields")').click()
    page.wait_for_timeout(4000)
    page.locator('button:has-text("Run validation")').click()
    page.wait_for_timeout(3000)
    tabs = page.locator('[role="tab"]').all_text_contents()
    print("Found role=tab:", tabs)
    for el in page.locator('[role="tab"]').all():
        print("HTML:", el.evaluate("el => el.outerHTML"))
    browser.close()
