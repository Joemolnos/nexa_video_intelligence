# Videó Pszichometriai Elemző Webapp

Ez az alkalmazás videók pszichometriai elemzését teszi lehetővé webes felületen, teljesen automatizált folyamattal.

## Funkciók

1. **Videófájl feltöltése** - Válasszon ki és töltsön fel egy videót elemzésre
2. **Automatikus elemzés** - A feltöltött videó automatikus elemzése a háttérben
3. **Valós idejű folyamatkövetés** - Az elemzés aktuális állapotának követése
4. **Interaktív dashboard** - Az elemzési eredmények vizualizációja interaktív grafikonokkal

## Telepítés

### Függőségek telepítése

```bash
pip install -r requirements.txt
```

### Szükséges Python csomagok

- Flask - Web keretrendszer
- Flask-CORS - Cross-Origin Resource Sharing támogatás
- OpenCV - Képfeldolgozás
- NumPy - Numerikus műveletek
- Librosa - Hangelemzés
- SoundFile - Hangfájl kezelés
- MoviePy - Videófájl kezelés

## Futtatás

Az alkalmazás elindításához futtassa az alábbi parancsot:

```bash
python app.py
```

Ezután nyissa meg a böngészőben a következő címet: http://localhost:5000

## Használati útmutató

1. **Videó feltöltése**
   - Kattintson a "Videó feltöltése" gombra
   - Válassza ki a kívánt videófájlt a számítógépéről

2. **Elemzés indítása**
   - A feltöltés után kattintson az "Elemzés indítása" gombra
   - Az elemzés folyamatát nyomon követheti a folyamatjelzőn

3. **Eredmények megtekintése**
   - Az elemzés befejezése után automatikusan megjelennek az eredmények a dashboardon
   - A különböző grafikonok és mutatók segítségével részletesen megvizsgálhatja a videó pszichometriai jellemzőit

4. **Korábbi elemzések megtekintése**
   - A "Korábbi elemzés betöltése" gombbal betöltheti a legutóbbi manuálisan készített elemzés eredményét is

## Technikai háttér

Az alkalmazás Python backend-et használ Flask-kel, ami a videó elemzését végzi, és JavaScript frontendet a vizualizációhoz. Az elemzés több lépésből áll:

1. Videó feldolgozása képkockánként
2. Kép jellemzők elemzése (intenzitás, mozgás, kontraszt, dinamika)
3. Hangjellemzők elemzése (hangerő, energia, hangmagasság, tempó)
4. Színpszichológiai elemzés
5. Pszichológiai paraméterek számítása (öröm, arousal, dominancia, stb.)
6. Adatok összegzése és CSV-be mentése

## Könyvtárszerkezet

- `app.py` - Flask alkalmazás
- `analyze_video_task.py` - Háttérfolyamat a videó elemzéséhez
- `no_gui_analyzer.py` - Videó elemző algoritmusok
- `index.html` - Webes felület
- `dashboard.js` - Dashboard funkciók JavaScript kódja
- `styles.css` - CSS stílusok
- `uploads/` - Feltöltött videók mappája
- `results/` - Elemzési eredmények mappája 

# Tudományos Háttér és Pszichológiai Modellek

Ez a fejezet részletesen bemutatja a rendszer által használt pszichológiai modelleket és számítási módszereket. A VideoElemző egy multidiszciplináris megközelítést alkalmaz, integrálva többféle pszichológiai elméletet a videók komplex értékeléséhez.

## 1. Implementált Pszichológiai Modellek

### 1.1. Mehrabian-Russell PAD Érzelmi Modell

A rendszer elsődleges érzelmi keretrendszere a Mehrabian és Russell által kifejlesztett PAD (Pleasure-Arousal-Dominance) modell, amely három alapvető dimenzióban írja le az érzelmi állapotokat:

- **Pleasure (Öröm)**: A kellemes-kellemetlen spektrumán helyezi el az érzelmi állapotot (0-1 skálán)
- **Arousal (Éberség)**: Az éberség vagy izgalom szintjét jelzi (0-1 skálán)
- **Dominance (Dominancia)**: A kontroll érzésének mértékét mutatja (0-1 skálán)

**Implementáció helye**: `no_gui_analyzer.py`, a `compute_psych_params()` függvényben

**Hivatkozás**: Mehrabian, A., & Russell, J. A. (1974). An approach to environmental psychology. MIT Press.

### 1.2. Berlyne Optimális Arousal Elmélete

Daniel Berlyne esztétikai élményre vonatkozó elmélete szerint az esztétikai élvezet és az arousal (éberség) szint között fordított U-alakú összefüggés van. Ez azt jelenti, hogy se a túl alacsony, se a túl magas arousal nem optimális - a közepes szint vezet a legnagyobb élvezethez.

**Implementáció**: A `compute_psych_params()` függvényben a pleasure számításakor alkalmazzuk:

```python
# Optimális arousal tartomány az örömhöz (0.3-0.8 között jó)
arousal_pleasure_effect = 1 - abs(arousal - 0.55) * 0.8
arousal_pleasure_effect = max(0.3, arousal_pleasure_effect)
```

**Hivatkozás**: Berlyne, D. E. (1971). Aesthetics and psychobiology. Appleton-Century-Crofts.

### 1.3. Csíkszentmihályi Flow Elmélete

Csíkszentmihályi Mihály Flow elmélete szerint az optimális élmény akkor következik be, amikor a kihívás és a készség egyensúlyban van. Ha a kihívás túl nagy a készségekhez képest, szorongás keletkezik; ha túl kicsi, unalom.

**Implementáció**: A Flow állapot számítása a következő módon történik:

```python
# Kognitív kihívás mértéke
challenge = cognitive_load * s_intensity * s_contrast * (0.7 + 0.3 * dynamics)

# Optimális kihívási tartomány (Flow zóna)
skill_match = 1 - abs(challenge - 0.55) * 0.9
skill_match = max(0.4, skill_match)  # Minimum érték biztosítása

# Flow állapot számítása
flow_state = skill_match * min(1, arousal * 1.3) * (color_harmony > 0.3) * (1 - 0.5 * narrative_tension)
```

**Hivatkozás**: Csikszentmihalyi, M. (1990). Flow: The psychology of optimal experience. Harper & Row.

### 1.4. Zillmann Excitation-Transfer Elmélete

Dolf Zillmann modellje szerint az érzelmi állapotok "átvihetők" egyik helyzetről a másikra, és az arousal (izgalom) nem azonnal csökken. Ez magyarázza, hogy a médiában látott feszültség hogyan hat a nézők érzelmi állapotára.

**Implementáció**: Elsősorban a stressz szint számításában és a narratív elemek feldolgozásában alkalmazzuk:

```python
# Negatív arousal számítása (amikor az arousal magas, de nem pozitív kontextusban)
negative_arousal = arousal * clamp(1 - pleasure * 1.3) * clamp(1 - dominance * 0.7)
```

**Hivatkozás**: Zillmann, D. (1971). Excitation transfer in communication-mediated aggressive behavior. Journal of Experimental Social Psychology, 7(4), 419–434.

### 1.5. Lang Limited Capacity Model

Annie Lang korlátozott kapacitás modellje szerint a nézők korlátozott kognitív erőforrásokkal rendelkeznek az információfeldolgozáshoz, és ezeket automatikusan és kontrolláltan osztják el.

**Implementáció**: A kognitív terhelés és a neurális aktivitás számításaiban alkalmazzuk:

```python
visual_complexity = (contrast * 0.4 + intensity * 0.3 + motion * 0.3)
cognitive_load = (visual_complexity * 0.5 + audio_energy * 0.3 + dynamics * 0.2)
neural_activity = (intensity * 0.3 + motion * 0.3 + contrast * 0.2 + audio_energy * 0.2)
```

**Hivatkozás**: Lang, A. (2000). The limited capacity model of mediated message processing. Journal of Communication, 50(1), 46-70.

## 2. Számítási Folyamatok Részletes Dokumentációja

### 2.1. Videó Feldolgozás Folyamata (`analyze_video()`)

A teljes videó elemzési folyamat a következő lépésekből áll:

1. **Videó betöltése**: OpenCV használatával képkockánként dolgozzuk fel a videót
2. **Audio extrakció**: MoviePy és Librosa könyvtárak használatával nyerjük ki a hangjellemzőket
3. **Képkocka-feldolgozás**: Minden képkockán a következő méréseket végezzük:
   - Intenzitás (a kép átlagos fényereje)
   - Mozgás (az egymást követő képkockák különbsége)
   - Kontraszt (éldetektálás Canny módszerrel)
   - Domináns színek azonosítása
4. **Adatok szűrése és simítása**: Mozgóátlagok és ablakozás alkalmazása a zajcsökkentés érdekében
5. **Narratív elemzés**: A feszültség és feloldás mintázatainak felismerése
6. **Pszichológiai paraméterek számítása**: A `compute_psych_params()` függvény meghívása minden képkockára

### 2.2. Arousal (Éberség) Számítása

Az arousal a néző stimulációjának, izgatottságának szintjét jelzi. Összetett számítás, amely több tényezőt vesz figyelembe:

```python
arousal = clamp(0.4 * prev_arousal + 0.6 * (
    0.25 * s_intensity * (1 + 0.3 * s_contrast) +  # Vizuális intenzitás és kontraszt
    0.25 * s_motion * (1 + 0.2 * dynamics) +       # Mozgás és változások
    0.20 * audio_volume * (1 + 0.3 * audio_pitch) + # Hangerő és hangmagasság
    0.15 * audiovisual_synergy +                   # Audio-vizuális interakció
    0.15 * color_arousal))                         # Színek arousal hatása
```

**Magyarázat**:
- **Időbeli folytonosság**: Az előző érték 40%-át megtartja a simaság érdekében
- **Vizuális jellemzők**: Intenzitás és kontraszt hatása (25%)
- **Mozgás hatása**: Dinamikus jelenetek növelik az arousalt (25%)
- **Audio jellemzők**: A hangerő és magasabb hangok serkentő hatása (20%)
- **Audio-vizuális szinergia**: A hang és kép együttes hatása (15%)
- **Színek hatása**: Bizonyos színek (pl. vörös) magasabb arousalt okoznak (15%)

### 2.3. Pleasure (Öröm) Számítása

A pleasure a néző által átélt kellemes érzések mértékét jelzi:

```python
pleasure = clamp(0.3 * prev_pleasure + 0.7 * (
    0.3 * s_intensity * arousal_pleasure_effect +  # Intenzitás × optimális arousal
    0.2 * motion_effect +                          # Optimális mozgás
    0.3 * max(0.45, valence_effect) +              # Szín és hang valencia
    0.1 * max(0.4, color_harmony) +                # Színharmónia
    0.1 * (narrative_payoff if narrative_payoff > 0 else 0.2)))  # Narratív feloldás
```

**Magyarázat**:
- **Optimális arousal hatás**: Berlyne elmélete alapján az arousal-öröm görbe implementálása
- **Mozgás optimuma**: A túl heves és a túl statikus tartalom is csökkenti az örömöt
- **Valencia hatás**: A színek és hangok érzelmi töltete (valence) közvetlenül befolyásolja az örömöt
- **Színharmónia**: A harmonikus színösszeállítás növeli az örömöt
- **Narratív feloldás**: A történetben bekövetkező feszültségoldás örömöt okoz

### 2.4. Dominance (Dominancia) Számítása

A dominancia a néző kontrollérzését, magabiztosságát jelzi a tartalom befogadása során:

```python
dominance = clamp(0.3 * prev_dominance + 0.7 * (
    0.4 * max(0.4, predictability) +              # Előrejelezhetőség
    0.3 * intensity_impact +                      # Intenzív, de strukturált hatások
    0.2 * max(0.4, color_dominance) +             # Színek dominancia hatása
    0.1 * max(0.5, cognitive_effect)))           # Optimális kognitív terhelés
```

**Magyarázat**:
- **Előrejelezhetőség**: Az előrelátható tartalom növeli a kontrollérzetet (40%)
- **Intenzitás hatás**: Az erőteljes, de strukturált ingerek fokozzák a dominanciát (30%)
- **Színek dominanciája**: Bizonyos színek (pl. fekete, vörös) dominanciát sugallnak (20%)
- **Kognitív terhelés**: Az optimális kognitív terhelés növeli a kontrollérzetet (10%)

### 2.5. Boredom (Unalom) Számítása

Az unalom akkor keletkezik, amikor a tartalom nem nyújt elegendő stimulációt, vagy túlságosan monoton:

```python
# Stimuláció hiánya
low_stimulation = clamp(1 - (
    0.5 * max(0.3, s_intensity) + 
    0.3 * max(0.25, s_motion) + 
    0.2 * max(0.25, audio_energy)))

# Monotonitás - alacsony változatosság
monotony = clamp(1 - dynamics * 2.5)
monotony = min(monotony, 0.8)  # Maximum 0.8

# Érzelmi hatás hiánya
low_emotional_impact = clamp(1 - (
    0.7 * pleasure + 
    0.3 * abs(arousal - 0.5) * 1.5))

# Összesített unalom
boredom = clamp(0.2 * low_stimulation + 
                0.3 * monotony +
                0.2 * low_emotional_impact +
                0.3 * (1 - flow_state))

# Maximum korlátozás
boredom = min(boredom, 0.85)
```

**Magyarázat**:
- **Alacsony stimuláció**: A kevés vizuális és audio inger unalmat okoz
- **Monotonitás**: Az alacsony dinamika és változatosság unalomhoz vezet
- **Érzelmi hatás hiánya**: A pleasure és az arousal hiánya növeli az unalmat
- **Flow hiánya**: Ha nem alakul ki flow állapot, az unalom növekszik
- **Maximum korlátozás**: Az unalom értéke sosem haladhatja meg a 0.85-öt

### 2.6. Engagement (Elkötelezettség) Számítása

Az elkötelezettség a néző bevonódásának, figyelmének mértékét jelzi:

```python
# Optimális intenzitás és mozgás hatása
intensity_engagement = s_intensity * (1 - abs(s_intensity - 0.65) * 0.5)
motion_engagement = s_motion * (1 - abs(s_motion - 0.55) * 0.6)

# Elkötelezettség számítása
engagement = clamp(
    0.15 * max(0.3, intensity_engagement) +      # Optimális intenzitás
    0.15 * max(0.3, motion_engagement) +         # Optimális mozgás
    0.10 * max(0.2, s_contrast) +                # Kontraszt (figyelem)
    0.15 * pleasure +                            # Öröm hatása
    0.10 * (1 - abs(arousal - 0.65) * 1.0) +     # Optimális arousal
    0.10 * max(0.3, visual_engagement) +         # Vizuális érdekesség
    0.10 * max(0.2, audio_energy * (1 + 0.3 * dynamics)) + # Hanghatások
    0.15 * max(0.3, flow_state) +                # Flow állapot
    0.05 * (narrative_payoff * 2 + 0.15))        # Narratív hatás

# Minimum érték biztosítása
engagement = max(engagement, 0.25)
```

**Magyarázat**:
- **Optimális intenzitás és mozgás**: Fordított U-alakú összefüggés (15-15%)
- **Kontraszt hatása**: A vizuális kontraszt segíti a figyelmet (10%)
- **Öröm**: A kellemes érzések növelik az elkötelezettséget (15%)
- **Optimális arousal**: A túl alacsony vagy túl magas arousal csökkenti az elkötelezettséget (10%)
- **Vizuális érdekesség**: A vizuálisan érdekes tartalom jobban leköti a figyelmet (10%)
- **Hanghatások**: Az erőteljes hangok és a változatosság növeli az elkötelezettséget (10%)
- **Flow állapot**: A flow közvetlenül növeli az elkötelezettséget (15%)
- **Narratív hatás**: A történet fejlődése és feszültségfeloldása növeli az elkötelezettséget (5%)
- **Minimum garancia**: Az elkötelezettség sosem csökken 0.25 alá

### 2.7. Stress Level (Stressz Szint) Számítása

A stressz szint a néző által átélt negatív feszültség mértékét jelzi:

```python
# Negatív arousal - amikor az arousal kellemetlenséggel és kontrollvesztéssel párosul
negative_arousal = arousal * clamp(1 - pleasure * 1.3) * clamp(1 - dominance * 0.7)

# Kiszámíthatatlan, intenzív hatások
unpredictable_impact = dynamics * s_intensity * clamp(1 - predictability * 1.2)

# Túl magas kognitív terhelés
cognitive_stress = cognitive_load * (cognitive_load > 0.75) * 1.2

# Narratív feszültség hatása
tension_effect = narrative_tension * clamp(1 - narrative_payoff * 0.7)

# Összesített stressz
stress_level = clamp(
    0.30 * negative_arousal +                 # Negatív arousal
    0.20 * unpredictable_impact +             # Kiszámíthatatlanság
    0.15 * cognitive_stress +                 # Túl magas kognitív terhelés
    0.15 * (color_arousal * clamp(1 - color_valence * 1.3)) + # Stresszes színek
    0.20 * tension_effect)                    # Narratív feszültség

# Maximum korlátozás
stress_level = min(stress_level, 0.85)
```

**Magyarázat**:
- **Negatív arousal**: Az arousal akkor okoz stresszt, ha alacsony pleasure és dominance értékekkel párosul (30%)
- **Kiszámíthatatlanság**: A váratlan, erőteljes változások stresszt okoznak (20%)
- **Kognitív túlterhelés**: A túl sok, komplex információ feldolgozása stresszt okoz (15%)
- **Színek hatása**: A magas arousal értékű, negatív valenciájú színek stresszt keltenek (15%)
- **Narratív feszültség**: A történet feszültsége közvetlenül befolyásolja a stressz szintet (20%)
- **Maximum korlátozás**: A stressz sosem haladhatja meg a 0.85-öt

## 3. Színpszichológiai Elemzés

A színpszichológiai elemzést az `analyze_color_psychology()` függvény végzi, amely a következő tudományos kutatásokat használja alapul:

1. **Valdez & Mehrabian (1994)**: A színek hatása az érzelmekre, a PAD modellre vetítve
2. **Elliot & Maier (2014)**: Színek pszichológiai hatása az emberi működésre és teljesítményre
3. **Wilms & Oberfeld (2018)**: Az árnyalat, telítettség és fényerő hatásai az érzelmi reakciókra

**Színtérkép implementáció**:

```python
color_psych_map = {
    'red':      {'color': [1.0, 0.0, 0.0], 'arousal': 0.85, 'valence': 0.45, 'dominance': 0.80},
    'green':    {'color': [0.0, 1.0, 0.0], 'arousal': 0.35, 'valence': 0.65, 'dominance': 0.55},
    'blue':     {'color': [0.0, 0.0, 1.0], 'arousal': 0.25, 'valence': 0.60, 'dominance': 0.40},
    'yellow':   {'color': [1.0, 1.0, 0.0], 'arousal': 0.75, 'valence': 0.80, 'dominance': 0.65},
    'orange':   {'color': [1.0, 0.5, 0.0], 'arousal': 0.80, 'valence': 0.70, 'dominance': 0.60},
    'purple':   {'color': [0.5, 0.0, 0.5], 'arousal': 0.45, 'valence': 0.45, 'dominance': 0.65},
    'pink':     {'color': [1.0, 0.7, 0.7], 'arousal': 0.50, 'valence': 0.75, 'dominance': 0.30},
    'brown':    {'color': [0.6, 0.3, 0.1], 'arousal': 0.25, 'valence': 0.35, 'dominance': 0.65},
    'black':    {'color': [0.0, 0.0, 0.0], 'arousal': 0.40, 'valence': 0.15, 'dominance': 0.85},
    'white':    {'color': [1.0, 1.0, 1.0], 'arousal': 0.15, 'valence': 0.70, 'dominance': 0.40},
    'gray':     {'color': [0.5, 0.5, 0.5], 'arousal': 0.10, 'valence': 0.35, 'dominance': 0.35}
}
```

**Számítási folyamat**:
1. A domináns színek azonosítása K-means klaszterezéssel történik
2. Minden azonosított színhez megtaláljuk a legközelebbi ismert színt a térképből
3. A színek pszichológiai hatását súlyozzuk a képen elfoglalt területük arányával
4. A színharmónia számítása a színek közötti távolságok és esztétikai szabályok alapján történik

## 4. Hangjellemzők Elemzése

A hang elemzése két fő függvénnyel történik:
- `extract_audio_features()`: A teljes hang elemzése és jellemzők kinyerése
- `get_audio_features_at_time()`: A jellemzők lekérése egy adott időpontban

**Főbb hangjellemzők**:
- **Hangerő (Volume)**: Az audio jel RMS (Root Mean Square) értéke
- **Hangfényesség (Brightness)**: Spektrális centroid - a hang "fényességét" jelzi
- **Hangmagasság (Pitch)**: Az észlelt frekvencia, ami a hang magasságát adja
- **Tempó (Tempo)**: A zene vagy beszéd tempója BPM-ben (Beat Per Minute)

**Számítás**:
```python
# Jellemzők kinyerése Librosa könyvtárral
rms_energy = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr, n_fft=frame_length, hop_length=hop_length)[0]
tempo, _ = librosa.beat.beat_track(y=y, sr=sr)

# Audio energia számítása
audio_energy = (volume * 0.6 + brightness * 0.4)
```

## 5. Továbbfejlesztési Javaslatok

A jelenlegi modell jó alapot nyújt, de további finomhangolás szükséges a pontosabb eredmények érdekében.

### 5.1. A Modellek Továbbfejlesztése

#### 5.1.1. Adaptív Baseline
A jelenlegi rendszer minden videót ugyanazokkal a paraméterekkel értékel. Egy adaptív baseline bevezetése, amely figyelembe veszi a műfajt és a célközönséget, jelentősen javíthatná a pontosságot.

**Javaslat**:
```python
def adapt_parameters_by_genre(genre):
    if genre == "action":
        return {"arousal_baseline": 0.7, "movement_weight": 0.4}
    elif genre == "drama":
        return {"arousal_baseline": 0.4, "narrative_weight": 0.6}
    # további műfajok...
```

#### 5.1.2. Személyre Szabott Profilok
Felhasználói visszajelzések alapján személyre szabott profilok létrehozása, amelyek figyelembe veszik az egyéni preferenciákat.

**Javaslat**:
```python
def adjust_for_user_preferences(base_values, user_profile):
    # Alap értékek módosítása a felhasználói preferenciák alapján
    adjusted_values = {}
    for key, value in base_values.items():
        if key in user_profile:
            sensitivity = user_profile[key]
            adjusted_values[key] = value * sensitivity
        else:
            adjusted_values[key] = value
    return adjusted_values
```

#### 5.1.3. Kontextuális Tényezők
A videó kontextusának (pl. narratív struktúra, kulturális referenciák) mélyebb elemzése és beépítése a modellbe.

**Javaslat**:
```python
def analyze_narrative_context(video_data):
    # Narratív fázisok felismerése (bevezetés, kibontakozás, tetőpont, lezárás)
    phases = detect_narrative_phases(video_data)
    
    # Fázis-specifikus elemzés
    phase_contexts = {}
    for phase_name, phase_data in phases.items():
        phase_contexts[phase_name] = {
            "expected_arousal": calculate_expected_arousal(phase_name),
            "narrative_importance": calculate_importance(phase_name, phase_data)
        }
    
    return phase_contexts
```

### 5.2. Technikai Fejlesztési Irányok

#### 5.2.1. Gépi Tanulás Integrálása
A jelenlegi szabály-alapú rendszer kiegészítése gépi tanulási modellekkel, amelyek valós nézői visszajelzésekből tanulnak.

**Javaslat**:
```python
def train_engagement_model(video_features, human_engagement_data):
    # Jellemzők előkészítése
    X = preprocess_features(video_features)
    y = human_engagement_data
    
    # Modell tanítása
    model = RandomForestRegressor()
    model.fit(X, y)
    
    return model

def predict_engagement(model, new_video_features):
    X_new = preprocess_features(new_video_features)
    return model.predict(X_new)
```

#### 5.2.2. Mély Neuronhálók Alkalmazása
Konvolúciós és rekurrens neuronhálók alkalmazása a komplex minták és időbeli összefüggések felismerésére.

**Javaslat**:
```python
def build_temporal_emotion_model():
    model = Sequential([
        LSTM(64, return_sequences=True, input_shape=(None, feature_dim)),
        Dropout(0.2),
        LSTM(32),
        Dense(6, activation='sigmoid')  # 6 érzelmi paraméter előrejelzése
    ])
    model.compile(optimizer='adam', loss='mse')
    return model
```

#### 5.2.3. Multimodális Elemzés Fejlesztése
A vizuális és audiális elemek közötti kapcsolatok mélyebb elemzése, figyelembe véve az időbeli szinkronitást és a szemantikai kongruenciát.

**Javaslat**:
```python
def compute_crossmodal_congruence(visual_features, audio_features):
    # Időbeli összehangoltság mérése
    temporal_alignment = measure_temporal_alignment(visual_features, audio_features)
    
    # Szemantikai kongruencia (pl. vidám zene vidám képekkel)
    semantic_congruence = measure_semantic_match(visual_features, audio_features)
    
    # Arousal kongruencia (pl. izgalmas zene izgalmas képekkel)
    arousal_congruence = correlation(visual_features["arousal"], audio_features["arousal"])
    
    return (temporal_alignment + semantic_congruence + arousal_congruence) / 3
```

### 5.3. Validációs Javaslatok

Az algoritmus pontosságának javításához szükséges validációs módszerek:

#### 5.3.1. A/B Tesztelés
Különböző algoritmus-változatok összehasonlítása valós felhasználói visszajelzések alapján.

#### 5.3.2. Eye-tracking Validáció
Szemkövetés használata annak mérésére, hogy a felhasználók figyelme valóban oda összpontosul-e, ahol az algoritmus magas engagement értéket jelez.

#### 5.3.3. Biometrikus Validáció
Galvánbőr-reakció (GSR), pulzus és más biometrikus adatok gyűjtése a pszichológiai hatások objektív méréséhez.

#### 5.3.4. Nagymintás Felhasználói Tesztelés
Különböző demográfiai csoportokból származó nézők reakcióinak összegyűjtése és összehasonlítása az algoritmus előrejelzéseivel.

## 6. Aktuális Korlátok és Következő Lépések

### 6.1. Ismert Korlátok

1. **Optimizmus-pesszimizmus egyensúly**: A jelenlegi modell még mindig hajlamos pesszimistaként értékelni bizonyos tartalomtípusokat.
2. **Univerzális vs. egyéni értékelés**: A modell jelenleg nem veszi figyelembe az egyéni preferenciákat és kulturális különbségeket.
3. **Szemantikai megértés hiánya**: A tartalom jelentésének mélyebb elemzése még hiányzik (pl. humor, irónia felismerése).
4. **Kontextuális elemzés korlátai**: A nagyobb narratív struktúrák és kontextusok értelmezése korlátozott.

### 6.2. Prioritási Sorrend a Továbbfejlesztéshez

1. **Negatív elfogultság korrekciója**: További minőségellenőrzés és hangolás a túlzottan pesszimista értékelések csökkentésére.
2. **Adaptív baseline bevezetése**: Műfaj-specifikus alap paraméterek beállítása.
3. **Kontextuális analízis fejlesztése**: A narratív struktúra mélyebb elemzését lehetővé tevő algoritmusok implementálása.
4. **Multimodális elemzés bővítése**: Az audió és vizuális elemek közötti kapcsolatok pontosabb modellezése.
5. **Felhasználói visszajelzések integrálása**: A rendszer tanulási képességének fejlesztése valós felhasználói adatok alapján.

## 7. Fejlett Pszichometriai Modellek és Optimalizációs Javaslatok

A jelenlegi pszichológiai modellek megfelelő elméleti alapot biztosítanak, azonban a megvalósításukban több kritikus hiányosság azonosítható. Az alábbiakban részletesen bemutatjuk a problémákat és a javasolt korszerűsítéseket.

### 7.1. Azonosított Problémák a Jelenlegi Implementációban

#### 7.1.1. Túlzott Linearitás az Érzelmi Modellezésben

A PAD dimenziók jelenlegi számítási módszere túlságosan egyszerűsített lineáris kombinációkon alapul, ami nem képes megragadni az érzelmi élmény valódi komplexitását:

```python
# Jelenlegi problémás megközelítés
arousal = clamp(0.4 * prev_arousal + 0.6 * (
    0.25 * s_intensity * (1 + 0.3 * s_contrast) +  
    0.25 * s_motion * (1 + 0.2 * dynamics) +      
    0.20 * audio_volume * (1 + 0.3 * audio_pitch) + 
    0.15 * audiovisual_synergy +                   
    0.15 * color_arousal))
```

Az ilyen lineáris kombinációk több szempontból is problematikusak:
- Nem modellezik az érzelmi ingerek közötti komplex nemlineáris kölcsönhatásokat
- Az alkalmazott súlyozások (0.25, 0.20, stb.) empirikus validáció nélkül kerültek meghatározásra
- Az időbeli dinamika túlságosan leegyszerűsített (egyszerű exponenciális simítás)
- A különböző videó típusok és kontextusok speciális követelményeit nem veszik figyelembe

#### 7.1.2. Hiányos Keresztmodális Integráció

A jelenlegi audiovisual_synergy számítás nem veszi figyelembe a különböző érzékszervi modalitások (hang és kép) közötti szemantikai összhangot és időbeli korrelációt.

#### 7.1.3. Adaptivitás Hiánya

A rendszer minden videóra ugyanazokat a paramétereket és súlyozásokat alkalmazza, figyelmen kívül hagyva a műfaji különbségeket és a kontextuális tényezőket.

### 7.2. Korszerű Pszichometriai Keretrendszer

#### 7.2.1. SCREAM Modell Implementációja

A hagyományos PAD modellt javasoljuk kiegészíteni a modernebb SCREAM (Stimulus, Context, Reactive, Evaluative, Affective Model) megközelítéssel, amely beépíti a kontextuális tényezőket és az idői dinamikát.

```python
def compute_affective_state(visual_data, audio_data, context, history):
    # Inger intenzitás számítása több dimenzió mentén
    stimulus_intensity = compute_stimulus_strength(visual_data, audio_data)
    
    # Kontextuális tényezők elemzése (műfaj, narratív struktúra, célközönség)
    context_factor = analyze_narrative_context(context)
    
    # Közvetlen, reflexszerű érzelmi reakció komponens
    reactive_component = compute_immediate_reaction(stimulus_intensity, history)
    
    # Kognitív értékelési komponens (magasabb szintű feldolgozás)
    evaluative_component = cognitive_appraisal(context, stimulus_intensity)
    
    # Öröm dimenzió: reaktív és értékelő komponensek nemlineáris kombinációja
    pleasure = weighted_nonlinear_combination([
        (reactive_component['pleasure'], 0.4),
        (evaluative_component['pleasure'], 0.6)
    ], curve_type='sigmoid')
    
    # Arousal dimenzió: adaptív transzfer függvény az időbeli dinamika modellezésére
    arousal = adaptive_transfer_function(
        reactive_component['arousal'], 
        history['arousal'],
        decay_rate=compute_adaptive_decay(context)
    )
    
    # Dominancia dimenzió: kontextus által modulált számítás
    dominance = context_modulated_dominance(evaluative_component, context_factor)
    
    return {
        'pleasure': pleasure,
        'arousal': arousal,
        'dominance': dominance,
        'cognitive_appraisal': evaluative_component,
        'reactive_state': reactive_component
    }
```

Ez a modell több előnnyel rendelkezik:
- Elkülöníti az automatikus (reaktív) és tudatos (értékelő) érzelmi feldolgozást
- Figyelembe veszi a kontextust és annak hatását az érzelmi értelmezésre
- Nemlineáris kombinációkat alkalmaz az érzelmi dimenziók számításához
- Explicit módon modellezi az időbeli érzelmi dinamikát

#### 7.2.2. Nemlineáris Modellezés és Adaptív Algoritmusok

A lineáris súlyozás helyett nemlineáris függvényeket és adaptív algoritmusokat javaslunk:

```python
def compute_arousal(visual_features, audio_features, history, video_type):
    # Adaptív súlyozás a videó típusa alapján
    weights = get_adaptive_weights(video_type)
    
    # Keresztmodális integráció nemlineáris modellje
    cross_modal_effect = sigmoid(
        dot_product(visual_features, audio_features) * weights['synergy_factor']
    )
    
    # Szenzoros habituáció modellezése (a hosszú ideig tartó ingerek hatása csökken)
    habituation_factor = compute_habituation(history['exposure_time'])
    
    # Idői dinamika modellezése differenciálegyenlet-rendszerrel
    arousal_change_rate = compute_arousal_dynamics(
        current_stimulus=weighted_features(visual_features, audio_features, weights),
        current_state=history['recent_arousal'],
        habituation_factor=habituation_factor
    )
    
    # Arousal érték számítása
    raw_arousal = history['arousal'] + arousal_change_rate * time_delta
    
    # Nemlineáris határolás (0-1 tartomány)
    arousal = sigmoid_bounded(raw_arousal, bounds=(0, 1))
    
    return arousal
```

A nemlineáris modellezés előnyei:
- Valósághűbb reprezentációja az érzelmi dinamikának
- A szenzoros habituáció figyelembevétele (a hosszantartó ingerek hatása csökken)
- Videó típushoz adaptálódó súlyozás
- Differenciálegyenletek a pontosabb időbeli dinamika érdekében

#### 7.2.3. Fejlett Audioelemzés

A jelenlegi egyszerű hangelemzést kibővített módszerekkel javasoljuk felváltani:

```python
def enhanced_audio_analysis(audio_signal, sample_rate):
    # Alap spektrális jellemzők
    mfcc = librosa.feature.mfcc(y=audio_signal, sr=sample_rate, n_mfcc=20)
    spectral_contrast = librosa.feature.spectral_contrast(y=audio_signal, sr=sample_rate)
    
    # Érzelmi jellemzők hangból
    energy = librosa.feature.rms(y=audio_signal)
    zero_crossing_rate = librosa.feature.zero_crossing_rate(audio_signal)
    
    # Zenei jellemzők
    tempo, beats = librosa.beat.beat_track(y=audio_signal, sr=sample_rate)
    harmonic, percussive = librosa.effects.hpss(audio_signal)
    
    # Audio esemény felismerés (pl. nevetés, kiáltás, zaj)
    audio_events = audio_event_recognizer.classify(audio_signal, sample_rate)
    
    # Érzelmi hangosztályozás beszéd esetén
    speech_segments = extract_speech_segments(audio_signal, sample_rate)
    speech_emotions = speech_emotion_classifier.predict(speech_segments)
    
    return {
        'spectral_features': np.vstack([mfcc, spectral_contrast]),
        'energy_dynamics': energy,
        'rhythmic_features': {
            'tempo': tempo,
            'beat_positions': beats,
            'rhythmic_regularity': compute_rhythm_regularity(beats)
        },
        'harmonic_features': compute_harmonic_features(harmonic),
        'percussive_features': compute_percussive_features(percussive),
        'audio_events': audio_events,
        'speech_emotions': speech_emotions
    }
```

A fejlett audioelemzés előnyei:
- A hang szerkezetének mélyebb elemzése (harmóniai és ritmus jellemzők)
- Beszédfelismerés és beszédalapú érzelemelemzés
- Audio események (nevetés, sírás, kiáltás) felismerése
- A zene érzelmi hatásának precízebb modellezése

#### 7.2.4. Bayesi Paraméteroptimalizálás

A modell paramétereinek empirikus validációja és optimalizálása érdekében Bayesi optimalizációt javaslunk:

```python
def optimize_model_parameters(training_data, validation_data):
    # Paramétertér definiálása
    param_space = {
        'arousal_weights': hp.uniform('aw', 0.1, 0.5),
        'pleasure_decay': hp.uniform('pd', 0.2, 0.8),
        'dominance_factor': hp.uniform('df', 0.3, 0.7),
        'synergy_coefficient': hp.loguniform('sc', -3, 0),
        'motion_impact': hp.normal('mi', 0.25, 0.1)
    }
    
    # Célfüggvény definiálása
    def objective(params):
        model = PsychometricModel(**params)
        model.fit(training_data['features'], training_data['labels'])
        predictions = model.predict(validation_data['features'])
        
        # Többcélú optimalizálás: pontosság és pszichológiai érvényesség
        accuracy = compute_prediction_metrics(predictions, validation_data['labels'])
        psychological_validity = evaluate_psychological_validity(model, validation_criteria)
        
        # Súlyozott kombinált cél (kisebb érték jobb)
        return -(0.7 * accuracy + 0.3 * psychological_validity)
    
    # Bayesi optimalizálás futtatása
    best_params = fmin(
        fn=objective,
        space=param_space,
        algo=tpe.suggest,
        max_evals=100
    )
    
    return best_params
```

A Bayesi optimalizálás előnyei:
- Empirikus adatokra alapozott paraméterbecslés
- Többcélú optimalizálás (pontosság és pszichológiai érvényesség egyidejű maximalizálása)
- Hatékonyabb keresés a paramétertérben a hagyományos rácskereséssel szemben
- A modell bizonytalanságának explicit kezelése

### 7.3. Színpszichológia Továbbfejlesztése

A színpszichológiai elemzés kritikus komponens, amely részletesebb megvalósítást igényel:

```python
def advanced_color_psychology(frame_colors, scene_context, cultural_context="western"):
    # Kulturális különbségek figyelembevétele
    cultural_color_maps = get_cultural_color_map(cultural_context)
    
    # Színek érzelmi hatásának számítása a kontextus függvényében
    color_emotions = []
    for color, percentage in frame_colors:
        # Alapvető színhatás
        base_emotion = map_color_to_emotion(color, cultural_color_maps)
        
        # Kontextuális módosítók
        context_modifier = compute_context_modifiers(scene_context, color)
        
        # Színkombinációs hatások (harmónia, kontraszt, dominancia)
        combination_effect = analyze_color_combinations(frame_colors, color)
        
        # Végső érzelmi hatás
        color_emotion = {
            'base': base_emotion,
            'modified': {
                'arousal': base_emotion['arousal'] * context_modifier['arousal_mod'],
                'valence': base_emotion['valence'] * context_modifier['valence_mod'],
                'dominance': base_emotion['dominance'] * context_modifier['dominance_mod']
            },
            'percentage': percentage,
            'combination_effects': combination_effect
        }
        
        color_emotions.append(color_emotion)
    
    # Komplex színhatás integrálása
    integrated_color_effect = integrate_color_emotions(color_emotions)
    
    # Időbeli színdinamika elemzése
    color_dynamics = analyze_color_dynamics(frame_colors, previous_colors)
    
    return {
        'individual_colors': color_emotions,
        'integrated_effect': integrated_color_effect,
        'color_dynamics': color_dynamics,
        'cultural_context': cultural_context
    }
```

A fejlett színpszichológia előnyei:
- Kulturális különbségek figyelembevétele (színek jelentése kultúránként változik)
- Kontextuális hatások modellezése (ugyanaz a szín más hatást kelthet különböző kontextusban)
- Színkombinációk és harmónia részletesebb elemzése
- Időbeli színdinamika elemzése (színváltások, színdinamika)

### 7.4. Implementációs Útmutató

A javasolt fejlesztések bevezetéséhez a következő lépéseket ajánljuk:

1. **Moduláris Architektúra Kialakítása**
   - A pszichometriai számításokat különálló modulokba szervezni
   - Egyértelmű interfészek definiálása a modulok között

2. **Adatgyűjtés és Validáció**
   - Reprezentatív videó adatbázis létrehozása különböző műfajokból
   - Annotált adatkészlet készítése a gépi tanulási modellek betanításához
   - Felhasználói visszajelzések gyűjtése a szubjektív érzelmi hatásokról

3. **Fokozatos Bevezetés**
   - Először az alapvető nemlineáris modellek bevezetése
   - A keresztmodális integráció fejlesztése
   - Végül a teljes SCREAM modell implementálása

4. **Validációs Protokoll Kidolgozása**
   - A/B tesztelési módszertan
   - Objektív és szubjektív metrikák definiálása
   - A predikciók összevetése biometrikus adatokkal (GSR, EEG, pupilladilatáció)

### 7.5. Várható Előnyök

A javasolt fejlesztések implementálásával a következő előnyök várhatók:

1. **Pontosabb Érzelmi Predikciók**
   - Különösen a komplex, több modalitást kombináló videók esetén
   - A kulturális és kontextuális tényezők figyelembevételével

2. **Jobb Generalizálás**
   - Azonos modell alkalmazhatósága különböző műfajú videókra
   - Kulturális különbségek kezelése

3. **Tudományos Megalapozottság**
   - Empirikusan validált paraméterek
   - A modern affektív tudomány eredményeinek integrálása

4. **Felhasználói Relevancia**
   - Személyre szabás lehetősége
   - Praktikus, kontextusba helyezett pszichológiai elemzés

A fenti fejlesztések integrálásával a VideoElemző rendszer jelentősen meghaladhatja a jelenlegi, lineáris modelleken alapuló megközelítések korlátait, és valóban state-of-the-art pszichometriai elemzési képességeket nyújthat.

---

© 2023 VideoElemző Rendszer Technikai Dokumentáció 