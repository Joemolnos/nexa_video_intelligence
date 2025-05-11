document.addEventListener('DOMContentLoaded', function() {
    // AOS (Animate On Scroll) inicializálása
    AOS.init({
        duration: 800,
        easing: 'ease-out',
        once: true
    });
    
    // DOM elemek kiválasztása
    const loadDataBtn = document.getElementById('loadDataBtn');
    const statsQuickview = document.getElementById('statsQuickview');
    const dashboardContainer = document.querySelector('.dashboard-container');
    const infoBtn = document.getElementById('infoBtn');
    const infoPanel = document.getElementById('infoPanel');
    const closeInfoBtn = document.getElementById('closeInfoBtn');
    
    // Új elemek a fájlfeltöltéshez és elemzéshez
    const videoFileInput = document.getElementById('videoFileInput');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const uploadInfo = document.getElementById('uploadInfo');
    const uploadedFileName = document.getElementById('uploadedFileName');
    const uploadedFileSize = document.getElementById('uploadedFileSize');
    const analysisProgress = document.getElementById('analysisProgress');
    const progressBar = document.getElementById('progressBar');
    const progressPercent = document.getElementById('progressPercent');
    const progressStatus = document.getElementById('progressStatus');
    const progressMessage = document.getElementById('progressMessage');
    const errorMessage = document.getElementById('errorMessage');
    
    // Grafikonok változói
    let charts = {};
    let selectedFile = null;
    let currentTaskId = null;
    let statusCheckInterval = null;
    
    // Színpszichológiai indikátorok
    const colorIndicators = {
        arousal: document.getElementById('colorArousalIndicator'),
        valence: document.getElementById('colorValenceIndicator'),
        dominance: document.getElementById('colorDominanceIndicator'),
        harmony: document.getElementById('colorHarmonyIndicator')
    };
    
    // Info panel kezelése
    if (infoBtn) {
    infoBtn.addEventListener('click', function() {
        infoPanel.classList.remove('opacity-0', 'translate-y-20');
        infoBtn.classList.add('hidden');
    });
    }
    
    if (closeInfoBtn) {
    closeInfoBtn.addEventListener('click', function() {
        infoPanel.classList.add('opacity-0', 'translate-y-20');
        setTimeout(() => {
            infoBtn.classList.remove('hidden');
        }, 500);
    });
    }
    
    // Fájl feltöltés kezelése
    videoFileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            selectedFile = file;
            analyzeBtn.disabled = false;
            
            // Fájl információk megjelenítése
            uploadedFileName.textContent = file.name;
            uploadedFileSize.textContent = formatFileSize(file.size);
            uploadInfo.classList.remove('hidden');
            
            // Hibaüzenet elrejtése, ha volt
            errorMessage.classList.add('hidden');
        }
    });
    
    // Fájlméret formázása
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    // Elemzés indítása
    analyzeBtn.addEventListener('click', function() {
        if (!selectedFile) {
            displayError('Kérjük, válasszon ki egy videófájlt az elemzéshez!');
            return;
        }
        
        // Elemzés indítása
        startAnalysis(selectedFile);
    });
    
    // Elemzés indítása
    function startAnalysis(file) {
        // Elemzés előkészítése
        analyzeBtn.disabled = true;
        analysisProgress.classList.remove('hidden');
        errorMessage.classList.add('hidden'); // Minden korábbi hiba elrejtése
        updateProgress(0, 'Előkészítés', 'Fájl feltöltése...');
        
        // FormData létrehozása a fájl feltöltéséhez
        const formData = new FormData();
        formData.append('video', file);
        
        console.log("Videó feltöltés indítása...");
        
        // Feltöltés indítása
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Hiba történt a feltöltés során.');
            }
            return response.json();
        })
        .then(data => {
            // Sikeres feltöltés esetén indítjuk az elemzés követését
            console.log("Feltöltés sikeres, elemzés indítása:", data);
            currentTaskId = data.task_id;
            
            // Indítsuk azonnal az állapot ellenőrzést, hogy ne ragadjon be 5%-nál
            updateProgress(3, 'Feltöltve', 'Videó elemzés indítása...');
            
            // Állapot ellenőrzés indítása
            startStatusCheck(currentTaskId);
        })
        .catch(error => {
            console.error("Feltöltési hiba:", error);
            displayError(`Feltöltési hiba: ${error.message}`);
            analyzeBtn.disabled = false;
            analysisProgress.classList.add('hidden');
        });
    }
    
    // Állapot ellenőrzése
    function startStatusCheck(taskId) {
        // Ha már fut egy időzítő, leállítjuk
        if (statusCheckInterval) {
            clearInterval(statusCheckInterval);
        }
        
        // Rövidebb várakozási idő, gyakoribb frissítéshez
        const intervalTime = 700; // Gyorsabb frissítés
        let failedAttempts = 0;
        const maxFailedAttempts = 12; // Több próbálkozás
        let lastProgress = 0;
        let stuckCounter = 0;
        const maxStuckCount = 10; // Rövidebb idő a beavatkozáshoz
        let lastStatusUpdateTime = Date.now();
        let hasBecomeStuck = false;
        
        // Hangelemzési szakasz különleges kezelése
        let isInCriticalPhase = false;
        let criticalPhaseStartTime = 0;
        const criticalPhaseTimeout = 30000; // 30 másodperc a hangelemzéshez maximum
        
        console.log(`Státusz ellenőrzés indítása: ${taskId}`);
        
        // Indítási animáció a haladásjelzőn
        animateProgressStart();
        
        // Állapot ellenőrzése periodikusan
        statusCheckInterval = setInterval(() => {
            // Az aktuális idő
            const now = Date.now();
            
            // Időtúllépés ellenőrzése
            const fetchTimeout = 3000; // 3 másodperc timeout - gyorsabb visszajelzés
            
            // AbortController az időtúllépés kezeléséhez
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), fetchTimeout);
            
            // Állapot lekérése cache-mentesen
            fetch(`/status/${taskId}?nocache=${Date.now()}`, {
                signal: controller.signal,
                headers: { 
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache',
                    'Expires': '0'
                }
            })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP hiba: ${response.status}`);
                    }
                    return response.json();
                })
                .then(status => {
                    // Töröljük a timeout időzítőt és a sikertelen próbálkozások számlálóját
                    clearTimeout(timeoutId);
                    failedAttempts = 0;
                    
                    console.log("Státusz válasz:", status);
                    
                    // Frissítsük az utolsó állapotfrissítés idejét
                    lastStatusUpdateTime = now;
                    
                    if (status.status === 'completed') {
                        // Elemzés kész
                        clearInterval(statusCheckInterval);
                        updateProgress(100, 'Kész', 'Az elemzés sikeresen befejeződött!');
                        stopProgressAnimation();
                        
                        // Eredmények betöltése
                        loadAnalysisResults(status.summary_csv);
                    }
                    else if (status.status === 'error') {
                        // Hiba történt
                        clearInterval(statusCheckInterval);
                        stopProgressAnimation();
                        
                        let errorMsg = status.message || 'Ismeretlen hiba történt';
                        displayError(`Elemzési hiba: ${errorMsg}`);
                        console.error('Elemzési hiba:', status);
                        
                        // Újra engedélyezzük az elemzés gombot
                        analyzeBtn.disabled = false;
                        
                        // Hibaüzenet részletes megjelenítése
                        errorMessage.innerHTML = `
                            <div class="p-3 bg-red-900 bg-opacity-50 rounded-lg">
                                <h4 class="font-bold text-white mb-2">Elemzési hiba történt:</h4>
                                <p class="text-sm text-red-200 mb-2">${errorMsg}</p>
                                <p class="text-xs text-red-300">Kérjük, próbáljon meg egy másik videófájlt, vagy ellenőrizze a szerver hibanaplóját további részletekért.</p>
                            </div>
                        `;
                    } 
                    else if (status.status === 'processing') {
                        // Folyamatban
                        let progress = status.progress || 0;
                        
                        // Ellenőrizzük a kritikus szakaszokat
                        if (progress >= 4 && progress <= 12) {
                            // A hangelemzés kritikus szakaszában vagyunk - 5% körül
                            if (!isInCriticalPhase) {
                                isInCriticalPhase = true;
                                criticalPhaseStartTime = now;
                                console.log("Belépés a kritikus szakaszba:", progress);
                                // Azonnali visszajelzés a felhasználónak
                                animateProgressInCriticalPhase(progress);
                            }
                            
                            // Ellenőrizzük, nem telt-e el túl sok idő a kritikus szakaszban
                            const timeInCriticalPhase = now - criticalPhaseStartTime;
                            
                            // Gyakoribb animáció a kritikus szakaszban
                            if (timeInCriticalPhase % 1000 < 200) {
                                // Minden másodpercben frissítjük az animációt
                                animateProgressInCriticalPhase(progress);
                            }
                            
                            if (timeInCriticalPhase > criticalPhaseTimeout) {
                                // Túl sok idő telt el a kritikus szakaszban, manuálisan léptetjük tovább
                                progress = 15; // Ugrás 15%-ra
                                console.log("Kritikus szakasz időtúllépés, ugrás:", progress);
                            }
                        } else if (isInCriticalPhase) {
                            // Kiléptünk a kritikus szakaszból
                            isInCriticalPhase = false;
                            console.log("Kilépés a kritikus szakaszból:", progress);
                            stopProgressAnimation();
                        }
                        
                        // Ellenőrizzük, hogy beragadt-e az állapot
                        if (progress === lastProgress && !isInCriticalPhase) {
                            stuckCounter++;
                            console.log(`Azonos haladás: ${progress}%, counter: ${stuckCounter} / ${maxStuckCount}`);
                            
                            if (stuckCounter >= maxStuckCount) {
                                // Manuális növelés, hogy láthatóan haladjon
                                if (!hasBecomeStuck) {
                                    hasBecomeStuck = true;
                                    console.log("Haladás beragadt, manuális animálás");
                                }
                                
                                // Manuális haladás animálása
                                animateProgressWhenStuck(progress);
                            }
                        } else {
                            // Haladás változott, visszaállítjuk a számlálót
                            stuckCounter = 0;
                            hasBecomeStuck = false;
                            stopProgressAnimation();
                        }
                        
                        // Ügyelünk arra, hogy a haladás mindig növekedjen vagy ugyanaz maradjon
                        let progressBarValue = progress;
                        const progressBarElement = document.getElementById("progressBar");
                        if (progressBarElement) {
                            const currentWidth = progressBarElement.style.width || "0%";
                            const currentValue = parseInt(currentWidth) || 0;
                            if (currentValue > progressBarValue) {
                                console.log(`Haladás nem csökkentése: ${currentValue}% > ${progressBarValue}%`);
                                progressBarValue = currentValue;
                            }
                        }
                        
                        // Frissítjük a haladásjelzőt
                        updateProgress(progressBarValue, 'Feldolgozás', status.message || 'Elemzés folyamatban...');
                        
                        // Frissítjük az utolsó haladás értékét
                        lastProgress = progress;
                    }
                })
                .catch(error => {
                    // Töröljük a timeout időzítőt
                    clearTimeout(timeoutId);
                    
                    // Növeljük a sikertelen próbálkozások számát
                    failedAttempts++;
                    
                    console.warn(`Állapot lekérdezési hiba (${failedAttempts}/${maxFailedAttempts})`, error);
                    
                    // Ellenőrizzük, hogy túl sok idő telt-e el a legutóbbi sikeres válasz óta
                    const timeWithoutUpdate = now - lastStatusUpdateTime;
                    const maxTimeWithoutUpdate = 15000; // 15 másodperc
                    
                    if (timeWithoutUpdate > maxTimeWithoutUpdate) {
                        // Túl sok idő telt el frissítés nélkül, animáljuk a haladást
                        if (!hasBecomeStuck) {
                            hasBecomeStuck = true;
                            console.log("Túl sok idő válasz nélkül, manuális animálás");
                        }
                        
                        // Manuális haladás animálása
                        animateProgressWhenStuck(lastProgress);
                    }
                    
                    // Csak akkor jelezzük a hibát, ha elértük a maximum próbálkozást
                    if (failedAttempts >= maxFailedAttempts) {
                        clearInterval(statusCheckInterval);
                        stopProgressAnimation();
                        
                        // Részletesebb hibaüzenet
                        let errorDetail = '';
                        if (error.name === 'AbortError') {
                            errorDetail = 'A lekérdezés időtúllépés miatt megszakadt.';
                        } else {
                            errorDetail = error.message || 'Ismeretlen hálózati hiba';
                        }
                        
                        displayError(`Nem sikerült lekérdezni az elemzés állapotát: ${errorDetail}`);
                        
                        // Újra engedélyezzük az elemzés gombot
                        analyzeBtn.disabled = false;
                    } else {
                        // Változtassuk a státusz üzenetet, hogy a felhasználó lássa, hogy még dolgozunk rajta
                        updateProgress(null, 'Kapcsolat hiba', `Kapcsolódási probléma, újrapróbálkozás... (${failedAttempts}/${maxFailedAttempts})`);
                    }
                });
        }, intervalTime);
    }
    
    // Haladás animáció indítása
    function animateProgressStart() {
        // A kezdeti animációs osztály hozzáadása
        const progressBar = document.getElementById("progressBar");
        if (progressBar) {
            progressBar.classList.add("progress-pulse");
        }
    }
    
    // Haladás animáció a kritikus szakaszban
    function animateProgressInCriticalPhase(baseProgress) {
        const progressBar = document.getElementById("progressBar");
        if (progressBar) {
            // Dinamikusabb animáció, hogy a felhasználó lássa a haladást
            const randomIncrement = Math.random() * 1.5; // 0-1.5% véletlenszerű növekedés
            const effectiveProgress = Math.min(Math.max(baseProgress + randomIncrement, 5), 12);
            
            // Változó üzenet, hogy látszódjon a frissítés
            const time = new Date().toLocaleTimeString();
            const messages = [
                `Hangsáv kinyerése és elemzése (${time})...`,
                `Audió stream feldolgozása (${time})...`,
                `Hangelemzés folyamatban (${time})...`
            ];
            const message = messages[Math.floor(Math.random() * messages.length)];
            
            updateProgress(effectiveProgress, 'Hangelemzés', message);
            
            // Erősebb pulzáló animáció
            progressBar.classList.add("progress-pulse");
        }
    }
    
    // Haladás animáció beragadás esetén
    function animateProgressWhenStuck(baseProgress) {
        const progressBar = document.getElementById("progressBar");
        if (progressBar) {
            // Növeljük az alapértéket, hogy a felhasználó lássa a haladást
            const effectiveProgress = baseProgress + 2;
            updateProgress(effectiveProgress, 'Feldolgozás', 'Az elemzés folyamatban van, kérem várjon türelemmel...');
            
            // Animációs osztály hozzáadása
            progressBar.classList.add("progress-pulse");
        }
    }
    
    // Haladás animáció leállítása
    function stopProgressAnimation() {
        const progressBar = document.getElementById("progressBar");
        if (progressBar) {
            progressBar.classList.remove("progress-pulse");
        }
    }
    
    // Haladás frissítése
    function updateProgress(percent, status, message) {
        progressBar.style.width = `${percent}%`;
        progressPercent.textContent = `${percent}%`;
        progressStatus.textContent = status;
        progressMessage.textContent = message;
    }
    
    // Elemzési eredmények betöltése
    function loadAnalysisResults(summaryFile) {
        // CSV adat lekérése
        fetch(`/results/${summaryFile}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP hiba: ${response.status}`);
                }
                return response.text();
            })
            .then(csvData => {
                processCsvData(csvData);
            })
            .catch(error => {
                displayError(`Eredmények betöltési hiba: ${error.message}`);
            });
    }
    
    // Korábbi elemzések adatainak betöltése
    loadDataBtn.addEventListener('click', function() {
        loadData();
        loadDataBtn.disabled = true;
        loadDataBtn.innerHTML = '<span class="flex items-center"><svg class="animate-spin -ml-1 mr-2 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>Adatok feldolgozása...</span>';
    });
    
    // CSV adatok betöltése és feldolgozása
    function loadData() {
        console.log('CSV betöltése...');
        
        // Próbáljuk meg XMLHttpRequest-tel
        const xhr = new XMLHttpRequest();
        xhr.open('GET', 'video_analysis_summary.csv', true);
        xhr.onload = function() {
            if (xhr.status === 200) {
                try {
                    processCsvData(xhr.responseText);
                } catch (error) {
                    displayError(`CSV feldolgozási hiba: ${error.message}`);
                }
            } else {
                displayError(`Hiba történt az adatok betöltése során (XMLHttpRequest): ${xhr.status} ${xhr.statusText}`);
            }
        };
        xhr.onerror = function() {
            console.error('XMLHttpRequest hiba:', xhr);
            displayError('Hálózati hiba történt az adatok betöltése során. Ellenőrizze, hogy a video_analysis_summary.csv fájl létezik-e és elérhető-e, és hogy webszerverről fut-e az oldal (pl. python -m http.server).');
        };
        xhr.send();
    }
        
        // CSV adatok feldolgozása
        function processCsvData(csvData) {
            // CSV adatok feldolgozása Papa Parse segítségével
            Papa.parse(csvData, {
                header: true,
                encoding: "UTF-8",  // Explicitly set UTF-8 encoding
                skipEmptyLines: true,
                complete: function(results) {
                    try {
                        console.log("CSV feldolgozás sikeres:", results);
                        const data = processData(results.data);
                        displayQuickStats(data);
                        createCharts(data);
                        updateColorPsychology(data);
                        
                        // Dashboard megjelenítése
                        dashboardContainer.classList.add('opacity-100');
                    
                        // Ha az elemzésből jövünk, elrejtjük a progress-t
                        analysisProgress.classList.add('hidden');
                        
                        // Betöltő gomb frissítése
                        loadDataBtn.innerHTML = '<span class="flex items-center"><svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>Adatok betöltve</span>';
                        loadDataBtn.classList.remove('bg-purple-600', 'hover:bg-purple-700');
                        loadDataBtn.classList.add('bg-green-600', 'hover:bg-green-700');
                        loadDataBtn.disabled = false;
                    } catch (error) {
                        console.error("Hiba az adatok feldolgozása során:", error);
                        displayError(`Adatfeldolgozási hiba: ${error.message}`);
                    }
                },
                error: function(error) {
                    console.error('Papa Parse hiba:', error);
                    displayError(`CSV feldolgozási hiba: ${error.message}`);
                }
            });
        }
        
        function displayError(message) {
        console.error('Hiba:', message);
        errorMessage.innerHTML = `<div class="p-2 bg-red-900 bg-opacity-50 rounded">${message}</div>`;
        errorMessage.classList.remove('hidden');
        
        // Ha elemzés közben történt a hiba, újra engedélyezzük az elemzés gombot
        analyzeBtn.disabled = selectedFile ? false : true;
        
        // Betöltő gomb visszaállítása
            loadDataBtn.disabled = false;
        loadDataBtn.innerHTML = '<span class="flex items-center"><svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path></svg>Adatok betöltése</span>';
    }
    
    // Adatok feldolgozása a grafikonokhoz
    function processData(rawData) {
        const processedData = {};
        
        rawData.forEach(row => {
            if (row.parameter && row.average) {
                processedData[row.parameter] = {
                    average: parseFloat(row.average),
                    min: parseFloat(row.min),
                    max: parseFloat(row.max),
                    std_dev: parseFloat(row.std_dev)
                };
            }
        });
        
        return processedData;
    }
    
    // Gyors statisztikák megjelenítése
    function displayQuickStats(data) {
        statsQuickview.innerHTML = '';
        statsQuickview.classList.remove('hidden');
        
        const keyStats = [
            { key: 'pleasure', label: 'Öröm', icon: '😊' },
            { key: 'engagement', label: 'Elkötelezettség', icon: '🔍' },
            { key: 'stress_level', label: 'Stressz', icon: '😰' },
            { key: 'cognitive_load', label: 'Kog. Terhelés', icon: '🧠' }
        ];
        
        keyStats.forEach((stat, index) => {
            if (data[stat.key]) {
                const statValue = (data[stat.key].average * 100).toFixed(0);
                const statElement = document.createElement('div');
                statElement.className = 'stat-card';
                statElement.innerHTML = `
                    <div class="stat-icon">${stat.icon}</div>
                    <div class="stat-value">${statValue}%</div>
                    <div class="stat-label">${stat.label}</div>
                `;
                statsQuickview.appendChild(statElement);
                
                // Késleltetett animáció
                setTimeout(() => {
                    statElement.classList.add('fade-in-up');
                }, 100 * index);
            }
        });
    }
    
    // Színpszichológiai indikátorok frissítése
    function updateColorPsychology(data) {
        const colorParams = {
            'color_arousal': 'arousal',
            'color_valence': 'valence',
            'color_dominance': 'dominance',
            'color_harmony': 'harmony'
        };
        
        for (const [dataKey, indicatorKey] of Object.entries(colorParams)) {
            if (data[dataKey] && colorIndicators[indicatorKey]) {
                const value = data[dataKey].average;
                colorIndicators[indicatorKey].style.left = `${value * 100}%`;
                
                // Tudományos alapú színskálák a különböző értékekhez
                let color;
                if (indicatorKey === 'arousal') {
                    // Arousal: kék (alacsony) -> piros (magas)
                    color = `hsl(${Math.floor(240 - value * 240)}, 85%, 65%)`;
                } else if (indicatorKey === 'valence') {
                    // Valence: piros (negatív) -> zöld (pozitív)
                    color = `hsl(${Math.floor(value * 120)}, 85%, 65%)`;
                } else if (indicatorKey === 'dominance') {
                    // Dominancia: lila (alacsony) -> narancs (magas)
                    color = `hsl(${Math.floor(280 + value * 60)}, 85%, 65%)`;
                } else {
                    // Harmónia: sárga (diszharmónikus) -> türkiz (harmonikus)
                    color = `hsl(${Math.floor(value * 60 + 160)}, 85%, 65%)`;
                }
                
                colorIndicators[indicatorKey].style.background = color;
                
                // Tudoményos alapú értelmezés hozzáadása
                const parentContainer = colorIndicators[indicatorKey].parentElement.parentElement;
                const descElement = parentContainer.querySelector('p.text-sm');
                
                if (descElement) {
                    let interpretation = "";
                    
                    if (indicatorKey === 'arousal') {
                        if (value < 0.3) interpretation = "Nyugtató, alacsony aktivációs hatás";
                        else if (value < 0.6) interpretation = "Mérsékelt stimuláció";
                        else interpretation = "Erősen stimuláló, figyelemfelkeltő hatás";
                    } 
                    else if (indicatorKey === 'valence') {
                        if (value < 0.3) interpretation = "Negatív érzelmi hatás";
                        else if (value < 0.6) interpretation = "Semleges érzelmi hatás";
                        else interpretation = "Pozitív, kellemes érzelmi hatás";
                    }
                    else if (indicatorKey === 'dominance') {
                        if (value < 0.3) interpretation = "Alárendeltség, gyengeség érzete";
                        else if (value < 0.6) interpretation = "Kiegyensúlyozott erőviszonyok";
                        else interpretation = "Erős dominancia, kontroll érzete";
                    }
                    else { // harmony
                        if (value < 0.3) interpretation = "Diszharmónikus, feszültségkeltő";
                        else if (value < 0.6) interpretation = "Mérsékelt harmónia";
                        else interpretation = "Harmonikus, kellemes kapcsolódás";
                    }
                    
                    // Eredeti leírás megtartása, interpretáció hozzáadása
                    const originalDesc = descElement.getAttribute('data-original-desc') || descElement.textContent;
                    if (!descElement.getAttribute('data-original-desc')) {
                        descElement.setAttribute('data-original-desc', originalDesc);
                    }
                    
                    descElement.innerHTML = `${originalDesc}<br><strong>Eredmény (${Math.round(value * 100)}%):</strong> ${interpretation}`;
                }
            }
        }
    }
    
    // Pszichológiai paraméterek tudományos értelmezése
    function interpretPsychParams(chartData) {
        const interpretations = document.getElementById('psychInterpretations');
        if (!interpretations) return;
        
        // Átlagértékek kiszámítása
        const avgPleasure = calculateAverage(chartData.pleasure);
        const avgArousal = calculateAverage(chartData.arousal);
        const avgEngagement = calculateAverage(chartData.engagement);
        const avgBoredom = calculateAverage(chartData.boredom);
        const avgStress = calculateAverage(chartData.stress);
        
        // PAD modell értelmezés
        let emotionalImpact = "";
        
        if (avgPleasure > 0.7 && avgArousal > 0.6) {
            emotionalImpact = "Izgatottság, lelkesedés, örömteli élénkség";
        } else if (avgPleasure > 0.7 && avgArousal < 0.4) {
            emotionalImpact = "Nyugodt elégedettség, békés öröm";
        } else if (avgPleasure < 0.3 && avgArousal > 0.6) {
            emotionalImpact = "Szorongás, nyugtalanság, feszültség";
        } else if (avgPleasure < 0.3 && avgArousal < 0.4) {
            emotionalImpact = "Lehangoltság, unalom, apátia";
        } else {
            emotionalImpact = "Mérsékelt érzelmi hatás";
        }
        
        // Flow elmélet alapú értelmezés
        let flowState = "";
        if (avgEngagement > 0.7 && avgBoredom < 0.3 && avgStress < 0.4) {
            flowState = "Optimális flow állapot - a néző teljesen bevonódik";
        } else if (avgEngagement < 0.4 && avgBoredom > 0.6) {
            flowState = "Unalom - túl kevés stimuláció vagy kihívás";
        } else if (avgEngagement < 0.4 && avgStress > 0.6) {
            flowState = "Szorongás - túl intenzív vagy fenyegető tartalom";
        } else {
            flowState = "Mérsékelt bevonódás";
        }
        
        // Eredmények megjelenítése
        interpretations.innerHTML = `
            <div class="p-4 dashboard-panel mt-4">
                <h3 class="text-xl font-semibold mb-3">Tudományos értelmezés</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <h4 class="font-medium text-lg">Érzelmi hatás (PAD modell)</h4>
                        <p class="text-gray-300">${emotionalImpact}</p>
                        <div class="flex items-center mt-2">
                            <span class="text-sm">Öröm: ${Math.round(avgPleasure * 100)}%</span>
                            <span class="mx-2">|</span>
                            <span class="text-sm">Éberség: ${Math.round(avgArousal * 100)}%</span>
                        </div>
                    </div>
                    <div>
                        <h4 class="font-medium text-lg">Nézői bevonódás (Flow elmélet)</h4>
                        <p class="text-gray-300">${flowState}</p>
                        <div class="flex items-center mt-2">
                            <span class="text-sm">Elkötelezettség: ${Math.round(avgEngagement * 100)}%</span>
                            <span class="mx-2">|</span>
                            <span class="text-sm">Unalom: ${Math.round(avgBoredom * 100)}%</span>
                            <span class="mx-2">|</span>
                            <span class="text-sm">Stressz: ${Math.round(avgStress * 100)}%</span>
                        </div>
                    </div>
                </div>
                <div class="mt-3 text-sm text-gray-400">
                    <p>A fenti értelmezések pszichológiai kutatásokon alapulnak, beleértve Mehrabian-Russell PAD modelljét és Csíkszentmihályi Flow elméletét.</p>
                </div>
            </div>
        `;
    }
    
    // Átlag számítása egy adatsorozatból
    function calculateAverage(dataArray) {
        if (!dataArray || dataArray.length === 0) return 0;
        const sum = dataArray.reduce((a, b) => a + b, 0);
        return sum / dataArray.length;
    }
    
    // Pszichológiai grafikon frissítése
    function updateChartWithData(data) {
        const ctx = document.getElementById('psychChart').getContext('2d');
        
        if (!ctx) {
            console.error("Canvas kontextus nem található");
            return;
        }
        
        // Leszűrjük az adatokat, hogy csak minden n-edik pontot mutassunk
        // a grafikon átláthatósága érdekében
        const samplingRate = Math.max(1, Math.floor(data.timePoints.length / 20));
        const filteredTimePoints = [];
        const filteredPleasure = [];
        const filteredArousal = [];
        const filteredBoredom = [];
        const filteredEngagement = [];
        const filteredStress = [];
        
        for (let i = 0; i < data.timePoints.length; i += samplingRate) {
            filteredTimePoints.push(data.timePoints[i]);
            filteredPleasure.push(data.pleasure[i]);
            filteredArousal.push(data.arousal[i]);
            filteredBoredom.push(data.boredom[i]);
            filteredEngagement.push(data.engagement[i]);
            filteredStress.push(data.stress[i]);
        }
        
        // Ha létezik már chart, akkor azt frissítjük
        if (window.psychChart) {
            window.psychChart.data.labels = filteredTimePoints;
            window.psychChart.data.datasets[0].data = filteredPleasure;
            window.psychChart.data.datasets[1].data = filteredStress;
            window.psychChart.data.datasets[2].data = filteredBoredom;
            window.psychChart.data.datasets[3].data = filteredEngagement;
            
            // Narratív feszültség hozzáadása új adatsorként, ha elérhető
            if (data.narrative_tension && data.narrative_tension.length > 0) {
                const filteredTension = [];
                for (let i = 0; i < data.narrative_tension.length; i += samplingRate) {
                    filteredTension.push(data.narrative_tension[i]);
                }
                
                if (window.psychChart.data.datasets.length < 5) {
                    window.psychChart.data.datasets.push({
                        label: 'Narratív Feszültség',
                        data: filteredTension,
                        borderColor: 'rgba(255, 193, 7, 1)',
                        backgroundColor: 'rgba(255, 193, 7, 0.1)',
                        borderWidth: 2,
                        pointRadius: 0,
                        tension: 0.4
                    });
                } else {
                    window.psychChart.data.datasets[4].data = filteredTension;
                }
            }
            
            window.psychChart.update();
        } else {
            const datasets = [
                {
                    label: 'Öröm',
                    data: filteredPleasure,
                    borderColor: 'rgba(244, 114, 182, 1)',
                    backgroundColor: 'rgba(244, 114, 182, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    pointRadius: 3,
                    pointHoverRadius: 6,
                    fill: false
                },
                {
                    label: 'Stressz',
                    data: filteredStress,
                    borderColor: 'rgba(249, 115, 22, 1)',
                    backgroundColor: 'rgba(249, 115, 22, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    pointRadius: 3,
                    pointHoverRadius: 6,
                    fill: false
                },
                {
                    label: 'Unalom',
                    data: filteredBoredom,
                    borderColor: 'rgba(20, 184, 166, 1)',
                    backgroundColor: 'rgba(20, 184, 166, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    pointRadius: 3,
                    pointHoverRadius: 6,
                    fill: false
                },
                {
                    label: 'Elkötelezettség',
                    data: filteredEngagement,
                    borderColor: 'rgba(168, 85, 247, 1)',
                    backgroundColor: 'rgba(168, 85, 247, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    pointRadius: 3,
                    pointHoverRadius: 6,
                    fill: false
                }
            ];
            
            // Narratív feszültség hozzáadása, ha elérhető
            if (data.narrative_tension && data.narrative_tension.length > 0) {
                const filteredTension = [];
                for (let i = 0; i < data.narrative_tension.length; i += samplingRate) {
                    filteredTension.push(data.narrative_tension[i]);
                }
                
                datasets.push({
                    label: 'Narratív Feszültség',
                    data: filteredTension,
                    borderColor: 'rgba(255, 193, 7, 1)',
                    backgroundColor: 'rgba(255, 193, 7, 0.1)',
                    borderWidth: 2,
                    pointRadius: 0,
                    tension: 0.4
                });
            }
            
            window.psychChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: filteredTimePoints,
                    datasets: datasets
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top',
                            labels: {
                                color: 'rgba(209, 213, 219, 1)',
                                font: {
                                    family: 'Inter, sans-serif',
                                    size: 12
                                }
                            }
                        },
                        tooltip: {
                            mode: 'index',
                            intersect: false,
                            backgroundColor: 'rgba(17, 24, 39, 0.9)',
                            titleFont: {
                                family: 'Inter, sans-serif',
                                size: 14
                            },
                            bodyFont: {
                                family: 'Inter, sans-serif',
                                size: 13
                            },
                            padding: 12,
                            borderColor: 'rgba(75, 85, 99, 0.5)',
                            borderWidth: 1
                        }
                    },
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    },
                    scales: {
                        x: {
                            grid: {
                                color: 'rgba(55, 65, 81, 0.3)'
                            },
                            ticks: {
                                color: 'rgba(209, 213, 219, 0.8)',
                                font: {
                                    family: 'Inter, sans-serif',
                                    size: 11
                                }
                            },
                            title: {
                                display: true,
                                text: 'Videó idő',
                                color: 'rgba(209, 213, 219, 0.8)',
                                font: {
                                    family: 'Inter, sans-serif',
                                    size: 12,
                                    weight: 'bold'
                                }
                            }
                        },
                        y: {
                            min: 0,
                            max: 1,
                            grid: {
                                color: 'rgba(55, 65, 81, 0.3)'
                            },
                            ticks: {
                                color: 'rgba(209, 213, 219, 0.8)',
                                font: {
                                    family: 'Inter, sans-serif',
                                    size: 11
                                },
                                callback: function(value) {
                                    return `${(value * 100).toFixed(0)}%`;
                                }
                            },
                            title: {
                                display: true,
                                text: 'Érték (%)',
                                color: 'rgba(209, 213, 219, 0.8)',
                                font: {
                                    family: 'Inter, sans-serif',
                                    size: 12,
                                    weight: 'bold'
                                }
                            }
                        }
                    }
                }
            });
        }
        
        // Flow állapot és narratív szerkezet értelmezése
        updateFlowStateAnalysis(data);
        
        // Pszichológiai paraméterek tudományos értelmezése
        interpretPsychParams(data);
    }
    
    // Flow állapot és narratív szerkezet elemzés
    function updateFlowStateAnalysis(data) {
        const flowContainer = document.getElementById('flowStateAnalysis');
        if (!flowContainer) return;
        
        // Számoljuk ki a Flow állapotot 
        // (optimális arousal és engagement kombinációja)
        let flowMoments = 0;
        let optimalArousalCount = 0;
        let highEngagementCount = 0;
        let lowBoredomCount = 0;
        
        for (let i = 0; i < data.arousal.length; i++) {
            // Flow állapot: optimális arousal (0.5-0.8), magas engagement (>0.6), alacsony boredom (<0.3)
            const isOptimalArousal = data.arousal[i] >= 0.5 && data.arousal[i] <= 0.8;
            const isHighEngagement = data.engagement[i] >= 0.6;
            const isLowBoredom = data.boredom[i] <= 0.3;
            
            if (isOptimalArousal) optimalArousalCount++;
            if (isHighEngagement) highEngagementCount++;
            if (isLowBoredom) lowBoredomCount++;
            
            if (isOptimalArousal && isHighEngagement && isLowBoredom) {
                flowMoments++;
            }
        }
        
        // Narratív feszültség elemzése
        let hasStrongNarrativeTension = false;
        let hasClearNarrativeRelease = false;
        let tensionPeaks = 0;
        
        if (data.narrative_tension && data.narrative_tension.length > 0) {
            // Feszültségi csúcsok keresése
            for (let i = 5; i < data.narrative_tension.length - 5; i++) {
                if (data.narrative_tension[i] > 0.6 && 
                    data.narrative_tension[i] > data.narrative_tension[i-5] &&
                    data.narrative_tension[i] > data.narrative_tension[i+5]) {
                    tensionPeaks++;
                }
            }
            
            // Erős feszültség és feloldás
            const maxTension = Math.max(...data.narrative_tension);
            hasStrongNarrativeTension = maxTension > 0.7;
            
            if (data.narrative_payoff && data.narrative_payoff.length > 0) {
                const maxPayoff = Math.max(...data.narrative_payoff);
                hasClearNarrativeRelease = maxPayoff > 0.6;
            }
        }
        
        // Flow állapot százalék
        const flowPercentage = Math.round((flowMoments / data.arousal.length) * 100);
        
        // Narratív érzelmi hatás
        let narrativeImpact = "";
        if (tensionPeaks >= 3) {
            narrativeImpact = "Erőteljes érzelmi ritmus több feszültségi csúccsal";
        } else if (tensionPeaks > 0) {
            narrativeImpact = "Mérsékelt érzelmi dramaturgia";
        } else if (hasStrongNarrativeTension) {
            narrativeImpact = "Fokozatosan növekvő feszültség";
        } else {
            narrativeImpact = "Egyenletes érzelmi intenzitás";
        }
        
        if (hasClearNarrativeRelease) {
            narrativeImpact += ", határozott érzelmi feloldással";
        }
        
        // Flow állapot szintje
        let flowState = "";
        if (flowPercentage >= 60) {
            flowState = "Erős flow állapot";
        } else if (flowPercentage >= 30) {
            flowState = "Mérsékelt flow állapot";
        } else if (flowPercentage >= 10) {
            flowState = "Alkalmi flow állapot";
        } else {
            flowState = "Minimális flow élmény";
        }
        
        // Nézői figyelem jellemzői
        const avgEngagement = calculateAverage(data.engagement);
        const avgBoredom = calculateAverage(data.boredom);
        const engagementStability = 1 - calculateVariability(data.engagement);
        
        let attentionPattern = "";
        if (avgEngagement > 0.7 && engagementStability > 0.7) {
            attentionPattern = "Tartósan magas figyelem";
        } else if (avgEngagement > 0.6 && engagementStability > 0.5) {
            attentionPattern = "Stabil, jó szintű figyelem";
        } else if (avgEngagement > 0.5 && engagementStability < 0.5) {
            attentionPattern = "Ingadozó figyelem";
        } else if (avgBoredom > 0.6) {
            attentionPattern = "Figyelemhiány, unalom jelei";
        } else {
            attentionPattern = "Mérsékelt, változó figyelem";
        }
        
        // Eredmények megjelenítése
        flowContainer.innerHTML = `
            <div class="p-4 dashboard-panel mt-4">
                <h3 class="text-xl font-semibold mb-3">Flow Állapot és Narratív Struktúra</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <h4 class="font-medium text-lg">Flow Állapot Elemzés</h4>
                        <p class="text-gray-300">${flowState} (${flowPercentage}% időtartamban)</p>
                        <div class="flex items-center mt-2 text-sm text-gray-400">
                            <div class="flex-1">
                                <div class="h-2 rounded-full bg-gray-700">
                                    <div class="h-2 rounded-full bg-purple-500" style="width: ${Math.min(100, flowPercentage)}%"></div>
                                </div>
                                <div class="mt-1 flex justify-between">
                                    <span>Gyenge</span>
                                    <span>Erős</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div>
                        <h4 class="font-medium text-lg">Narratív Érzelmi Struktúra</h4>
                        <p class="text-gray-300">${narrativeImpact}</p>
                        <div class="mt-2 text-sm text-gray-400 flex items-center">
                            <div class="mr-2">Feszültségi csúcsok:</div>
                            <div class="flex">
                                ${Array(Math.min(5, tensionPeaks)).fill('<span class="w-2 h-4 bg-yellow-500 mx-0.5 rounded-sm"></span>').join('')}
                                ${Array(Math.max(0, 5 - tensionPeaks)).fill('<span class="w-2 h-4 bg-gray-700 mx-0.5 rounded-sm"></span>').join('')}
                            </div>
                        </div>
                    </div>
                </div>
                <div class="mt-4">
                    <h4 class="font-medium text-lg">Nézői Figyelem Mintázata</h4>
                    <p class="text-gray-300">${attentionPattern}</p>
                    <div class="grid grid-cols-3 gap-2 mt-3">
                        <div class="text-center">
                            <div class="text-2xl font-bold">${Math.round(avgEngagement * 100)}%</div>
                            <div class="text-sm text-gray-400">Átlagos elkötelezettség</div>
                        </div>
                        <div class="text-center">
                            <div class="text-2xl font-bold">${Math.round(avgBoredom * 100)}%</div>
                            <div class="text-sm text-gray-400">Átlagos unalom</div>
                        </div>
                        <div class="text-center">
                            <div class="text-2xl font-bold">${Math.round(engagementStability * 100)}%</div>
                            <div class="text-sm text-gray-400">Figyelem stabilitás</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Variabilitás számítása egy adatsorozatban
    function calculateVariability(dataArray) {
        if (!dataArray || dataArray.length < 2) return 0;
        
        let diffs = 0;
        for (let i = 1; i < dataArray.length; i++) {
            diffs += Math.abs(dataArray[i] - dataArray[i-1]);
        }
        
        return diffs / (dataArray.length - 1);
    }
    
    // Grafikonok létrehozása
    function createCharts(data) {
        // Idősor diagram
        const timelineChart = document.getElementById('timelineChart');
        if (timelineChart) {
            // Szimulált idősor adatok (mivel a summary CSV-ben csak átlagok vannak)
            // Valós esetben ezeket az adatokat a teljes video_analysis.csv-ből kellene kinyerni
            const timePoints = 20; // 20 időpont a videóban
            const timeLabels = Array.from({length: timePoints}, (_, i) => `${Math.round(i * (100/timePoints))}%`);
            
            // Szimulált adatok generálása a meglévő átlagok és szórások alapján
            const generateTimeSeries = (avg, stdDev, points) => {
                return Array.from({length: points}, () => {
                    // Normál eloszlású véletlen szám generálása az átlag és szórás alapján
                    let rand = 0;
                    for (let i = 0; i < 6; i++) {
                        rand += Math.random();
                    }
                    rand = (rand - 3) * stdDev + avg;
                    // Értékek korlátozása 0 és 1 közé
                    return Math.max(0, Math.min(1, rand));
                });
            };
            
            // Adatsorok generálása
            const pleasureData = generateTimeSeries(data.pleasure?.average || 0.5, data.pleasure?.std_dev || 0.1, timePoints);
            const stressData = generateTimeSeries(data.stress_level?.average || 0.2, data.stress_level?.std_dev || 0.05, timePoints);
            const boredomData = generateTimeSeries(data.boredom?.average || 0.3, data.boredom?.std_dev || 0.15, timePoints);
            const engagementData = generateTimeSeries(data.engagement?.average || 0.7, data.engagement?.std_dev || 0.1, timePoints);
            
            charts.timeline = new Chart(timelineChart, {
                type: 'line',
                data: {
                    labels: timeLabels,
                    datasets: [
                        {
                            label: 'Öröm',
                            data: pleasureData,
                            borderColor: 'rgba(236, 72, 153, 1)',
                            backgroundColor: 'rgba(236, 72, 153, 0.2)',
                            borderWidth: 3,
                            tension: 0.4,
                            pointRadius: 4,
                            pointHoverRadius: 6,
                            fill: false
                        },
                        {
                            label: 'Stressz',
                            data: stressData,
                            borderColor: 'rgba(249, 115, 22, 1)',
                            backgroundColor: 'rgba(249, 115, 22, 0.2)',
                            borderWidth: 3,
                            tension: 0.4,
                            pointRadius: 4,
                            pointHoverRadius: 6,
                            fill: false
                        },
                        {
                            label: 'Unalom',
                            data: boredomData,
                            borderColor: 'rgba(20, 184, 166, 1)',
                            backgroundColor: 'rgba(20, 184, 166, 0.2)',
                            borderWidth: 3,
                            tension: 0.4,
                            pointRadius: 4,
                            pointHoverRadius: 6,
                            fill: false
                        },
                        {
                            label: 'Elkötelezettség',
                            data: engagementData,
                            borderColor: 'rgba(168, 85, 247, 1)',
                            backgroundColor: 'rgba(168, 85, 247, 0.2)',
                            borderWidth: 3,
                            tension: 0.4,
                            pointRadius: 4,
                            pointHoverRadius: 6,
                            fill: false
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {
                        mode: 'index',
                        intersect: false
                    },
                    plugins: {
                        legend: {
                            position: 'top',
                            labels: {
                                color: '#e2e8f0',
                                font: {
                                    family: 'Inter, sans-serif',
                                    size: 14,
                                    weight: 'bold'
                                },
                                boxWidth: 20,
                                usePointStyle: true,
                                pointStyle: 'circle',
                                padding: 20
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(15, 23, 42, 0.9)',
                            titleColor: '#e2e8f0',
                            bodyColor: '#e2e8f0',
                            borderColor: 'rgba(79, 172, 254, 0.3)',
                            borderWidth: 1,
                            padding: 12,
                            displayColors: true,
                            callbacks: {
                                label: function(context) {
                                    return `${context.dataset.label}: ${(context.raw * 100).toFixed(0)}%`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: 'Videó idő',
                                color: '#e2e8f0',
                                font: {
                                    family: 'Inter, sans-serif',
                                    size: 14,
                                    weight: 'bold'
                                },
                                padding: {top: 10, bottom: 10}
                            },
                            ticks: {
                                color: '#e2e8f0',
                                font: {
                                    size: 12
                                },
                                padding: 8
                            },
                            grid: {
                                color: 'rgba(148, 163, 184, 0.2)',
                                tickLength: 8
                            }
                        },
                        y: {
                            beginAtZero: true,
                            max: 1,
                            title: {
                                display: true,
                                text: 'Érték (%)',
                                color: '#e2e8f0',
                                font: {
                                    family: 'Inter, sans-serif',
                                    size: 14,
                                    weight: 'bold'
                                },
                                padding: {top: 10, left: 10, right: 10, bottom: 10}
                            },
                            ticks: {
                                color: '#e2e8f0',
                                font: {
                                    size: 12
                                },
                                padding: 8,
                                callback: function(value) {
                                    return `${(value * 100).toFixed(0)}%`;
                                }
                            },
                            grid: {
                                color: 'rgba(148, 163, 184, 0.2)',
                                tickLength: 8
                            }
                        }
                    },
                    animation: {
                        duration: 2000,
                        easing: 'easeOutQuart'
                    }
                }
            });
        }

        // Érzelmi állapot radar diagram
        const emotionalRadarChart = document.getElementById('emotionalRadarChart');
        if (emotionalRadarChart) {
            charts.emotionalRadar = new Chart(emotionalRadarChart, {
                type: 'radar',
                data: {
                    labels: ['Öröm', 'Éberség', 'Dominancia', 'Elkötelezettség', 'Érzelmi variabilitás'],
                    datasets: [{
                        label: 'Érzelmi Profil',
                        data: [
                            data.pleasure?.average || 0,
                            data.arousal?.average || 0,
                            data.dominance?.average || 0,
                            data.engagement?.average || 0,
                            data.emotional_variability?.average || 0
                        ],
                        backgroundColor: 'rgba(168, 85, 247, 0.4)',
                        borderColor: 'rgba(168, 85, 247, 1)',
                        pointBackgroundColor: 'rgba(168, 85, 247, 1)',
                        pointBorderColor: '#fff',
                        pointHoverBackgroundColor: '#fff',
                        pointHoverBorderColor: 'rgba(168, 85, 247, 1)',
                        borderWidth: 3,
                        pointRadius: 5,
                        pointHoverRadius: 7
                    }]
                },
                options: {
                    scales: {
                        r: {
                            beginAtZero: true,
                            max: 1,
                            ticks: {
                                display: false,
                                stepSize: 0.2
                            },
                            pointLabels: {
                                color: '#e2e8f0',
                                font: {
                                    size: 14,
                                    weight: 'bold'
                                }
                            },
                            grid: {
                                color: 'rgba(148, 163, 184, 0.2)'
                            },
                            angleLines: {
                                color: 'rgba(148, 163, 184, 0.2)'
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            backgroundColor: 'rgba(15, 23, 42, 0.9)',
                            titleColor: '#e2e8f0',
                            bodyColor: '#e2e8f0',
                            borderColor: 'rgba(79, 172, 254, 0.3)',
                            borderWidth: 1,
                            padding: 12,
                            displayColors: false,
                            callbacks: {
                                label: function(context) {
                                    const label = context.chart.data.labels[context.dataIndex];
                                    const value = context.raw;
                                    return `${label}: ${(value * 100).toFixed(0)}%`;
                                }
                            }
                        }
                    },
                    animation: {
                        duration: 1500,
                        easing: 'easeOutQuart'
                    }
                }
            });
        }
        
        // Gauge diagramok
        createGaugeChart('pleasureGauge', 'Öröm', data.pleasure?.average || 0, 
                         ['rgba(236, 72, 153, 1)', 'rgba(236, 72, 153, 0.7)', 'rgba(236, 72, 153, 0.4)']);
        createGaugeChart('arousalGauge', 'Éberség', data.arousal?.average || 0,
                         ['rgba(20, 184, 166, 1)', 'rgba(20, 184, 166, 0.7)', 'rgba(20, 184, 166, 0.4)']);
        createGaugeChart('dominanceGauge', 'Dominancia', data.dominance?.average || 0,
                         ['rgba(249, 115, 22, 1)', 'rgba(249, 115, 22, 0.7)', 'rgba(249, 115, 22, 0.4)']);
        createGaugeChart('engagementGauge', 'Elkötelezettség', data.engagement?.average || 0,
                         ['rgba(168, 85, 247, 1)', 'rgba(168, 85, 247, 0.7)', 'rgba(168, 85, 247, 0.4)']);
        
        // Kognitív Terhelés és Stressz szint donut diagramok
        createDonutChart('cognitiveLoadChart', 'Kognitív Terhelés', data.cognitive_load?.average || 0,
                        ['rgba(168, 85, 247, 1)', 'rgba(30, 41, 59, 0.7)'], 'cognitiveLoadValue');
        createDonutChart('stressLevelChart', 'Stressz Szint', data.stress_level?.average || 0,
                         ['rgba(249, 115, 22, 1)', 'rgba(30, 41, 59, 0.7)'], 'stressLevelValue');
        
        // Unalom vs Érdeklődés
        const boredomChart = document.getElementById('boredomChart');
        if (boredomChart) {
            const boredomValue = data.boredom?.average || 0;
            const interestValue = 1 - boredomValue;
            
            charts.boredom = new Chart(boredomChart, {
                type: 'doughnut',
                data: {
                    labels: ['Érdeklődés', 'Unalom'],
                    datasets: [{
                        data: [interestValue, boredomValue],
                        backgroundColor: ['rgba(74, 222, 128, 1)', 'rgba(148, 163, 184, 1)'],
                        borderWidth: 0,
                        hoverOffset: 10
                    }]
                },
                options: {
                    cutout: '50%',
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                color: '#e2e8f0',
                                font: {
                                    size: 14,
                                    weight: 'bold'
                                },
                                padding: 20,
                                usePointStyle: true,
                                pointStyle: 'circle'
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(15, 23, 42, 0.9)',
                            titleColor: '#e2e8f0',
                            bodyColor: '#e2e8f0',
                            borderColor: 'rgba(79, 172, 254, 0.3)',
                            borderWidth: 1,
                            padding: 12,
                            displayColors: true,
                            callbacks: {
                                label: function(context) {
                                    return `${context.label}: ${(context.raw * 100).toFixed(0)}%`;
                                }
                            }
                        }
                    },
                    animation: {
                        animateRotate: true,
                        animateScale: true,
                        duration: 1500,
                        easing: 'easeOutQuart'
                    }
                }
            });
        }
        
        // Vizuális Stimuláció Bar Chart
        const visualChart = document.getElementById('visualChart');
        if (visualChart) {
            charts.visual = new Chart(visualChart, {
                type: 'bar',
                data: {
                    labels: ['Intenzitás', 'Mozgás', 'Kontraszt', 'Dinamika'],
                    datasets: [{
                        label: 'Vizuális jellemzők',
                        data: [
                            data.intensity?.average || 0,
                            data.motion?.average || 0,
                            data.contrast?.average || 0,
                            data.dynamics?.average || 0
                        ],
                        backgroundColor: [
                            'rgba(56, 189, 248, 0.8)',
                            'rgba(14, 165, 233, 0.8)',
                            'rgba(2, 132, 199, 0.8)',
                            'rgba(3, 105, 161, 0.8)'
                        ],
                        borderColor: [
                            'rgba(56, 189, 248, 1)',
                            'rgba(14, 165, 233, 1)',
                            'rgba(2, 132, 199, 1)',
                            'rgba(3, 105, 161, 1)'
                        ],
                        borderWidth: 2,
                        borderRadius: 6,
                        hoverBackgroundColor: [
                            'rgba(56, 189, 248, 1)',
                            'rgba(14, 165, 233, 1)',
                            'rgba(2, 132, 199, 1)',
                            'rgba(3, 105, 161, 1)'
                        ]
                    }]
                },
                options: {
                    indexAxis: 'y',
                    scales: {
                        x: {
                            beginAtZero: true,
                            max: 1,
                            grid: {
                                color: 'rgba(148, 163, 184, 0.2)'
                            },
                            ticks: {
                                color: '#e2e8f0',
                                callback: function(value) {
                                    return `${(value * 100).toFixed(0)}%`;
                                }
                            }
                        },
                        y: {
                            grid: {
                                display: false
                            },
                            ticks: {
                                color: '#e2e8f0',
                                font: {
                                    weight: 'bold'
                                }
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            backgroundColor: 'rgba(15, 23, 42, 0.9)',
                            titleColor: '#e2e8f0',
                            bodyColor: '#e2e8f0',
                            borderColor: 'rgba(79, 172, 254, 0.3)',
                            borderWidth: 1,
                            padding: 12,
                            displayColors: false,
                            callbacks: {
                                label: function(context) {
                                    return `Érték: ${(context.raw * 100).toFixed(0)}%`;
                                }
                            }
                        }
                    },
                    animation: {
                        delay: function(context) {
                            return context.dataIndex * 200;
                        },
                        duration: 1000,
                        easing: 'easeOutQuart'
                    }
                }
            });
        }
        
        // Audio Stimuláció Bar Chart
        const audioChart = document.getElementById('audioChart');
        if (audioChart) {
            charts.audio = new Chart(audioChart, {
                type: 'bar',
                data: {
                    labels: ['Hangerő', 'Energia', 'Hangmagasság', 'Tempó'],
                    datasets: [{
                        label: 'Audio jellemzők',
                        data: [
                            data.audio_volume?.average || 0,
                            data.audio_energy?.average || 0,
                            data.audio_pitch?.average || 0,
                            data.audio_tempo?.average || 0
                        ],
                        backgroundColor: [
                            'rgba(236, 72, 153, 0.8)',
                            'rgba(219, 39, 119, 0.8)',
                            'rgba(190, 24, 93, 0.8)',
                            'rgba(157, 23, 77, 0.8)'
                        ],
                        borderColor: [
                            'rgba(236, 72, 153, 1)',
                            'rgba(219, 39, 119, 1)',
                            'rgba(190, 24, 93, 1)',
                            'rgba(157, 23, 77, 1)'
                        ],
                        borderWidth: 2,
                        borderRadius: 6,
                        hoverBackgroundColor: [
                            'rgba(236, 72, 153, 1)',
                            'rgba(219, 39, 119, 1)',
                            'rgba(190, 24, 93, 1)',
                            'rgba(157, 23, 77, 1)'
                        ]
                    }]
                },
                options: {
                    indexAxis: 'y',
                    scales: {
                        x: {
                            beginAtZero: true,
                            max: 1,
                            grid: {
                                color: 'rgba(148, 163, 184, 0.2)'
                            },
                            ticks: {
                                color: '#e2e8f0',
                                callback: function(value) {
                                    return `${(value * 100).toFixed(0)}%`;
                                }
                            }
                        },
                        y: {
                            grid: {
                                display: false
                            },
                            ticks: {
                                color: '#e2e8f0',
                                font: {
                                    weight: 'bold'
                                }
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            backgroundColor: 'rgba(15, 23, 42, 0.9)',
                            titleColor: '#e2e8f0',
                            bodyColor: '#e2e8f0',
                            borderColor: 'rgba(79, 172, 254, 0.3)',
                            borderWidth: 1,
                            padding: 12,
                            displayColors: false,
                            callbacks: {
                                label: function(context) {
                                    return `Érték: ${(context.raw * 100).toFixed(0)}%`;
                                }
                            }
                        }
                    },
                    animation: {
                        delay: function(context) {
                            return context.dataIndex * 200;
                        },
                        duration: 1000,
                        easing: 'easeOutQuart'
                    }
                }
            });
        }
        
        // Gauge diagram létrehozása
        function createGaugeChart(canvasId, label, value, colors) {
            const canvas = document.getElementById(canvasId);
            if (!canvas) return;
            
            charts[canvasId] = new Chart(canvas, {
                type: 'doughnut',
                data: {
                    datasets: [{
                        data: [value, 1 - value],
                        backgroundColor: [colors[0], 'rgba(30, 41, 59, 0.3)'],
                        borderWidth: 0,
                        circumference: 180,
                        rotation: -90
                    }]
                },
                options: {
                    cutout: '75%',
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            enabled: false
                        }
                    },
                    animation: {
                        duration: 1500,
                        easing: 'easeOutQuart'
                    },
                    layout: {
                        padding: 10
                    }
                },
                plugins: [{
                    id: 'gaugeText',
                    afterDraw: function(chart) {
                        const width = chart.width;
                        const height = chart.height;
                        const ctx = chart.ctx;
                        
                        ctx.restore();
                        
                        // Érték kiírása
                        const valueText = `${Math.round(value * 100)}%`;
                        ctx.font = 'bold 24px Inter, sans-serif';
                        ctx.fillStyle = colors[0];
                        ctx.textBaseline = 'middle';
                        ctx.textAlign = 'center';
                        ctx.fillText(valueText, width / 2, height - 30);
                        
                        ctx.save();
                    }
                }]
            });
        }

        // Donut diagram létrehozása
        function createDonutChart(canvasId, label, value, colors, valueElementId) {
            const canvas = document.getElementById(canvasId);
            if (!canvas) return;
            
            const valueEl = document.getElementById(valueElementId);
            if (valueEl) {
                valueEl.textContent = `${Math.round(value * 100)}%`;
            }
            
            charts[canvasId] = new Chart(canvas, {
                type: 'doughnut',
                data: {
                    datasets: [{
                        data: [value, 1 - value],
                        backgroundColor: colors,
                        borderWidth: 0,
                        hoverOffset: 10
                    }]
                },
                options: {
                    cutout: '75%',
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            enabled: false
                        }
                    },
                    animation: {
                        duration: 1500,
                        easing: 'easeOutQuart'
                    }
                }
            });
        }
    }
});