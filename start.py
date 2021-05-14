import os
import re
import time
import socket

from urllib.request import urlretrieve
from urllib.error import HTTPError, URLError
from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException, NoSuchElementException, ElementNotInteractableException
from PIL import Image
from pygame import mixer
from datetime import date



class Crawler:
    def __init__(self):
        # 이미지들이 저장될 경로 및 폴더 이름
        self.path = "./img"
        self.date = str(date.today())

        # 검색어 입력 및 중복 검사
        self.query = input(" 원하는 이미지를 입력해주세요 ")
        while self.checking(self.query) is True:
            self.query = input("원하는 이미지를 입력해주세요 ")

        # 드라이버 경로 지정 (Chrome)
        self.driver = webdriver.Chrome("chromedriver.exe")

        # clickAndRetrieve() 과정에서 urlretrieve이 너무 오래 걸릴 경우를 대비해 타임 아웃 지정
        socket.setdefaulttimeout(30)

        # 크롤링한 이미지 수 초기화함
        self.crawled_count = 0


    def scroll_down(self):
        scroll_count = 0
        # 스크롤 위치값 얻고 last_height 에 저장함
        last_height = self.driver.execute_script("return document.body.scrollHeight")

        # 결과 더보기 버튼을 클릭했는지 유무
        after_click = False

        while True:
            # 스크롤 다운
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            scroll_count += 1
            if scroll_count == 1:
                break
            time.sleep(2)

            # 스크롤 위치값 얻고 new_height 에 저장
            new_height = self.driver.execute_script("return document.body.scrollHeight")

            # 스크롤이 최하단이며
            if last_height == new_height:

                # 결과 더보기 버튼을 클릭한적이 있는 경우
                if after_click is True:
                    break

                # 결과 더보기 버튼을 클릭한적이 없는 경우
                if after_click is False:
                    if self.driver.find_element_by_css_selector(".mye4qd").is_displayed():
                        self.driver.find_element_by_css_selector(".mye4qd").click()
                        print("> 결과 더보기 클릭")
                        after_click = True
                    elif NoSuchElementException:
                        print("> 이미지 갯수가 100개 이하임")
                        print("> 스크롤 다운 종료")
                        break

            last_height = new_height

    def click_and_retrieve(self, index, img, img_list_length):

        try:
            # 이미지 클릭
            img.click()
            time.sleep(1.5)
            src = self.driver.find_element_by_xpath('//*[@id="Sva75c"]/div/div/div[3]/div[2]/c-wiz/div/div[1]/div[1]/div/div[2]/a/img').get_attribute('src')

            # 저장될 이미지 파일 경로
            dst = f"{self.path}/{self.date}/{self.query}/{self.crawled_count + 1}"

            # 확장자
            if re.search(r"jpeg|png", src):
                ext = re.search(r"jpeg|png", src).group()
            else:
                ext = "jpg"

            # 이미지 저장
            urlretrieve(src, f"{dst}.{ext}")
            print(f"> {index + 1} / {img_list_length} 번째 사진 저장 ({ext})")
            self.crawled_count += 1
        except HTTPError:
            print("> HTTPError & 패스")
            pass

    def crawling(self):

        print("> 크롤링 시작")

        # 이미지 고급검색 중 이미지 유형 '사진'
        url = f"https://www.google.com/search?as_st=y&tbm=isch&hl=ko&as_q={self.query}&as_epq=&as_oq=&as_eq=&cr=&as_sitesearch=&safe=images&tbs=itp:photo"
        self.driver.get(url)
        self.driver.maximize_window()
        self.scroll_down()

        div = self.driver.find_element_by_xpath('//*[@id="islrg"]/div[1]')
        # class_name에 공백이 있는 경우 여러 클래스가 있는 것이므로 아래와 같이 css_selector로 찾음
        img_list = div.find_elements_by_css_selector(".rg_i.Q4LuWd")

        # 다운로드 디렉토리 생성(추가적으로 안해도되는데 보기쉬우라고 설정해둠)
        os.makedirs(self.path + '/' + self.date + '/' + self.query)
        print(f"> {self.path}/{self.date}/{self.query} 생성")

        for index, img in enumerate(img_list):
            try:
                self.click_and_retrieve(index, img, len(img_list))

            except ElementClickInterceptedException:
                print("> ElementClickInterceptedException")
                self.driver.execute_script("window.scrollTo(0, window.scrollY + 3)")
                print("> 3만큼 스크롤 다운 및 3초 슬립")
                time.sleep(3)
                self.click_and_retrieve(index, img, len(img_list))

            except NoSuchElementException:
                print("> NoSuchElementException")
                self.driver.execute_script("window.scrollTo(0, window.scrollY + 100)")
                print("> 100만큼 스크롤 다운 및 3초 슬립")
                time.sleep(3)
                self.click_and_retrieve(index, img, len(img_list))

            except ConnectionResetError:
                print("> ConnectionResetError & 패스")
                pass

            except URLError:
                print("> URLError & 패스")
                pass

            except socket.timeout:
                print("> socket.timeout & 패스")
                pass

            except socket.gaierror:
                print("> socket.gaierror & 패스")
                pass

            except ElementNotInteractableException:
                print("> ElementNotInteractableException")
                break

        try:
            print("> 크롤링 종료 (성공률: %.2f%%)" % (self.crawled_count / len(img_list) * 100.0))

        except ZeroDivisionError:
            print("> img_list 가 비어있음")

        self.driver.quit()

    def filtering(self, size):
        print("> 필터링 시작")

        filtered_count = 0
        dir_name = f"{self.path}/{self.date}/{self.query}"
        for index, file_name in enumerate(os.listdir(dir_name)):
            try:
                file_path = os.path.join(dir_name, file_name)
                img = Image.open(file_path)

                # 이미지 해상도의 가로와 세로가 모두 size 이하인 경우
                if img.width <= size and img.height <= size:
                    img.close()
                    os.remove(file_path)
                    print(f"> {index} 번째 사진 삭제")
                    filtered_count += 1

            # 이미지 파일이 깨져있는 경우
            except OSError:
                os.remove(file_path)
                filtered_count += 1

        print(f"> 필터링 종료 (총 갯수: {self.crawled_count - filtered_count})")

    def checking(self, query):
        # 입력 받은 검색어가 이름인 폴더가 존재하면 중복으로 판단
        for dir_name in os.listdir(self.path):
            file_list = os.listdir(f"{self.path}/{dir_name}")
            if query in file_list:
                print(f"> 중복된 검색어: ({dir_name})")
                return True

crawler = Crawler()
crawler.crawling()
crawler.filtering(350)
os.system('pause')