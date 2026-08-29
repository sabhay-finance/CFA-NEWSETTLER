# CFA SETTLER — Static Newspaper Generator

This is a free, automated news digest designed for CFA Level 1 Candidates. It fetches articles from 18 sources, extracts full text paragraphs, and generates a pure HTML file.

## 🚀 How to Publish to the Internet (100% Free)

You have all the files ready in this folder. To put it online, follow these steps:

### Step 1: Create a GitHub Repository

1. Go to [github.com/new](https://github.com/new)
2. Name it `cfa-settler` (or whatever you prefer).
3. Important: Check the box to make it **Public** (required for free GitHub Pages).
4. Click **Create repository**.

### Step 2: Upload This Folder

Upload **all** the files inside the folder you are currently looking at (`Desktop/cfa-github-ready`). 
*Make sure the `.github` folder gets uploaded properly (it might be hidden on Mac, if you upload via browser drag-and-drop).*

Or, run this in your Mac Terminal:
```bash
cd ~/Desktop/cfa-github-ready
git init
git add .
git commit -m "Initial setup"
git branch -M main
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

### Step 3: Grant GitHub Actions Write Access
GitHub needs permission to save the newly downloaded news back into your repository.
1. On your GitHub repo page, click **Settings** > **Actions** > **General**.
2. Scroll to the bottom to **Workflow permissions**.
3. Select **Read and write permissions**.
4. Click **Save**.

### Step 4: Turn on GitHub Pages
1. Go to **Settings** > **Pages** (on the left menu).
2. Under "Build and deployment", set the source to **Deploy from a branch**.
3. Under "Branch", select `main` and `/ (root)`.
4. Click **Save**.

### Step 5: Run it for the first time
1. Go to the **Actions** tab at the top of your GitHub repo.
2. Click **Update CFA Daily Digest** on the left.
3. Click the **Run workflow** dropdown, and click **Run workflow**.

Wait about 1-2 minutes for it to finish. Once it does, your live website will be available at:
👉 `https://YOUR_GITHUB_USERNAME.github.io/YOUR_REPO_NAME/`

*Note: It will automatically refresh in the background 3 times a day (7:00 AM, 1:00 PM, and 7:00 PM IST).*
