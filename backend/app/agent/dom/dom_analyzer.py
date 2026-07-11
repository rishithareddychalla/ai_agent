"""
DOM Analyzer – Intelligent element discovery without hardcoded selectors
"""

import asyncio
from typing import Optional, List, Tuple
from loguru import logger
from playwright.async_api import Page, ElementHandle, Locator


class SelectorCandidate:
    """A potential selector with a confidence score."""
    def __init__(self, selector: str, confidence: float, strategy: str):
        self.selector = selector
        self.confidence = confidence
        self.strategy = strategy
    
    def __repr__(self):
        return f"<SelectorCandidate selector='{self.selector}' confidence={self.confidence:.2f}>"


class DOMAnalyzer:
    """
    Intelligent DOM element discovery that does NOT rely on hardcoded selectors.
    
    Uses multiple strategies in order of confidence:
    1. ARIA label / accessible name
    2. Placeholder text
    3. Label text association
    4. Button/link visible text
    5. Role + name combination
    6. Data attributes
    7. CSS class heuristics
    8. Relative positioning to known anchors
    """

    async def find_element(
        self,
        page: Page,
        description: str,
        element_type: Optional[str] = None,
        timeout_ms: int = 5000,
    ) -> Optional[Locator]:
        """
        Find a page element using multiple strategies.
        
        Args:
            page: Playwright page
            description: Human-readable description (e.g., "search box", "submit button")
            element_type: Optional hint ('button', 'input', 'link', 'select', 'checkbox')
            timeout_ms: Timeout per strategy attempt
            
        Returns:
            Playwright Locator if found, None otherwise
        """
        candidates = await self._generate_candidates(page, description, element_type)
        
        for candidate in sorted(candidates, key=lambda c: c.confidence, reverse=True):
            try:
                locator = page.locator(candidate.selector).first
                # Check if element is visible within timeout
                await locator.wait_for(state="visible", timeout=min(timeout_ms, 3000))
                logger.debug(
                    f"Element found via '{candidate.strategy}': {candidate.selector}"
                )
                return locator
            except Exception:
                continue
        
        logger.warning(f"Could not find element matching: '{description}'")
        return None

    def _clean_description(self, description: str) -> str:
        """Clean command verbs and fillers from natural language element descriptions."""
        cleaned_desc = description.strip().rstrip(".!?;,").strip("'\"")
        
        # Remove common prefixes (case-insensitive)
        prefixes_to_remove = [
            "click the ", "click on the ", "click on ", "click ",
            "press the ", "press ", "tap the ", "tap on the ", "tap on ", "tap ",
            "type ", "enter ", "fill in ", "fill ", "select the ", "select ",
            "navigate to ", "go to ", "open the ", "open ",
            "the ", "a ", "an "
        ]
        
        prefixes_to_remove.sort(key=len, reverse=True)
        
        desc_lower = cleaned_desc.lower()
        for prefix in prefixes_to_remove:
            if desc_lower.startswith(prefix):
                cleaned_desc = cleaned_desc[len(prefix):]
                desc_lower = cleaned_desc.lower()
                cleaned_desc = cleaned_desc.strip("'\"")
                desc_lower = cleaned_desc.lower()
                
        # Remove common suffixes
        suffixes_to_remove = [
            " button", " link", " field", " input", " text box", " box", " dropdown", " text"
        ]
        suffixes_to_remove.sort(key=len, reverse=True)
        
        desc_lower = cleaned_desc.lower()
        for suffix in suffixes_to_remove:
            if desc_lower.endswith(suffix):
                cleaned_desc = cleaned_desc[:-len(suffix)]
                desc_lower = cleaned_desc.lower()
                cleaned_desc = cleaned_desc.strip("'\"")
                desc_lower = cleaned_desc.lower()
                
        # Clean leading/trailing articles again just in case
        desc_lower = cleaned_desc.lower()
        for art in ["the ", "a ", "an "]:
            if desc_lower.startswith(art):
                cleaned_desc = cleaned_desc[len(art):]
                break
                
        return cleaned_desc.strip().rstrip(".!?;,").strip("'\"")

    async def _generate_candidates(
        self,
        page: Page,
        description: str,
        element_type: Optional[str],
    ) -> List[SelectorCandidate]:
        """Generate a list of selector candidates for the description."""
        cleaned_description = self._clean_description(description)
        logger.debug(f"Generating candidates for: '{description}' (cleaned: '{cleaned_description}')")

        candidates = []
        desc_lower = cleaned_description.lower().strip()
        words = desc_lower.split()

        # Define CSS type restrictions to prevent matching incorrect tag types (e.g. an <a> tag matching input searches)
        prefix = ""
        if element_type == "input" or element_type == "search":
            prefix = ":is(input, textarea, [contenteditable], [role='textbox'])"
        elif element_type == "button":
            prefix = ":is(button, input[type='button'], input[type='submit'], [role='button'])"
        elif element_type == "link":
            prefix = ":is(a, [role='link'])"

        # ─── Strategy 1: ARIA label ──────────────────────────────
        candidates.append(SelectorCandidate(
            selector=f'{prefix}[aria-label*="{cleaned_description}" i]',
            confidence=0.95,
            strategy="aria-label",
        ))
        candidates.append(SelectorCandidate(
            selector=f'{prefix}[aria-labelledby*="{cleaned_description}" i]',
            confidence=0.90,
            strategy="aria-labelledby",
        ))

        # ─── Strategy 2: Placeholder text ────────────────────────
        candidates.append(SelectorCandidate(
            selector=f'{prefix}[placeholder*="{cleaned_description}" i]',
            confidence=0.88,
            strategy="placeholder",
        ))

        # ─── Strategy 2b: Label association ────────────────────────
        # Try to find labels that contain words from our description (e.g. "username")
        # and match them via 'for' attribute or nested inputs.
        for word in words:
            if len(word) > 2:
                try:
                    labels = await page.locator(f'label:has-text("{word}")').all()
                    for label in labels:
                        for_id = await label.get_attribute("for")
                        if for_id:
                            candidates.append(SelectorCandidate(
                                selector=f'{prefix}#{for_id}' if prefix else f'#{for_id}',
                                confidence=0.91,
                                strategy=f"label-association-{word}",
                            ))
                        # Check if the input is nested inside the label
                        nested_input = label.locator("input, textarea, [role='textbox']")
                        if await nested_input.count() > 0:
                            candidates.append(SelectorCandidate(
                                selector=f'label:has-text("{word}") :is(input, textarea, [role="textbox"])',
                                confidence=0.89,
                                strategy=f"nested-label-{word}",
                            ))
                except Exception as le:
                    logger.debug(f"Label matching failed for word '{word}': {le}")

        # ─── Strategy 3: Visible text (buttons/links) ───────────
        if element_type != "link":
            candidates.append(SelectorCandidate(
                selector=f'button:has-text("{cleaned_description}")',
                confidence=0.85,
                strategy="button-text",
            ))
        if element_type != "button" and element_type != "input" and element_type != "search":
            candidates.append(SelectorCandidate(
                selector=f'a:has-text("{cleaned_description}")',
                confidence=0.85,
                strategy="link-text",
            ))

        # ─── Strategy 4: Role-based selectors ────────────────────
        if element_type == "button":
            candidates.extend([
                SelectorCandidate(
                    selector=f'role=button[name="{cleaned_description}" i]',
                    confidence=0.92,
                    strategy="role-button",
                ),
                SelectorCandidate(
                    selector=f'input[type="submit"][value*="{cleaned_description}" i]',
                    confidence=0.80,
                    strategy="submit-input",
                ),
            ])
        elif element_type == "input" or element_type == "search":
            candidates.extend([
                SelectorCandidate(
                    selector='input[type="search"]',
                    confidence=0.82,
                    strategy="search-input-type",
                ),
                SelectorCandidate(
                    selector='input[name*="search" i]',
                    confidence=0.78,
                    strategy="search-name-attr",
                ),
                SelectorCandidate(
                    selector='input[name*="query" i]',
                    confidence=0.78,
                    strategy="query-name-attr",
                ),
                SelectorCandidate(
                    selector='input[name*="q" i]',
                    confidence=0.75,
                    strategy="q-name-attr",
                ),
            ])
        elif element_type == "link":
            candidates.append(SelectorCandidate(
                selector=f'role=link[name="{cleaned_description}" i]',
                confidence=0.90,
                strategy="role-link",
            ))

        # ─── Strategy 5: Data attributes ─────────────────────────
        candidates.extend([
            SelectorCandidate(
                selector=f'{prefix}[data-testid*="{desc_lower}" i]',
                confidence=0.87,
                strategy="data-testid",
            ),
            SelectorCandidate(
                selector=f'{prefix}[data-label*="{cleaned_description}" i]',
                confidence=0.85,
                strategy="data-label",
            ),
        ])

        # ─── Strategy 6: Name/id/class heuristics ────────────────
        for word in words[:3]:  # Use first 3 words
            candidates.extend([
                SelectorCandidate(
                    selector=f'{prefix}[name*="{word}" i]',
                    confidence=0.65,
                    strategy=f"name-{word}",
                ),
                SelectorCandidate(
                    selector=f'{prefix}[id*="{word}" i]',
                    confidence=0.65,
                    strategy=f"id-{word}",
                ),
            ])

        # ─── Strategy 7: Partial text matching ───────────────────
        for word in words[:2]:
            if len(word) > 3:  # Skip short words
                if element_type != "link":
                    candidates.append(SelectorCandidate(
                        selector=f'button:has-text("{word}")',
                        confidence=0.55,
                        strategy=f"partial-button-{word}",
                    ))
                if element_type != "button" and element_type != "input" and element_type != "search":
                    candidates.append(SelectorCandidate(
                        selector=f'a:has-text("{word}")',
                        confidence=0.55,
                        strategy=f"partial-link-{word}",
                    ))
                candidates.append(SelectorCandidate(
                    selector=f'{prefix}[aria-label*="{word}" i]',
                    confidence=0.60,
                    strategy=f"partial-aria-{word}",
                ))

        # ─── Strategy 8: Ordinal list matching ───────────────────
        # Check if description refers to a list item (e.g. "first product result", "2nd link")
        ordinal_map = {
            "first": 1, "1st": 1, "top": 1,
            "second": 2, "2nd": 2,
            "third": 3, "3rd": 3,
            "fourth": 4, "4th": 4,
            "fifth": 5, "5th": 5
        }
        
        has_ordinal = False
        target_index = 1
        for word, val in ordinal_map.items():
            if word in desc_lower:
                has_ordinal = True
                target_index = val
                break
                
        # If the description contains ordinal words OR generic product list nouns (like "product result")
        generic_list_nouns = ["product", "result", "item", "link", "card", "image"]
        has_generic_noun = any(noun in desc_lower for noun in generic_list_nouns)
        
        if has_ordinal or has_generic_noun:
            # We construct structural nth-match selectors
            base_selectors = [
                '[data-component-type="s-search-result"]',
                '.s-result-item',
                '.product-card',
                '.product-item',
                'div.g',
                '.product',
                '.item',
                '.card',
                'h2',
                'h3',
                'a'
            ]
            
            for base in base_selectors:
                if element_type == "link" or element_type == "button" or base in ["h2", "h3"]:
                    if base == 'a':
                        # If base is a link itself, select it directly
                        candidates.append(SelectorCandidate(
                            selector=f':nth-match(a, {target_index})',
                            confidence=0.40,
                            strategy=f"ordinal-direct-link-{target_index}",
                        ))
                    else:
                        candidates.append(SelectorCandidate(
                            selector=f':nth-match({base}, {target_index}) a',
                            confidence=0.70 if "product" in base or "result" in base else 0.50,
                            strategy=f"ordinal-card-link-{base}-{target_index}",
                        ))
                else:
                    candidates.append(SelectorCandidate(
                        selector=f':nth-match({base}, {target_index})',
                        confidence=0.55,
                        strategy=f"ordinal-card-{base}-{target_index}",
                    ))

        return candidates

    async def extract_page_data(
        self,
        page: Page,
        schema: Optional[dict] = None,
    ) -> dict:
        """
        Extract structured data from the current page.
        
        Args:
            page: Playwright page
            schema: Optional expected data structure (key: CSS selector)
            
        Returns:
            dict of extracted data
        """
        extracted = {}

        # Extract page metadata
        extracted["url"] = page.url
        extracted["title"] = await page.title()

        if schema:
            for key, selector in schema.items():
                try:
                    elements = await page.locator(selector).all()
                    texts = [await el.inner_text() for el in elements[:20]]
                    extracted[key] = texts if len(texts) > 1 else (texts[0] if texts else None)
                except Exception:
                    extracted[key] = None
        else:
            # Auto-extract common patterns
            extracted.update(await self._auto_extract(page))

        return extracted

    async def _auto_extract(self, page: Page) -> dict:
        """Auto-extract common data patterns from any page."""
        data = {}
        
        # Extract headings
        try:
            h1_elements = await page.locator("h1").all()
            data["headings_h1"] = [await h.inner_text() for h in h1_elements[:5]]
        except Exception:
            data["headings_h1"] = []

        # Extract all paragraph text (limited)
        try:
            paragraphs = await page.locator("p").all()
            data["paragraphs"] = [await p.inner_text() for p in paragraphs[:10] if await p.inner_text()]
        except Exception:
            data["paragraphs"] = []

        # Extract all links
        try:
            links = await page.locator("a[href]").all()
            link_data = []
            for link in links[:30]:
                try:
                    text = await link.inner_text()
                    href = await link.get_attribute("href")
                    if text and href:
                        link_data.append({"text": text.strip(), "href": href})
                except Exception:
                    pass
            data["links"] = link_data
        except Exception:
            data["links"] = []

        # Extract tables
        try:
            tables = await page.locator("table").all()
            table_data = []
            for table in tables[:3]:
                rows = await table.locator("tr").all()
                table_rows = []
                for row in rows[:20]:
                    cells = await row.locator("td, th").all()
                    row_data = [await cell.inner_text() for cell in cells]
                    if any(row_data):
                        table_rows.append(row_data)
                if table_rows:
                    table_data.append(table_rows)
            data["tables"] = table_data
        except Exception:
            data["tables"] = []

        # Extract meta description
        try:
            meta = await page.locator('meta[name="description"]').get_attribute("content")
            data["meta_description"] = meta
        except Exception:
            data["meta_description"] = None

        return data

    async def wait_for_navigation_complete(self, page: Page, timeout_ms: int = 15000):
        """Wait for the page to fully load after navigation."""
        try:
            await page.wait_for_load_state("networkidle", timeout=timeout_ms)
        except Exception:
            try:
                await page.wait_for_load_state("domcontentloaded", timeout=timeout_ms)
            except Exception:
                logger.warning("Page load timeout – continuing anyway")
