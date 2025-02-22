import requests
from bs4 import BeautifulSoup
import time
import json 
from tqdm import tqdm

time.sleep(5) 

weibo_Search_URL = 'https://s.weibo.com/weibo?q=' # 微博搜索URL
weibo_main_URL = "https://weibo.com/" # 微博主页URL

# cookie 和 User_Agent 需要为自己的
cookie = "你自己的cookie，该cookie需要为手动登录后"
User_Agent = "你自己的用户代理"

keywords = ["霸王茶姬","茶百道","阿水大杯茶","古茗"] # 需要其他关键词就向这里面添加，['keyword1','keyword2',...]

header = {
    "User-Agent":User_Agent,
    "Cookie":cookie
}
for keyword in keywords:
    pages = 10      # 每个关键词爬取的博客页数
    print(f"这是第{keywords.index(keyword)+1}个关键词--{keyword}...")
    for page in range(1,pages+1):
        print(f"当前位于第{page}页...")

        weibo_Search_URL = f'{weibo_Search_URL}{keyword}&page={page}'

        response = requests.get(url=weibo_Search_URL,headers=header)
        time.sleep(5)

        response.encoding = "utf-8"
        weibo_search = response.text

        search_soup = BeautifulSoup(weibo_search,"html.parser")
        all_cards = search_soup.find_all("div",class_="card-wrap",attrs={"action-type":"feed_list_item"})

        print(f"正在获取关于关键词{keyword}博客...")

        for card in all_cards:
            
            # Blog_content = card.find("p",attrs={"node-type":"feed_list_content"},class_="txt").get_text(separator="\n").strip() # blog内容
            Blog_content = card.find("p", attrs={"node-type": "feed_list_content"}, class_="txt")
            print(f"-------------------------------------------------------{type(Blog_content)}--------------------------------------------------")
            if Blog_content:
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
                    upID = href.get("href").split("/")[3].split("?")[0] # 博主的ID，原格式-> //weibo.com/5652018762?refer_flag=1001030103_
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

            comments_header={
                "User-Agent":User_Agent,
                "cookie":cookie
            }
            


            '''
            当前面对每页的评论数量的问题需要处理，需要实时更新数量多少，不能直接给定，否则当当前评论区个数小于这个值时会出现死循环 ，疑似非bug
            暂定在while这个部分进行获取评论数量，并修改 if comment_count < 20: 

            新的问题，最后不爬取数据，出现评论量不增加的问题，怀疑是URL请求评论链接格式有问题
            '''
            
            while True:
                if next_max_id == 0:
                    comments_require_URL = f"https://weibo.com/ajax/statuses/buildComments?is_reload=1&id={cardID}&is_show_bulletin={blogFlag}&is_mix=0&count=10&uid={upID}&fetch_level=0&locale=zh-CN" 
                else:
                    comments_require_URL = f"https://weibo.com/ajax/statuses/buildComments?flow=0&is_reload=1&id={cardID}&is_show_bulletin={blogFlag}&is_mix=0&max_id={next_max_id}&count=20&uid={upID}&fetch_level=0&locale=zh-CN" # 接下来的请求URL
                
                commnets = requests.get(url=comments_require_URL,headers=comments_header)
                time.sleep(5)
                commnets.encoding = "utf-8"
                blog_commnets = commnets.text
                comments_data = json.loads(blog_commnets)

                if comment_count == 0: #已经爬取的评论数
                    total_number = comments_data["total_number"]
                    if total_number == 0: # 没有评论的情况
                        comments_list = ["该评论区没有评论！"]
                        print("该评论区没有评论！")
                        break 

                max_id_list.append(next_max_id)
                next_max_id = comments_data["max_id"]

                print(comments_require_URL)

                for idx in tqdm(range(0,len(comments_data["data"]))):
                    comment_content = comments_data["data"][idx]["text_raw"]
                    # comment_IP = comments_data["data"][idx]["source"]
                    commenter_ID = comments_data["data"][idx]["user"]["idstr"]
                    # comment_date = comments_data["data"][idx]["created_at"]
                    commenter_name = comments_data["data"][idx]["user"]["screen_name"]
                    # comment = f"[{comment_date}]  [{commenter_name}]  [{commenter_ID}]  [{comment_IP}]  [{comment_content}]\n"
                    comment = f"[{commenter_name}]  [{commenter_ID}]  [{comment_content}]\n"
                    comments_list.append(comment)
                    with open(f"Weibo_{keyword}_comments.txt",'a',encoding="utf-8") as file: # 将博客内容写入txt文件
                        file.writelines(comment)

                previous_count = comment_count
                comment_count = len(comments_list)

                if (comment_count >= total_number) or (previous_count == comment_count) or (next_max_id in max_id_list):
                    break
            
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