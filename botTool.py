import json, io, random

def getToken(tokenFname):
    token = None
    with io.StringIO() as strbuf:
        if not isinstance(tokenFname, str):
            strbuf.write("올바른 문자열이 아닙니다")
        else :
            try:
                with open(tokenFname, "r") as twrap:
                    tokenWrap = json.load(twrap)
                    token = tokenWrap["token"]
            except FileNotFoundError :
                strbuf.write("토큰을 불러오지 못했습니다.")
        print(strbuf.getvalue())
    return token

