import getpass
import time

import selenium
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.alert import Alert
import common as Com
import slack as Slack
import requests
from bs4 import BeautifulSoup

driver = webdriver.Chrome()
driver.implicitly_wait(1)


def set_driver():
    """
    드라이버 세팅 후 메인페이지 이동
    :return:
    """
    driver.get(Com.main_url_path)
    # driver.implicitly_wait(1)
    # driver.maximize_window()
    move_login_page()


def move_login_page():
    """
    로그인 페이지 이동 후 로그인 입력
    :return:
    """
    driver.get(Com.main_url_path + Com.login_url_path)
    # driver.implicitly_wait(1)
    input_login_text()


def move_data_center_margin_page():
    """
    데이터 센터 - 마진 10000원이상
    :return:
    """
    # 데이터센터 - 마진 10,000원 이상 이동
    driver.get(Com.main_url_path + Com.margin_url_path)

    # 특정 상품 가져오기
    get_product()

    # driver.find_element(By.XPATH, '//*[@id="prd_form"]/ul/li[3]/dl/dd[1]/span[1]').click()
    #
    # send_smart_store()


def move_data_center_sparta_page():
    """
    데이터 센터 - 스파르타 페이지
    :return:
    """
    # 데이터센터 - 스파르타 페이지 이동
    driver.get(Com.main_url_path + Com.dataCenter_sparta_url_path)

    # 특정 상품 가져오기
    get_product(8_000)


def move_data_center_page():
    """
    데이터 센터 페이지에서 상품 선택
    1. 스마트스토어로 보내기(o)
    2. 엑셀폼 다운로드(x)
    :return:
    """
    # 데이터센터로 이동
    driver.get(Com.main_url_path + Com.dataCenter_url_path)

    # 특정 상품 가져오기
    get_product(10_000)

    # 전체선택
    # driver.find_element(By.CLASS_NAME, "btn_check_all").click()


def get_product(min_price=1000):
    """
    1. 현재페이지에 상품을 다 가져온다.
    2. 특정 금액 이상 상품을 가져온다
    3. 2번에서 가져온 상품을 체크 한다.
    4. 19 이미지가 없는 것만 가지고 온다
    :return:
    """
    search_data = driver.find_element(By.CLASS_NAME, "product_section").find_elements(By.CLASS_NAME, "product_set")
    data_dic_in_array = [{}]
    for sect in search_data:
        # 타이틀코드
        product_code = sect.find_element(By.CLASS_NAME, "product_code")
        # 타이틀
        product_title = sect.find_element(By.CLASS_NAME, "product_title")
        # 가격
        product_price = sect.find_element(By.CLASS_NAME, "product_price").find_element(By.CLASS_NAME, "price")
        # 판매신청완료
        product_success = sect.find_element(By.CLASS_NAME, "product_check").find_element(By.CLASS_NAME, "sale_state")
        # 19세 이상 가능 구분
        product_adult = None

        try:
            # 19 이미지가 없는 것만 업로드 한다
            product_adult = sect.find_element(By.CLASS_NAME, "product_img").find_element(By.CLASS_NAME, "icon_19")
        except NoSuchElementException:
            print("No Found")
        finally:
            # 19 이미지가 없는것만..
            if not product_adult:

                # 판매신청완료 안된 것만
                if not product_success.text:
                    price_int = (product_price.text).replace(',', '')

                    # 최소금액원 이상인 것만
                    if int(price_int) >= min_price:
                        print(product_code.text)
                        print(product_title.text)
                        print("=========================")
                        driver.implicitly_wait(5)
                        elem = sect.find_element(By.CLASS_NAME, "checkbox_label")
                        driver.execute_script("arguments[0].scrollIntoView(true);", elem)
                        driver.implicitly_wait(5)
                        try:
                            elem.click()
                        except NoSuchElementException as err:
                            Slack.send_slack_message(
                                '스마트스토어 상품 체크하는데 실패 하였습니다. \n다음 상품을 체크합니다. \n\t==체크박스 클릭하는 부분== \n\t코드: {0} \n\t타이틀: {1} \n\t에러메세지: {2}'.format(
                                    product_code.text,
                                    product_title.text,
                                    err
                                )
                            )
                            pass

                        data_dic_in_array.append(
                            {'code': product_code.text,
                             'title': product_title.text,
                             'price': product_price.text}
                        )

    del data_dic_in_array[0]
    print(len(data_dic_in_array))

    if len(data_dic_in_array) > 0:
        # 스마트스토어 보내기 버튼 클릭
        send_smart_store(len(data_dic_in_array))
    else:
        print("올릴 상품 없음")
        Slack.send_slack_message('스마트스토어에 업로드 할 상품이 없습니다.')


def send_smart_store(cnt):
    """
    선택된 상품 스마트 스토어로 보내기
    :return:
    """
    # driver.find_element(By.XPATH, "//div[@onclick='smartstore_download()']").click()
    elem = driver.find_element(By.XPATH, "//div[@onclick='smartstore_download()']")
    driver.execute_script("arguments[0].scrollIntoView(true);", elem)
    elem.click()
    time.sleep(2)

    try:
        driver.find_element(By.CLASS_NAME, "smart_modi_btn").click()
        time.sleep(5)
        driver.implicitly_wait(10)
        Alert(driver).accept()
        Slack.send_slack_message('스마트스토어에 {0}건 상품을 등록했습니다.'.format(cnt))
    except NoSuchElementException as err:
        print("alert Fail::", err)
        Slack.send_slack_message('스마트스토어에 업로드를 실패하였습니다.(NoSuchElementException: {0})'.format(err))
    except Exception as err:
        print("alert Fail::", err)
        Slack.send_slack_message('스마트스토어에 업로드를 실패하였습니다.에러메세지: {0}'.format(err))
        pass


def input_login_text():
    """
    로그인 페이지에 로그인 입력 후 메인페이지 및 데이터 센터 페이지로 이동
    :return:
    """
    # ID, 패스워드 클리어
    driver.find_element(By.ID, "login").clear()
    driver.find_element(By.ID, "password").clear()

    # ID, 패스워드 입력
    driver.find_element(By.ID, "login").send_keys(Com.user_id)
    driver.find_element(By.ID, "password").send_keys(Com.user_pw)

    # 로그인버튼 클릭
    driver.find_element(By.CLASS_NAME, "btn.btn-block.btn-lg").click()

    # 메인으로 이동
    driver.get(Com.main_url_path)

    # 데이터센터 카테고리이동
    # move_data_center_page()

    # 데이터 센터 스파르타 카테고리 이동
    move_data_center_sparta_page()

    # 마진 1000원 이상
    # move_data_center_margin_page()


if __name__ == '__main__':
    set_driver()
