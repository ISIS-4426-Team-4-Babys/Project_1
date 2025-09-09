# Plan de Pruebas de Carga y Análisis de Capacidad

## 1) Objetivo
Evaluar la capacidad de la Aplicación bajo escenarios de **humo, carga progresiva y estrés**, midiendo **tiempos de respuesta, throughput y utilización de recursos** para identificar cuellos de botella y establecer una línea base de desempeño para las siguientes entregas.

---

## 2) Entorno de pruebas

### 2.1 Arquitectura bajo prueba
- **Backend**: Python/FastAPI en Docker; PostgreSQL (metadatos); **ChromaDB** (vectorial); **RabbitMQ** (colas asíncronas); Workers (ingesta → extracción → chunking → embeddings → upsert).  
- **Frontend**: React servido por **Nginx**; panel docente y chat estudiante.  
- **Servicios de IA**: Google AI (embeddings y LLM) → invocación desde workers/API.  
- **Observabilidad**: Prometheus + Grafana (app/infra); logs centralizados.

### 2.2 Limitaciones
- Límites de tasa/quotas en Google AI (LLM/embeddings).  
- Memoria de ChromaDB con múltiples namespaces (multi-tenancy).  
- Conexiones simultáneas/canales en RabbitMQ.  
- Latencia del almacenamiento en upserts masivos.

---

## 3) Criterios de aceptación (SLOs)

### Web Chat
- **p95 ≤ 8 s**, promedio ≤ 5 s, **error rate < 1%** por agente.

### Ingesta
- Documento **20 MB**: **p95 upload→indexed ≤ 3 min** (chunking + embeddings en workers).  
- **Throughput de upsert**: ≥ **1000 chunks/min**.

### Utilización de recursos
- **CPU** promedio < 80%, **RAM** < 85%, **disco** < 70%.

---

## 4) Escenarios de prueba (rutas críticas)

### A. Chat web
1. Login estudiante → listar agentes accesibles  
2. Chat con prompts de distintas longitudes.
3. Validar **citas** en la respuesta (`sources.length > 0`)  

**Métricas:** latencia (avg/p95), error rate, throughput (req/min).  
**Criterio:** p95 ≤ 8 s, error < 1%.

---

### B. Ingesta (capa batch)
1. Login docente → carga de **PDF/DOCX/PPTX** (≥ 20 MB y 2–8 MB)  
2. Polling de estado hasta `indexed`  
3. Registrar tiempo **upload→indexed** y **chunks/min**  

**Métricas:** tiempo total de indexación, throughput de upsert, errores de tarea.  
**Criterio:** p95 ≤ 3 min; ≥ 1200 chunks/min.

---

### C. Carga realista
- **85%** de usuarios en **Chat** y **15%** en **Ingesta** en paralelo.  
- Validar que la ingesta no degrade el p95 del chat por encima del SLO.

---

## 5) Estrategia y etapas
- **Humo**: 10 usuarios / 2 min (rutas y aserciones básicas).  
- **Carga progresiva**: 10 → 50 → 100 → 300 → 500 usuarios.  
- **Estrés**: 500 → 700 → 900 … hasta degradación clara (**p95 > 12 s** o **error ≥ 5%**).  

---

## 6) Diseño del entorno del cliente de carga

### 6.1 Herramienta principal
- **Apache JMeter** (HTTP(S), Summary Report, JSON Extractor, Timers, CSV DataSet Config).  

### 6.2 Apoyo (humo)
- **ApacheBench (ab)** para pruebas rápidas de endpoints.

### 6.3 Infraestructura del generador de carga
- **EC2** (4 vCPU, 16 GB RAM, 100 GB SSD) en `us-east-1`.  
  **Justificación**: suficiente para **~1000 usuarios virtuales** y baja latencia.

### 6.4 Monitoreo durante las pruebas
- **Aplicación**: métricas (latencia_ms, tokens, colas); logs estructurados.  
- **Infra**: CPU/RAM/IO/Net (Prometheus + Grafana / CloudWatch).  
- **Vector DB**: latencia de búsqueda y Queries per second.

---

## 7) Parámetros y datos

### 7.1 Ambiente de pruebas
- **CPU**: 4 vCPUs | **RAM**: 16 GB | **Disco**: SSD 100 GB 

### 7.2 Dataset de prueba
- 2 agentes (dos cursos distintos).  
- 3 materiales por agente: `doc_teoria.pdf` (~20 MB), `clase_X.pptx` (~8 MB), `taller.docx` (~2 MB).  
- 30 prompts (chat): 60% cortos / 30% medios / 10% largos.

### 7.3 Configuración JMeter
- **Header Manager**: `Authorization: Bearer ${TOKEN}`, `Content-Type: application/json`.  
- **Timers**: Uniform Random (20s–2m) para “think time”.  
- **Aserciones**: `status == 200`, `sources.length > 0`.

---

## 8) Topología de prueba

| Escenario   | Usuarios / Concurrencia  | Duración  | KPIs                              | Resultado esperado              |
| ----------- | ------------------------ | --------- | --------------------------------- | ------------------------------- |
| A – Chat    | 10→50→100→300→500        | 5–10 min  | p95, avg, error rate, req/min     | p95 ≤ 8 s, err < 1%             |
| B – Ingesta | 20 trabajos concurrentes | 10–20 min | tiempo upload→indexed, chunks/min | p95 ≤ 3 min; ≥ 1000 chunks/min  |
| C – Real (80)| 68 chat / 12 ingesta     | 15 min    | p95 chat, p95 ingesta             | p95 chat ≤ 8 s; ingesta ≤ 3 min |

---

## 9) Tabla de escenarios y resultados esperados (preliminares)

```mermaid
flowchart TD
  LC[Load Client (JMeter/ab)] --> N[Nginx/Load Balancer]
  N --> API[Backend API - FastAPI]
  API --> PG[(PostgreSQL)]
  API --> VDB[(ChromaDB)]
  API --> MQ[(RabbitMQ)]
  MQ --> WK[Workers RAG]
  WK --> AI[Google AI APIs]
```

## 10) Criterios de salida (stoppers)

- Error rate ≥ 5% sostenido (≥ 3 min).
- p95 > 12 s en Chat durante la prueba de estrés.
- CPU > 95% sostenida o throttling de IO/Net prolongado.

## 11) Recomendaciones para escalar la solución

