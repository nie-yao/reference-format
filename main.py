#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 27 19:15:23 2025

@author: ynie
"""

import re
import os


PROPER_NOUNS = {"Kalman", "Markov", "AUV", "AUVs", "GPS"}
ORG_NAMES = {"IEEE", "ACM", "CAA", "MIT"}
LOWER_WORDS = {"of", "in", "on", "for", "the", "a", "an", "and"}

def extract_bibitems_from_file(file_path):
    """
    从文件中提取所有的bibitem条目
    
    Args:
        filename (str): 文件路径
    
    Returns:
        list: 包含所有bibitem条目的字符串列表
    """
    try:
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        pattern = r'@((?:(?!@).)*)'
        items = re.findall(pattern, content, re.DOTALL)
        
        # 清理每个条目（去除多余的空白字符）
        cleaned_items = []
        for item in items:
            # 去除首尾空白并规范化内部空白
            cleaned_item = re.sub(r'\s+', ' ', item.strip())
            cleaned_items.append(cleaned_item)
        
        return cleaned_items
    
    except FileNotFoundError:
        print(f"错误：找不到文件 {file_path}")
        return []
    except Exception as e:
        print(f"读取文件时出错：{e}")
        return []


def parse_bibtex_entry(s):
    # 使用正则表达式匹配 entry 类型（如 article, book 等）和 label
    entry_match = re.search(r'@?([a-zA-Z]+)\{([^,]+),', s)
    if not entry_match:
        raise ValueError("Invalid BibTeX entry: expected '@entry{label,' format.")
    entry_type = entry_match.group(1).strip()
    label = entry_match.group(2).strip()

    # 使用正则表达式匹配所有键值对
    pattern = re.compile(r'(\w+)\s*=\s*\{((?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*)\}')
    matches = pattern.findall(s)

    # 构建结果字典
    result = {
        'type': entry_type,  # 新增 entry_type 字段（如 'article', 'book'）
        'label': label,
    }

    for key, value in matches:
        result[key.strip()] = value.strip()
        
    # 处理作者
    result['author'] = format_authors(result['author'])
    # 处理题目
    result['title'] = format_title(result['title'])
    # 处理期刊名
    if result['type'] == 'article':
        result['journal'] = format_journal(result['journal'])
    elif result['type'] == 'inproceedings':
        result['booktitle'] = format_journal(result['booktitle'])
    elif result['type'] == 'book':
        result['publisher'] = format_journal(result['publisher'])

    return result


def format_title(title):
    
    words = title.split()
    formatted_words = []
    
    for i, word in enumerate(words):
        # 检查是否是数学公式（如 $H_2$）
        if re.search(r'\$(?:[^$]|\{[^{}]+\})+\$', word):
            formatted_words.append(word)
            continue
        
        # 检查是否是专有名词
        if word in PROPER_NOUNS:
            formatted_words.append(word)
            continue
        
        # 处理第一个单词（首字母大写，其余小写）
        if i == 0:
            formatted_word = word[0].upper() + word[1:].lower()
        else:
            formatted_word = word.lower()
        
        formatted_words.append(formatted_word)
    
    return ' '.join(formatted_words)


def format_authors(author_str):
    # Step 1: 用 'and' 分割成多个作者
    authors = [a.strip() for a in author_str.split('and')]
    
    formatted_authors = []
    for author in authors:
        if author == 'others':
            formatted_authors.append('et al.')
            continue
            
        # Step 2: 用 ',' 分割姓和名
        parts = [p.strip() for p in author.split(',')]
        if not parts:
            continue
        
        # 姓（首字母大写，其余小写）
        last_name = parts[0]
        if last_name:
            last_name = last_name[0].upper() + last_name[1:].lower()
        
        # 名（缩写为首字母加 '.'）
        first_names = []
        for name in parts[1:]:
            first_names.append(name[0].upper() + '.')
        
        # 组合：名缩写~姓（如 T.~Ba{\c{s}}ar）
        formatted_name = '~'.join(first_names + [last_name])
        formatted_authors.append(formatted_name)
    
    # Step 3: 合并所有作者
    if not formatted_authors:
        return ""
    
    if len(formatted_authors) == 1:
        return formatted_authors[0]
    elif formatted_authors[-1] == 'et al.':
        return ', '.join(formatted_authors[:-1]) + ' ' + formatted_authors[-1]
    else:
        return ', '.join(formatted_authors[:-1]) + ', and ' + formatted_authors[-1]


def format_journal(str):
    
    words = str.split()
    formatted_words = []
    
    for word in words:
        # 检查是否是组织名
        if any(substring in word for substring in ORG_NAMES):
            formatted_words.append(word.upper())
            continue
        
        # arXiv
        if 'arxiv' in word.lower():
            formatted_word = re.sub(r"arxiv", "arXiv", word, flags=re.IGNORECASE)
            formatted_words.append(formatted_word)
            continue
        
        # 介词、冠词
        if word in LOWER_WORDS:
            formatted_words.append(word.lower())
            continue
        
        # 首字母大写，其余小写
        formatted_word = word[0].upper() + word[1:].lower()
        
        formatted_words.append(formatted_word)
    
    return ' '.join(formatted_words)


def process_single_bibitem(bibitem):
    """
    处理单个bibitem条目的函数（占位符）
    
    Args:
        bibitem (str): 单个bibitem条目字典
    
    Returns:
        str: 处理后的结果
    
    Note:
        这是一个占位符函数，具体的处理逻辑需要根据实际需求实现
        可能的处理包括：
        - 解析作者、标题、期刊等信息
        - 格式转换
        - 数据清理
        - 信息提取
        等等
    """
    
    # 字符串转为字典
    bibitem = parse_bibtex_entry(bibitem)
    
    bib_info = ''
    
    # 添加标签
    bib_info += '\\bibitem'
    bib_info += '{' + bibitem['label'] + '}'
    bib_info += '\n'
    
    # 添加作者
    bib_info += bibitem['author'] + ', '
    
    # 添加题目
    # bib_info += bibitem['title'] + ', '
    bib_info += '``' + bibitem['title'] + '," '
    
    # 添加刊名、会议名
    if bibitem['type'] == 'article':
        bib_info += '\\textit{' + bibitem['journal'] + '}'
    elif bibitem['type'] == 'inproceedings':
        bib_info += '\\textit{' + bibitem['booktitle'] + '}'
    elif bibitem['type'] == 'book':
        bib_info += '\\textit{' + bibitem['publisher'] + '}'
    bib_info += ', '
    
    #添加其他信息
    if "volume" in bibitem:
        bib_info += 'vol.~' + bibitem['volume'] + ', '
    if "number" in bibitem:
        bib_info += 'no.~' + bibitem['number'] + ', '
    if "pages" in bibitem:
        bib_info += 'pp.~' + bibitem['pages'] + ', '
    if "year" in bibitem:
        bib_info += bibitem['year'] + '.'
    
    return {'code': bib_info, 'meta': bibitem}


def sort_bibitems(bibitems_list):
    
    def extract_surname(author_str):
        """
        从作者字符串中提取姓氏
        
        参数:
        author_str -- 作者字符串，格式如 "Z.~Zhang" 或 "Zhang, Z."
        
        返回:
        姓氏字符串
        """
        # 处理空字符串
        if not author_str:
            return ""
        
        # 获取第一个作者（逗号分隔的第一个部分）
        if ',' in author_str:
            first_author = author_str.split(',')[0].strip()
        else:
            first_author = author_str.strip()
        
        # 提取姓氏（最后一个单词）
        parts = first_author.split('~')
        if not parts:
            return ""
        surname = parts[-1]
        
        # 移除可能的标点符号
        return surname.strip('.').strip()
    
    # 多级排序
    return sorted(
        bibitems_list,
        key=lambda x: (
            # 1. 按姓氏排序
            extract_surname(x.get('meta', {}).get('author', '')).lower(),
            # 2. 按出版年份排序（年份小的在前）
            int(x.get('meta', {}).get('year', 0))
        )
    )

    return bibitems_list


def remove_uncited(bibitems_list):
    # 读取论文内容
    with open('main.tex', 'r', encoding='utf-8') as file:
        content = file.read()
            
    for i, bibitem in enumerate(bibitems_list):
        label = bibitem['meta']['label']
        if label not in content:
            bibitems_list.pop(i)
    
    # title_groups = defaultdict(list)
    # for item in bibitems_list:
    #     title = item['meta']['title']
    #     title_groups[title].append(item)
    
    # # 找出所有有重复 title 的组
    # duplicates = {title: items for title, items in title_groups.items() if len(items) > 1}
    
    # print(duplicates)
    
    return bibitems_list
    

def remove_duplicates(bibitems_list):
    seen_titles = set()
    unique_list = []
    
    for item in bibitems_list:
        title = item.get('meta', {}).get('title')
        if title not in seen_titles:
            seen_titles.add(title)
            unique_list.append(item)
    
    return unique_list


def process_bibitems(bibitems_list):
    """
    批量处理bibitem条目列表
    
    Args:
        bibitems_list (list): 包含bibitem条目的字符串列表
    
    Returns:
        list: 处理后的结果列表
    """    
    processed_results = []
    
    print(f"开始处理 {len(bibitems_list)} 个bibitem条目...")
    
    for i, bibitem in enumerate(bibitems_list, 1):
        try:
            # 调用处理函数处理单个条目
            processed_result = process_single_bibitem(bibitem)
            processed_results.append(processed_result)
                
        except Exception as e:
            print(f"处理第 {i} 个条目时出错: {e}")
            # 可以选择跳过错误条目或添加错误标记
            processed_results.append(f"ERROR: {bibitem}")
    
    print(f"格式化完成。共处理 {len(processed_results)} 个条目。")
    
    processed_results = sort_bibitems(processed_results)
    print("排序完成。")
    
    processed_results = remove_uncited(processed_results)
    print(f"已删除未引用的条目！剩余 {len(processed_results)} 个条目。")

    processed_results = remove_duplicates(processed_results)
    print(f"已删除重复的条目！剩余 {len(processed_results)} 个条目。")
    
    return processed_results


if __name__ == "__main__":
    file_path = "ref.bib"
    bibitems = extract_bibitems_from_file(file_path)
    processed_results = process_bibitems(bibitems)
    
    name, ext = os.path.splitext(file_path)
    output_path = f"{name}_cleaned.txt"
    with open(output_path, 'w', encoding='utf-8') as f:
        # 写入文件头
        f.write("\\begin{thebibliography}{99}\n\n")
        
        # 写入列表条目，中间用空行隔开
        for item in processed_results:
            f.write(item['code'])
            f.write("\n\n")
        
        # 写入文件尾
        f.write("\\end{thebibliography}")
        
        