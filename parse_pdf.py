"""Worker script: downloads one Nadex PDF and prints the bracketing strikes as JSON.

Usage: python parse_pdf.py <url> <market_open>

Stdout: JSON with keys 'above' and 'below' (nullable), or 'miss'/'error' keys.
Called by getNadexContracts.ipynb — do not run directly.
"""
import io
import json
import re
import socket
import sys

import pypdfium2 as pdfium
import requests

socket.setdefaulttimeout(15)  # covers SSL handshake, which requests timeout= misses

PRODUCT_FILTER = "US 500"
EXPIRY_FILTER  = "4:15PM"
TYPE_FILTER    = "Binary Daily"   # exclude Weekly binary and Spread/Knock-Out contracts
_STRIKE_RE = re.compile(r'US 500[^>+\d]*[>+]([\d]{4,5}(?:\.\d+)?)')


def main():
    url = sys.argv[1]
    market_open = float(sys.argv[2])

    print('DEBUG:downloading', file=sys.stderr, flush=True)
    try:
        resp = requests.get(url, timeout=(10, 30))
    except requests.RequestException as e:
        print(json.dumps({'error': str(e)}))
        return

    print(f'DEBUG:downloaded status={resp.status_code} bytes={len(resp.content)}', file=sys.stderr, flush=True)

    if resp.status_code != 200:
        print(json.dumps({'miss': True}))
        return

    print('DEBUG:parsing', file=sys.stderr, flush=True)
    strikes = []
    pdf = pdfium.PdfDocument(resp.content)
    for i in range(len(pdf)):
        page = pdf[i]
        textpage = page.get_textpage()
        text = textpage.get_text_range()
        textpage.close()
        page.close()
        for line in text.splitlines():
            if PRODUCT_FILTER not in line or EXPIRY_FILTER not in line or TYPE_FILTER not in line:
                continue
            m = _STRIKE_RE.search(line)
            if m:
                strikes.append(float(m.group(1)))
    pdf.close()

    if not strikes:
        print(json.dumps({'above': None, 'below': None}))
        return

    strikes = sorted(set(strikes))
    belows = [s for s in strikes if s <= market_open]
    aboves = [s for s in strikes if s > market_open]

    print(json.dumps({
        'above': min(aboves) if aboves else None,
        'below': max(belows) if belows else None,
    }))


if __name__ == '__main__':
    main()
