import requests
import pandas as pd
import mysql.connector
from mysql.connector import Error
import random
import time
import logging
import math
import os
from datasets import load_dataset
from sentence_transformers import SentenceTransformer, util
from cachetools import LRUCache, LFUCache

def get_db_conn(retries=20, delay=3):
    for attempt in range(1, retries + 1):
        try:
            conn = mysql.connector.connect(
                host= 'mysql_base',
                user='usuario',
                password='pass123',
                database='mi_base',
                autocommit=False,
                charset="utf8mb4"
            )
            if conn.is_connected():
                logging.info("Conectado a MySQL (%s).", 'mysql')
                return conn
        except Exception as e:
            logging.warning("Intento %d/%d - no se pudo conectar a MySQL: %s", attempt, retries, e)
            time.sleep(delay)
    raise RuntimeError("No se pudo conectar a la base de datos MySQL.")

conn = get_db_conn()
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS respuestas (
  id INT AUTO_INCREMENT PRIMARY KEY,
  pregunta TEXT,
  respuesta_dataset TEXT,
  respuesta_llm TEXT,
  score FLOAT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) CHARACTER SET = utf8mb4;
""")
conn.commit()

insert_sql = "INSERT INTO respuestas (pregunta, respuesta_dataset, respuesta_llm, score) VALUES (%s, %s, %s, %s)"

cache_lru = LRUCache(maxsize=500)
cache_lfu = LFUCache(maxsize=500)

timestamps = {}

def get_from_cache(pregunta, db_conn):
    global hits_lru, misses_lru, hits_lfu, misses_lfu
    now = time.time()
    respuesta_cache = None

    
    if pregunta in cache_lru and now - timestamps.get(pregunta, 0) < 600:
        hits_lru += 1
        respuesta_cache = cache_lru[pregunta]
    else:
        misses_lru += 1
    
    if pregunta in cache_lfu and now - timestamps.get(pregunta, 0) < 600:
        hits_lfu += 1
        _ = cache_lfu[pregunta]  
    else:
        misses_lfu += 1
    
    if respuesta_cache is None:
        with db_conn.cursor(buffered=True) as cursor:
            cursor.execute("SELECT respuesta_llm FROM respuestas WHERE pregunta = %s", (pregunta,))
            row = cursor.fetchone()
        if row:
            respuesta = row[0]
            if pregunta not in cache_lru:
                cache_lru[pregunta] = respuesta

            if pregunta not in cache_lfu:
                cache_lfu[pregunta] = respuesta
            timestamps[pregunta] = now

    return respuesta_cache




def update_cache(pregunta, respuesta):
    now = time.time()
    cache_lru[pregunta] = respuesta
    cache_lfu[pregunta] = respuesta
    timestamps[pregunta] = now



questions_list = []
hit_rate_lru = []
miss_rate_lru = []
hit_rate_lfu = []
miss_rate_lfu = []
hits_lru = 0
misses_lru = 0
hits_lfu = 0
misses_lfu = 0
   
df = pd.read_csv("/preguntas/test.csv")

model = SentenceTransformer("all-MiniLM-L6-v2")

print(f"Dataset cargado con {len(df)} filas.")

count = 0
committed = 0

for i in range(10000):     
  print("Pregunta", i)
  if (i+1) % 20 == 0:  

    total_lru = hits_lru + misses_lru
    hit_rate_lru_pct = (hits_lru / total_lru) * 100 if total_lru > 0 else 0
    miss_rate_lru_pct = (misses_lru / total_lru) * 100 if total_lru > 0 else 0

    total_lfu = hits_lfu + misses_lfu
    hit_rate_lfu_pct = (hits_lfu / total_lfu) * 100 if total_lfu > 0 else 0
    miss_rate_lfu_pct = (misses_lfu / total_lfu) * 100 if total_lfu > 0 else 0

    print(f"\nDespués de {i+1} preguntas:")
    print(f"LRU → Hits: {hit_rate_lru_pct:.2f}%, Misses: {miss_rate_lru_pct:.2f}%")
    print(f"LFU → Hits: {hit_rate_lfu_pct:.2f}%, Misses: {miss_rate_lfu_pct:.2f}%")
    
    print("Número de entradas en LRU:", len(cache_lru))
    print("Número de entradas en LFU:", len(cache_lfu))

    with conn.cursor() as cursor:
        cursor.execute("SELECT AVG(score) FROM respuestas")
        promedio = cursor.fetchone()[0]
        print("Promedio de score:", promedio)




  random_row = df.sample(1).iloc[0]
  
  pregunta = str(random_row.iloc[2])
  respuesta_real = str(random_row.iloc[3])
  
  print("\n--- Pregunta Aleatoria ---")
  print("Pregunta:", pregunta)
  print("Respuesta esperada (dataset):", respuesta_real)
  

  econtrado = get_from_cache(pregunta, conn)

  if econtrado == None:

    res = requests.post("http://host.docker.internal:11434/api/generate", json={
        "model": "phi3",
        "stream": False,
        "prompt": pregunta,
        "options": {
        "num_predict": 100,
        }
      })
    
    data = res.json()
    respuesta = data.get('response') or data.get('text') or f"Error: {data.get('error','No response')}"
    print("Respuesta de Ollama:", respuesta) 

    update_cache(pregunta, respuesta)  
    
    emb1 = model.encode(respuesta, convert_to_tensor=True)
    emb2 = model.encode(respuesta_real, convert_to_tensor=True)
    score = util.cos_sim(emb1, emb2).item()
  
    logging.info("Score: %.6f", score)
  
    try:
          with conn.cursor() as cursor:
           cursor.execute(insert_sql, (pregunta, respuesta_real, respuesta, score))
          count += 1
          conn.commit()
    except Exception:
          logging.exception("Error al insertar en la BD, se omite esta fila.")
  
  else:
      print("Se encontro en el cache la respuesta")

if count > 0:
    conn.commit()
    logging.info("Committed final %d rows.", count)

cursor.close()
conn.close()
logging.info("Proceso finalizado.")
  
  
print("\n--- Métrica de similitud ---")
print("Metrica: ", score)


  
