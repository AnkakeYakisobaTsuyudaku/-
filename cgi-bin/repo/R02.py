import datetime
import io
import json
import sys
import requests
import cgi
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import base64
from io import BytesIO

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

form = cgi.FieldStorage()

hantei = ""

u_1 = form.getvalue('mon', 0)
u_2 = form.getvalue('day', 0)
u_3 = form.getvalue('hour', 0)

html = ""

if u_1 != 0 and u_2 != 0 and u_3 != 0:
    response = requests.get(
        'https://api.open-meteo.com/v1/forecast',
        params={
            "latitude": 35.6785,
            "longitude": 139.6823,
            "timezone": "Asia/Tokyo",
            "hourly": ["temperature_2m", "relativehumidity_2m", "precipitation", "weathercode"]})

    result = json.loads(response.text)

    hourly_time = result["hourly"]["time"]
    temperatures = result["hourly"]["temperature_2m"]
    kosuiryo = result["hourly"]["precipitation"]
    weather = result["hourly"]["weathercode"]

    six_hours_time = []
    six_hours_weathercode = []
    six_hours_temperature = []
    six_hours_precipitation = []

    if len(u_1) == 1:
        u_1 = f"0{u_1}"
    if len(u_2) == 1:
        u_2 = f"0{u_2}"    
    if len(u_3) == 1:
        u_3 = f"0{u_3}"

    search_date = f"2022-{u_1}-{u_2}T{u_3}:00"
    if  search_date in hourly_time:
        day = hourly_time.index(search_date)
        for x in range(day, day+6):
            six_hours_time.append(hourly_time[x])
            six_hours_weathercode.append(weather[x])
            six_hours_temperature.append(temperatures[x])

        x_time = []

        for x in six_hours_time:
            temp = x.split("T")
            x_time.append(temp[1])

        sunny_count = 0
        cloudy_count = 0
        rainy_count = 0

        for x in six_hours_weathercode:
            weather_num = int(x)
            if 0 <= weather_num <= 1:
                sunny_count += 1
            elif 2 <= weather_num <= 3:
                cloudy_count += 1
            else:
                rainy_count += 1

        if rainy_count >= 1:
            hantei = f"<h2>洗濯<br>不可</h2>"
        else:
            if sunny_count > cloudy_count:
                hantei = f"<h2>洗濯<br>可能</h2>"
            else:
                hantei = f"<h2>洗濯<br>微妙</h2>"        

        if 16 <= int(u_3) <= 23 or 0 <= int(u_3) <= 3:
            hantei = f"<h2>洗濯<br>非推奨</h2>"

        fig, ax1 = plt.subplots( )
        ax1.plot(x_time, six_hours_temperature ,"b-")
        ax1.set_ylabel("temperature")

        ax2 = ax1.twinx()

        ax2.plot(x_time, six_hours_weathercode ,"r-")
        ax2.set_ylabel("weathercode")

        tmpfile = BytesIO()
        fig.savefig(tmpfile, format='png')
        encoded = base64.b64encode(tmpfile.getvalue()).decode('utf-8')

        html = '<img src=\'data:image/png;base64,{}\'>'.format(encoded)
    else:
        hantei = f"<h2>判定<br>不能</h2>"
        
style = """
    <style>
    .main{
        display:flex;
        align-items: center;
        justify-content: center;
        }
    .container{
        display: flex;
        justify-content: space-around; 
    }
    h1 { font-family: serif }
    h4 { font-family: sans-serif}
    h2 {font-size: 20px;}
    h2 { font-family: serif}
</style>
"""

template = f"""
<html><head>
    <meta charset = "utf-8">
    <title>この日は東京都で洗濯できるのか</title>
    {style}
</head>
<body>
<div class="main">
    <form action="/cgi-bin/repo/R02.py" method="post">
    <h1>洗濯判定くん</h1>
        　<h4>入力した時間から六時間後までの天気のデータを、
        <a href="https://open-meteo.com/en">Open-Meteo</a>
        の提供するapiから取得して出力します。
        <br>
        　以下のボックスに今日から一週間後までの月日時を入力してください。
        <br>
        <label for="date">日付</label>
        <input type="number" name="mon" value="{u_1}" min="1" max="12" required>
        月
        <input type="number" name="day" value="{u_2}" min="1" max="31" required>
        日
        <input type="number" name="hour" value="{u_3}" min="0" max="23" required>
        時</h4>
        <br>
        <input type="submit" value="送信">
        <h4>グラフ中の赤い線はweathercode、青い線は気温の推移を示す</h4>
    </form>
    </div>
    <div class="container">
    <p>{hantei}</p>
    {html}
    </div>
</body>
</html>
"""

print("Content-type: text/html\n")
print(template)
