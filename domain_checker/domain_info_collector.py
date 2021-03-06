import logging

from typing import List, Set

from .settings import Settings

import aiohttp

logger = logging.getLogger(__name__)

API_URL = (
    f"https://api.jsonwhois.io/whois/domain?key={Settings.API_KEY}&domain={{domain}}"
)


async def _fetch(url: str, session: aiohttp.ClientSession) -> dict:
    async with session.get(url) as resp:
        logger.info(f"fetcing {url}")
        return await resp.json()


def _extract_info_from_response(response: dict) -> dict:
    result = response["result"]
    status = result["status"] or ""
    nameservers = result["nameservers"] or ""
    if isinstance(status, list):
        status = ", ".join(status)
    if isinstance(nameservers, list):
        nameservers = ", ".join(nameservers)
    return {
        "domain": result["name"],
        "nameservers": nameservers,
        "registered": result["registered"],
        "registration_date": result["created"],
        "expiration_date": result["expires"],
        "status": status,
        "extra_info": result,
    }


async def fetch_domains_info(domains: List[str] or Set[str]) -> List[dict]:
    url = API_URL
    async with aiohttp.ClientSession() as session:

        domains_info = []
        for domain in domains:
            try:
                resp = await _fetch(url.format(domain=domain), session)
                info = _extract_info_from_response(resp)
            except Exception as err:
                logging.exception(err)
            else:
                domains_info.append(info)

    return domains_info
