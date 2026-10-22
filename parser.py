import asyncio
import logging
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from typing import Dict, List

logger = logging.getLogger(__name__)


def _safe_err(exc: BaseException) -> str:
    return str(exc).encode("ascii", errors="replace").decode("ascii")


async def _launch_browser(playwright):
    launch_args = {
        "headless": True,
        "args": ["--disable-blink-features=AutomationControlled"],
    }
    last_error = None
    for channel in (None, "msedge", "chrome"):
        try:
            if channel is None:
                return await playwright.chromium.launch(**launch_args)
            return await playwright.chromium.launch(channel=channel, **launch_args)
        except Exception as exc:
            last_error = exc
            logger.warning("Browser launch failed (%s): %s", channel or "bundled", _safe_err(exc))
    raise RuntimeError(f"Could not launch browser: {_safe_err(last_error)}")


async def parse_upwork_rss(rss_url: str) -> List[Dict[str, str]]:
    """Надежный парсер Upwork через HTML-страницу поиска с эмуляцией реального браузера."""
    jobs = []
    # Превращаем RSS-ссылку в обычный URL поиска
    search_url = rss_url.replace("/nx/search/jobs/rss", "/nx/search/jobs/")

    try:
        async with async_playwright() as p:
            # Запускаем браузер с аргументами, чтобы обходить защиту Cloudflare
            browser = await _launch_browser(p)
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 800}
            )
            page = await context.new_page()

            logger.info("Opening Upwork search: %s", search_url)
            try:
                await page.goto(search_url, timeout=45000, wait_until="domcontentloaded")
                await asyncio.sleep(3)
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(2)

                await page.wait_for_selector(
                    "article, section.up-card-section, div.job-tile, [data-test='JobTile'], a[data-test='job-title']",
                    timeout=15000,
                )
            except Exception as e:
                logger.warning("Job cards did not load in time: %s", _safe_err(e))

            html_content = await page.content()
            await browser.close()

            soup = BeautifulSoup(html_content, "html.parser")

            # Ищем карточки по всем возможным актуальным селекторам Upwork
            job_cards = soup.select("article, section.up-card-section, div.job-tile, [data-test='JobTile']")
            logger.info("Job cards found: %s", len(job_cards))

            if not job_cards:
                title_links = soup.select("a[data-test='job-title'], h2 a.job-title-link, h2 a")
                for title_elem in title_links:
                    title = title_elem.get_text(strip=True)
                    href = title_elem.get("href", "")
                    if not href or len(title) <= 3:
                        continue
                    link = "https://www.upwork.com" + href if href.startswith("/") else href
                    jobs.append({
                        "id": link,
                        "title": title,
                        "link": link,
                        "published_at": "Just now",
                        "description": title,
                    })
                unique_jobs = {job["link"]: job for job in jobs}.values()
                jobs = list(unique_jobs)
                logger.info("Unique jobs from title links: %s", len(jobs))
                return jobs

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
            logger.info("Unique jobs total: %s", len(jobs))

    except Exception as e:
        logger.error("Upwork HTML parse failed: %s", _safe_err(e))

    return jobs