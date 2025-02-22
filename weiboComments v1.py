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
            print(f"---------------------------{type(Blog_content)}---------------------------")
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
                    comment_content = comments_data["data"][idx]["text_raw"] # 评论内容
                    # comment_IP = comments_data["data"][idx]["source"] # IP
                    commenter_ID = comments_data["data"][idx]["user"]["idstr"] # ID
                    # comment_date = comments_data["data"][idx]["created_at"] # Date
                    commenter_name = comments_data["data"][idx]["user"]["screen_name"] # nick-name 昵称
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
# 声明
在使用本代码时，您必须遵守以下规定：

## 合规性声明
1. 遵守法律：使用本爬虫代码必须遵守所有适用的法律法规，包括但不限于版权法、隐私法、计算机欺诈和滥用法等。
2. 网站条款：在启动爬虫之前，请确保您已阅读并遵守目标网站的“服务条款”、“使用协议”和“robots.txt”文件。某些网站可能禁止或限制自动化数据收集行为。
3. 尊重隐私：在使用爬虫代码时，请尊重用户的隐私权。不要收集、存储或分享任何个人敏感信息。

## 使用限制
1. 非商业用途：除非获得开发者的明确书面许可，否则本爬虫代码仅供个人学习、研究或非商业用途使用。
2. 频率限制：为了减少对目标网站服务器的影响，请合理设置爬虫的访问频率。避免过度请求导致服务器负载过重。
3. 数据使用：收集的数据仅用于合法、道德和合规的目的。不得将数据用于任何形式的骚扰、歧视或非法活动。

## 免责声明
1. 准确性：开发者不对爬虫代码的准确性、完整性或适用性做出任何保证。使用爬虫代码时，请自行承担风险，并进行必要的测试和验证。
2. 第三方责任：对于因使用本爬虫代码而产生的任何第三方索赔、损失或损害（包括但不限于对目标网站的损害），开发者不承担任何责任。

##附加条款
请注意，本声明可能随时更新。在使用爬虫代码之前，请务必检查最新的声明内容。此外，开发者保留对爬虫代码及其声明的最终解释权。

'''

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

