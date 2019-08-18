import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import requests, lxml, os, time, requests, json
from wordcloud import WordCloud
from base64 import b64encode
from datetime import datetime, timedelta

taskdone = False
trial = 0
waittime = 60

fontpath='font.otf'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'
}

#갤러리ID
gid = ''

#갤러리 링크
link = 'https://gall.dcinside.com/board/lists/?id=' + gid

#탐색 날짜 범위 (ex. days=1 : 1일 이내, 0:측정 시작순간 이후)
#설정 날짜의 딱 자정으로 설정됩니다 (ex. 8.18 1:45AM -> 8.18 00:00AM)
drange = 1

if not os.path.isfile('lastupd.txt'): open('lastupd.txt', 'w').write(datetime.now().strftime('%Y-%m-%d'))


while (True):
    #날짜 갱신이 안되어있을시 본격적 작업 시작
    if datetime.strptime(open('lastupd.txt', 'r').read(), '%Y-%m-%d') < datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):

        #날짜 갱신
        open('lastupd.txt', 'w').write(datetime.now().strftime('%Y-%m-%d'))

        while not taskdone and trial < 5:
            try:
                #마이너, 정식갤러리 판별
                r = requests.get('https://gall.dcinside.com/board/lists/?id=' + gid, headers = headers).text
                print('갤러리 형식:', end=' ')

                #마이너 갤러리일 경우
                if 'location.replace' in r:
                    link = link.replace('board/','mgallery/board/')    
                    print('마이너')
                    
                else:
                    print('정식')
                
                ystday = (datetime.now() - timedelta(days=drange)).replace(hour=0, minute=0, second=0, microsecond=0)
                print(ystday, '이후의 게시글을 수집합니다.')

                i = 0
                tdata = ''
                ndata = ''
                fin = False

                while not fin:
                    time.sleep(0.5)
                    
                    i += 1
                    print('페이지 읽는 중... [{}번째...]'.format(i))#, end='\r')

                    r = requests.get(link + '&page=' + str(i), headers = headers).text    
                    bs = BeautifulSoup(r, 'lxml')

                    posts = bs.find_all('tr', class_='ub-content us-post')

                    for p in posts:
                        title = p.find('td', class_='gall_tit ub-word').a

                        #공지 제외 (볼드태그 찾을때 str 처리 해줘야 찾기가능)
                        if not '<b>' in str(title):
                            title = title.text
                            nick = p.find("td", {"class", "gall_writer ub-writer"})
                            date = datetime.strptime(p.find('td', class_='gall_date').get('title'), "%Y-%m-%d %H:%M:%S")

                            #초 단위까지는 안 가도록 함
                            if date > ystday:
                                tdata += title + '\n' #제목 값
                                ndata += nick.text.strip() + '\n' #닉네임 값
                            else:
                                print('기간 초과:', date)
                                fin = True
                                break
                                 

                print()
                print('워드클라우드 생성 중... [1/2]')
                wc_title = WordCloud(font_path=fontpath, width=1200, height=1000, background_color='white').generate(tdata)
                print('워드클라우드 생성 중... [2/2]')
                wc_nick = WordCloud(font_path=fontpath, width=1200, height=1000, background_color='white').generate(ndata)

                print('이미지 저장 중...')
                wc_title.to_file('title.png')
                wc_nick.to_file('nick.png')

                hotkey = sorted(wc_title.words_.items(), key=(lambda x: x[1]), reverse = True)[0][0]
                hotnick = ''
                
                for n in sorted(wc_nick.words_.items(), key=(lambda x: x[1]), reverse = True):
                    if n[0] != 'ㅇㅇ':
                        hotnick = n[0]
                        break
                

                print('오늘의 핵심 키워드:', hotkey)
                print('오늘의 잉여 닉네임:', hotnick)

                print('저장 완료')
                taskdone = True
            except Exception as e:
                print('뭔가 문제가 있습니다. 다시 해보겠습니다.')
                print('오류 메시지:', str(e))
                print('시도 횟수:', str(trial))
                trial += 1
                time.sleep(5)


        if taskdone == True:
            taskdone = False
            trial = 0

            while not taskdone and trial < 5:
                try:
                    #이미지 업로드

                    client_id = ''
                    headers = {"Authorization": "Client-ID " + client_id}
                    api_key = ''

                    url = "https://api.imgur.com/3/upload.json"
                    t_img = ''
                    n_img = ''

                    print('이미지 업로드 중... [1/2]')
                    r = requests.post(
                        url, 
                        headers = headers,
                        data = {
                            'key': api_key, 
                            'image': b64encode(open('title.png', 'rb').read()),
                            'type': 'base64',
                            'name': 'title.png',
                            'title': gid + ' ' + str(ystday) + ' posts WC'
                        }
                    )

                    t_img = json.loads(r.text)['data']['link']

                    print('이미지 업로드 중... [2/2]')
                    r = requests.post(
                        url, 
                        headers = headers,
                        data = {
                            'key': api_key, 
                            'image': b64encode(open('nick.png', 'rb').read()),
                            'type': 'base64',
                            'name': 'nick.png',
                            'title': gid + ' ' + str(ystday) + ' nick WC'
                        }
                    )

                    n_img = json.loads(r.text)['data']['link']


                    page_source='''<p><span style="font-family: Arial, sans-serif; font-size: 14pt;">오늘의 [gallid] 갤러리 단어 클라우드</span></p>
                    <p><br></p><span style="font-family: Arial, sans-serif;">
                    </span><img src="[title_image]"><p></p>
                    <p><span style="font-family: Arial, sans-serif; font-size: 10pt;">※ 단어가 클수록 빈도가 높습니다</span></p>
                    <p><br></p>
                    <p><span style="font-family: Arial, sans-serif; font-size: 14pt;">오늘의 핵심 키워드: <b>[hotkey]</b></span></p>
                    <p><br></p>
                    <p><br></p>
                    <p><br></p>
                    <p><span style="font-family: Arial, sans-serif; font-size: 14pt;">오늘의 [gallid] 갤러리 갤러 클라우드</span></p>
                    <p><br></p><span style="font-family: Arial, sans-serif;">
                    </span><img src="[nick_image]"><p></p>
                    <p><br></p>
                    <p><span style="font-family: Arial, sans-serif;">※ 단어가 클수록 폐인입니다</span></p>
                    <p><br></p>
                    <p><span style="font-family: Arial, sans-serif; font-size: 14pt;">오늘의 폐인 갤러: <b>[hotnick]</b></span><br></p>
                    <p><br></p>
                    <p><br></p>
                    <p><br></p>
                    <p style="text-align: right;"><span style="font-family: Arial, sans-serif; font-size: 9pt; color: rgb(116, 116, 116);">본 게시글은 자동 작성되었습니다</span></p>'''


                    page_source = page_source.replace('[gallid]', gid)
                    page_source = page_source.replace('[title_image]', t_img)
                    page_source = page_source.replace('[nick_image]', n_img)
                    page_source = page_source.replace('[hotkey]', hotkey)
                    page_source = page_source.replace('[hotnick]', hotnick)

                    open('page.txt', 'w').write(page_source)

                    taskdone = True
                    print('작업이 모두 성공하였습니다.')
                    
                except Exception as e:
                    print('뭔가 문제가 있습니다. 다시 해보겠습니다.')
                    print('오류 메시지:', str(e))
                    print('시도 횟수:', str(trial))
                    trial += 1
                    time.sleep(5)

        print('업로드 스크립트 끝.')



        #============================글쓰기 시작============================

        from selenium import webdriver

        id = ''
        pw = ''
        url = 'https://www.dcinside.com/'
        #주의!! : 아직 갤러리 작성 페이지 마이너갤러리로만 설정해놓음
        gall = 'https://gall.dcinside.com/mgallery/board/write/?id=' + gid
        title = '오늘의 갤러리 워드클라우드 (' + str(ystday.month) + '월 ' + str(ystday.day) + '일~)'
        content = open('page.txt', 'r').read()

        # 가상디스플레이
        from pyvirtualdisplay import Display
        display = Display(visible=0, size=(800, 800))  
        display.start()
        print('디스플레이 드라이버 로드...')

        # 크롬 환경 변수
        print('환경 변수 설정...')
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument('window-size=800x600')
        options.add_argument("disable-gpu")

        #크롬 드라이버 로드
        print('chromedriver 로드...')
        driver = webdriver.Chrome('/usr/lib/chromium-browser/chromedriver', options=options)
        driver.implicitly_wait(3)

        # 디시인사이드 로그인 페이지 로드
        print('dcinside 로그인 작업 중...')
        driver.get(url)

        # 아이디
        driver.find_element_by_name('user_id').send_keys(id)
        # 패스워드
        driver.find_element_by_name('pw').send_keys(pw)
        # 로그인
        driver.find_element_by_id('login_ok').click()

        # 글을 쓰고자 하는 갤러리로 이동
        print('갤러리 글쓰기 페이지 접속...')
        driver.get(gall)
        time.sleep(3)

        # 제목 입력
        print('글 제목 입력중...')
        driver.find_element_by_name('subject').send_keys(title)
        driver.execute_script("window.scrollTo(0, 100)")

        # HTML으로 쓰기 방식 변경
        print('HTML 글쓰기 방식 변경...')
        driver.find_element_by_id("tx_switchertoggle").click();
        time.sleep(1)

        # 글쓰기 폼으로 진입
        print('글쓰기 폼으로 프레임 전환...')
        driver.switch_to.frame(driver.find_element_by_xpath("//iframe[@name='tx_canvas_wysiwyg']"))
        #print(driver.page_source)

        #본문 입력
        print('본문 입력중...')
        driver.find_element_by_tag_name("body").send_keys(content)

        driver.switch_to_default_content()
        #글쓰기 저장
        print('저장 후 전송중...')
        time.sleep(3)
        driver.find_element_by_xpath("//button[@class='btn_blue btn_svc write']").click()
        #저장 딜레이
        time.sleep(1)
        #웹페이지 닫기
        print('작업 마무리중...')
        driver.close()

        display.sendstop()
        display.stop()

    print('대기중... (' + str(waittime) + ')')
    time.sleep(waittime)
    
