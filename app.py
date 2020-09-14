from flask import Flask

app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello World!'


if __name__ == '__main__':
    app.run()

'''
    1. !틀어줘 노래제목/유튜브 링크 | !music title/youtube link
    - 유튜브 링크가 아니면 동작하지 않습니다
    * Only available youtube link
    - 유튜브에서 듣고싶은 음악 혹은 플레이리스트를 찾아서 틀어줍니다. 라디오 모드로 링크가 재생됩니다.
    * Find music or playlist what you wanna hear in Youtube, playing it only radio mode
    
    1. !로또 | !lotto
    - 이번주 예상 1등 로또번호를 알려줍니다.
    * Tell expected 1st Win Korean Lottery number in Channel

    1. !랜덤 요소1, 요소2, 요소3... | !random ele1, ele2, ele3...
    - 임의로 하나를 선택해줍니다.
    * Choose one among what you enter elements
'''