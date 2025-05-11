import sys
import os
import json
import time
import shutil
import csv
import traceback
import gc
import psutil
import threading
from no_gui_analyzer import analyze_video

# Globális változók a státusz követéséhez
GLOBAL_PROGRESS = 0
GLOBAL_STATUS = "processing"
GLOBAL_MESSAGE = "Előkészítés..."
PROCESSING_ACTIVE = True

# Időkorlát kezelése
TIMEOUT_SECONDS = 1800  # 30 perc maximum feldolgozási idő
processing_timeout = False
timeout_timer = None

# Windows-kompatibilis időkorlát kezelése
def setup_timeout():
    """Platformfüggetlen időkorlát beállítása"""
    global timeout_timer, processing_timeout
    
    # Időzítő függvény, amely lejáratkor beállítja a processing_timeout flaget
    def timeout_handler():
        global processing_timeout
        processing_timeout = True
        print("Időkorlát túllépés! A feldolgozás megszakítva.")
    
    # Windows-kompatibilis időzítő indítása
    timeout_timer = threading.Timer(TIMEOUT_SECONDS, timeout_handler)
    timeout_timer.daemon = True
    timeout_timer.start()

# Időzítő leállítása
def cancel_timeout():
    """Időzítő leállítása, ha már nem szükséges"""
    global timeout_timer
    if timeout_timer is not None:
        timeout_timer.cancel()
        timeout_timer = None

def update_status(task_id, status, progress=0, message=""):
    """Állapot frissítése a státuszfájlban"""
    global GLOBAL_PROGRESS, GLOBAL_STATUS, GLOBAL_MESSAGE
    
    # Globális változók frissítése
    GLOBAL_STATUS = status
    GLOBAL_PROGRESS = progress
    GLOBAL_MESSAGE = message
    
    # Státusz adatok összeállítása
    status_data = {
        'status': status,
        'progress': progress,
        'message': message,
        'updated_at': time.time()
    }
    
    # Biztosítjuk, hogy mindig frissen írjuk az állapotot
    status_file = os.path.join('results', f'{task_id}_status.json')
    try:
        with open(status_file, 'w') as f:
            json.dump(status_data, f)
        
        # Alapos flusholás
        f.flush()
        try:
            os.fsync(f.fileno())
        except:
            pass  # Windows esetén nem mindig elérhető
    except Exception as e:
        print(f"Hiba a státusz frissítése során: {e}")
    
    # Jelzés a felhasználónak a konzolon is
    print(f"Állapot frissítve: {status} - {progress}% - {message}")

def get_memory_usage():
    """Aktuális memóriahasználat lekérdezése"""
    try:
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        return memory_info.rss / (1024 * 1024)  # MB-ban
    except:
        return 0  # Fallback, ha nem sikerül lekérdezni

def free_memory():
    """Memória felszabadítása"""
    # Kézi szemétgyűjtés
    gc.collect()
    
    try:
        # Linux/Unix rendszereken
        if os.name == 'posix':
            import ctypes
            ctypes.CDLL("libc.so.6").malloc_trim(0)
    except Exception as e:
        # Hiba esetén csak jelzünk, nem állítjuk le a programot
        print(f"Memória optimalizálási figyelmeztetés: {e}")
    
    # További szemétgyűjtés
    gc.collect()

def status_update_thread(task_id):
    """Szál a státusz rendszeres frissítésére"""
    # Kezdeti késleltetés, hogy a fő folyamat elindulhasson
    time.sleep(0.5)
    
    # Kis növekvő progressz, hogy a felhasználó lássa a haladást
    artificial_progress = 0
    
    while PROCESSING_ACTIVE:
        # Hangelemzésnél kritikus az 5%-os pont, ezért külön kezeljük
        if GLOBAL_STATUS == "processing" and GLOBAL_PROGRESS >= 4 and GLOBAL_PROGRESS <= 6:
            # Gyorsabb és látványosabb növekedés, hogy ne ragadjon be 5%-nál
            artificial_progress += 0.3
            if artificial_progress > 5:
                artificial_progress = 0
                
            # A globális haladás és a mesterséges növekedés maximuma
            effective_progress = max(GLOBAL_PROGRESS, 5 + artificial_progress)
            
            # Frissített üzenet hogy a felhasználó lássa, hogy dolgozunk rajta
            time_str = time.strftime("%H:%M:%S", time.localtime())
            
            # Változatos üzenetek használata a felhasználói élmény javításához
            messages = [
                f"Hangsáv kinyerése a videóból... [{time_str}]",
                f"Audió feldolgozás folyamatban... [{time_str}]",
                f"Hangelemzés végrehajtása... [{time_str}]"
            ]
            import random
            enhanced_message = messages[random.randint(0, len(messages)-1)]
            
            # Frissítjük a státuszt a mesterségesen növelt haladással
            update_status(task_id, GLOBAL_STATUS, effective_progress, enhanced_message)
        else:
            # Normál állapotfrissítés
            update_status(task_id, GLOBAL_STATUS, GLOBAL_PROGRESS, GLOBAL_MESSAGE)
        
        # Várunk a következő frissítésig - gyorsabb frissítés a jobb visszajelzésért
        time.sleep(0.5)  # Gyakoribb frissítés

def main():
    """Fő feladatvégrehajtó függvény"""
    global processing_timeout, PROCESSING_ACTIVE, GLOBAL_PROGRESS, GLOBAL_STATUS, GLOBAL_MESSAGE
    
    if len(sys.argv) < 3:
        print("Használat: python analyze_video_task.py <video_file> <task_id>")
        sys.exit(1)
    
    video_path = sys.argv[1]
    task_id = sys.argv[2]
    
    # Időtúllépés kezelő beállítása
    setup_timeout()
    
    # Státusz frissítés szál indítása
    status_thread = threading.Thread(target=status_update_thread, args=(task_id,))
    status_thread.daemon = True
    status_thread.start()
    
    # Ellenőrizzük, hogy a videófájl létezik-e
    if not os.path.exists(video_path):
        error_message = f"A videófájl nem található: {video_path}"
        GLOBAL_STATUS = "error"
        GLOBAL_MESSAGE = error_message
        GLOBAL_PROGRESS = 0
        # Várunk, hogy a státusz szál frissíthesse a fájlt
        time.sleep(1)
        PROCESSING_ACTIVE = False
        print(error_message)
        return
    
    results_dir = 'results'
    
    # Kimeneti fájlnevek
    full_csv = os.path.join(results_dir, f'{task_id}_full.csv')
    summary_csv = os.path.join(results_dir, f'{task_id}_summary.csv')
    
    try:
        # Inicializáljuk a folyamatot, státuszt
        GLOBAL_PROGRESS = 1
        GLOBAL_MESSAGE = "Videó betöltése és elemzés előkészítése..."
        GLOBAL_STATUS = "processing"
        
        # Memória felszabadítás
        free_memory()
        initial_memory = get_memory_usage()
        print(f"Kezdeti memóriahasználat: {initial_memory:.2f} MB")
        
        # Videó előkészítés
        GLOBAL_PROGRESS = 3
        GLOBAL_MESSAGE = "Videó dekódolás és előkészítés..."
        time.sleep(0.5)  # Rövid várakozás hogy a státusz frissüljön
        
        # KRITIKUS SZAKASZ BEGIN - A HANGELEMZÉS
        GLOBAL_PROGRESS = 5
        GLOBAL_MESSAGE = "Hangsáv kinyerése a videóból (ez több időt vehet igénybe)..."
        time.sleep(0.5)  # Rövid várakozás hogy a státusz frissüljön
        
        # Progress callback
        def progress_callback(frame_idx, total_frames):
            global GLOBAL_PROGRESS, GLOBAL_MESSAGE
            
            if processing_timeout:
                raise TimeoutError("Időkorlát túllépés - a feldolgozás túl hosszú ideig tart")
            
            progress = int((frame_idx / total_frames) * 100) if total_frames > 0 else 0
            
            # Skálázzuk a tényleges haladást az 10-95% tartományba
            # Ezzel a hangelemzés és az előkészítő szakaszok is a 0-10% tartományba esnek
            scaled_progress = 10 + int(progress * 0.85)
            
            # Csak a tényleges lényeges változásoknál frissítünk, hogy ne blokkoljuk a folyamatot
            if abs(scaled_progress - GLOBAL_PROGRESS) >= 2:
                GLOBAL_PROGRESS = scaled_progress
                mem_usage = get_memory_usage()
                GLOBAL_MESSAGE = f"Videó elemzése: {progress}% (Memória: {mem_usage:.1f} MB)"
                
                # Aktív memóriakezelés
                if frame_idx % 200 == 0:
                    free_memory()
        
        # Videó elemzés
        try:
            # Explicit beállítások a no_gui_analyzer-nek
            success = analyze_video(
                video_path, 
                output_csv=full_csv,
                progress_callback=progress_callback
            )
            
            # Időtúllépés kezelése
            if processing_timeout:
                GLOBAL_STATUS = "error"
                GLOBAL_MESSAGE = "Időkorlát túllépés - a feldolgozás túl hosszú ideig tart"
                GLOBAL_PROGRESS = 0
                time.sleep(1)  # Várunk, hogy a státusz szál frissíthesse a fájlt
                return
                
        except MemoryError:
            GLOBAL_STATUS = "error"
            GLOBAL_MESSAGE = "Memória túlcsordulás - a videó túl nagy a feldolgozáshoz. Próbálkozzon rövidebb videóval."
            GLOBAL_PROGRESS = 0
            time.sleep(1)  # Várunk, hogy a státusz szál frissíthesse a fájlt
            return
        except Exception as e:
            GLOBAL_STATUS = "error"
            GLOBAL_MESSAGE = f"Hiba a videó feldolgozás során: {str(e)}"
            GLOBAL_PROGRESS = 0
            time.sleep(1)  # Várunk, hogy a státusz szál frissíthesse a fájlt
            return
            
        if not success:
            GLOBAL_STATUS = "error"
            GLOBAL_MESSAGE = "A videóelemzés nem sikerült. Ellenőrizze a videófájlt."
            GLOBAL_PROGRESS = 0
            time.sleep(1)  # Várunk, hogy a státusz szál frissíthesse a fájlt
            return
        
        # Töröljük az időzítőt, mert túl vagyunk a számításigényes részen
        cancel_timeout()
        
        # Ellenőrizzük, hogy a CSV létrejött-e
        if not os.path.exists(full_csv):
            GLOBAL_STATUS = "error"
            GLOBAL_MESSAGE = "A CSV fájl nem jött létre az elemzés során."
            GLOBAL_PROGRESS = 0
            time.sleep(1)  # Várunk, hogy a státusz szál frissíthesse a fájlt
            return
        
        # Adatok feldolgozása
        GLOBAL_PROGRESS = 96
        GLOBAL_MESSAGE = "Elemzési adatok feldolgozása..."
        
        # Memória felszabadítás a CSV feldolgozás előtt
        free_memory()
        
        # CSV összegzés
        try:
            with open(full_csv, 'r', encoding='utf-8') as full_file:
                reader = csv.reader(full_file)
                header = next(reader)
                
                # A parameter oszlop a CSV-ben az utolsó oszlop
                param_index = len(header) - 1
                
                # Ha létezik összegző adatsor, azt kiemeljük
                summary_rows = []
                for row in reader:
                    if len(row) > param_index and row[param_index] == 'SUMMARY':
                        summary_rows.append(row)
            
            # Ha találtunk összegző adatsorokat, létrehozzuk a summary fájlt
            if summary_rows:
                with open(summary_csv, 'w', newline='', encoding='utf-8') as summary_file:
                    writer = csv.writer(summary_file)
                    writer.writerow(['parameter', 'average', 'min', 'max', 'std_dev'])
                    for row in summary_rows:
                        writer.writerow([row[0], row[1], row[2], row[3], row[4]])
                
                # Adatok feldolgozása kész
                GLOBAL_STATUS = "completed"
                GLOBAL_PROGRESS = 100
                GLOBAL_MESSAGE = "Elemzés sikeresen befejezve"
                time.sleep(1)  # Várunk, hogy a státusz szál frissíthesse a fájlt
            else:
                # Alternatív eljárás
                found_summary_section = False
                summary_data = []
                
                with open(full_csv, 'r', encoding='utf-8') as full_file:
                    for line in full_file:
                        if "Összegző statisztikák" in line:
                            found_summary_section = True
                            continue
                            
                        if found_summary_section and line.strip():
                            row = next(csv.reader([line]))
                            if len(row) >= 5:
                                summary_data.append(row[:5])
                
                if summary_data:
                    with open(summary_csv, 'w', newline='', encoding='utf-8') as summary_file:
                        writer = csv.writer(summary_file)
                        writer.writerow(['parameter', 'average', 'min', 'max', 'std_dev'])
                        for row in summary_data:
                            writer.writerow(row)
                        
                    # Adatok feldolgozása kész
                    GLOBAL_STATUS = "completed"
                    GLOBAL_PROGRESS = 100
                    GLOBAL_MESSAGE = "Elemzés sikeresen befejezve"
                    time.sleep(1)  # Várunk, hogy a státusz szál frissíthesse a fájlt
                else:
                    GLOBAL_STATUS = "error"
                    GLOBAL_MESSAGE = "Nem találtunk összegző statisztikákat a CSV fájlban."
                    GLOBAL_PROGRESS = 0
                    time.sleep(1)  # Várunk, hogy a státusz szál frissíthesse a fájlt
                
        except Exception as e:
            GLOBAL_STATUS = "error"
            GLOBAL_MESSAGE = f"Hiba az összegző adatok feldolgozása során: {str(e)}"
            GLOBAL_PROGRESS = 0
            time.sleep(1)  # Várunk, hogy a státusz szál frissíthesse a fájlt
            traceback.print_exc()
        
    except Exception as e:
        # Hiba esetén frissítjük az állapotot
        GLOBAL_STATUS = "error"
        GLOBAL_MESSAGE = f"Hiba történt: {str(e)}"
        GLOBAL_PROGRESS = 0
        time.sleep(1)  # Várunk, hogy a státusz szál frissíthesse a fájlt
        traceback.print_exc()
        
    finally:
        # Biztosítsuk, hogy az időzítő mindig le legyen állítva
        cancel_timeout()
        
        # Státusz frissítő szál leállítása
        PROCESSING_ACTIVE = False
        
        # Végső memória felszabadítás
        free_memory()
        final_memory = get_memory_usage()
        print(f"Kezdeti memória: {initial_memory:.2f} MB, Végső memória: {final_memory:.2f} MB")

if __name__ == "__main__":
    main() 