# -*- coding:utf-8 -*-
import sys
import pypinyin
import time

#------DFA算法
class DFAFilter(object):
    #------初始化
    def __init__(self):         
        self.keyword_chains = {}  # 关键词链表
        self.delimit = '\x00'  # 限定
        
    #------将变形组合的敏感词加入敏感词链      
    def add(self, keyword , real_word):
        keyword = keyword.lower()  # 敏感词英文变为小写
        chars = keyword.strip()    # 敏感词去除首尾空格和换行
        if not chars:              # 如果敏感词为空直接返回
            return
        level = self.keyword_chains
                                   # 遍历敏感字的每个字
        for i in range(len(chars)):
                                   # 如果这个敏感词已经存在字符链的key中就进入其子字典
            if chars[i] in level:
                level = level[chars[i]]
            else:
                if not isinstance(level, dict): #如果level不是字典跳出for循环
                    break
                for j in range(i, len(chars)):
                    level[chars[j]] = {}
                    last_level, last_char = level, chars[j]
                    level = level[chars[j]]
                last_level[last_char] = {self.delimit: real_word}
                break
        if i == len(chars) - 1:
            level[self.delimit] =real_word
            
    #--------对原敏感词的变形组合：ex:法--fa--f--氵去 or 功--gong--g--工力--工（y与功同音）  
    def transhape(self, path,word_split):     
        with open(path, encoding='utf-8') as f:
            for keyword in f:               #添加敏感词入字典链，敏感词去除首尾的符号
                keyword=keyword.strip()
                if '\u4e00' <= keyword <= '\u9fa5':
                    lens=len(keyword)
                    ls=[]
                    for i in range(0,lens):
                        if i==0:
                            lb=0                #左边界
                            ls.append(keyword[i])
                            ls.append(str(pinyin(keyword[i])))
                            ls.append(str(pinyin(keyword[i]))[0])
                            rb=3                #右边界
                            if keyword[i] in word_split:
                                if pinyin(word_split[keyword[i]][0])==pinyin(keyword[i]):#左右结构的偏旁刚好又是和该字是同音字
                                    ls.append(word_split[keyword[i]][0])
                                    rb=rb+1
                                ls.append(word_split[keyword[i]])
                                rb=rb+1
                        else:                            
                            cnt=0
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
                                
                                cnt=cnt+3
                                if keyword[i] in word_split:
                                    if pinyin(word_split[keyword[i]][0])==pinyin(keyword[i]):#左右结构的偏旁刚好又是和该字是同音字
                                        char=ls[j]
                                        char=char+word_split[keyword[i]][0]
                                        ls.append(char)
                                        cnt=cnt+1
                                    char=ls[j]
                                    char=char+word_split[keyword[i]]
                                    ls.append(char)
                                    cnt=cnt+1
                            lb=rb
                            rb=rb+cnt                         
                    for i in range(lb,rb):
                        self.add(str(ls[i]).strip(),keyword)   #keyword是真实的敏感词
                else:
                    self.add(str(keyword).strip(),keyword) 
                    
    #--------遍历待检测文本，检测敏感词，计算敏感词数量，定位敏感词出现的位置                  
    def detecting(self, text):
        whole_text=text.read()              #全文
        text.seek(0)
        #whole_text=text.read().lower()     #此处补充一个全文行数的计算函数
        level=self.keyword_chains
        start=0                             #检索文本的索引
        ret=[]                              #检测结果的内容列表
        lines=1                             #总行数
        exlis="1234567890"
        posi=[]                             #文本每行右边界的下标
        line=text.readline()                #再按行读取，来确定当前敏感词所在行
        posi.append(len(line)-1)
        while start < len(whole_text):
            level = self.keyword_chains
            step_ins = 0                    #敏感词的长度
            rl_word=""                      #真正的敏感词
            fk_word=""                      #伪装的敏感词
            flag=0                          #是否有出现中文
            fnum=0                          #是否出现数字
            interval=[]                     #敏感词每个字出现在待检测文本中的位置
            index=start
            first=0                         #是否是敏感词的第一个字
            while(start>posi[-1]):
                line=text.readline()
                if not line:
                    break
                posi.append(posi[-1]+len(line))
                lines=lines+1
                #line=line.lower()
            for char in whole_text[start:]:
                
                if char in level or char.lower() in level:#涵盖中文的拼音，汉字，首写字母，左右结构拆分，以及正常的英文敏感词
                    if len(interval)>0 and index-interval[-1]-1>20:
                         break
                    first=1
                    real_char=char
                    if char.lower() in level:
                        real_char=char.lower()
                    step_ins += 1
                    interval.append(index)
                    if '\u4e00' <=char<= '\u9fa5':          #说明出现中文
                        flag=1                        
                    fk_word=fk_word+char
                    if self.delimit not in level[real_char]:
                        level = level[real_char]
                    else:
                        level=level[real_char]
                        #处理特殊情况-----falung---->falungong取后者
                        you=0                               #是否有更优选
                        xu_word=""
                        for k in whole_text[start+step_ins:]:
                            if k in level:
                                xu_word=xu_word+k
                                if self.delimit not in level[k]:
                                    level = level[k]
                                else:
                                    level = level[k]
                                    you=1
                                    rl_word=level[self.delimit]
                                    s=""
                                    s="Line"+str(lines)+": <"+rl_word+"> "+fk_word+xu_word
                                    ret.append(s)
                                    start += step_ins - 1
                                    break
                            else:
                                break
                        if you==1:
                            break
                        #------没有特殊情况，则正常执行
                        if len(level[self.delimit])!=0 and '\u4e00' <= level[self.delimit]<= '\u9fa5':#说明该词属于中文敏感词，又已知插入数字的中文敏感词无效
                            if fnum==1:
                                  break
                        rl_word=level[self.delimit]
                        s=""
                        s="Line"+str(lines)+": <"+rl_word+"> "+fk_word
                        ret.append(s)
                        start += step_ins - 1
                        break
                elif '\u4e00' <=char<= '\u9fa5':#处理同音字，繁体字的情况
                    py_char=pinyin(char)
                    exist=0                     #是否是同音字或是繁体字
                    rl_char=""                  #检测字符对应在敏感词库中的同音字或是繁体字
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
    #time1 = time.time()
    #----------命令行传参
    if len(sys.argv) == 1:
        be_detected_file = "C://Users//duan//Desktop//org.txt"#"C://Users//duan//Desktop//test.txt"
        reference_file= "C://Users//duan//Desktop//words.txt"
        result_file = "C://Users//duan//Desktop//00.txt"
    elif len(sys.argv) == 4:
        reference_file = sys.argv[1]   #参照文本（敏感词）
        be_detected_file = sys.argv[2] #待检测文本
        result_file = sys.argv[3]      #结果文本
    else:
        print("命令行错误")
        exit(0)
        
    #------生成拆分汉字左右结构的词链    
    split_file=open("wordsplit.txt", "r", encoding="utf-8").read()
    word_split={}                       #拆分的字典，键为 被拆分汉字，值为拆分出来的左右结构
    for char in split_file.split():
        word_split[char[0]]=char[1:]
        
    #-------生成敏感词链      
    test_tool = DFAFilter()             #生成测试工具对象
    test_tool.transhape(reference_file,word_split)

    #-------开始对待检测文本进行检测
    text=open(be_detected_file, "r", encoding="utf-8")
    result = test_tool.detecting(text)
    
    #-------将检测结果定向输出到指定路径下
    open(result_file, "w", encoding="utf-8").write(result)
    #print(result)
    


