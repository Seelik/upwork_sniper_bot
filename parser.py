import urllib.request
import xml.etree.ElementTree as ET
from typing import Dict, List


def parse_upwork_rss(rss_url: str) -> List[Dict[str, str]]:
  """Парсит RSS-ленту Upwork и возвращает список словарей с данными вакансий."""
  jobs = []

  try:
    # Загружаем RSS с User-Agent, чтобы Upwork не блокировал запрос
    req = urllib.request.Request(
        rss_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )

    with urllib.request.urlopen(req) as response:
      xml_data = response.read()

    # Парсим XML
    root = ET.fromstring(xml_data)

    # В RSS элементы вакансий находятся внутри тега <item>
    for item in root.findall(".//item"):
      title_elem = item.find("title")
      link_elem = item.find("link")
      guid_elem = item.find("guid")
      pub_date_elem = item.find("pubDate")
      description_elem = item.find("description")

      title = title_elem.text if title_elem is not None else "No Title"
      link = link_elem.text if link_elem is not None else ""
      # Используем guid как уникальный ID, если его нет — берем ссылку
      job_id = (
          guid_elem.text
          if guid_elem is not None
          else (link if link else title)
      )
      published_at = pub_date_elem.text if pub_date_elem is not None else ""
      description = (
          description_elem.text if description_elem is not None else ""
      )

      jobs.append({
          "id": job_id,
          "title": title,
          "link": link,
          "published_at": published_at,
          "description": description,
      })

  except Exception as e:
    print(f"Ошибка при парсинге RSS: {e}")

  return jobs


if __name__ == "__main__":
  # Пример тестовой ссылки на RSS Upwork (сюда можно будет подставить реальный URL фильтра)
  test_url = "https://www.upwork.com/ab/feed/jobs/rss?q=python"
  print(f"Тестируем парсинг ленты: {test_url}")
  parsed_jobs = parse_upwork_rss(test_url)
  print(f"Найдено вакансий: {len(parsed_jobs)}")
  if parsed_jobs:
    print("Первая вакансия:", parsed_jobs[0]["title"])