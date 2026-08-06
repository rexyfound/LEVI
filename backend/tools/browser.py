from playwright.sync_api import sync_playwright

_playwright = None
_browser = None
_page = None

INTERACTIVE_SELECTOR = (
    "input, textarea, button, select, a[href], "
    "[role='button'], [role='link'], [role='textbox'], "
    "[contenteditable='true']"
)

def _get_page():
    global _playwright, _browser, _page

    if _playwright is None:
        _playwright = sync_playwright().start()

    if _browser is None:
        _browser = _playwright.chromium.launch(headless=False)

    if _page is None or _page.is_closed():
        _page = _browser.new_page()

    return _page


def browser_open(url):
    if not url.startswith(("http://", "https://")):
        return {"error": "Invalid URL"}

    try:
        page = _get_page()
        page.goto(url, wait_until="domcontentloaded", timeout=30000)

        return {
            "success": True,
            "title": page.title(),
            "url": page.url
        }

    except Exception as e:
        return {"error": str(e)}


def browser_snapshot():
    try:
        page = _get_page()

        elements = page.locator(INTERACTIVE_SELECTOR)

        visible = []
        count = min(elements.count(), 80)

        for i in range(count):
            element = elements.nth(i)

            try:
                if not element.is_visible():
                    continue

                tag = element.evaluate("el => el.tagName.toLowerCase()")

                text = (element.inner_text() or "").strip()
                placeholder = element.get_attribute("placeholder")
                aria_label = element.get_attribute("aria-label")
                role = element.get_attribute("role")
                input_type = element.get_attribute("type")

                name = (
                    aria_label
                    or placeholder
                    or text
                    or element.get_attribute("name")
                    or element.get_attribute("title")
                    or ""
                ).strip()

                if not role:
                    if tag in ("input", "textarea"):
                        role = "textbox"
                    elif tag == "button":
                        role = "button"
                    elif tag == "a":
                        role = "link"
                    elif tag == "select":
                        role = "combobox"
                    else:
                        role = tag

                # Skip useless unnamed elements
                if not name and role not in ("textbox", "combobox"):
                    continue

                item = {
                    "id": i,
                    "role": role
                }

                if name:
                    item["name"] = name[:80]

                if input_type and input_type not in ("text",):
                    item["type"] = input_type

                visible.append(item)

            except Exception:
                continue

        return {
            "title": page.title()[:100],
            "url": page.url,
            "elements": visible
        }

    except Exception as e:
        return {"error": str(e)}


def browser_click(index):
    try:
        page = _get_page()

        elements = page.locator(INTERACTIVE_SELECTOR)

        element = elements.nth(index)

        if not element.is_visible():
            return {"error": "Element is not visible"}

        element.click()

        page.wait_for_timeout(500)

        return {
            "success": True,
            "title": page.title(),
            "url": page.url
        }

    except Exception as e:
        return {"error": str(e)}


def browser_type(index, text):
    try:
        page = _get_page()

        elements = page.locator(INTERACTIVE_SELECTOR)

        element = elements.nth(index)

        if not element.is_visible():
            return {"error": "Element is not visible"}

        element.fill(text)

        return {
            "success": True,
            "typed": text
        }

    except Exception as e:
        return {"error": str(e)}
def browser_type_by_text(label, text):
    try:
        page = _get_page()

        # Try placeholder first
        locator = page.get_by_placeholder(label, exact=False)

        if locator.count() > 0:
            locator.first.fill(text)

            return {
                "success": True,
                "method": "placeholder",
                "field": label,
                "typed": text
            }

        # Try accessible label
        locator = page.get_by_label(label, exact=False)

        if locator.count() > 0:
            locator.first.fill(text)

            return {
                "success": True,
                "method": "label",
                "field": label,
                "typed": text
            }

        # Try aria-label
        locator = page.locator(
            f'[aria-label*="{label}" i]'
        )

        if locator.count() > 0:
            locator.first.fill(text)

            return {
                "success": True,
                "method": "aria-label",
                "field": label,
                "typed": text
            }

        return {
            "error": f'No input found matching "{label}"'
        }

    except Exception as e:
        return {
            "error": str(e)
        }    
def browser_press(label, key):
    try:
        page = _get_page()

        # Try placeholder
        locator = page.get_by_placeholder(label, exact=False)

        if locator.count() > 0:
            locator.first.press(key)

            return {
                "success": True,
                "field": label,
                "key": key,
                "url": page.url
            }

        # Try accessible label
        locator = page.get_by_label(label, exact=False)

        if locator.count() > 0:
            locator.first.press(key)

            return {
                "success": True,
                "field": label,
                "key": key,
                "url": page.url
            }

        # Try aria-label
        locator = page.locator(
            f'[aria-label*="{label}" i]'
        )

        if locator.count() > 0:
            locator.first.press(key)

            return {
                "success": True,
                "field": label,
                "key": key,
                "url": page.url
            }

        return {
            "error": f'No element found matching "{label}"'
        }

    except Exception as e:
        return {
            "error": str(e)
        }
def browser_observe():
    try:
        page = _get_page()

        elements = page.locator(
            "input, textarea, button, select, a[href], "
            "[role='button'], [role='link'], [role='textbox'], "
            "[contenteditable='true']"
        )

        observed = []

        count = min(elements.count(), 100)

        for i in range(count):
            element = elements.nth(i)

            try:
                if not element.is_visible():
                    continue

                tag = element.evaluate(
                    "el => el.tagName.toLowerCase()"
                )

                text = (element.inner_text() or "").strip()
                placeholder = element.get_attribute("placeholder")
                aria_label = element.get_attribute("aria-label")
                role = element.get_attribute("role")
                input_type = element.get_attribute("type")
                value = element.get_attribute("value")

                if input_type == "password":
                    value = None

                # Determine useful human-readable name
                name = (
                    aria_label
                    or placeholder
                    or text
                    or element.get_attribute("name")
                    or element.get_attribute("title")
                    or ""
                )

                # Infer role
                if not role:
                    if tag in ["input", "textarea"]:
                        role = "textbox"
                    elif tag == "button":
                        role = "button"
                    elif tag == "a":
                        role = "link"
                    elif tag == "select":
                        role = "combobox"
                    else:
                        role = tag

                observed.append({
                    "id": i,
                    "role": role,
                    "name": name[:120],
                    "tag": tag,
                    "type": input_type,
                    "value": value,
                    "enabled": element.is_enabled()
                })

            except Exception:
                continue

        return {
            "title": page.title(),
            "url": page.url,
            "elements": observed
        }

    except Exception as e:
        return {
            "error": str(e)
        }
def browser_scroll(direction="down", amount=700):
    try:
        page = _get_page()

        amount = abs(int(amount))

        if direction.lower() == "up":
            amount = -amount

        page.mouse.wheel(0, amount)
        page.wait_for_timeout(500)

        return {
            "success": True,
            "direction": direction,
            "amount": abs(amount),
            "url": page.url
        }

    except Exception as e:
        return {"error": str(e)}    