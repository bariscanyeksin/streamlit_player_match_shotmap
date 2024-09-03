import matplotlib.pyplot as plt
from mplsoccer import VerticalPitch
import streamlit as st
import requests
import os
from matplotlib import font_manager as fm
import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from io import BytesIO
from matplotlib.colors import to_rgba
import pandas as pd
from matplotlib.table import Table
from datetime import datetime
import base64
import io

st.set_page_config(
    page_title="Süper Lig - Oyuncu Maç Şut Haritası",
    initial_sidebar_state="expanded"
)

st.markdown(
    """
    <style>
        /* Sidebar içindeki tüm text input elementlerini hedef alma */
        input[id^="text_input"] {
            background-color: #242C3A !important;  /* Arka plan rengi */
        }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

    html, body, [class*="cache"], [class*="st-"]  {
        font-family: 'Poppins', sans-serif;
    }
    </style>
    """, 
    unsafe_allow_html=True
)

st.markdown(
    """
    <style>
        /* Bilgisayarlar için */
        @media (min-width: 1024px) {
            .block-container {
                width: 750px;
                max-width: 750px;
                padding-top: 0px;
            }
        }

        /* Tabletler için (genellikle 768px - 1024px arası ekran genişliği) */
        @media (min-width: 768px) and (max-width: 1023px) {
            .block-container.st-emotion-cache-13ln4jf.ea3mdgi5 {
                width: 700px;
                max-width: 700px;
            }
        }

        /* Telefonlar için (genellikle 768px ve altı ekran genişliği) */
        @media (max-width: 767px) {
            .block-container.st-emotion-cache-13ln4jf.ea3mdgi5 {
                width: 100%;
                max-width: 100%;
                padding-left: 10px;
                padding-right: 10px;
            }
        }
        .stDownloadButton {
            display: flex;
            justify-content: center;
            text-align: center;
        }
        .stDownloadButton button {
            background-color: rgba(51, 51, 51, 0.17);
            color: gray;  /* Text color */
            border: 0.5px solid gray;  /* Thin gray border */
            transition: background-color 0.5s ease;
        }
        .stDownloadButton button:hover {
            background-color: rgba(51, 51, 51, 0.65);
            border: 1px solid gray;  /* Thin gray border */
        }
        .stDownloadButton button:active {
            background-color: rgba(51, 51, 51, 0.17);
            color: gray;  /* Text color */
            border: 0.5px solid gray;  /* Thin gray border */
            transition: background-color 0.5s ease;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Sidebar'a görsel ekleme
image_url = "https://images.fotmob.com/image_resources/logo/leaguelogo/71.png"  # Görselin URL'si

# Görseli bir HTML div ile ortalama
image_html = f"""
    <div style="display: flex; justify-content: center;">
        <img src="{image_url}" width="100">
    </div>
    """

st.sidebar.markdown(image_html, unsafe_allow_html=True)

plt.rcParams['figure.dpi'] = 300
current_dir = os.path.dirname(os.path.abspath(__file__))

# Poppins fontunu yükleme
font_path = os.path.join(current_dir, 'fonts', 'Poppins-Regular.ttf')
prop = fm.FontProperties(fname=font_path)

bold_font_path = os.path.join(current_dir, 'fonts', 'Poppins-SemiBold.ttf')
bold_prop = fm.FontProperties(fname=bold_font_path)

pitch = VerticalPitch(corner_arcs=True, half=True, pitch_type='uefa', pitch_color='#0e1117', line_color='#818f86', goal_type='box')

fig, ax = pitch.draw(figsize=(16, 9))
fig.patch.set_facecolor('#0e1117')
fig.set_figwidth(7.5)

ax.axis('off')

primary_text_color = '#818f86'

# API'den maç verilerini çekmek için bir fonksiyon
def fetch_finished_matches():
    api_url = "https://www.fotmob.com/api/leagues?id=71&ccode3=TUR"
    response = requests.get(api_url)
    data = response.json()
    allmatches = data['matches']['allMatches']
    
    finished_matches = []
    for match in allmatches:
        if match['status']['finished']:
            finished_matches.append(match)
    
    return finished_matches

# Biten maçları çek
finished_matches = fetch_finished_matches()

# Haftaları ve maçları hazırlamak için bir sözlük oluştur
matches_by_week = {}
for match in finished_matches:
    # Haftayı belirlemek için match['round'] kullanılabilir
    week_number = f"Hafta {match['round']}"
    if week_number not in matches_by_week:
        matches_by_week[week_number] = []
    matches_by_week[week_number].append(match)

# Haftaların sıralı listesi
week_options = sorted(matches_by_week.keys(), key=lambda x: int(x.split()[-1]))

# Son haftayı varsayılan olarak seçme
latest_week = week_options[-1]

# Sol tarafta bir selectbox ile hafta seçimi
selected_week = st.sidebar.selectbox("Haftayı Seçin", week_options, index=week_options.index(latest_week))

# Seçilen haftanın maçlarını gösteren dinamik selectbox
matches = matches_by_week[selected_week]
match_options = [f"{match['home']['name']} vs {match['away']['name']}" for match in matches]

# Haftanın son maçını belirleme
latest_match_display = f"{matches[-1]['home']['name']} vs {matches[-1]['away']['name']}"

# Eğer haftanın son maçı varsa seçili olarak ayarla
selected_match = st.sidebar.selectbox(
    "Maç Seçin",
    match_options,
    index=match_options.index(latest_match_display) if latest_match_display in match_options else 0
)

# Seçilen maçın detaylarını bul
match_details = next(match for match in matches_by_week[selected_week] if f"{match['home']['name']} vs {match['away']['name']}" == selected_match)

# Maç detaylarını çekmek için matchId kullan
match_id = match_details['id']
match_api_url = f"https://www.fotmob.com/api/matchDetails?matchId={match_id}"
match_response = requests.get(match_api_url)
match_data = match_response.json()

general_data = match_data['general']
week = general_data['matchRound']
matchDay = general_data['matchTimeUTCDate']
parsed_date = datetime.fromisoformat(matchDay[:-1])
formatted_date = parsed_date.strftime("%d.%m.%Y")
leagueName = general_data['leagueName']
leagueSeason = general_data['parentLeagueSeason']
leagueString = f"{leagueName} - {leagueSeason}"
weekString = f"{week}. Hafta | {formatted_date}"

# Şut haritası verilerini al
shotmap = match_data['content']['shotmap']['shots']

home_name = match_details['home']['name']
away_name = match_details['away']['name']
skor = match_details['status']['scoreStr']
result_string = f"{home_name} {skor} {away_name}"

ax.text(0.94, 1.075, leagueString, transform=ax.transAxes, fontsize=8, fontproperties=prop, color=primary_text_color,
        verticalalignment='top', horizontalalignment='right')

ax.text(0.94, 1.035, weekString, transform=ax.transAxes, fontsize=8, fontproperties=prop, color=primary_text_color,
        verticalalignment='top', horizontalalignment='right')

ax.text(0.94, 1, result_string, transform=ax.transAxes, fontsize=8, fontproperties=prop, color=primary_text_color,
        verticalalignment='top', horizontalalignment='right')

# Oyuncu isimleri ve şut sayılarını içeren bir sözlük oluştur
player_shot_counts = {}
for shot in shotmap:
    if shot['expectedGoals'] is not None:
        player_name = shot['fullName']
        if player_name in player_shot_counts:
            player_shot_counts[player_name] += 1
        else:
            player_shot_counts[player_name] = 1

# Şut sayılarına göre oyuncuları çoktan aza sıralayalım
sorted_players = sorted(player_shot_counts.items(), key=lambda item: item[1], reverse=True)
sorted_player_names = [player[0] for player in sorted_players]

# Yeni selectbox: Oyuncu seçimi (şut sayısına göre sıralı)
selected_player = st.sidebar.selectbox("Oyuncu Seçin", sorted_player_names)

# Seçilen oyuncunun şutlarını filtrele
player_shots = [shot for shot in shotmap if shot['fullName'] == selected_player]

# Sol üst köşeye oyuncu ismi ve görselini eklemek için
player_name = selected_player
player_id = player_shots[0]['playerId']  # Oyuncu ID'sini ilk şuttan alıyoruz
team_id = player_shots[-1]['teamId']  # Oyuncu ID'sini ilk şuttan alıyoruz

player_detailed_stats = match_data['content']['playerStats'][str(player_id)]

# JSON verilerinde her bir anahtarı kontrol et ve yoksa '-' döndür
player_xG_sum = player_detailed_stats.get('stats', [{}])[0].get('stats', {}).get('Expected goals (xG)', {}).get('stat', {}).get('value', '-')
player_xGOT_sum = player_detailed_stats.get('stats', [{}])[0].get('stats', {}).get('Expected goals on target (xGOT)', {}).get('stat', {}).get('value', '-')

# Oyuncu görselini URL'den çekme
url = f'https://images.fotmob.com/image_resources/playerimages/{player_id}.png'
response = requests.get(url)
img = mpimg.imread(BytesIO(response.content))

# Görseli ekleme
imagebox = OffsetImage(img, zoom=0.3)
ab = AnnotationBbox(imagebox, (0.05, 1.1), frameon=False, xycoords='axes fraction', box_alignment=(0, 1))
ax.add_artist(ab)

# Oyuncu görselini URL'den çekme
#url_teamlogo = f'https://images.fotmob.com/image_resources/logo/teamlogo/{team_id}.png'
#response_teamlogo = requests.get(url_teamlogo)
#img_teamlogo = mpimg.imread(BytesIO(response_teamlogo.content))

# Görseli ekleme
#imagebox_teamlogo = OffsetImage(img_teamlogo, zoom=0.27, alpha=0.3)
#ab_teamlogo = AnnotationBbox(imagebox_teamlogo, (0.4497, 0.203), frameon=False, xycoords='axes fraction', box_alignment=(0, 1))
#ax.add_artist(ab_teamlogo)

def get_team_name(team_id):
    api_url = f"https://www.fotmob.com/api/teams?id={team_id}"
    response = requests.get(api_url)
    data = response.json()
    return data

team_data = get_team_name(team_id)
team_name = team_data["details"]["name"]

# Oyuncu ismini ekleme
ax.text(0.165, 1.07, player_name, transform=ax.transAxes, fontsize=16, fontproperties=bold_prop,
        verticalalignment='top', horizontalalignment='left', color='white', weight='bold')

ax.text(0.165, 1.018, team_name, transform=ax.transAxes, fontsize=10, fontproperties=prop,
        verticalalignment='top', horizontalalignment='left', color=primary_text_color)

goal_color = '#f5cb36'
attemptSaved_color = '#3066d9'
miss_color = 'red'

# Seçilen oyuncunun şut haritasını çiz
for shot in player_shots:
    if shot['expectedGoals'] is not None:
        if shot['eventType'] == 'Goal':
            shot_color = goal_color
            pitch.lines(shot['x'], shot['y'], 105, shot['goalCrossedY'], ax=ax, color=to_rgba(shot_color, alpha=0.5), lw=1)
            pitch.scatter(shot['x'], shot['y'], ax=ax, c=shot_color, s=round(shot['expectedGoals'], 2)*800, edgecolors='black', marker='*', alpha=0.8, lw=0.5)
        if shot['eventType'] == 'AttemptSaved':
            shot_color = attemptSaved_color
            if (shot['isBlocked'] == True) & (shot['expectedGoalsOnTarget'] == 0):
                pitch.lines(shot['x'], shot['y'], shot['blockedX'], shot['blockedY'], ax=ax, color=to_rgba(shot_color, alpha=0.5), lw=1)
            elif (shot['isBlocked'] == False) & (shot['expectedGoalsOnTarget'] > 0):
                pitch.lines(shot['x'], shot['y'], shot['blockedX'], shot['blockedY'], ax=ax, color=to_rgba(shot_color, alpha=0.5), lw=1)
            else:
                pitch.lines(shot['x'], shot['y'], 105, shot['goalCrossedY'], ax=ax, color=to_rgba(shot_color, alpha=0.25), lw=1)
            pitch.scatter(shot['x'], shot['y'], ax=ax, c=shot_color, s=round(shot['expectedGoals'], 2)*800, edgecolors='black', marker='o', alpha=0.8, lw=1.5)
        if shot['eventType'] == 'Miss':
            shot_color = miss_color
            pitch.lines(shot['x'], shot['y'], 105, shot['goalCrossedY'], ax=ax, color=to_rgba(shot_color, alpha=0.25), lw=1)
            pitch.scatter(shot['x'], shot['y'], ax=ax, c=shot_color, s=round(shot['expectedGoals'], 2)*800, edgecolors='black', marker='x', alpha=0.8, lw=1.5)
        else:
            shot_color = 'gray'

ax.text(0.937, 0.08, '@bariscanyeksin\nVeri: FotMob', transform=ax.transAxes,
        fontsize=7, fontproperties=prop, ha='right', va='bottom', color=primary_text_color, weight='normal', alpha=0.5)

pitch.scatter(58,66,ax=ax,c=goal_color, s=100, edgecolors='black', marker='*', alpha=0.5, lw=0.5)
pitch.scatter(56,66,ax=ax,c=attemptSaved_color, s=100, edgecolors='black', marker='o', alpha=0.5, lw=1.5)
pitch.scatter(54,66,ax=ax,c=miss_color, s=50, edgecolors='black', marker='x', alpha=0.5, lw=1.5)

ax.text(0.1, 0.147, 'Gol', transform=ax.transAxes,
        fontsize=7, fontproperties=prop, ha='left', va='bottom', color=primary_text_color, weight='normal', alpha=0.5)
ax.text(0.1, 0.1155, 'Kurtarış/Blok', transform=ax.transAxes,
        fontsize=7, fontproperties=prop, ha='left', va='bottom', color=primary_text_color, weight='normal', alpha=0.5)
ax.text(0.1, 0.082, 'İsabetsiz', transform=ax.transAxes,
        fontsize=7, fontproperties=prop, ha='left', va='bottom', color=primary_text_color, weight='normal', alpha=0.5)

# İngilizce terimlerin Türkçe karşılıkları
situation_translation = {
    'RegularPlay': 'Akan Oyun',
    'SetPiece': 'Duran Top',
    'ThrowInSetPiece': 'Taç Atışı',
    'FreeKick': 'Serbest Vuruş',
    'FastBreak': 'Hızlı Hücum',
    'FromCorner': 'Köşe Vuruşu',
    'Penalty': 'Penaltı',
    'IndividualPlay': 'Bireysel'
}

shootType_translation = {
    'RightFoot': 'Sağ Ayak',
    'LeftFoot': 'Sol Ayak',
    'Header': 'Kafa Vuruşu',
    'OtherBodyParts': 'Diğer'
}

result_translation = {
    'Goal': 'Gol',
    'Miss': 'İsabetsiz',
    'Post': 'Direk'
}

# Şutları tablo olarak göstermek için
table_data = [
    {
        'Şut Dakikası': f"{shot['min']}'",
        'xG': '-' if shot.get('isOwnGoal', False) else round(shot['expectedGoals'], 2) if isinstance(shot['expectedGoals'], (float, int)) else None,
        'xGOT': '-' if (shot.get('isOwnGoal', False)) or (shot['expectedGoalsOnTarget'] == 0) else round(shot['expectedGoalsOnTarget'], 2) if isinstance(shot['expectedGoalsOnTarget'], (float, int)) else None,
        'Hazırlanış': situation_translation.get(shot['situation'], shot['situation']),
        'Vuruş Tipi': shootType_translation.get(shot['shotType'], shot['shotType']),
        'Sonuç': 'Kurtarış' if (shot['eventType'] == 'AttemptSaved' and shot['expectedGoalsOnTarget'] > 0) else 'Blok' if (shot['eventType'] == 'AttemptSaved' and shot['expectedGoalsOnTarget'] == 0) else result_translation.get(shot['eventType'], shot['eventType'])
    }
    for shot in player_shots
]

# DataFrame oluşturma
df_shots = pd.DataFrame(table_data)

# Toplamlar için yeni bir satır ekleme
df_shots.loc[4] = [
    '',
    player_xG_sum,
    player_xGOT_sum,
    '',
    '',
    ''
]

# Sabit genişlik, dinamik yükseklik ve şut haritası altına sabit konum ayarları
fixed_table_width = 0.895  # Genişlik sabit
column_width = fixed_table_width / len(df_shots.columns)

# Satır yüksekliğini dinamik olarak belirleme
row_height = 0.04  # Her satır için sabit bir yükseklik
total_height = row_height * (len(df_shots) + 1)  # Başlık + veri satırları

# Tablonun üst kısmını sabit tutmak için y konumunu ayarlama
shotmap_top_y = -0.02  # Şut haritasının hemen altına yerleştirmek için

# Tabloyu yatay olarak ortalamak için x konumunu hesaplama
# (Ekseni tam ortalamak için genişliğin yarısını çıkartıyoruz)
x_position = (1 - fixed_table_width) / 2

# Tablonun dinamik yüksekliği için bbox ayarları
table = Table(ax, bbox=[x_position, shotmap_top_y - total_height, fixed_table_width, total_height])

# Tablo başlığı
for j, column in enumerate(df_shots.columns):
    cell = table.add_cell(0, j, width=column_width, height=row_height, text=column, loc='center', facecolor=to_rgba('lightgray', alpha=0.125))
    cell.get_text().set_fontproperties(bold_prop)
    cell.get_text().set_color(primary_text_color)
    cell.set_edgecolor(to_rgba(primary_text_color, alpha=0.2))
    cell.get_text().set_fontsize(24)

for i, row in enumerate(df_shots.itertuples(index=False)):
    for j, value in enumerate(row):
        # Alt toplam satırı için kontrol
        if i == len(df_shots) - 1:
            if j == 1 or j == 2:  # Sadece xG ve xGOT sütunları
                font_prop = bold_prop
                facecolor = to_rgba('lightgray', alpha=0.125)
                edgecolor = to_rgba(primary_text_color, alpha=0.2)
                text = value
            else:  # Diğer sütunlar için hücreyi boş bırak
                font_prop = prop
                facecolor = 'none'
                edgecolor = 'none'
                text = ''  # Toplam satırındaki diğer sütunları boş bırak
        else:
            font_prop = prop
            facecolor = to_rgba('lightgray', alpha=0)
            edgecolor = to_rgba(primary_text_color, alpha=0.2)
            text = value
        
        # Hücreyi oluştur ve ayarları yap
        cell = table.add_cell(i + 1, j, width=column_width, height=row_height, text=text, loc='center')
        cell.get_text().set_fontproperties(font_prop)
        cell.get_text().set_color(primary_text_color)
        cell.set_facecolor(facecolor)
        cell.set_edgecolor(edgecolor)

# Tabloyu eksene ekleme
ax.add_table(table)

ax.axis('off')
# Görseli göster
st.pyplot(fig)

player_name_replaced = player_name.replace(" ", "_")
match_name_replaced = f"{home_name}_{away_name}"
    
buf = io.BytesIO()
plt.savefig(buf, format="png", dpi = 300, bbox_inches = "tight")
buf.seek(0)
file_name = f"{player_name_replaced}_{match_name_replaced}_Şut_Haritası.png"

st.download_button(
    label="Grafiği İndir",
    data=buf,
    file_name=file_name,
    mime="image/png"
)

# Function to convert image to base64
def img_to_base64(img_path):
    with open(img_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# Signature section
st.sidebar.markdown("---")  # Add a horizontal line to separate your signature from the content

# Load and encode icons
twitter_icon_base64 = img_to_base64("icons/twitter.png")
github_icon_base64 = img_to_base64("icons/github.png")
twitter_icon_white_base64 = img_to_base64("icons/twitter_white.png")  # White version of Twitter icon
github_icon_white_base64 = img_to_base64("icons/github_white.png")  # White version of GitHub icon

# Display the icons with links at the bottom of the sidebar
st.sidebar.markdown(
    f"""
    <style>
    .sidebar {{
        width: auto;
    }}
    .sidebar-content {{
        display: flex;
        flex-direction: column;
        height: 100%;
        margin-top: 10px;
    }}
    .icon-container {{
        display: flex;
        justify-content: center;
        margin-top: auto;
        padding-bottom: 20px;
        gap: 30px;  /* Space between icons */
    }}
    .icon-container img {{
        transition: filter 0.5s cubic-bezier(0.4, 0, 0.2, 1);  /* Smooth and natural easing */
    }}
    .icon-container a:hover img {{
        filter: brightness(0) invert(1);  /* Inverts color to white */
    }}
    </style>
    <div class="sidebar-content">
        <!-- Other sidebar content like selectbox goes here -->
        <div class="icon-container">
            <a href="https://x.com/bariscanyeksin" target="_blank">
                <img src="data:image/png;base64,{twitter_icon_base64}" alt="Twitter" width="30">
            </a>
            <a href="https://github.com/bariscanyeksin" target="_blank">
                <img src="data:image/png;base64,{github_icon_base64}" alt="GitHub" width="30">
            </a>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)
