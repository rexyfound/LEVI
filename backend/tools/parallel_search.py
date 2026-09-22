import json
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

def _fetch_ddg_search(query: str, max_results: int = 5) -> dict:
    """Fetch search results from DuckDuckGo HTML / Lite API."""
    try:
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )
        with urllib.request.urlopen(req, timeout=6) as response:
            html = response.read().decode("utf-8", errors="ignore")
            
        # Parse basic links & snippets
        import re
        results = []
        snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', html, re.DOTALL)
        titles = re.findall(r'<a class="result__url[^>]*>(.*?)</a>', html, re.DOTALL)
        
        for i in range(min(max_results, len(snippets))):
            clean_snippet = re.sub(r'<[^>]+>', '', snippets[i]).strip()
            clean_title = re.sub(r'<[^>]+>', '', titles[i]).strip() if i < len(titles) else ""
            if clean_snippet:
                results.append({"title": clean_title, "snippet": clean_snippet})
                
        if results:
            return {"source": "DuckDuckGo", "success": True, "results": results}
        return {"source": "DuckDuckGo", "success": False, "error": "No results found"}
    except Exception as e:
        return {"source": "DuckDuckGo", "success": False, "error": str(e)}

def _fetch_wikipedia_search(query: str) -> dict:
    """Fetch search summary from Wikipedia REST API."""
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(query)}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "LEVI-Agent/1.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            extract = data.get("extract")
            title = data.get("title")
            if extract:
                return {
                    "source": "Wikipedia",
                    "success": True,
                    "results": [{"title": title, "snippet": extract, "url": data.get("content_urls", {}).get("desktop", {}).get("page", "")}]
                }
        return {"source": "Wikipedia", "success": False, "error": "No extract"}
    except Exception as e:
        return {"source": "Wikipedia", "success": False, "error": str(e)}

def parallel_web_search(query: str) -> dict:
    """
    Run parallel search across multiple search engines.
    Returns the first successful result set immediately.
    """
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(_fetch_ddg_search, query),
            executor.submit(_fetch_wikipedia_search, query)
        ]
        
        results = []
        for future in as_completed(futures):
            try:
                res = future.result()
                if res.get("success"):
                    return res
                else:
                    results.append(res)
            except Exception:
                pass
                
        return {
            "success": False,
            "query": query,
            "error": "All search engines timed out or returned no results.",
            "attempts": results
        }
