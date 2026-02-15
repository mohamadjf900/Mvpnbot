import asyncio
import aiohttp
import logging
from database import add_proxy

PROXY_SOURCES = [
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
]

async def fetch_proxies_from_url(session, url):
    try:
        async with session.get(url) as resp:
            if resp.status == 200:
                text = await resp.text()
                lines = text.strip().split('\n')
                if "http.txt" in url:
                    proxy_type = "HTTP"
                elif "socks4.txt" in url:
                    proxy_type = "SOCKS4"
                elif "socks5.txt" in url:
                    proxy_type = "SOCKS5"
                else:
                    proxy_type = "UNKNOWN"
                for line in lines[:50]:  # فقط 50 تا اول
                    parts = line.strip().split(':')
                    if len(parts) == 2:
                        ip, port = parts[0], parts[1]
                        await add_proxy(proxy_type, ip, int(port))
                logging.info(f"Added {len(lines[:50])} proxies from {url}")
    except Exception as e:
        logging.error(f"Error fetching {url}: {e}")

async def update_proxies_periodically():
    while True:
        async with aiohttp.ClientSession() as session:
            tasks = [fetch_proxies_from_url(session, url) for url in PROXY_SOURCES]
            await asyncio.gather(*tasks)
        await asyncio.sleep(6 * 3600)  # هر ۶ ساعت
