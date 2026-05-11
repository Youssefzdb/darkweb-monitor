#!/usr/bin/env python3
"""
Dark Web Monitor - Threat Intelligence Framework
Author: Youssef Zeidi | Red Team Specialist
"""

import argparse, requests, json, re, time
from datetime import datetime

PASTE_SITES = [
    "https://pastebin.com/api/api_post.php",
]

def banner():
    print("""
    ╔══════════════════════════════════════╗
    ║      Dark Web Monitor v1.0           ║
    ║      Threat Intelligence Framework   ║
    ╚══════════════════════════════════════╝
    """)

def check_tor():
    try:
        proxies = {"http": "socks5h://127.0.0.1:9050", "https": "socks5h://127.0.0.1:9050"}
        r = requests.get("http://check.torproject.org", proxies=proxies, timeout=10)
        if "Congratulations" in r.text:
            print("[+] Tor connection: ACTIVE")
            return True
    except:
        pass
    print("[!] Tor not running. Start with: tor &")
    return False

def search_leaks(keywords, use_tor=False):
    """Search HaveIBeenPwned and public breach databases"""
    results = []
    proxies = {"http": "socks5h://127.0.0.1:9050", "https": "socks5h://127.0.0.1:9050"} if use_tor else {}
    
    for keyword in keywords:
        print(f"[*] Checking: {keyword}")
        
        # Check HIBP for email
        if "@" in keyword:
            try:
                headers = {"hibp-api-key": "YOUR_HIBP_KEY", "User-Agent": "DarkWebMonitor"}
                r = requests.get(
                    f"https://haveibeenpwned.com/api/v3/breachedaccount/{keyword}",
                    headers=headers, proxies=proxies, timeout=10
                )
                if r.status_code == 200:
                    breaches = r.json()
                    print(f"  [!] {keyword} found in {len(breaches)} breaches!")
                    for b in breaches:
                        print(f"      - {b['Name']} ({b['BreachDate']})")
                    results.append({"keyword": keyword, "breaches": breaches})
                elif r.status_code == 404:
                    print(f"  [+] {keyword} not found in known breaches")
            except Exception as e:
                print(f"  [!] HIBP check failed: {e}")
        
        time.sleep(1.5)  # Rate limiting
    
    return results

def extract_iocs(text):
    """Extract IOCs from text"""
    iocs = {
        "ips": re.findall(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b", text),
        "domains": re.findall(r"\b[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b", text),
        "emails": re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text),
        "hashes_md5": re.findall(r"\b[a-fA-F0-9]{32}\b", text),
        "hashes_sha256": re.findall(r"\b[a-fA-F0-9]{64}\b", text),
        "btc_addresses": re.findall(r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b", text),
    }
    return {k: list(set(v)) for k, v in iocs.items() if v}

def save_report(results, output):
    report = {
        "timestamp": datetime.now().isoformat(),
        "results": results
    }
    with open(output, "w") as f:
        json.dump(report, f, indent=2)
    print(f"[+] Report saved: {output}")

def main():
    banner()
    parser = argparse.ArgumentParser()
    parser.add_argument("--keywords", required=True, help="Comma-separated keywords to monitor")
    parser.add_argument("--tor", action="store_true", help="Route through Tor")
    parser.add_argument("--output", default="monitor_report.json")
    args = parser.parse_args()

    keywords = [k.strip() for k in args.keywords.split(",")]
    
    if args.tor:
        check_tor()
    
    print(f"[*] Monitoring {len(keywords)} keywords...")
    results = search_leaks(keywords, args.tor)
    save_report(results, args.output)

if __name__ == "__main__":
    main()
