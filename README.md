# 爬取微博评论
在使用本代码时，您必须遵守以下规定：
您可以在遵守许可证条款的前提下，将本代码用于个人、学术或非商业用途，同时禁止用于非法用途。
您不得去除、更改或隐藏本代码中的版权声明、作者信息或许可证声明。
对于因使用本代码而产生的任何损失或损害，作者不承担任何责任。

## 代码解析

```python
# 导入相关库文件
import requests
from bs4 import BeautifulSoup
import time
import json 
from tqdm import tqdm # 进度可视化

time.sleep(5) # 保护机制，防止内部缺少在get请求之间添加时间间隔

weibo_Search_URL = 'https://s.weibo.com/weibo?q='  # 微博搜索URL
weibo_main_URL = "https://weibo.com/"  # 微博主页URL

# cookie 和 User_Agent 需要为自己的
cookie = "你自己的cookie，该cookie需要为手动登录后"
User_Agent = "你自己的用户代理"

keywords = ["霸王茶姬","茶百道","阿水大杯茶","古茗"] # 需要其他关键词就向这里面添加，['keyword1','keyword2',...]

# 请求头自定义
header = {
    "User-Agent":User_Agent,
    "Cookie":cookie
}

# 在关键词列表中进行遍历，对每个关键词进行爬取，同时生成对应的关键词评论txt文件
for keyword in keywords: 
    pages = 10      # 每个关键词爬取的博客页数
    print(f"这是第{keywords.index(keyword)+1}个关键词--{keyword}...")
    for page in range(1,pages+1):
        print(f"当前位于第{page}页...")

        weibo_Search_URL = f'{weibo_Search_URL}{keyword}&page={page}' # 根据关键词生成搜索URL

        response = requests.get(url=weibo_Search_URL,headers=header)
        time.sleep(5)

        response.encoding = "utf-8"
        weibo_search = response.text

        search_soup = BeautifulSoup(weibo_search,"html.parser")
        all_cards = search_soup.find_all("div",class_="card-wrap",attrs={"action-type":"feed_list_item"}) 
        # 一个card就是一个博客blog

        print(f"正在获取关于关键词{keyword}博客...")

        for card in all_cards:
            Blog_content = card.find("p", attrs={"node-type": "feed_list_content"}, class_="txt")
            print(f"---------------------------{type(Blog_content)}---------------------------")
            
            if Blog_content: # 这里没有使用try catch 捕捉异常，就是为了在出现问题时跳过该部分blog内容，而不中断程序运行
                Blog_content = Blog_content.get_text(separator="\n").strip()
            else:
                Blog_content = "未找到内容"  # 或者其他默认值
                break
                
            up_name = card.find("p",attrs={"node-type":"feed_list_content"},class_="txt").get("nick-name") # 博主名

            cardID = card.get("mid") # card的mid属性

            upID = "" # 博主ID
            href_list = card.find_all("a") 
            for href in href_list:
                if "weibo.com" in href.get("href"):
                    upID = href.get("href").split("/")[3].split("?")[0] 
                    # 博主的ID，原格式-> //weibo.com/5652018762?refer_flag=1001030103_，5652018762即为博主ID
                    break

            blog_info = "===========================< blog & 评论 上分界线 >===========================\n"\
                +f"当前位于第{page}页...\n"\
                +f"正在获取博客下的评论，当前位于第{all_cards.index(card)+1}个博客...\n"\
                    +up_name+"\n"+upID+"\n"+Blog_content\
                    +"===========================< blog & 评论 下分界线 >===========================\n"
            print(blog_info)
            with open(f"Weibo_{keyword}_comments.txt",'a',encoding="utf-8") as file: # 将博客内容写入txt文件
                file.write(blog_info)

            commenter_name = ""
            commenter_ID = ""
            commenter_IP = ""
            comment_date = ""
            comment_content = ""
            comment = ""

            comments_list = []
            max_id_list = []
            total_number = 0
            comment_count = 0
            next_max_id = 0

            blogFlag = 2 # 不知道 1 和 3 代表什么，但查看时都有出现过
			
            # 评论URL的请求头
            comments_header={
                "User-Agent":User_Agent,
                "cookie":cookie
            }
            
            while True:
                # 由于第一次请求URL和之后的URL多出max_id和flow=0的部分，所以需要定义对应的评论请求URL
                if next_max_id == 0: 
                    comments_require_URL = f"https://weibo.com/ajax/statuses/buildComments?is_reload=1&id={cardID}&is_show_bulletin={blogFlag}&is_mix=0&count=10&uid={upID}&fetch_level=0&locale=zh-CN" 
                else:
                    comments_require_URL = f"https://weibo.com/ajax/statuses/buildComments?flow=0&is_reload=1&id={cardID}&is_show_bulletin={blogFlag}&is_mix=0&max_id={next_max_id}&count=20&uid={upID}&fetch_level=0&locale=zh-CN" # 接下来的请求URL
                
                commnets = requests.get(url=comments_require_URL,headers=comments_header)
                time.sleep(5)
                commnets.encoding = "utf-8"
                blog_commnets = commnets.text
                comments_data = json.loads(blog_commnets) # URL获得的评论为JSON数据格式

                if comment_count == 0: #已经爬取的评论数，该操作为初始化操作，用于记录该blog下已经爬取的评论数
                    total_number = comments_data["total_number"] # 在初始化时同时获得总的评论数
                    if total_number == 0: # 没有评论的情况
                        comments_list = ["该评论区没有评论！"]
                        print("该评论区没有评论！")
                        break 

                max_id_list.append(next_max_id) # 存储已经使用过的max_id，用于判断是否重复使用max_id
                next_max_id = comments_data["max_id"]

                # print(comments_require_URL) 查看请求URL
				
                # 获得JSON中的评论部分
                for idx in tqdm(range(0,len(comments_data["data"]))): 
                    comment_content = comments_data["data"][idx]["text_raw"] # 评论内容
                    # comment_IP = comments_data["data"][idx]["source"] # IP
                    commenter_ID = comments_data["data"][idx]["user"]["idstr"] # ID
                    # comment_date = comments_data["data"][idx]["created_at"] # Date
                    commenter_name = comments_data["data"][idx]["user"]["screen_name"] # nick-name 昵称
                    # comment = f"[{comment_date}]  [{commenter_name}]  [{commenter_ID}]  [{comment_IP}]  [{comment_content}]\n"
                    comment = f"[{commenter_name}]  [{commenter_ID}]  [{comment_content}]\n" #评论内容
                    # comments_list.append(comment) # 向列表中添加评论，该部分可以用于在读取当前blog下所有评论之后，一次性写入文件，减少IO操作
                    with open(f"Weibo_{keyword}_comments.txt",'a',encoding="utf-8") as file: # 将博客下的评论逐个写入txt文件
                        file.writelines(comment)
                        
				# with open(f"Weibo_{keyword}_comments.txt",'a',encoding="utf-8") as file: # 将博客下的所有评论一次性写入txt文件
                #         file.writelines(comment)
                
                # 判断评论数是否增加 => 是否不在爬取新评论
                previous_count = comment_count 
                comment_count = len(comments_list)
				
                # 已经爬取的评论数超过总数 / 爬取的评论数不再增加 / max_id已经被使用
                if (comment_count >= total_number) or (previous_count == comment_count) or (next_max_id in max_id_list):
                    break
            
            # 重置
            max_id_list = []
            comments_list = []
            total_number = 0
            comment_count = 0
            next_max_id = 0

'''
已知BUG：
1.莫名出现 AttributeError: 'NoneType' object has no attribute 'get_text' 错误：
    遇到这个问题时，需要关闭程序重新运行，同时需要手动删除所有生成txt文件
2.无法依次利用关键词列表获得的关键词进行准确搜索，会出现重复使用的情况：
    出现该种情况时，可以把keywords中的其他关键词删除，并删除已经生成的当前关键词的txt文档，重新运行程序，相当于手动一个一个关键词爬取
                或者不删除其他关键词，只删除已经爬取过的关键词，但仍然需要删除当前出现问题的关键词的txt文档，最后重新运行
                
注：文件写入模式为附加，因此每次写入位置都会在文档最后，如果需要修改写入模式为 覆盖 的话，需要在 with open(...) 部分，将内部的 a 修改为 w
'''

'''
TODO
1.获取博主IP
2.自定义爬取评论条数，不满足时继续爬取，而不是固定爬取几页
'''
```

