#!/usr/bin/env python3

import requests
import argparse
import sys
import time
import json
from urllib.parse import urlparse
from datetime import datetime
import re
import socket

# terminal colors cause i hate plain text
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
WHITE = '\033[97m'
BOLD = '\033[1m'
END = '\033[0m'
GRAY = '\033[90m'

def show_banner():
    banner = f"""
{CYAN}{BOLD}
██╗   ██╗██████╗ ██╗         ██████╗ ███████╗███████╗██╗     ███████╗██████╗ 
██║   ██║██╔══██╗██║         ██╔══██╗██╔════╝██╔════╝██║     ██╔════╝██╔══██╗
██║   ██║██████╔╝██║   █████╗██████╔╝█████╗  █████╗  ██║     █████╗  ██████╔╝
██║   ██║██╔══██╗██║   ╚════╝██╔═══╝ ██╔══╝  ██╔══╝  ██║     ██╔══╝  ██╔══██╗
╚██████╔╝██║  ██║███████╗    ██║     ███████╗███████╗███████╗███████╗██║  ██║
 ╚═════╝ ╚═╝  ╚═╝╚══════╝    ╚═╝     ╚══════╝╚══════╝╚══════╝╚══════╝╚═╝  ╚═╝
{END}
{YELLOW}                    peel back the layers of any URL{END}
{GRAY}                            mason j. hawkins{END}
"""
    print(banner)

def loading_dots(text, seconds=1.5):
    # this animation is kinda useless but looks cool
    spinner = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    end_time = time.time() + seconds
    i = 0
    while time.time() < end_time:
        print(f"\r{CYAN}{spinner[i % len(spinner)]}{END} {text}", end="", flush=True)
        time.sleep(0.08)
        i += 1
    print(f"\r{GREEN}✓{END} {text}")

class URLPeeler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        self.shorteners = [
            'bit.ly', 'tinyurl.com', 't.co', 'goo.gl', 'ow.ly', 'short.link',
            'rb.gy', 'is.gd', 'buff.ly', 'tiny.cc', 'cutt.ly', 'rebrand.ly',
            'clck.ru', 'short.io', 'smarturl.it', 'linktr.ee', 'soo.gd', 'v.gd',
            'adfoc.us', 'adf.ly', 'adfly.com', 'q.gs', 'j.gs', 'u.to',
            'bc.vc', 'adfoc.us', 'oke.io', 'exe.io', 'links-url.com',
            'shrinkearn.com', 'shrinkme.io', 'ouo.io', 'ouo.press'
        ]
        
        self.ip_loggers = [
            'grabify.link', 'iplogger.org', 'iplogger.com', 'iplogger.ru',
            'yip.su', 'blasze.tk', 'ps3cfw.com', 'bmwforum.co', 'minecraft-forum.net',
            'xbox360iso.com', 'free-avast.com', 'fuglekos.com', 'quickmessage.io',
            'stopify.co', 'bmwforum.co', 'leancoding.co', 'spottyfly.com',
            'urlz.fr', 'iplis.ru', 'iplogger.co', 'skypegrab.net', 'youporn.com',
            'leancoding.co', 'spottyfly.com', '2no.co', 'ipgrabber.ru',
            'whatstheirip.com', 'ipgrab.net'
        ]
        
        self.bad_tlds = ['.tk', '.ml', '.ga', '.cf', '.click', '.download', '.loan', '.top', '.work']
        self.sus_words = [
            'download', 'exe', 'zip', 'rar', 'scam', 'free', 'win', 'prize',
            'urgent', 'suspended', 'verify', 'confirm', 'update', 'security',
            'bitcoin', 'crypto', 'investment', 'doubled', 'logger', 'grabber',
            'tracker', 'ip-', 'track', 'discord', 'steam', 'account', 'login',
            'hack', 'cheat', 'crack', 'keygen', 'torrent', 'porn'
        ]
    
    def get_ip(self, domain):
        try:
            return socket.gethostbyname(domain)
        except:
            return "couldn't resolve"
    
    def check_threats(self, original, final):
        threats = []
        risk = 0
        
        parsed_original = urlparse(original)
        parsed_final = urlparse(final)
        orig_domain = parsed_original.netloc.lower()
        final_domain = parsed_final.netloc.lower()
        path = parsed_final.path.lower() + parsed_final.query.lower()
        
        for logger in self.ip_loggers:
            if logger in orig_domain or logger in final_domain:
                threats.append(f"IP LOGGER DETECTED: {logger}")
                risk += 10  # max risk
                break
        
        if any(ad in orig_domain for ad in ['adfoc.us', 'adf.ly', 'adfly']):
            threats.append("adfocus link detected - often hides malicious content")
            risk += 6
        
        for tld in self.bad_tlds:
            if tld in final_domain:
                threats.append(f"suspicious tld: {tld}")
                risk += 3
                break
        
        found_words = []
        for word in self.sus_words:
            if word in final.lower():
                found_words.append(word)
        
        if found_words:
            threats.append(f"suspicious keywords: {', '.join(found_words[:3])}")
            risk += len(found_words)
        
        file_extensions = ['.exe', '.zip', '.rar', '.dmg', '.apk', '.msi', '.deb']
        for ext in file_extensions:
            if ext in path:
                threats.append(f"direct file download: {ext}")
                risk += 4
                break
        
        if re.match(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', final_domain):
            threats.append("using raw ip address")
            risk += 3
        
        # brand impersonation check
        brands = ['paypal', 'amazon', 'google', 'microsoft', 'apple', 'netflix', 'spotify']
        for brand in brands:
            if brand in final_domain and not final_domain.endswith(f'{brand}.com'):
                threats.append(f"possible {brand} impersonation")
                risk += 5
                break
        
        if any(param in parsed_final.query.lower() for param in ['track', 'utm_', 'click', 'ref=']):
            if 'track' in parsed_final.query.lower():
                threats.append("tracking parameters detected")
                risk += 2
        
        if any(ad in orig_domain for ad in ['adfoc.us', 'adf.ly', 'ouo.io', 'bc.vc']):
            if orig_domain != final_domain:
                threats.append("ad service redirect - destination unknown until clicked")
                risk += 4
        
        return threats, risk
    
    def is_shortener(self, url):
        domain = urlparse(url).netloc.lower()
        return (any(short in domain for short in self.shorteners) or 
                any(logger in domain for logger in self.ip_loggers))
    
    def peel_url(self, url):
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        loading_dots("checking url structure...")
        
        try:
            start = time.time()
            response = self.session.head(url, allow_redirects=True, timeout=12)
            response_time = round((time.time() - start) * 1000)
            
            final_url = response.url
            redirects = []
            
            if hasattr(response, 'history'):
                redirects = [r.url for r in response.history]
                redirects.append(final_url)
            
            loading_dots("analyzing for threats...")
            
            # security check
            threats, risk_score = self.check_threats(url, final_url)
            
            # get ip
            parsed_final = urlparse(final_url)
            ip = self.get_ip(parsed_final.netloc)
            
            loading_dots("generating report...")
            
            # figure out risk level (more aggressive scoring)
            if risk_score >= 10:
                risk_level = "CRITICAL"
                risk_color = RED
            elif risk_score >= 6:
                risk_level = "HIGH"
                risk_color = RED
            elif risk_score >= 3:
                risk_level = "MEDIUM" 
                risk_color = YELLOW
            else:
                risk_level = "LOW"
                risk_color = GREEN
            
            return {
                'original': url,
                'final': final_url,
                'redirects': redirects,
                'status': response.status_code,
                'response_time': response_time,
                'is_shortened': self.is_shortener(url),
                'redirect_count': len(redirects) - 1 if redirects else 0,
                'ip': ip,
                'threats': threats,
                'risk_score': risk_score,
                'risk_level': risk_level,
                'risk_color': risk_color,
                'safe': response.status_code == 200 and risk_score < 6,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'server': response.headers.get('Server', 'unknown'),
                'content_type': response.headers.get('Content-Type', 'unknown')
            }
            
        except Exception as e:
            return {
                'original': url,
                'error': str(e),
                'safe': False,
                'risk_level': 'ERROR',
                'risk_score': 0,
                'risk_color': RED,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

def show_results(result):
    if 'error' in result:
        print(f"\n{RED}{'='*70}{END}")
        print(f"{RED}{BOLD}   ANALYSIS FAILED{END}")
        print(f"{RED}{'='*70}{END}")
        print(f"{RED}error: {result['error']}{END}")
        return
    
    # main header
    print(f"\n{CYAN}{'='*70}{END}")
    print(f"{CYAN}{BOLD}   URL ANALYSIS REPORT{END}")
    print(f"{CYAN}{'='*70}{END}")
    
    # basic info
    print(f"\n{BOLD}basic info{END}")
    print(f"{GRAY}original:{END} {WHITE}{result['original']}{END}")
    print(f"{GRAY}final:{END}    {WHITE}{result['final']}{END}")
    print(f"{GRAY}status:{END}   {GREEN if result['status'] == 200 else RED}{result['status']}{END}")
    print(f"{GRAY}time:{END}     {YELLOW}{result['response_time']}ms{END}")
    
    if result['ip'] != "couldn't resolve":
        print(f"{GRAY}ip:{END}       {BLUE}{result['ip']}{END}")
    
    # security stuff
    print(f"\n{BOLD}security{END}")
    risk_color = result['risk_color']
    print(f"{GRAY}risk:{END}     {risk_color}{BOLD}{result['risk_level']}{END} ({result['risk_score']}/10)")
    print(f"{GRAY}shortened:{END} {YELLOW if result['is_shortened'] else GREEN}{'yes' if result['is_shortened'] else 'no'}{END}")
    print(f"{GRAY}redirects:{END} {YELLOW if result['redirect_count'] > 2 else GREEN}{result['redirect_count']}{END}")
    
    # threats
    if result['threats']:
        print(f"\n{BOLD}threats found{END}")
        for i, threat in enumerate(result['threats'], 1):
            if "IP LOGGER" in threat.upper():
                print(f"{RED}   !!! CRITICAL: {threat} !!!{END}")
            else:
                print(f"{RED}   • {threat}{END}")
    else:
        print(f"\n{GREEN}no obvious threats{END}")
    
    # tech details  
    print(f"\n{BOLD}technical{END}")
    print(f"{GRAY}server:{END}   {WHITE}{result['server']}{END}")
    print(f"{GRAY}type:{END}     {WHITE}{result['content_type'][:40]}{'...' if len(result['content_type']) > 40 else ''}{END}")
    
    # redirect chain
    if result['redirect_count'] > 0:
        print(f"\n{BOLD}redirect chain{END}")
        for i, url in enumerate(result['redirects']):
            color = YELLOW if i < len(result['redirects']) - 1 else GREEN
            print(f"{GRAY}   {i+1}.{END} {color}{url}{END}")
    
    # verdict
    print(f"\n{BOLD}verdict{END}")
    if result['risk_level'] == 'CRITICAL':
        print(f"{RED}{BOLD}   !!! EXTREMELY DANGEROUS - DO NOT CLICK !!!{END}")
    elif result['safe']:
        print(f"{GREEN}{BOLD}   probably safe{END}")
    else:
        print(f"{RED}{BOLD}   looks sketchy - be careful{END}")
    
    print(f"\n{GRAY}analyzed: {result['timestamp']}{END}")
    print(f"{CYAN}{'='*70}{END}")

def get_url_input():
    """Get URL from user input if not provided as argument"""
    while True:
        try:
            url = input(f"{YELLOW}enter url to analyze: {WHITE}")
            if url.strip():
                return url.strip()
            print(f"{RED}please enter a valid url{END}")
        except KeyboardInterrupt:
            print(f"\n{YELLOW}cancelled by user{END}")
            return None

def main():
    parser = argparse.ArgumentParser(description="URL-PEELER - analyze urls", add_help=False)
    parser.add_argument('url', nargs='?', help="url to analyze")
    parser.add_argument('-j', '--json', action='store_true', help="json output")
    parser.add_argument('-o', '--output', help="save to file")
    parser.add_argument('--no-banner', action='store_true', help="skip banner")
    parser.add_argument('-h', '--help', action='store_true', help="show help")
    
    try:
        args = parser.parse_args()
    except:
        args = argparse.Namespace(url=None, json=False, output=None, no_banner=False, help=False)
    
    if args.help:
        print("URL-PEELER - peel back url layers")
        print("usage: python url_peeler.py [url] [options]")
        print("\noptions:")
        print("  -j, --json     output as json")
        print("  -o FILE        save results to file") 
        print("  --no-banner    skip the banner")
        print("  -h, --help     show this help")
        return
    
    if not args.no_banner:
        show_banner()
    
    # get url from args or user input
    url = args.url
    if not url:
        url = get_url_input()
        if not url:
            return
    
    print(f"\n{YELLOW}target: {WHITE}{url}{END}")
    print(f"{GRAY}starting analysis...{END}\n")
    
    peeler = URLPeeler()
    result = peeler.peel_url(url)
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        show_results(result)
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n{GREEN}saved to {args.output}{END}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}stopped by user{END}")
    except Exception as e:
        print(f"\n{RED}something broke: {e}{END}")
