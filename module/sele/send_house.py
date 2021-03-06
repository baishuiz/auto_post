# 发送房源页面

from ..sele import *
from constant.logger import *
from ..sele.page_login import PageLogin
from util.common.img_loader import ImgLoader
from util.common.timeout import set_timeout

def get_house_code(code):
    code = str(code)
    length = 6 - len(code)
    house_code = "SH%s%s"%("0"*length, code)
    return house_code

class SendHouse(PageLogin, ImgLoader):

    def __init__(self, username, house_list=[], browser=None):
        self.username = username
        self.send_ajk = True
        global usertype
        if browser is not None:
            self.browser = browser
        else:
            PageLogin.__init__(self, username)
            self.browser = self.login
            usertype = self.usertype
        self.usertype = usertype
        self.house_list = house_list
        self.current_house_info = None
        self.main_window = self.browser.window_handles[0]

    @contextmanager
    def wait_for_new_window(self, driver, timeout=20):
        handles_before = driver.window_handles
        yield
        WebDriverWait(driver, timeout).until(lambda driver: len(handles_before) != len(driver.window_handles))

    @property
    def send(self):
        for house_info in self.house_list:
            self.current_house_info = house_info
            yield self.__send_single__                  # 将单条发送的结果返回给main函数
            
    @property
    def __send_single__(self):
        browser = self.browser
        
        try:
            self.__check__                              # 发布预检查
        except Exception as e:
            sele_err("系统错误：房源推送失败！ 房源编号：%s， 报错信息：%s"%(str(self.current_house_info[0:2]), str(e)))
            return False
            
        try:
            self.__to_send_page__                       # 跳转到发布页面
            self.__choose_platform__                    # 弹出框中勾选全部发布方式
            self.__send_info__                          # 将有关的数据发送到网页前端
            self.__check_result__                       # 检查发送结果是否正常
        except SystemExit:
            browser.close()
            raise
        except Exception as e:
            sele_err("系统错误：房源推送失败！ 房源编号：%s， 报错信息：%s"%(str(self.current_house_info[0:2]), str(e)))
            return False
        finally:
            if len(browser.window_handles) != 1:
                browser.close()                         # 关闭当前窗口
            browser.switch_to_window(self.main_window)  # 切换回主窗口
            self.browser = browser                      # 赋值类中的browser对象
        sele_info("系统提示：房源发送成功！ 房源编号：%s"%(str(self.current_house_info[0:2])))
        return True

    @property
    def __to_send_page__(self):
        '''点击进入信息填写页'''
        browser = self.browser

        click_message = WebDriverWait(browser, 20).until(EC.presence_of_element_located((By.ID, "js_sms")))
        click_message.click()

        zufang = browser.find_element_by_partial_link_text(u"租房")
        zufang.click()

        time.sleep(1)

        with self.wait_for_new_window(browser):
            fabu = browser.find_element_by_xpath('//a[@href="/house/publish/rent/?from=manage"]')
            fabu.click()

        # 切换到发布窗口
        new_window = browser.window_handles[1]
        browser.switch_to_window(new_window)
        browser.maximize_window()

        self.browser = browser
    
    @property
    def __choose_platform__(self):
        '''选择发布平台'''
        browser = self.browser

        if self.usertype == 2:
            # 点击提示信息： 全选
            queding = WebDriverWait(browser, 20).until(EC.presence_of_element_located((By.XPATH, '//input[@class="ui-button ui-button-positive ui-button-medium"]')))
            time.sleep(0.5)
            raw_text = browser.page_source
            re_choose_web_1 = re.findall("""<input id=\"chooseWeb_1\".+value=\"1\"(.+)type.+""", raw_text)[0].strip()
            re_choose_web_2 = re.findall("""<input id=\"chooseWeb_2\".+value=\"2\"(.+)type.+""", raw_text)[0].strip()

            if self.send_ajk == True:   # 发送安居客
                if re_choose_web_1 == "":
                    platform_anjuke = browser.find_element_by_id("chooseWeb_1")
                    platform_anjuke.click()
            else:
                if re_choose_web_1 != "":
                    platform_anjuke = browser.find_element_by_id("chooseWeb_1")
                    platform_anjuke.click()
            if re_choose_web_2 == "":
                platform_58 = browser.find_element_by_id("chooseWeb_2")
                platform_58.click()

            queding.click()

        self.browser = browser

    @property
    def __check__(self):
        '''预检查模块'''
        import random
        (sheet, idx, community, addr, floor_num, total_floor, area, price, title, house_type, source) = self.__get_info__
        sele_info("开始发布房源 来源数据[%s - %d] 房源信息[%s]"%(sheet, idx, "%s %s %s %s %s %s %s %s"%(community, addr, floor_num, total_floor, area, price, title, house_type)))
        
        # 检查房源图片
        try:
            self.img = ImgLoader("/data/imgs/%d/"%(random.randint((source-1)*100,source*100)))
        except Exception:
            raise

    @property
    def __send_info__(self):
        '''通过给出的数据填写表单'''
        _ = (_, idx, community, addr, floor_num, total_floor, area, price, title, house_type, _) = self.__get_info__    #解析房源数据
        house_imgs = self.img.room_imgs
        
        self.check_title(title)                                                                                 #检查标题是否有非法关键词

        hz_entire = True
        browser = self.browser

        ##############START##############
        try:
            clear_e = browser.find_element_by_css_selector("#formcache-refuse")
            clear_e.click()
        except Exception:
            pass

        # 选择整租
        if hz_entire is True:
            zhengzu = browser.find_element_by_id("hz-entire")
            zhengzu.click()

        # 输入房源编号
        housecode = browser.find_element_by_name("housecode")
        housecode.clear()
        housecode.send_keys(get_house_code(idx))

        # 输入地标名称
        community_e = browser.find_element_by_xpath("""//*[@id="community_unite"]""")
        community_e.clear()
        community_e.send_keys(addr)
        housecode.click()
        time.sleep(1)
        community_e.click()
        time.sleep(1)
        try:
            community_es = browser.find_element_by_xpath("""/html/body/div[4]/div/form/div[3]/div/ul/li""")
            community_es.click()
        except Exception:
            community_e.clear()
            community_e.send_keys(community)
            housecode.click()
            time.sleep(2)
            community_e.click()
            time.sleep(2)
            try:
                community_es = browser.find_element_by_xpath("""/html/body/div[4]/div/form/div[3]/div/ul/li""")
                community_es.click()
            except Exception:
                raise RuntimeError("没有在发布平台找到对应的地标！")

        # 输入户型
        # 室：自定义
        room = browser.find_element_by_name("room")
        room.clear()
        room.send_keys(house_type)

        # 厅：1
        hall = browser.find_element_by_name("hall")
        hall.clear()
        hall.send_keys(1)

        # 卫：1
        bathRoom = browser.find_element_by_name("bathroom")
        bathRoom.clear()
        bathRoom.send_keys(1)

        # 输入当前楼层
        floor = browser.find_element_by_css_selector("div.ui-form:nth-child(10) > input:nth-child(2)")
        floor.clear()
        floor.send_keys(floor_num)

        # 输入总楼层
        allFloor = browser.find_element_by_css_selector("input.ui-form-input:nth-child(5)")
        allFloor.clear()
        allFloor.send_keys(total_floor)

        # 有无电梯：无
        havaElevator = browser.find_element_by_css_selector("div.ui-form:nth-child(11) > label:nth-child(3)")
        havaElevator.click()

        time.sleep(1)

        # 选择房屋类型: 普通住宅
        # 2: 普通住宅 3:公寓 4: 别墅 5: 平房 6: 新里洋房 7: 老公房 8: 其他
        real_house_type = 2
        houseType = browser.find_element_by_css_selector("#select-housetype > div:nth-child(2) > div:nth-child(1) > span:nth-child(1)")
        houseType.click()
        normalHouse = browser.find_element_by_css_selector(".exia-light > ul:nth-child(2) > li:nth-child(%d)" % real_house_type)
        normalHouse.click()

        time.sleep(1)

        # 选择房屋类型: 精装修
        # 2: 毛坯　3: 简单装修 4: 精装修 5: 豪华装修
        real_decorate_level = 4
        decorateLevel = browser.find_element_by_css_selector("#select-housefit > div:nth-child(2) > div:nth-child(1) > span:nth-child(1)")
        decorateLevel.click()
        jingzhuangxiu = browser.find_element_by_css_selector(".exia-light > ul:nth-child(2) > li:nth-child(%d)" % real_decorate_level)
        jingzhuangxiu.click()

        time.sleep(1)

        # 选择房屋朝向: 南
        orientation = browser.find_element_by_css_selector("#select-exposure > div:nth-child(2) > div:nth-child(1) > span:nth-child(1)")
        orientation.click()
        south = browser.find_element_by_css_selector(".exia-light > ul:nth-child(2) > li:nth-child(3)")
        south.click()

        # 房屋特性列表 - 下面为需要勾选
        house_addons_lists = {
            u"冰箱": 1,
            u"电视": 2,
            u"洗衣机": 3,
            u"热水器": 4,
            u"空调": 5,
            u"宽带": 6,
            u"沙发": 7,
            u"床": 8,
            u"暖气": 9,
            u"衣柜": 10,
            u"可做饭": 11,
            u"独立卫生间": 12,
            u"独立阳台": 13
        }

        real_house_addons = [u"冰箱",  u"洗衣机", u"热水器", u"空调", u"宽带", u"沙发", u"床", u"衣柜", u"可做饭", u"独立卫生间", u"独立阳台"]

        # 选择设置配套设施
        for idxx in real_house_addons:
            if idxx in house_addons_lists:
                value = house_addons_lists[idxx]
                item = browser.find_element_by_css_selector(
                    "label.ui-checkbox-label:nth-child(%d) > input:nth-child(1)" % value)
                item.click()

        time.sleep(1)

        # 填写出租间面积
        roomArea = browser.find_element_by_name("roomarea")
        roomArea.send_keys(area)

        # 填写租金
        rentprice = browser.find_element_by_name("rentprice")
        rentprice.send_keys(price)

        # 填写付款方式: 面议
        paytype = browser.find_element_by_css_selector("#select-paymode > div:nth-child(2) > div:nth-child(1) > span:nth-child(1)")
        paytype.click()
        mianyi = browser.find_element_by_css_selector(".exia-light > ul:nth-child(2) > li:nth-child(8)")
        mianyi.click()

        if self.send_ajk == True:
            # 选择无中介费
            noCommission = browser.find_element_by_name("noCommission")
            noCommission.click()

            time.sleep(1)

        # 填写房源标题
        title_e = browser.find_element_by_name("title")
        title_e.send_keys(u"%s" % title)

        time.sleep(1)

        # 填写房源内容，使预编辑的模板
        use_template = browser.find_element_by_css_selector(".use-tpl")
        use_template.click()
        time.sleep(3)    # 暂停3秒，等待模板选择窗口弹出

        # 默认选择地一个模板
        first_template = browser.find_element_by_css_selector("dl.clearfix > dd:nth-child(2) > label:nth-child(1) > input:nth-child(1)")
        first_template.click()
        template_confirm_button = browser.find_element_by_css_selector("a.ui-button-positive:nth-child(1)")
        template_confirm_button.click()

        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # 上传房源图片
        # 每次完一张图片，要等待上传框再次显示才能传下一张
        # 因为网络延迟和DOM加载需要时间
        room_img_count=0
        img_err_count = 0
        for img in house_imgs[:-1]:
            try:
                room_img_count = self.upload_img(img, room_img_count)
            except Exception:
                img_err_count += 1
                sele_warn("上传图片超时... 本条图片已忽略")
        
        if img_err_count > 4:
            raise RuntimeError("上传图片数量不足！")

        if self.send_ajk == True:
            # 上传户型图图片
            house_type_image = browser.find_element_by_css_selector("#model-fileupload")
            house_type_image.send_keys(house_imgs[-1])
            time.sleep(1)

        # 点击提交按钮
        publish_rent_add = browser.find_element_by_id("publish-rent-add")
        publish_rent_add.click()
        push_status = browser.find_element_by_css_selector(".result-title")

        
        ###############END###############

    @property
    def __get_info__(self):
        house_info = self.current_house_info
        house_info[3] = house_info[3].split('/')[-1]
        return tuple(house_info)

    def check_title(self, title):
        import json, requests

        cookies = self.browser.get_cookies()
        cookie = dict()
        for cook in cookies:
            cookie[cook["name"]] = cook["value"]
        check_json = json.loads(requests.get("http://vip.58ganji.com/ajax/house/illegal/?kw=%s"%title,cookies=cookie).text)
        if check_json["st"] == False:
            pass
        else:
            kws = [kw["keyword"] for kw in check_json["details"]]
            for kw in kws:
                house_title = title.replace(kw,"**")
            sele_warn("检查出错误 房间标题修改为：%s"%house_title)

    @property
    def __check_result__(self):
        from urllib.parse import unquote
        import sys

        time.sleep(2)
        url = self.browser.current_url.strip()
        url = unquote(url)

        if url.find("条数上限值150") != -1:
            '''58发送条数到达上限'''
            sele_fatal("58发送条数到达上限")
            raise SystemExit("58发送条数到达上限")

        elif url.find("发布房源+超出有效操作数") != -1:
            '''安居客发送数量达到上限'''
            self.send_ajk = False
            raise RuntimeError("安居客发送数量达到上限！")

        elif url.find("调用API超时") != -1:
            '''调用API超时'''
            raise RuntimeError("调用API超时！")

        elif url.find("操作太频繁") != -1:
            '''操作太频繁'''
            raise RuntimeError("操作太频繁")

        else:
            pass
    

    @set_timeout(12)
    def upload_img(self, img, room_img_count):
        '''上传单张图片 超时时间为12秒'''
        t1 = time.time()
        room_image = self.browser.find_element_by_id("room_fileupload")
        room_image.send_keys(img)
        time.sleep(1)
        room_img_count += 1

        while True:
            boxes = self.browser.find_elements_by_css_selector("#room-upload-display > div:nth-child(1)")
            upload_box_length = len(self.browser.find_elements_by_css_selector("#room-upload-display > div"))-1
            if upload_box_length == room_img_count:
                return room_img_count
            time.sleep(1)