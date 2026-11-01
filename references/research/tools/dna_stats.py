# -*- coding: utf-8 -*-
"""
陈金龙表达 DNA 统计脚本（R3）
原则：所有正则显式写出；每条"零出现"结论必须再用宽口径复核（--wide）。
用法：
  python dna_stats.py            # 全样本 + 分体裁
  python dna_stats.py --wide     # 宽口径复核（列命中片段）
"""
import re, sys, os, json, statistics, itertools

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ART = os.path.join(BASE, 'sources', 'articles')

FILES = [
    ('A1', 'A1-dajiangshi-2021.txt', '学术论文'),
    ('A2', 'A2-kangzhan-minzu-2025.txt', '学术论文'),
    ('A3', 'A3-wenhuashi-30nian-2024.txt', '学术史综述'),
    ('A4', 'A4-jinian-leixing-2017.txt', '专著章节'),
    ('A5', 'A5-jinian-fangshi-2017.txt', '专著章节'),
    ('A6', 'A6-gmw-2022-dangshi.txt', '党报笔谈'),
    ('A7', 'A7-nanfang-interview-2024.txt', '访谈'),
    ('A8', 'A8-jindaishi-1996-fragment.txt', '碎片(1996)'),
]

# ---------- 句子切分 ----------
# 只在 。！？ 后切；吞掉紧跟的后引号/后括号，避免把引文内部的句号当断点
SENT_END = re.compile(r'[。！？]+[”』」）)]*')
HEAD = re.compile(r'^(?:[一二三四五六七八九十]+[、．.]|（[一二三四五六七八九十]+）|\d+[．.、])')


def paragraphs(t):
    return [p.strip() for p in t.split('\n') if p.strip()]


def sentences(t):
    out = []
    for p in paragraphs(t):
        # 小标题（无句末标点且短）单独成句，避免并入正文
        if len(p) < 40 and not SENT_END.search(p):
            out.append(p)
            continue
        pos = 0
        for m in SENT_END.finditer(p):
            s = p[pos:m.end()].strip()
            if s:
                out.append(s)
            pos = m.end()
        tail = p[pos:].strip()
        if tail:
            out.append(tail)
    return [s for s in out if len(s) >= 2]


def nchars(t):
    return len(re.sub(r'\s', '', t))


def per_k(n, total, k=1000):
    return round(k * n / total, 2) if total else 0.0


# ---------- 指标定义 ----------
PUNCT = {
    '逗号，': r'，',
    '句号。': r'。',
    '分号；': r'；',
    '顿号、': r'、',
    '冒号：': r'：',
    '前引号“': r'“',
    '后引号”': r'”',
    '单引号‘': r'‘',
    '括号（）': r'[（）()]',
    '破折号——': r'——',
    '问号？': r'[？?]',
    '感叹号！': r'[！!]',
    '省略号……': r'……',
}

STRUCT = {
    '首先': r'首先', '其次': r'其次', '再次': r'再次', '最后': r'最后',
    '第一': r'第一[，、,]', '第二': r'第二[，、,]', '第三': r'第三[，、,]',
    '一是': r'一是', '二是': r'二是', '三是': r'三是', '四是': r'四是',
    '总之': r'总之', '因此': r'因此', '但是': r'但是', '然而': r'然而',
    '不过': r'不过', '同时': r'同时', '另一方面': r'另一方面', '一方面': r'一方面',
    '也就是说': r'也就是说', '换言之': r'换言之', '事实上': r'事实上',
    '当然': r'当然', '只有': r'只有', '才能': r'才能', '必须': r'必须',
    '应当': r'应当', '需要': r'需要', '关键在于': r'关键在于',
    '本质上': r'本质上', '根本': r'根本', '归根到底': r'归根到底',
    '可见': r'可见', '可以说': r'可以说', '这表明': r'这表明',
}

# 对举句式：窄口径（不跨逗号）与宽口径（允许跨逗号，仅不跨句末）
DUIJIAO = {
    '不仅…而且(窄)': r'不仅[^，。；]{0,40}?而且',
    '不仅…而且(宽)': r'不仅[^。；]{0,40}?而且',
    '既…又(窄)': r'既[^，。；]{0,25}?又',
    '既…又(宽)': r'既[^。；]{0,25}?又',
    '不是…而是(窄)': r'不是[^，。；]{0,40}?而是',
    '不是…而是(宽)': r'不是[^。；]{0,40}?而是',
    '所谓': r'所谓',
    '既…也(宽)': r'既[^。；]{0,30}?也',
    '是…而不是(宽)': r'是[^。；]{0,30}?而不是',
    '不是…也不是': r'不是[^。；]{0,30}?也不是',
    '既…更': r'既[^。；]{0,25}?更',
    '一方面…另一方面': r'一方面[^。]{0,80}?另一方面',
}

VERBS = ['考察', '分析', '梳理', '厘清', '揭示', '阐明', '论证', '表明', '指出',
         '认为', '强调', '呈现', '蕴含', '彰显', '体现', '建构', '重构',
         # 追加（陈金龙高频嫌疑词）
         '诠释', '勾勒', '阐释', '界定', '回溯', '折射', '审视', '塑造', '生成']

SOURCE = {
    '档案': r'档案|全宗|案卷|馆藏',
    '报刊名': r'《[^》]{2,14}(?:日报|晚报|周报|报|周刊|月刊|杂志|评论)》',
    '回忆录': r'回忆录|回忆',
    '年谱': r'年谱',
    '文集/文献': r'文集|文选|文献选编|文件选集|重要文献',
    '马恩列': r'马克思|恩格斯|列宁|斯大林',
    '毛邓江胡习': r'毛泽东|邓小平|江泽民|胡锦涛|习近平',
    '引语引导词(指出/认为/强调/提出/说)': r'(?:指出|认为|强调|提出|说)[：:]?[“]',
}

QUESTION = {
    '问号': r'[？?]',
    '反问标记': r'难道|岂不|岂能|何尝|不正是|怎能|何以',
    '设问标记': r'何以|为何|如何|是什么|为什么',
}

TIME = {
    '四位年份': r'\d{4}年',
    '年代': r'\d{2}年代',
    '月份': r'\d{1,2}月',
    '任意数字串': r'\d+',
    '第X次/届': r'第[一二三四五六七八九十百零\d]+[次届]',
}

QUOTE = re.compile(r'“([^”]{0,300})”')


def count(t, pat):
    return len(re.findall(pat, t))


def analyze(t):
    n = nchars(t)
    ss = sentences(t)
    L = [nchars(s) for s in ss]
    r = {}
    r['字数'] = n
    r['句数'] = len(ss)
    r['平均句长'] = round(sum(L) / len(L), 1) if L else 0
    r['中位句长'] = round(statistics.median(L), 1) if L else 0
    r['最长句'] = max(L) if L else 0
    r['最短句'] = min(L) if L else 0
    for th, key in ((100, '>100字句占比'), (150, '>150字句占比')):
        r[key] = round(100 * sum(1 for x in L if x > th) / len(L), 1) if L else 0
    r['<30字句占比'] = round(100 * sum(1 for x in L if x < 30) / len(L), 1) if L else 0
    # 分句（逗号链）长度：字数 / (逗号数 + 句数)
    ncomma = t.count('，')
    r['平均分句长'] = round(n / (ncomma + len(ss)), 1) if ss else 0
    r['最长句原文'] = ss[L.index(max(L))][:300] if L else ''

    for k, p in PUNCT.items():
        r['标点·' + k] = count(t, p)
    for k, p in PUNCT.items():
        r['密度·' + k] = per_k(count(t, p), n)
    for k, p in STRUCT.items():
        r['词·' + k] = count(t, p)
    for k, p in DUIJIAO.items():
        r['对举·' + k] = count(t, p)
    for v in VERBS:
        r['动·' + v] = count(t, v)
    for k, p in SOURCE.items():
        r['料·' + k] = count(t, p)
    for k, p in QUESTION.items():
        r['问·' + k] = count(t, p)
    for k, p in TIME.items():
        r['时·' + k] = count(t, p)
    for k, p in TIME.items():
        r['时密·' + k] = per_k(count(t, p), n)

    # 引号内容长度分档
    qs = QUOTE.findall(t)
    r['引号对'] = len(qs)
    r['引号内1字'] = sum(1 for q in qs if len(q) == 1)
    r['引号内2-4字'] = sum(1 for q in qs if 2 <= len(q) <= 4)
    r['引号内5-14字'] = sum(1 for q in qs if 5 <= len(q) <= 14)
    r['引号内≥15字(整句引文)'] = sum(1 for q in qs if len(q) >= 15)
    r['整句引文密度/千字'] = per_k(r['引号内≥15字(整句引文)'], n)
    r['引号均长'] = round(sum(len(q) for q in qs) / len(qs), 1) if qs else 0
    return r, ss, qs


def wide_check(t):
    """宽口径复核：对每个窄口径句式再放宽一次，并抽样展示命中片段"""
    print('\n########## 宽口径复核 ##########')
    pats = {
        '不仅…而且(超宽,不跨句末,允许80字)': r'不仅[^。；]{0,80}?而且',
        '既…又(超宽,80字)': r'既[^。；]{0,80}?又',
        '不是…而是(超宽,80字)': r'不是[^。；]{0,80}?而是',
        '不仅(单用)': r'不仅',
        '既(单用)': r'既(?!然)',
        '而是(单用)': r'而是',
    }
    for k, p in pats.items():
        ms = [m.group(0) for m in re.finditer(p, t)]
        print(f'{k}: {len(ms)} 次')
        for m in ms[:6]:
            print('    ▸', m[:90])


if __name__ == '__main__':
    rows = []
    for tag, fn, genre in FILES:
        p = os.path.join(ART, fn)
        if not os.path.exists(p):
            print('缺文件', fn); continue
        t = open(p, encoding='utf-8').read()
        r, ss, qs = analyze(t)
        r['tag'], r['体裁'] = tag, genre
        rows.append(r)
        if '--wide' in sys.argv:
            print(f'\n===== {tag} {fn} ({genre}) =====')
            wide_check(t)
        if '--quotes' in sys.argv:
            print(f'\n===== {tag} 引号内容抽样 =====')
            for q in qs[:25]:
                print('  “%s”' % q[:80])

    keys = ['tag', '体裁', '字数', '句数', '平均句长', '中位句长', '最长句', '最短句',
            '>100字句占比', '>150字句占比', '<30字句占比', '平均分句长']
    print('\t'.join(keys))
    for r in rows:
        print('\t'.join(str(r.get(k, '')) for k in keys))

    # 全指标明细
    allkeys = [k for k in rows[0] if k not in ('最长句原文',)]
    print('\n\n########## 明细（全指标） ##########')
    for k in allkeys:
        print(k, '\t', '\t'.join(str(r.get(k, '')) for r in rows))

    # 分体裁聚合
    print('\n\n########## 分体裁聚合 ##########')
    byg = {}
    for r in rows:
        byg.setdefault(r['体裁'], []).append(r)
    agg_keys = ['字数', '平均句长', '中位句长', '>100字句占比', '>150字句占比', '<30字句占比', '平均分句长']
    print('体裁\t样本数\t' + '\t'.join(agg_keys))
    for g, rs in byg.items():
        tot = sum(x['字数'] for x in rs)
        vals = []
        for k in agg_keys:
            if k == '字数':
                vals.append(tot)
            else:
                vals.append(round(sum(x[k] * x['字数'] for x in rs) / tot, 1))
        print(f'{g}\t{len(rs)}\t' + '\t'.join(map(str, vals)))

    json.dump(rows, open(os.path.join(BASE, 'research', 'tools', 'stats.json'), 'w',
                         encoding='utf-8'), ensure_ascii=False, indent=1)
