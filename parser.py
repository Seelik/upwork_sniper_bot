import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from typing import Dict, List


async def parse_upwork_rss(rss_url: str) -> List[Dict[str, str]]:
    """Надежный парсер Upwork через HTML-страницу поиска с эмуляцией реального браузера."""
    jobs = []
    # Превращаем RSS-ссылку в обычный URL поиска
    search_url = rss_url.replace("/nx/search/jobs/rss", "/nx/search/jobs/")

    try:
        async with async_playwright() as p:
            # Запускаем браузер с аргументами, чтобы обходить защиту Cloudflare
            browser = await p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 800}
            )
            page = await context.new_page()

            print(f"Открываем поиск Upwork: {search_url}")
            try:
                await page.goto(search_url, timeout=35000, wait_until="domcontentloaded")
                # Даем странице время на отрисовку клиентского JS
                await asyncio.sleep(4)
                
                # Ждем появления карточек вакансий
                await page.wait_for_selector(
                    "article, section.up-card-section, div.job-tile, [data-test='JobTile']",
                    timeout=12000,
                )
            except Exception as e:
                print(f"Не удалось дождаться прогрузки карточек: {e}")

            html_content = await page.content()
            await browser.close()

            soup = BeautifulSoup(html_content, "html.parser")

            # Ищем карточки по всем возможным актуальным селекторам Upwork
            job_cards = soup.select("article, section.up-card-section, div.job-tile, [data-test='JobTile']")
            print(f"Найдено карточек: {len(job_cards)}")

            for card in job_cards:
                title_elem = card.select_one(
                    "h2 a, a.job-title-link, h3 a, a[data-test='job-title'], [data-test='UpLink']"
                )
                desc_elem = card.select_one(
                    "[data-test='job-description-text'], [data-test='JobTileDescription'], div.job-description, p.mb-0"
                )

                if title_elem:
                    title = title_elem.get_text(strip=True)
                    href = title_elem.get("href", "")
                    link = "https://www.upwork.com" + href if href.startswith("/") else href
                    
                    if desc_elem:
                        description = desc_elem.get_text(separator=" ", strip=True)
                    else:
                        description = title

                    # Фильтруем пустые или системные заглушки
                    if len(title) > 3:
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
        print(f"Ошибка при парсинге HTML: {e}")

    return jobs