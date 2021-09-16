# -*- coding:utf-8 -*-
#拆分左右结构的汉字，还未实现，命令行执行文件传参还没实现
import pypinyin
import time
import math
from Pinyin2Hanzi import DefaultDagParams
from Pinyin2Hanzi import dag
import filecmp 
time1 = time.time()

# DFA算法
class DFAFilter(object):
    def __init__(self):
        self.keyword_chains = {}  # 关键词链表
        self.delimit = '\x00'  # 限定
        
    def sums(self,index):
        summ=0;
        for i in range(1,index+1):
            summ=summ+int(math.pow(3,i))
        return summ
      
    def add(self, keyword , real_word):
        keyword = keyword.lower()  # 关键词英文变为小写
        chars = keyword.strip()    # 关键字去除首尾空格和换行
        if not chars:              # 如果关键词为空直接返回
            return
        level = self.keyword_chains
                                   # 遍历关键字的每个字
        for i in range(len(chars)):
                                   # 如果这个字已经存在字符链的key中就进入其子字典
            if chars[i] in level:
                level = level[chars[i]]
            else:
                if not isinstance(level, dict):#如果level不是字典跳出for循环
                    break
                for j in range(i, len(chars)):
                    level[chars[j]] = {}
                    last_level, last_char = level, chars[j]
                    level = level[chars[j]]
                last_level[last_char] = {self.delimit: real_word}
                break
        if i == len(chars) - 1:
            level[self.delimit] =real_word
            
    def parse(self, path):     
        with open(path, encoding='utf-8') as f:
            for keyword in f:#添加关键词入字典链，关键词去除首尾的符号
                keyword=keyword.strip()
                if '\u4e00' <= keyword <= '\u9fa5':
                    lens=len(keyword)
                    ls=[]
                    for i in range(0,lens):
                        if i==0:
                            ls.append(keyword[i])
                            ls.append(str(pinyin(keyword[i])))
                            ls.append(str(pinyin(keyword[i]))[0])
                        elif i==1:
                            for j in range(0,3):
                                char=ls[j]
                                char=char+keyword[i]
                                ls.append(char)

                                char=ls[j]
                                char=char+str(pinyin(keyword[i]))
                                ls.append(char)

                                char=ls[j]
                                char=char+str(pinyin(keyword[i]))[0]
                                ls.append(char)  
                        else:
                            lb=self.sums(i-1)
                            rb=lb+int(math.pow(3,i))
                            for j in range(lb,rb):
                                char=ls[j]
                                char=char+keyword[i]
                                ls.append(char)

                                char=ls[j]
                                char=char+str(pinyin(keyword[i]))
                                ls.append(char)

                                char=ls[j]
                                char=char+str(pinyin(keyword[i]))[0]
                                ls.append(char)
                    lb=self.sums(lens-1)
                    rb=lb+int(math.pow(3,lens))                             
                    for i in range(lb,rb):
                        self.add(str(ls[i]).strip(),keyword)#一个参数是真实的敏感词
                else:
                    self.add(str(keyword).strip(),keyword) #00000
 
    def filter(self, text, repl="*"):
        whole_text=text.read()
        text.seek(0)
        #whole_text=text.read().lower() #此处补充一个全文行数的计算函数
        level=self.keyword_chains
        start=0   #检索文本的索引
        ret=[]    #检测结果的内容列表
        lines=1  #总行数
        exlis="1234567890"
        posi=[]#每行尾巴的下标
        line=text.readline()
        posi.append(len(line)-1)
        
        while start < len(whole_text):
            level = self.keyword_chains
            step_ins = 0 #敏感词的长度
            rl_word="" #真正的敏感词
            fk_word="" #伪装的敏感词
            flag=0     #是否有出现中文
            fnum=0     #是否出现数字
            interval=[]#敏感词每个字出现在文本中的位置
            index=start
            first=0
            while(start>posi[-1]):
                line=text.readline()
                if not line:
                    break
                posi.append(posi[-1]+len(line))
                lines=lines+1
                #line=line.lower()
            for char in whole_text[start:]:
                
                if char in level or char.lower() in level:#涵盖中文的拼音，汉字，首写字母，左右结构拆分，以及正常的英文敏感词
                    if len(interval)>0 and index-interval[-1]>20:
                          break
                    first=1
                    real_char=char
                    if char.lower() in level:
                        real_char=char.lower()
                    
                    interval.append(index)
                    if '\u4e00' <=char<= '\u9fa5':
                        flag=1                        
                    step_ins += 1
                    #rl_word=rl_word+char
                    fk_word=fk_word+char
                    if self.delimit not in level[real_char]:
                        level = level[real_char]
                    else:
                        level=level[real_char]
                        if len(level[self.delimit])!=0 and '\u4e00' <= level[self.delimit]<= '\u9fa5':#说明该词属于中文敏感词，又已知中文敏感词不可以插入数字
                            if fnum==1:
                                  break
                        rl_word=level[self.delimit]
                        s=""
                        s="Line"+str(lines)+": <"+rl_word+"> "+fk_word
                        ret.append(s)
                        start += step_ins - 1
                        break
                elif '\u4e00' <=char<= '\u9fa5':#同音字，繁体字的出现
                    #d=self.keyword_chains
                    py_char=pinyin(char)
                    exist=0  #是否是同音字或是繁体字
                    rl_char=""#检测字符对应在敏感词库中的同音字或是繁体字
                    for i in level.keys():
                        if py_char==pinyin(i):
                            rl_char=i
                            exist=1
                            break
                    if exist==1:
                        first=1
                        flag=1
                        if len(interval)>0 and index-interval[-1]>20:
                            break
                        interval.append(index)
                        step_ins += 1
                        rl_word=rl_word+rl_char
                        fk_word=fk_word+char
                        
                        if self.delimit not in level[rl_char]:
                            level = level[rl_char]
                        else:
                            level=level[rl_char]
                            rl_word=level[self.delimit]
                            s=""
                            s='Line'+('%s'%lines)+': <'+str(rl_word)+'> '+str(fk_word)
                            ret.append(s)
                            start += step_ins - 1
                            break
                    else:
                        break
                else:
                    if first==0:#说明是第一个
                        break
                    else:
                        if char=='\n'or '\u4e00' <=char<= '\u9fa5' or 'a'<=char.lower()<='z'or (flag==1 and char in exlis):
                            break
                        else:
                            if '0'<=char<='9':
                                fnum=1
                            fk_word=fk_word+char
                            step_ins += 1
                index=index+1
            start += 1
        ret.insert(0,"Total: "+str(len(ret)))
        return '\n'.join(ret)
        

def pinyin(word):
  s=""
  for i in pypinyin.pinyin(word, style=pypinyin.NORMAL):
        s+=' '.join(i)
  return s


if __name__ == "__main__":
    gfw = DFAFilter()
    path = "C://Users//duan//Desktop//words.txt"
    gfw.parse(path)
    
    text=open("C://Users//duan//Desktop//org.txt", "r", encoding="utf-8")
    #text=open("C://Users//duan//Desktop//org.txt", "r", encoding="utf-8").readlines()

    result = gfw.filter(text)
    text2=open("C://Users//duan//Desktop//00.txt", "w", encoding="utf-8").write(result)
    ans=open("C://Users//duan//Desktop//ans.txt", "r", encoding="utf-8")
    #print(filecmp.cmp(r'C://Users//duan//Desktop//ans.txt',r'C://Users//duan//Desktop//00.txt'))
    print(result)
    
    time2 = time.time()
    print('总共耗时：' + str(time2 - time1) + 's')


