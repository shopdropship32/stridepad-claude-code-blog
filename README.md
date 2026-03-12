# Stridepad Blog Generator

Automated daily SEO-optimized blog post generator for the Stridepad fitness store. Uses Claude AI to write Gen-Z-toned content targeting young fitness enthusiasts (18-30), then publishes to Shopify via a Make.com webhook.

## How it works

1. **Fetches products** from the Shopify Storefront API (falls back to a built-in catalog if not configured).
2. **Picks a topic** from a rotating list and selects 1-3 products to feature.
3. **Generates a blog post** via the Claude API — SEO-optimized with HTML formatting.
4. **Publishes to Shopify** by sending JSON to a Make.com webhook.

A GitHub Actions workflow runs this automatically every day at 8 AM UTC.

## Setup

### 1. Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/stridepad-claude-code-blog.git
cd stridepad-claude-code-blog
pip install -r requirements.txt
```

### 2. Environment variables

Create a `.env` file (or export these in your shell):

```bash
export ANTHROPIC_API_KEY="your-anthropic-api-key"
export MAKE_WEBHOOK_URL="https://hook.us1.make.com/your-webhook-id"
export SHOPIFY_BLOG_ID="your-blog-id"

# Optional – enable live product fetching
export SHOPIFY_STORE_DOMAIN="your-store.myshopify.com"
export SHOPIFY_STOREFRONT_TOKEN="your-storefront-access-token"
```

### 3. Run locally

```bash
python generate_blog.py
```

### 4. GitHub Actions (daily automation)

Add these as **repository secrets** in GitHub (Settings → Secrets and variables → Actions):

| Secret | Description |
|--------|-------------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
| `MAKE_WEBHOOK_URL` | Your Make.com webhook URL |
| `SHOPIFY_BLOG_ID` | Your Shopify blog ID |
| `SHOPIFY_STORE_DOMAIN` | *(Optional)* Your Shopify store domain |
| `SHOPIFY_STOREFRONT_TOKEN` | *(Optional)* Your Storefront API access token |

The workflow runs daily at 8 AM UTC and can also be triggered manually from the Actions tab.

### 5. Shopify Storefront API (optional)

To enable automatic product fetching:

1. In your Shopify admin, go to **Settings → Apps and sales channels → Develop apps**.
2. Create a new app and enable the **Storefront API** with `unauthenticated_read_product_listings` scope.
3. Copy the Storefront access token and your store domain into the environment variables above.

When configured, the script automatically picks up any new products you add to your store.

## Project structure

```
├── generate_blog.py            # Main script
├── requirements.txt            # Python dependencies
├── .github/workflows/
│   └── daily-blog.yml          # GitHub Actions workflow
├── .gitignore
└── README.md
```
