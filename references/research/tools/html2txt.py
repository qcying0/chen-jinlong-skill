# -*- coding: utf-8 -*-
"""HTML -> 纯文本抽取（去脚本/样式/标签，保留段落）"""
import re, sys, html

def to_text(path):
    raw = open(path, 'rb').read()
    for enc in ('utf-8', 'gb18030', 'utf-16'):
        try:
            s = raw.decode(enc)
            if s.count('\ufffd') > len(s) * 0.001:
                continue
            break
        except Exception:
            continue
    s = re.sub(r'(?is)<(script|style|noscript).*?</\1>', '', s)
    s = re.sub(r'(?i)<br\s*/?>', '\n', s)
    s = re.sub(r'(?i)</(p|div|h1|h2|h3|h4|li|tr|td|section|article)>', '\n', s)
    s = re.sub(r'(?s)<[^>]+>', '', s)
    s = html.unescape(s)
    s = s.replace('\u3000', ' ')
    lines = [re.sub(r'[ \t]+', ' ', ln).strip() for ln in s.split('\n')]
    lines = [ln for ln in lines if ln]
    return '\n'.join(lines)

if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    open(dst, 'w', encoding='utf-8').write(to_text(src))
    print(dst, len(open(dst, encoding='utf-8').read()))
