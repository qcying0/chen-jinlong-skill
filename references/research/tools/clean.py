# -*- coding: utf-8 -*-
"""按起止标记切出正文，另存为 A-*.txt（保留原文，不改字）"""
import re, os

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ART = os.path.join(BASE, 'sources', 'articles')

JOBS = [
    # (源文件, 输出名, 起始串, 结束串[不含])
    ('raw_dajiang.txt', 'A1-dajiangshi-2021.txt',
     '大历史观作为一种诠释历史的视野和方法', '勾勒中国共产党历史发展的脉络。'),
    ('tmp_d8bb79.txt', 'A2-kangzhan-minzu-2025.txt',
     '以史为鉴，方知兴替', '[责任编辑：张尧]'),
    ('tmp_648fe4.txt', 'A3-wenhuashi-30nian-2024.txt',
     '《当代中国史研究》创刊以来的30年', '［作者简介］'),
    ('qq7.txt', 'A4-jinian-leixing-2017.txt',
     '中国共产党举行的纪念活动，既有对国际共运', '中国共产党民主思想发展历程'),
    ('qq8.txt', 'A5-jinian-fangshi-2017.txt',
     '纪念活动的开展需要借助具体形式', '中国共产党安康历史'),
    ('gmw2022.txt', 'A6-gmw-2022-dangshi.txt',
     '中共党史学科建设以中共党史研究为基础', '22 /mpproperty'),
    ('tmp_c7ebbc.txt', 'A7-nanfang-interview-2024.txt',
     '治学经历：自1987年研究生毕业', '字号：小中大'),
    ('krzz1996.txt', 'A8-jindaishi-1996-fragment.txt',
     '"半殖民地半封建"是一个用来概括中国近代社会性质', '民国地方史的开创之作'),
]

for src, dst, s, e in JOBS:
    t = open(os.path.join(ART, src), encoding='utf-8').read()
    i = t.find(s)
    if i < 0:
        print('!! 起始串未命中', src, s)
        continue
    j = t.find(e, i + len(s)) if e else -1
    body = t[i: j if j > 0 else len(t)]
    body = re.sub(r'\n{2,}', '\n', body).strip()
    open(os.path.join(ART, dst), 'w', encoding='utf-8').write(body + '\n')
    print(dst, len(re.sub(r'\s', '', body)))
