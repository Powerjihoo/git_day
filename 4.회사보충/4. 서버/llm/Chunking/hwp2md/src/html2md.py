from lxml import html, etree
import re
import pcre
import tomd
from util import logger
import fire


class html2md():
    def __init__(self, html_str):
        parser = html.HTMLParser()
        if html_str == '':  # 2023-06-22 empty html 에러 우회
            html_str = "<span></span>"
        html_str = html_str.replace('<br>','\n')
        self.make_md(html_str, parser)
        # self.make_md_without_figure(html_str, parser)

    def make_md(self, html_str, parser):
        try:
            bytes_data = html_str.encode('utf-8')
            self.tree = html.fromstring(bytes_data, parser=parser)
        except Exception as ex:
            logger.error(f'html_str: {html_str}')
            logger.error(f'Exception: {ex}')
            self.md = html_str
            return
        # 테이블 변환
        self.conv_table()
        # 마크다운 변환
        self.md = self.html2md().strip()
        
    def make_md_without_figure(self, html_str, parser):
        # 2023-06-23 Q&A chunk json 에서는 그림 제거
        self.tree = html.fromstring(html_str, parser=parser)
        # 그림 제거
        self.remove_formula()
        # 테이블 변환
        self.conv_table()
        # 그림 제거 마크다운 변환
        self.md_without_img = self.html2md()
    
    def remove_formula(self):
        for elem in self.tree.xpath('//img'):
            elem.getparent().remove(elem)


    def html2md(self):
        if self.tree == None:
            return ''
        html_str = html.tostring(self.tree, encoding='UTF-8').decode('UTF-8')
        logger.debug("HTML_STR " + html_str[0:10])
        md = tomd.Tomd(html_str).markdown
        logger.debug("MD " + md)

        md = md.replace('&lt;', '<')
        md = md.replace('&gt;', '>')
        # print(md)
        return md

    def conv_table(self):
        # table 태그 선택
        remove_elems = {}
        for elem in self.tree.iter():
            if elem.tag == 'table':
                table = elem
                remove_elems[table] = []

                # caption, header와 body 태그 선택
                captions = table.xpath('./caption')
                header = table.xpath('./thead/tr')
                body = table.xpath('./tbody/tr')
                body = header + body
                if(len(body) == 0):
                    body = table.xpath('./tr')

                # print(etree.tostring(table, pretty_print=True).decode('utf-8'))
                # print(table.tag)
                # print(dir(table))
                # print(table.text_content)
                # print(table.sourceline)
                # print(body)

                col_cnt = 0

                # body 내용 추출
                body_rows = []
                matrix = {}
                first_row_has_row_span = False
                for row_idx, row in enumerate(body):
                    col_cnt = 0
                    if row_idx not in matrix:
                        matrix[row_idx] = {}
                    for rel_col_idx, cell in enumerate(row.xpath('./td')):
                        row_span = 1
                        col_span = 1
                        col_idx = rel_col_idx
                        while col_idx in matrix[row_idx]:
                            col_idx += 1
                        if 'colspan' in cell.attrib.keys():
                            colspan_str = cell.attrib['colspan']
                            colspan_str = "".join([char for char in colspan_str if char.isdigit()])
                            if colspan_str is not None and colspan_str != '':
                                col_span = int(colspan_str)
                        if 'rowspan' in cell.attrib.keys():
                            rowspan_str = cell.attrib['rowspan'].replace('\'','').replace('"','')
                            rowspan_str = "".join([char for char in rowspan_str if char.isdigit()])
                            if rowspan_str is not None and rowspan_str != '':
                                row_span = int(rowspan_str)
                        if row_span > 1:
                            for span_idx in range(1, row_span):
                                if row_idx + span_idx not in matrix:
                                    matrix[row_idx + span_idx] = {}
                                matrix[row_idx + span_idx][col_idx] = '^'
                                if row_idx+span_idx == 1:
                                    first_row_has_row_span = True
                        elif col_span > 1:
                            for span_idx in range(1, col_span):
                                matrix[row_idx][col_idx + span_idx] = ''
                        # cell_value = "</br>".join([p.text_content().strip() for p in cell.xpath('./p')])
                        cell_value = cell.text_content()
                        logger.debug(html.tostring(cell))
                        for img in cell.xpath('.//img'):
                            # print(img)
                            cell_value += 'ㅤ' + html.tostring(img).decode()
                        if cell_value == '':  # 2023-06-22 내용이 빈 td 처리
                            cell_value = 'ㅤ'
                        matrix[row_idx][col_idx] = cell_value
                    matrix[row_idx] = dict(sorted(matrix[row_idx].items()))
                matrix = dict(sorted(matrix.items()))
                
                if len(matrix) > 0:
                    col_cnt = len(matrix[0])
                    body_rows = ['|' + '|'.join([cell for cell in row.values()]) + '|' for row in matrix.values()]

                    # # 마크다운 테이블 생성
                    markdown_table = '\n'.join(body_rows)

                    # # 출력
                    logger.debug("MARKDOWN TABLE START " + markdown_table)
                    logger.debug("MARKDOWN TABLE END")
                    # elem.text = markdown_table
                    table.tag = 'table'
                    for key in table.attrib.keys():
                        table.attrib.pop(key)

                    for child in table: # 2023-06-22 child elem 제거 부분 수정
                        remove_elems[table].append(child)

                    caption_rows = []

                    for caption in captions:  # 2023-06-21 header row에 caption 추가
                        caption_rows.append('|' + caption.text_content() + '|' * col_cnt)

                    logger.debug('first_row_has_row_span ' + str(first_row_has_row_span))
                    
                    if first_row_has_row_span and len(caption_rows) == 0:  # 2023-06-22 header row에서 row span 안되므로, 빈 줄 추가
                        caption_rows.append('| ' + '|' * col_cnt)
                    
                    logger.debug(caption_rows)
                    
                    rows = caption_rows + body_rows
                    
                    for idx, row in enumerate(rows):
                        row_elem = html.Element('tr')
                        row_elem.text = row
                        table.append(row_elem)
                        if idx == 0:
                            row_elem = html.Element('tr')
                            row_elem.text = ('|' + '---|' * col_cnt)
                            table.append(row_elem)
        
        for table in remove_elems:  # 2023-06-22 child elem 제거 부분 수정
            for elem in remove_elems[table]:
                table.remove(elem)

def main(html_file='MOA_MOB.html', md_file='MOA_MOB.md'):
    logger.info(f'html_file: {html_file}, md_file: {md_file}')
    with open(html_file) as fp:
        html_str = fp.read()

    with open(md_file, 'w') as fp:
        md_str = html2md(html_str).md
        fp.write(md_str)


if __name__ == '__main__':
    fire.Fire(main)