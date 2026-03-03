#!/usr/bin/env python3
import json, subprocess, pathlib, datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
ACCOUNTS = DATA / "accounts"
RAW.mkdir(parents=True, exist_ok=True)
ACCOUNTS.mkdir(parents=True, exist_ok=True)

TARGET_HANDLE = "karpathy"  # interpreted from user request "Carpathie"

def run(cmd):
    return subprocess.check_output(cmd, text=True)

# resolve user id from latest tweet metadata
latest = json.loads(run(["bird", "user-tweets", TARGET_HANDLE, "-n", "1", "--json"]))
if not latest:
    raise SystemExit("Could not resolve target handle")
user_id = latest[0].get("authorId")

following_resp = json.loads(run(["bird", "following", "--user", user_id, "--all", "--json"]))
(RAW / "following.json").write_text(json.dumps(following_resp, indent=2))
following = following_resp.get("users", following_resp if isinstance(following_resp, list) else [])

manifest = {
    "targetHandle": TARGET_HANDLE,
    "targetUserId": user_id,
    "generatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
    "totalFollowing": len(following),
    "accounts": []
}

for i, u in enumerate(following, 1):
    handle = (u.get("username") or "").strip()
    if not handle:
        continue
    account = {
        "username": handle,
        "name": u.get("name", ""),
        "bio": u.get("description", ""),
        "followersCount": u.get("followersCount"),
        "followingCount": u.get("followingCount"),
        "profileUrl": f"https://x.com/{handle}",
        "tweets": []
    }
    try:
        tweets = json.loads(run(["bird", "user-tweets", handle, "-n", "10", "--json"]))
        for t in tweets:
            tid = t.get("id")
            if not tid:
                continue
            account["tweets"].append({
                "id": tid,
                "url": f"https://x.com/{handle}/status/{tid}",
                "createdAt": t.get("createdAt"),
                "text": t.get("text", ""),
                "likeCount": t.get("likeCount", 0),
                "retweetCount": t.get("retweetCount", 0),
                "replyCount": t.get("replyCount", 0)
            })
    except Exception as e:
        account["error"] = str(e)

    (ACCOUNTS / f"{handle}.json").write_text(json.dumps(account, indent=2))
    manifest["accounts"].append({
        "username": handle,
        "file": f"accounts/{handle}.json",
        "tweetCount": len(account["tweets"]),
        "error": account.get("error")
    })

    if i % 25 == 0:
        (DATA / "manifest.json").write_text(json.dumps(manifest, indent=2))

(DATA / "manifest.json").write_text(json.dumps(manifest, indent=2))
print(f"Done. following={len(following)} accounts saved")
