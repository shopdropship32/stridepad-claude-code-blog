#!/usr/bin/env python3
"""
Daily SEO-optimized blog post generator for a fitness e-commerce store.

Uses Claude API to generate Gen-Z-toned blog posts, fetches live products
from the Shopify Storefront API, and publishes via a Make.com webhook.
"""

import json
import os
import random
import sys
from datetime import datetime

import anthropic
import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"].strip()
MAKE_WEBHOOK_URL = os.environ["MAKE_WEBHOOK_URL"].strip()
SHOPIFY_BLOG_ID = os.environ["SHOPIFY_BLOG_ID"].strip()

# Optional – set these to enable live product fetching from Shopify
SHOPIFY_STORE_DOMAIN = (os.environ.get("SHOPIFY_STORE_DOMAIN") or "").strip() or None
SHOPIFY_STOREFRONT_TOKEN = (os.environ.get("SHOPIFY_STOREFRONT_TOKEN") or "").strip() or None

BLOG_AUTHOR = os.environ.get("BLOG_AUTHOR", "StridePad").strip()
DISCOUNT_CODE = "GETMOVING20"

# Fallback / default product catalog (used when Storefront API is unavailable)
DEFAULT_PRODUCTS = [
    {"title": "Fitness Tracker Watch", "price": "$59.95"},
    {"title": "HD Smartwatch", "price": "$69.95"},
    {"title": "Plantar Fasciitis Foot Roller", "price": "$39.95"},
    {"title": "Shiatsu Foot Massager (Premium)", "price": "$79.95"},
    {"title": "Shiatsu Foot Massager (Compact)", "price": "$36.67"},
    {"title": "Portable Walking Pad", "price": "$299.99"},
    {"title": "BPA-Free Water Bottle", "price": "$29.95"},
    {"title": "CamelBak Water Bottle", "price": "$49.95"},
    {"title": "Magnetic Gym Bag", "price": "$59.95"},
    {"title": "Yoga Foam Roller", "price": "from $3.23"},
    {"title": "Smart Neck Massager", "price": "from $15.22"},
    {"title": "Silicone Massage Cone", "price": "$10.54"},
]


# ---------------------------------------------------------------------------
# Shopify Storefront API – live product fetching
# ---------------------------------------------------------------------------
STOREFRONT_QUERY = """
{
  products(first: 50) {
    edges {
      node {
        title
        description
        priceRange {
          minVariantPrice {
            amount
            currencyCode
          }
          maxVariantPrice {
            amount
            currencyCode
          }
        }
        productType
        tags
        onlineStoreUrl
        images(first: 1) {
          edges {
            node {
              url
              altText
            }
          }
        }
      }
    }
  }
}
"""


def fetch_shopify_products() -> list[dict]:
    """Fetch products from the Shopify Storefront API.

    Returns a list of product dicts with 'title' and 'price' keys.
    Falls back to DEFAULT_PRODUCTS if the API is not configured or fails.
    """
    if not SHOPIFY_STORE_DOMAIN or not SHOPIFY_STOREFRONT_TOKEN:
        print("Shopify Storefront API not configured – using default catalog.")
        return DEFAULT_PRODUCTS

    url = f"https://{SHOPIFY_STORE_DOMAIN}/api/2024-01/graphql.json"
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Storefront-Access-Token": SHOPIFY_STOREFRONT_TOKEN,
    }

    try:
        resp = requests.post(url, json={"query": STOREFRONT_QUERY}, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        products = []
        for edge in data["data"]["products"]["edges"]:
            node = edge["node"]
            min_price = float(node["priceRange"]["minVariantPrice"]["amount"])
            max_price = float(node["priceRange"]["maxVariantPrice"]["amount"])

            if min_price == max_price:
                price_str = f"${min_price:.2f}"
            else:
                price_str = f"from ${min_price:.2f}"

            # Extract first product image if available
            image_url = ""
            image_alt = ""
            images = node.get("images", {}).get("edges", [])
            if images:
                image_node = images[0]["node"]
                image_url = image_node.get("url", "")
                image_alt = image_node.get("altText", "") or node["title"]

            products.append({
                "title": node["title"],
                "price": price_str,
                "description": node.get("description", ""),
                "product_type": node.get("productType", ""),
                "tags": node.get("tags", []),
                "url": node.get("onlineStoreUrl", ""),
                "image_url": image_url,
                "image_alt": image_alt,
            })

        if not products:
            print("Storefront API returned no products – using default catalog.")
            return DEFAULT_PRODUCTS

        print(f"Fetched {len(products)} products from Shopify Storefront API.")
        return products

    except Exception as exc:
        print(f"Storefront API error: {exc} – using default catalog.")
        return DEFAULT_PRODUCTS


# ---------------------------------------------------------------------------
# Blog topic generation
# ---------------------------------------------------------------------------
BLOG_TOPICS = [
    "morning workout routines for busy people",
    "how to stay hydrated during workouts",
    "best recovery tools after leg day",
    "walking pad workouts you can do while WFH",
    "gym bag essentials every fitness girlie needs",
    "foam rolling benefits most people don't know about",
    "foot care tips for runners and gym goers",
    "smartwatch features that actually help your fitness",
    "desk-to-gym transition tips for 9-to-5 workers",
    "self-care recovery routine after intense training",
    "how to build a home gym on a budget",
    "neck and shoulder tension relief for lifters",
    "beginner fitness mistakes and how to avoid them",
    "the science behind active recovery days",
    "hydration hacks that level up your performance",
    "why tracking your steps actually matters",
    "yoga and stretching routines for gym bros",
    "how to stay consistent with your fitness goals",
    "weekend warrior workout plans",
    "travel-friendly fitness gear you actually need",
    "mindful movement and why Gen Z is into it",
    "post-workout foot massage benefits",
    "how to pick the right fitness tracker for your goals",
    "sustainable fitness habits that stick",
    "the ultimate gym starter pack",
]


def pick_topic() -> str:
    """Pick a topic, incorporating the day-of-year for variety."""
    day_of_year = datetime.now().timetuple().tm_yday
    idx = day_of_year % len(BLOG_TOPICS)
    return BLOG_TOPICS[idx]


def pick_products(products: list[dict], count: int = 3) -> list[dict]:
    """Randomly pick 1-3 products to feature."""
    count = min(count, len(products))
    n = random.randint(1, count)
    return random.sample(products, n)


# ---------------------------------------------------------------------------
# Claude API – blog generation
# ---------------------------------------------------------------------------
def generate_blog_post(topic: str, featured_products: list[dict]) -> dict:
    """Use Claude to generate a full SEO-optimized blog post.

    Returns a dict with keys: title, body_html, tags, meta_description.
    """
    product_lines = []
    for p in featured_products:
        line = f"  - {p['title']} ({p['price']})"
        if p.get("image_url"):
            line += f"\n    Image URL: {p['image_url']}"
            line += f"\n    Image Alt: {p.get('image_alt', p['title'])}"
        if p.get("url"):
            line += f"\n    Product URL: {p['url']}"
        product_lines.append(line)
    product_lines = "\n".join(product_lines)

    prompt = f"""You are a content writer for a trendy online fitness store targeting young
fitness enthusiasts aged 18-30. Write in a fun, relatable Gen-Z tone — use casual
language, slang where appropriate, and keep it energetic and motivating. Avoid being
cringe or trying too hard.

TODAY'S TOPIC: {topic}

PRODUCTS TO PROMOTE (weave these in naturally — don't force them):
{product_lines}

DISCOUNT CODE: {DISCOUNT_CODE} (20% off — mention it once in the post, make it feel
like an insider tip, not a hard sell)

REQUIREMENTS:
1. Write an SEO-optimized blog post (800-1200 words).
2. The title should be catchy, include a relevant keyword, and be under 70 characters.
3. Use H2 and H3 subheadings to break up the content.
4. Include a compelling meta description (under 160 characters) with a primary keyword.
5. Suggest 5-8 relevant tags (comma-separated).
6. Format the body as clean HTML (use <h2>, <h3>, <p>, <strong>, <ul>/<li> tags).
7. Naturally mention the featured products with their prices in the body.
8. Include the discount code {DISCOUNT_CODE} once in a natural, non-pushy way.
9. End with a short call-to-action.
10. For each product that has an Image URL, embed the image in the blog using an <img> tag
    near where you mention the product. Use this format:
    <img src="IMAGE_URL" alt="IMAGE_ALT" style="max-width:100%;border-radius:12px;margin:16px 0;" />
    If a Product URL is provided, wrap the image in a link: <a href="PRODUCT_URL"><img ... /></a>
    Place images naturally within the content — after introducing the product or in a dedicated
    product highlight section. Do NOT group all images at the top or bottom.

Respond ONLY with valid JSON in this exact format (no markdown fences):
{{
  "title": "Your Blog Post Title Here",
  "body_html": "<h2>...</h2><p>...</p>...",
  "tags": "tag1, tag2, tag3, tag4, tag5",
  "meta_description": "Your meta description here under 160 chars."
}}"""

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()

    # Parse the JSON response
    try:
        post = json.loads(raw)
    except json.JSONDecodeError:
        # Try to extract JSON if wrapped in markdown fences
        if "```" in raw:
            json_str = raw.split("```")[1]
            if json_str.startswith("json"):
                json_str = json_str[4:]
            post = json.loads(json_str.strip())
        else:
            raise

    # Validate required keys
    for key in ("title", "body_html", "tags", "meta_description"):
        if key not in post:
            raise ValueError(f"Missing required key in response: {key}")

    return post


# ---------------------------------------------------------------------------
# Publish via Make.com webhook
# ---------------------------------------------------------------------------
def publish_to_shopify(post: dict) -> None:
    """Send the blog post to Shopify via the Make.com webhook."""
    payload = {
        "title": post["title"],
        "body_html": post["body_html"],
        "tags": post["tags"],
        "meta_description": post["meta_description"],
        "blog_id": SHOPIFY_BLOG_ID,
        "author": BLOG_AUTHOR,
    }

    resp = requests.post(MAKE_WEBHOOK_URL, json=payload, timeout=30)
    resp.raise_for_status()
    print(f"Published to Shopify via Make.com (status {resp.status_code}).")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print(f"--- Blog Generator | {datetime.now().strftime('%Y-%m-%d %H:%M')} ---")

    # 1. Fetch products (live from Shopify or fallback)
    products = fetch_shopify_products()

    # 2. Pick topic and products
    topic = pick_topic()
    featured = pick_products(products)
    print(f"Topic: {topic}")
    print(f"Featuring: {', '.join(p['title'] for p in featured)}")

    # 3. Generate blog post via Claude
    print("Generating blog post with Claude...")
    post = generate_blog_post(topic, featured)
    print(f"Title: {post['title']}")
    print(f"Tags: {post['tags']}")
    print(f"Meta: {post['meta_description']}")

    # 4. Publish
    print("Publishing to Shopify via Make.com webhook...")
    publish_to_shopify(post)

    print("Done!")


if __name__ == "__main__":
    main()
