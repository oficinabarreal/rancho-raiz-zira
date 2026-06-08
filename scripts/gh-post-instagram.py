#!/usr/bin/env python3
"""
gh-post-instagram.py — Publica banners Zira a Instagram desde GitHub Actions.
Usa la Instagram Graph API con token de negocio.
"""
import json, os, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
os.chdir(HERE)

INSTAGRAM_TOKEN = os.environ.get("CRM_INSTAGRAM_TOKEN", "")
INSTAGRAM_USER_ID = os.environ.get("CRM_INSTAGRAM_USER_ID", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

BANNERS_DIR = HERE / "assets" / "zira" / "banners"

def get_latest_banner():
    """Find the most recent SVG banner."""
    svgs = sorted(BANNERS_DIR.glob("zira-diario-*.svg"))
    return svgs[-1] if svgs else None


def convert_svg_to_png(svg_path):
    """Convert SVG to PNG for Instagram (needs Chromium)."""
    png_path = svg_path.with_suffix(".png")
    
    # Try Chromium headless
    import subprocess
    chrome_paths = [
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
    ]
    chrome = None
    for p in chrome_paths:
        if os.path.exists(p):
            chrome = p
            break
    
    if chrome:
        subprocess.run([
            chrome, "--headless", "--no-sandbox", "--disable-gpu",
            f"--screenshot={png_path}",
            f"--window-size=1080,1080",
            f"file://{svg_path.resolve()}"
        ], check=True, timeout=30, capture_output=True)
        if png_path.exists():
            return png_path
    return None


def post_to_instagram(image_path, caption):
    """Post image to Instagram via Graph API."""
    import requests
    
    # Step 1: Create media container
    url = f"https://graph.facebook.com/v22.0/{INSTAGRAM_USER_ID}/media"
    files = {"image": open(image_path, "rb")}
    data = {
        "access_token": INSTAGRAM_TOKEN,
        "caption": caption,
    }
    
    resp = requests.post(url, files=files, data=data, timeout=30)
    result = resp.json()
    
    if "id" not in result:
        print(f"❌ Instagram error: {result}")
        return False
    
    creation_id = result["id"]
    print(f"   Media created: {creation_id}")
    
    # Step 2: Publish
    pub_url = f"https://graph.facebook.com/v22.0/{INSTAGRAM_USER_ID}/media_publish"
    pub_data = {"access_token": INSTAGRAM_TOKEN, "creation_id": creation_id}
    pub_resp = requests.post(pub_url, data=pub_data, timeout=30)
    pub_result = pub_resp.json()
    
    if "id" in pub_result:
        print(f"✅ Published to Instagram! ID: {pub_result['id']}")
        return True
    else:
        print(f"❌ Publish error: {pub_result}")
        return False


def main():
    print("📸 Zira Instagram Poster (GitHub Actions)")
    print("=" * 50)
    
    if not INSTAGRAM_TOKEN or not INSTAGRAM_USER_ID:
        print("❌ Instagram token/ID not configured")
        print("   Set CRM_INSTAGRAM_TOKEN and CRM_INSTAGRAM_USER_ID secrets")
        sys.exit(0)  # Not fatal
    
    banner = get_latest_banner()
    if not banner:
        print("❌ No banners found in assets/zira/banners/")
        sys.exit(0)
    
    print(f"📄 Latest banner: {banner.name}")
    
    # Convert to PNG
    png = convert_svg_to_png(banner)
    if not png:
        print("⚠️  Could not convert SVG to PNG (Chromium not available)")
        print("   Posting SVG directly not supported by Instagram API")
        sys.exit(0)
    
    print(f"🖼️  Converted to PNG: {png.name}")
    
    # Caption
    caption = "🏔️ Buenos días desde la cordillera. Zira les saluda.\n\n#RanchoRaíz #Barreal #SanJuan #Andes #Zira #PosadaDeMontaña"
    
    # Post
    success = post_to_instagram(png, caption)
    if success:
        print("🎉 Posted successfully!")


if __name__ == "__main__":
    main()
