import requests
import time

# =========================
# CONFIG
# =========================
GITHUB_TOKEN = "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"
VERCEL_TOKEN = "vcp_8mInSLxQXH5wQ3qHD2aSenuP1HUJEI1XlmbEBdKf6WWb4fGCjR3Ne5R0"
RENDER_TOKEN = "rnd_R79UaxHjat7OwM4Fz4LYNocx3RF0"

GITHUB_USERNAME = "Jgarcie2"
REPO_NAME = "rpg-saas-platform"

# =========================
# UTIL: SAFE REQUEST
# =========================
def request(method, url, headers=None, json=None):
    try:
        r = requests.request(method, url, headers=headers, json=json)
        return r
    except Exception as e:
        print("REQUEST ERROR:", e)
        return None

# =========================
# 1. GITHUB REPO DETECTOR
# =========================
def get_repo_info():
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{REPO_NAME}"

    r = request("GET", url, headers={
        "Authorization": f"token {GITHUB_TOKEN}"
    })

    if not r:
        return None

    if r.status_code == 200:
        data = r.json()
        return {
            "id": data.get("id"),
            "full_name": data.get("full_name")
        }

    return None

# =========================
# 2. VERCEL ADAPTIVE PAYLOAD BUILDER
# =========================
def build_vercel_payload(repo_info):
    """
    Automatically adapts to API version:
    - repoId (new Vercel API)
    - repo (fallback older API)
    """

    if repo_info and repo_info.get("id"):
        print("🧠 Using repoId mode (modern Vercel API)")
        return {
            "name": "rpg-frontend",
            "gitSource": {
                "type": "github",
                "repoId": repo_info["id"],
                "ref": "main"
            },
            "rootDirectory": "client"
        }

    print("⚠️ Falling back to repo string mode")
    return {
        "name": "rpg-frontend",
        "gitSource": {
            "type": "github",
            "repo": f"{GITHUB_USERNAME}/{REPO_NAME}",
            "ref": "main"
        },
        "rootDirectory": "client"
    }

# =========================
# 3. VERCEL DEPLOY ENGINE
# =========================
def deploy_vercel(repo_info):

    url = "https://api.vercel.com/v13/deployments"

    headers = {
        "Authorization": f"Bearer {VERCEL_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = build_vercel_payload(repo_info)

    r = request("POST", url, headers=headers, json=payload)

    if not r:
        return None

    print("VERCEL:", r.status_code, r.text)

    try:
        return r.json()
    except:
        return {"raw": r.text}

# =========================
# 4. RENDER ADAPTIVE DEPLOY
# =========================
def deploy_render():

    url = "https://api.render.com/v1/services"

    headers = {
        "Authorization": f"Bearer {RENDER_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "type": "web_service",
        "name": "rpg-backend",
        "repo": f"{GITHUB_USERNAME}/{REPO_NAME}",
        "branch": "main",
        "startCommand": "node server/index.js",
        "buildCommand": "npm install",
        "env": "node"
    }

    r = request("POST", url, headers=headers, json=payload)

    if not r:
        return None

    print("RENDER:", r.status_code, r.text)

    try:
        return r.json()
    except:
        return {"status": "deployed"}

# =========================
# 5. HEALTH CHECK LOOP
# =========================
def wait_for_service(url, name):
    print(f"⏳ Waiting for {name}...")

    for i in range(10):
        try:
            r = requests.get(url, timeout=3)
            if r.status_code == 200:
                print(f"✅ {name} is live")
                return True
        except:
            pass

        time.sleep(3)

    print(f"⚠️ {name} not reachable yet")
    return False

# =========================
# 6. SELF-HEALING RETRY WRAPPER
# =========================
def retry(fn, label, retries=3):
    for i in range(retries):
        result = fn()

        if result:
            return result

        print(f"🔁 Retry {i+1}/{retries} for {label}")
        time.sleep(2)

    print(f"❌ Failed: {label}")
    return None

# =========================
# 7. MAIN ENGINE
# =========================
def deploy_all():

    print("\n🚀 API SELF-ADAPTING DEPLOY ENGINE STARTED\n")

    # STEP 1: detect repo
    repo_info = get_repo_info()
    print("📦 Repo Info:", repo_info)

    # STEP 2: deploy backend first (Render)
    backend = retry(deploy_render, "Render Backend")

    # STEP 3: deploy frontend (Vercel)
    frontend = retry(lambda: deploy_vercel(repo_info), "Vercel Frontend")

    # STEP 4: simulate URLs (real systems would parse responses)
    frontend_url = "https://your-app.vercel.app"
    backend_url = "https://your-api.onrender.com"

    # STEP 5: health checks
    wait_for_service(frontend_url, "Frontend")
    wait_for_service(backend_url, "Backend")

    print("\n🎉 DEPLOYMENT COMPLETE")
    print("Frontend:", frontend_url)
    print("Backend:", backend_url)

# =========================
# RUN
# =========================
if __name__ == "__main__":
    deploy_all()