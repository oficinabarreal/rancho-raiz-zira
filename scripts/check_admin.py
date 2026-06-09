#!/usr/bin/env python3
import re
import urllib.request
url = "https://oficinabarreal.github.io/rancho-raiz-zira/admin/"
with urllib.request.urlopen(url) as f:
    html = f.read().decode()
match = re.search(r'<script>(.*?)</script>', html, re.DOTALL)
if match:
    js = match.group(1)
    ld_start = js.find('function loadData')
    if ld_start >= 0:
        print(js[ld_start:ld_start+1500])
    else:
        print("loadData not found")
        init_start = js.rfind('function init')
        if init_start >= 0:
            print(js[init_start:init_start+500])
        else:
            print("init not found")
        # print last 200 chars
        print("LAST 300:", js[-300:])
else:
    print("NO SCRIPT TAG FOUND")
    print(html[:500])
