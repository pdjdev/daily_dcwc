import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import requests, lxml, os, time, json
from wordcloud import WordCloud
from base64 import b64encode
from datetime import datetime, timedelta

def midReturn(val, s, e):
    if s in val:
        val = val[val.find(s)+len(s):]
        if e in val: val = val[:val.find(e)]
    return val

taskdone = False
trial = 0

#탐색 날짜 범위 (ex. days=1 : 1일 이내, 0:측정 시작순간 이후)
#설정 날짜의 딱 자정으로 설정됩니다 (ex. 8.18 1:45AM -> 8.18 00:00AM)
drange = 1

fontpath='font.otf'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'
}

#갤러리ID
gid = ''

#갤러리 링크
link = 'https://gall.dcinside.com/board/lists/?id=' + gid

#마이너, 정식갤러리 판별
r = requests.get('https://gall.dcinside.com/board/lists/?id=' + gid, headers = headers).text
print('갤러리 형식:', end=' ')

#마이너 갤러리일 경우
if 'location.replace' in r:
    link = link.replace('board/','mgallery/board/')    
    print('마이너')
else:
    print('정식')


taskdone = False
trial = 0

while not taskdone and trial < 5:
    try:
                  
        ystday = (datetime.now() - timedelta(days=drange)).replace(hour=0, minute=0, second=0, microsecond=0)
        print(ystday, '이후의 게시글을 수집합니다.')

        i = 0
        tdata = ''
        ndata = ''
        fin = False
        r = None

        while not fin:
            time.sleep(0.5)
            
            i += 1
            print('페이지 읽는 중... [{}번째...]'.format(i))#, end='\r')
            titleok = False

            while not titleok:
                r = requests.get(link + '&page=' + str(i), headers = headers).text
                bs = BeautifulSoup(r, 'lxml')

                posts = bs.find_all('tr', class_='ub-content us-post')

                for p in posts:
                    title = p.find('td', class_='gall_tit ub-word')

                    #공지 제외 (볼드태그 찾을때 str 처리 해줘야 찾기가능)
                    if not '<b>' in str(title):
                        titleok = True
                        title = midReturn(str(title), '</em>', '</a>')
                        nick = p.find("td", {"class", "gall_writer ub-writer"})
                        date = datetime.strptime(p.find('td', class_='gall_date').get('title'), "%Y-%m-%d %H:%M:%S")
                        print(title)

                        #초 단위까지는 안 가도록 함
                        if date >= ystday:
                            tdata += title + '\n' #제목 값
                            ndata += nick.text.strip() + '\n' #닉네임 값
                        else:
                            print('기간 초과:', date)
                            fin = True
                            date = ystday
                            break
                        
                if not titleok:
                    print('게시글 크롤링 실패. 15초 후 다시 시도해 봅니다.')
                    i -= 1
                    time.sleep(15)
                         

        print()
        print('워드클라우드 생성 중... [1/2]')
        wc_title = WordCloud(font_path=fontpath, width=1200, height=1000, background_color='white', collocations=False).generate(tdata)

        print('이미지 저장 중...')
        wc_title.to_file('title.png')

        hotkey = sorted(wc_title.words_.items(), key=(lambda x: x[1]), reverse = True)[0][0]

        print('오늘의 핵심 키워드:', hotkey)

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

            print('이미지 업로드 중...')
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


            page_source = open('orgpage.txt', 'r').read()
            page_source = page_source.replace('[gallid]', gid)
            page_source = page_source.replace('[title_image]', t_img)
            page_source = page_source.replace('[hotkey]', hotkey)

            open('page.txt', 'w').write(page_source)

            taskdone = True
            print('작업이 모두 성공하였습니다.')
  
        except Exception as e:
            taskdone = False
            print('뭔가 문제가 있습니다. 다시 해보겠습니다.')
            print('오류 메시지:', str(e))
            print('시도 횟수:', str(trial))
            trial += 1
            time.sleep(5)

print('업로드 스크립트 끝.')

#============================글쓰기 시작============================

if taskdone:
    taskdone = False
    from selenium import webdriver

    id = ''
    pw = ''
    url = 'https://www.dcinside.com/'
    gall = 'https://gall.dcinside.com/mgallery/board/write/?id=' + gid
    title = '[@]오늘의 갤러리 워드클라우드 (' + str(ystday.month) + '월 ' + str(ystday.day) + '일~)'
    content = open('page.txt', 'r').read()

    # 리눅스를 위한 가상 디스플레이 드라이버 로드 
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

