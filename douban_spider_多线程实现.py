import re
import requests
import json
import threading
import random
from queue import Queue


#使用队列，不是多个线程同时爬取数据，而是多个线程负责不同的工作（数据爬取、数据保存）
lock = threading.Lock()
class Douban_spider:
    # 爬虫初始化函数
    def __init__(self, start_url):
        self.url = start_url
        self.url_queue = Queue()
        self.html_str_queue = Queue()
        self.content_queue = Queue()

    def choose_proxy(self):
        proxies = ["http://42.55.197.67:", "http://182.34.193.243:", "http://182.126.53.112:",
                   "http://123.134.181.199:", "http://112.83.158.19:", "http://144.123.68.181:",
                   "http://60.182.179.209:"]
        x = int(random.random() * 6)
        return {"http": proxies[x]}

    # 从字典中解析并且保存有用的json数据
    def get_data_list(self):
        while True:
            html_str = self.html_str_queue.get()
            movie_dict = json.loads(html_str)
            movie_num = len(movie_dict["subjects"])
            movie_list = movie_dict["subjects"]
            for i in range(movie_num):
                movie_name = movie_list[i]["title"]
                movie_rate = movie_list[i]["rate"]
                movie_playable = movie_list[i]["playable"]
                movie_is_new = movie_list[i]["is_new"]
                movie_cover = movie_list[i]["cover"]
                movie_url = movie_list[i]["url"]
                strs = movie_name + " " + movie_rate + " " + str(movie_playable) + " " + str(
                    movie_is_new) + " " + movie_cover + " " + movie_url
                self.content_queue.put(strs)
            self.html_str_queue.task_done()

    def save_file(self, type):
        while True:
            strs = self.content_queue.get()
            with open(type + ".txt", "a", encoding="utf-8") as f:
                f.writelines(strs + "\n")
                print(strs)
            f.close()
            self.content_queue.task_done()

    # 爬取网站数据
    def parse_url(self):
        # 使用代理实现爬取网站数据
        while True:
            self.url = self.url_queue.get()
            proxies = self.choose_proxy()
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"
            }
            # 使用requests请求豆瓣网站获取数据
            res = requests.get(self.url, proxies=proxies, headers=headers)
            while res.status_code != 200:
                proxies = self.choose_proxy()
                res = requests.get(self.url, proxies=proxies, headers=headers)
            html_str = res.content.decode()
            print(html_str)
            self.html_str_queue.put(html_str)
            self.url_queue.task_done()


    # 构造url地址,放入队列中
    def make_url(self):
        for i in range(26):
            self.url_queue.put(self.url.format(i*20))


    # 爬虫主函数
    def run(self, type):
        threading_list = []

        # 1. 构造url
        t_url = threading.Thread(target=self.make_url)
        threading_list.append(t_url)

        # 2. json数据获取
        # 发请求比较慢，使用多几个线程来发请求
        for i in range(10):
            t_parse = threading.Thread(target=self.parse_url)
            threading_list.append(t_parse)

        # 3. json数据转化为有用信息列表
        t_getdata = threading.Thread(target=self.get_data_list)
        threading_list.append(t_getdata)

        # 4. 将有用数据写入文件加以保存
        t_savedata = threading.Thread(target=self.save_file, args=(type,))
        threading_list.append(t_savedata)

        # 5. 启动四个进程
        for t in threading_list:
            # 把子进程设置为守护线程，主线程一旦结束，子线程也会结束
            t.setDaemon(True)
            t.start()

        for q in [self.url_queue,self.html_str_queue,self.content_queue]:
            q.join() #让主线程阻塞等待队列的任务完成之后再完成
        print("-----------------------主线程结束-----------------------")


def input_type():
    print("---------电视剧爬虫---V1.0--------")
    type_list = ["美剧", "英剧", "日剧", "国产剧", "港剧", "日本动画", "综艺", "纪录片"]
    print("可爬取类型：美剧、英剧、日剧、国产剧、港剧、日本动画、综艺、纪录片----")
    type = input("请输入您要爬取的电视剧类型：")
    while type not in type_list:
        print("----请输入正确的电视剧类型-----")
        type = input("请输入您要爬取的电视剧类型：")
    return type

if __name__ == "__main__":

    #用户输入type
    type = input_type()

    #初始化豆瓣爬虫对象
    douban_spider = Douban_spider("https://movie.douban.com/j/search_subjects?type=tv&tag=" + str(type) + "&sort=recommend&page_limit=20&page_start={}")

    # 先把文件头部写上
    with open(type + ".txt", "w", encoding="utf-8") as f:
        f.writelines("movie_name  movie_rate  str movie_playable  movie_is_new  movie_cover  movie_url")
    f.close()
    #启动豆瓣爬虫
    douban_spider.run(type)


