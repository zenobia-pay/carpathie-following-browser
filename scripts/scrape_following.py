#!/usr/bin/env python3
import json, subprocess, pathlib, datetime, os, traceback

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
ACCOUNTS = DATA / "accounts"
RAW.mkdir(parents=True, exist_ok=True)
ACCOUNTS.mkdir(parents=True, exist_ok=True)

TARGET_HANDLE = os.getenv("TARGET_HANDLE", "karpathy")  # from user request "Carpathie"
MAX_ACCOUNTS = int(os.getenv("MAX_ACCOUNTS", "150"))
JOURNAL_PATH = DATA / "journal.json"


def run(cmd):
    return subprocess.check_output(cmd, text=True)


def load_journal():
    if JOURNAL_PATH.exists():
        try:
            return json.loads(JOURNAL_PATH.read_text())
        except Exception:
            return []
    return []


def save_journal(entries):
    JOURNAL_PATH.write_text(json.dumps(entries, indent=2))


def append_journal(entry):
    j = load_journal()
    j.append(entry)
    save_journal(j)


def main():
    started = datetime.datetime.now(datetime.UTC).isoformat()
    journal_entry = {
        "startedAt": started,
        "targetHandle": TARGET_HANDLE,
        "mode": "following+bio+recent_tweets",
        "requestedMaxAccounts": MAX_ACCOUNTS,
        "status": "running"
    }

    try:
        latest = json.loads(run(["bird", "user-tweets", TARGET_HANDLE, "-n", "1", "--json"]))
        if not latest:
            raise RuntimeError("Could not resolve target handle")
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

        processed = 0
        errors = 0

        for i, u in enumerate(following, 1):
            if processed >= MAX_ACCOUNTS:
                break

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
                errors += 1

            (ACCOUNTS / f"{handle}.json").write_text(json.dumps(account, indent=2))
            manifest["accounts"].append({
                "username": handle,
                "file": f"accounts/{handle}.json",
                "tweetCount": len(account["tweets"]),
                "error": account.get("error")
            })

            processed += 1
            if i % 25 == 0:
                (DATA / "manifest.json").write_text(json.dumps(manifest, indent=2))

        (DATA / "manifest.json").write_text(json.dumps(manifest, indent=2))

        journal_entry.update({
            "finishedAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "status": "success",
            "targetUserId": user_id,
            "followingCount": len(following),
            "processedAccounts": processed,
            "errorAccounts": errors,
            "manifestPath": "data/manifest.json"
        })
        append_journal(journal_entry)

        print(f"Done. following={len(following)} processed={processed} errors={errors}")

    except Exception as e:
        journal_entry.update({
            "finishedAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "status": "failed",
            "error": str(e),
            "traceback": traceback.format_exc(limit=5)
        })
        append_journal(journal_entry)
        raise


if __name__ == "__main__":
    main()
