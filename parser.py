from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from typing import Dict, List


async def parse_upwork_rss(rss_url: str) -> List[Dict[str, str]]:
  """Асинхронно парсит Upwork через движок Chromium в Playwright."""
  jobs = []
  search_url = rss_url.replace("/rss", "/")

  try:
    async with async_playwright() as p:
      browser = await p.chromium.launch(headless=True)
      page = await browser.new_page(
          user_agent=(
              "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
              " (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
          )
      )

      await page.goto(search_url, timeout=30000)

      try:
        await page.wait_for_selector(
            "section.up-card-section, article.job-tile, h2.job-title",
            timeout=10000,
        )
      except Exception:
        pass

      html_content = await page.content()
      await browser.close()

      soup = BeautifulSoup(html_content, "html.parser")
      job_cards = soup.select(
          "section.up-card-section, article.job-tile, div.job-tile"
      )

      if not job_cards:
        job_cards = soup.select("h2.job-title a, h2 a")
        for a_tag in job_cards:
          title = a_tag.get_text(strip=True)
          link = "https://www.upwork.com" + a_tag.get("href", "")
          if title and link:
            jobs.append({
                "id": link,
                "title": title,
                "link": link,
                "published_at": "Just now",
                "description": title,
            })
      else:
        for card in job_cards:
          title_elem = card.select_one("h2 a, a.job-title-link")
          desc_elem = card.select_one("div.job-description, p.body-sm")

          if title_elem:
            title = title_elem.get_text(strip=True)
            link = "https://www.upwork.com" + title_elem.get("href", "")
            description = (
                desc_elem.get_text(strip=True) if desc_elem else title
            )

            jobs.append({
                "id": link,
                "title": title,
                "link": link,
                "published_at": "Just now",
                "description": description,
            })

  except Exception as e:
    print(f"Ошибка при асинхронном парсинге через Playwright: {e}")

  return jobs