from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from typing import Dict, List


async def parse_upwork_rss(rss_url: str) -> List[Dict[str, str]]:
    """Асинхронно парсит Upwork через Playwright и извлекает точные описания."""
    jobs = []
    search_url = rss_url.replace("/rss", "/")

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                )
            )

            print(f"Открываем страницу: {search_url}")
            await page.goto(search_url, timeout=30000)

            try:
                await page.wait_for_selector(
                    "section.up-card-section, article.job-tile, div.job-tile, [data-test='JobTile']",
                    timeout=10000,
                )
            except Exception:
                pass

            html_content = await page.content()
            await browser.close()

            soup = BeautifulSoup(html_content, "html.parser")

            # Находим карточки
            job_cards = soup.select(
                "section.up-card-section, article.job-tile, div.job-tile, [data-test='JobTile']"
            )
            print(f"Найдено карточек вакансий: {len(job_cards)}")

            for card in job_cards:
                title_elem = card.select_one(
                    "h2 a, a.job-title-link, h3 a, a[data-test='job-title'], [data-test='UpLink']"
                )
                
                # Точные селекторы описания Upwork
                desc_elem = card.select_one(
                    "[data-test='job-description-text'], [data-test='JobTileDescription'], div.job-description, p.mb-0"
                )

                if title_elem:
                    title = title_elem.get_text(strip=True)
                    href = title_elem.get("href", "")
                    link = "https://www.upwork.com" + href if href.startswith("/") else href
                    
                    # Извлекаем текст описания
                    if desc_elem:
                        description = desc_elem.get_text(separator=" ", strip=True)
                    else:
                        description = title

                    print(f"\n--- Вакансия: {title} ---")
                    print(f"Текст описания: {description[:120]}...")

                    jobs.append({
                        "id": link,
                        "title": title,
                        "link": link,
                        "published_at": "Just now",
                        "description": description,
                    })

            unique_jobs = {job["link"]: job for job in jobs}.values()
            jobs = list(unique_jobs)
            print(f"\nИтого уникальных вакансий: {len(jobs)}")

    except Exception as e:
        print(f"Ошибка при парсинге: {e}")

    return jobs