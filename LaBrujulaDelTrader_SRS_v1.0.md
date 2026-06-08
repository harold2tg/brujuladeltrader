# 🧭 La Brújula del Trader

**Software Requirements Specification (SRS)**  
*Plataforma de análisis estadístico para traders de XAUUSD*

---

| Campo | Valor |
| --- | --- |
| **Versión** | 1.0 |
| **Estado** | Borrador — en desarrollo |
| **Autor** | Harold Torres Gallo |
| **País** | Colombia (UTC-5) |
| **Fecha** | Junio 2025 |
| **Clasificación** | Confidencial — uso interno |

---

## Tabla de contenido

1. [Visión General del Producto](#1-visión-general-del-producto)
2. [Alcance del Sistema](#2-alcance-del-sistema)
3. [Integración con cTrader](#3-integración-con-ctrader)
4. [Requerimientos Funcionales](#4-requerimientos-funcionales)
5. [Requerimientos No Funcionales](#5-requerimientos-no-funcionales)
6. [Arquitectura del Sistema](#6-arquitectura-del-sistema)
7. [Planes del Producto](#7-planes-del-producto)
8. [Fases de Desarrollo](#8-fases-de-desarrollo)
9. [Glosario](#9-glosario)
10. [Historial de Cambios](#10-historial-de-cambios)

---

## 1. Visión General del Producto

### 1.1 Descripción

La Brújula del Trader es una plataforma de análisis estadístico para traders manuales de XAUUSD (oro/dólar). Permite importar el historial de operaciones desde cTrader —mediante conexión directa por API Key o carga manual de archivo CSV/Excel— y transforma esos datos en métricas, diagnósticos, reportes y recomendaciones generadas por inteligencia artificial.

El nombre refleja el propósito central del producto: orientar al trader con datos reales sobre su propia operativa, eliminando la intuición no validada y reemplazándola por evidencia estadística.

### 1.2 Problema que resuelve

La mayoría de traders de corto plazo operan sin registro estructurado de sus decisiones. Sin datos propios no es posible identificar qué funciona y qué no, lo que perpetúa ciclos de pérdida. La Brújula del Trader convierte el historial de cTrader en inteligencia accionable: ¿a qué hora ganás más? ¿cuándo deberías parar? ¿cuál es tu ratio real de riesgo/beneficio?

### 1.3 Usuarios objetivo

| Perfil | Descripción | Fase |
| --- | --- | --- |
| Trader personal | Scalper de XAUUSD, operativa manual, 0-3 años de experiencia | Fase 1-2 |
| Trader avanzado | Trader con criterio propio buscando validación estadística de sus estrategias | Fase 2-3 |
| Usuario SaaS | Cualquier trader intraday que opere desde cTrader, independiente del activo | Fase 4 |

### 1.4 Propuesta de valor

- Conexión directa con cTrader sin necesidad de exportar manualmente.
- Fallback robusto: si la API falla, el usuario sube su CSV/Excel y el sistema funciona igual.
- Análisis estadístico automático con diagnóstico en lenguaje natural generado por IA (Claude).
- Dashboard web y app móvil para consultar métricas en cualquier momento.
- Alertas inteligentes: avisa cuando el trader está en racha perdedora o supera su límite de pérdida diaria.
- Multiidioma desde el primer día: español e inglés.

---

## 2. Alcance del Sistema

### 2.1 Lo que el sistema HACE

| # | Funcionalidad | Descripción |
| --- | --- | --- |
| F-01 | Conexión cTrader | El usuario ingresa su API Key y Account ID de cTrader. El sistema consulta el historial de operaciones por día, mes o año usando cTrader Open API. |
| F-02 | Carga manual de archivo | El usuario sube un CSV o Excel exportado desde cTrader como alternativa a la conexión directa. El sistema detecta y normaliza automáticamente las columnas. |
| F-03 | Análisis estadístico | Calcula win rate, ratio R:R, PnL por hora/día/mes/sesión, rachas ganadoras y perdedoras, distribución de resultados, y simulaciones de mejora. |
| F-04 | Dashboard web | Visualización interactiva de todas las métricas con gráficos, tablas y filtros por período. |
| F-05 | App móvil | Versión compacta del dashboard para iOS y Android. Incluye resumen del día, alertas y journal de notas. |
| F-06 | Diagnóstico IA | Claude analiza las métricas del trader y genera narrativa en lenguaje natural con diagnóstico y recomendaciones personalizadas. |
| F-07 | Sistema de alertas | Reglas configurables por el usuario: máximo de pérdida por operación, rachas, límite diario. Notificaciones push en móvil. |
| F-08 | Reportes exportables | Genera reportes PDF y CSV del análisis mensual o anual. |
| F-09 | Autenticación y planes | Registro, login JWT, planes Free y Pro con límites diferenciados. |
| F-10 | Multiidioma | Interfaz completa en español e inglés con selector de idioma. |

### 2.2 Lo que el sistema NO HACE

> ❌ **FUERA DE ALCANCE** — El sistema NO ejecuta órdenes de trading. No se conecta a ningún broker para abrir, modificar ni cerrar posiciones.

> ❌ **FUERA DE ALCANCE** — No soporta MetaTrader, cAlgo, TradingView ni ninguna plataforma distinta a cTrader en la fase inicial.

> ❌ **FUERA DE ALCANCE** — No genera señales automáticas ni bots de trading. Es una herramienta de análisis y diagnóstico, no de ejecución.

> ❌ **FUERA DE ALCANCE** — No almacena ni procesa datos de tarjetas de crédito ni información financiera de cuentas bancarias.

---

## 3. Integración con cTrader

### 3.1 Mecanismo de conexión

La Brújula del Trader se conecta a cTrader usando cTrader Open API con autenticación por API Key. El usuario no necesita instalar nada adicional — solo copiar sus credenciales desde el panel de cTrader y pegarlas en la aplicación.

### 3.2 Credenciales requeridas del usuario

| Campo | Dónde obtenerlo en cTrader | Ejemplo |
| --- | --- | --- |
| Client ID | cTrader → Settings → Open API → My Apps | 12345 |
| Client Secret | cTrader → Settings → Open API → My Apps | abc123xyz... |
| Access Token | Generado tras autorizar la app con OAuth2 | eyJhbGci... |
| Account ID | cTrader → Account → Account ID | 67890123 |

> ℹ️ Las credenciales se almacenan cifradas en la base de datos usando AES-256. Nunca se muestran en texto plano después de guardarse.

### 3.3 Consultas al historial de operaciones

El sistema usa el mensaje `ProtoOADealListReq` de cTrader Open API para obtener el historial de deals (operaciones cerradas) filtrado por rango de fechas.

| Modo de consulta | Descripción | Límite cTrader API |
| --- | --- | --- |
| Por día | Trae todas las operaciones de una fecha específica | 5 req/seg histórico |
| Por mes | Trae operaciones del mes completo (desde día 1 hasta el último día) | 5 req/seg histórico |
| Por año | Divide el año en bloques de 30 días para respetar los límites de la API | 5 req/seg histórico |

> ℹ️ cTrader limita las consultas históricas a 5 solicitudes por segundo. El sistema implementa rate limiting interno y reintentos con backoff exponencial.

### 3.4 Fallback: carga manual de archivo

Si la conexión con cTrader falla o el usuario prefiere no conectar su cuenta, puede subir manualmente el archivo exportado desde cTrader. El sistema soporta dos formatos:

| Formato | Extensión | Cómo exportar desde cTrader |
| --- | --- | --- |
| CSV | `.csv` | cTrader → History → Click derecho → Export to CSV |
| Excel | `.xlsx` | cTrader → History → Click derecho → Export to Excel |

### 3.5 Columnas requeridas del archivo cTrader

El parser detecta automáticamente las columnas. Las siguientes son requeridas:

| Columna | Tipo | Notas del parser |
| --- | --- | --- |
| Símbolo | Texto | Debe ser XAUUSD. El sistema acepta otros activos pero solo analiza XAUUSD en la fase inicial. |
| Dirección de apertura | Texto | Valores aceptados: `Buy` / `Sell` |
| Hora de cierre (UTC-5) | Fecha/Hora | Formato: `DD/MM/YYYY HH:MM:SS.mmm` |
| Precio de entrada | Decimal | |
| Precio de cierre | Decimal | |
| $ neto | Decimal | Puede ser negativo. Cero se trata como pérdida. |
| Saldo $ | Decimal | Puede contener espacios no-breaking como separador de miles. El parser los elimina automáticamente. |

---

## 4. Requerimientos Funcionales

### 4.1 Módulo de autenticación (AUTH)

| ID | Requerimiento |
| --- | --- |
| RF-AUTH-01 | El sistema permite registrar un usuario con email, contraseña y nombre. |
| RF-AUTH-02 | El sistema autentica con JWT. El access token expira en 24 horas. El refresh token en 30 días. |
| RF-AUTH-03 | Las contraseñas se almacenan con bcrypt. Nunca en texto plano. |
| RF-AUTH-04 | El sistema invalida el token en logout (lista negra en Redis). |
| RF-AUTH-05 | Los errores de login no deben indicar si el email existe o no. Siempre respuesta genérica. |

### 4.2 Módulo de integración cTrader (CTRADER)

| ID | Requerimiento |
| --- | --- |
| RF-CT-01 | El usuario puede guardar sus credenciales de cTrader (Client ID, Client Secret, Access Token, Account ID) en su perfil. |
| RF-CT-02 | Las credenciales se almacenan cifradas (AES-256). No son visibles después de guardadas. |
| RF-CT-03 | El usuario puede probar la conexión antes de hacer la primera consulta. |
| RF-CT-04 | El usuario puede solicitar el historial por: día específico, mes completo, o año completo. |
| RF-CT-05 | Para consultas anuales, el sistema divide en bloques de 30 días para respetar los límites de la API de cTrader. |
| RF-CT-06 | Si la consulta a cTrader falla, el sistema muestra un error descriptivo y ofrece la opción de subir archivo manualmente. |
| RF-CT-07 | El sistema implementa reintentos automáticos con backoff exponencial (máximo 3 intentos). |

### 4.3 Módulo de carga de archivos (UPLOADS)

| ID | Requerimiento |
| --- | --- |
| RF-UP-01 | El sistema acepta archivos `.csv` y `.xlsx` con tamaño máximo de 10 MB. |
| RF-UP-02 | El archivo original se conserva siempre. Nunca se modifica ni elimina. |
| RF-UP-03 | El procesamiento es asíncrono. El endpoint retorna inmediatamente con un ID de estado. |
| RF-UP-04 | El usuario en plan Free puede tener máximo 5 uploads activos. El plan Pro es ilimitado. |
| RF-UP-05 | Si faltan columnas requeridas, el sistema rechaza el archivo con un mensaje que indica cuáles columnas faltan. |

### 4.4 Módulo de análisis estadístico (ANALYTICS)

El motor de análisis calcula las siguientes métricas sobre cada set de operaciones importado:

| Categoría | Métricas calculadas |
| --- | --- |
| Globales | Total ops, win rate, PnL neto, ganancia bruta, pérdida bruta, avg ganancia, avg pérdida, ratio R:R, breakeven win rate, mejor op, peor op, profit factor, saldo inicial y final, retorno %. |
| Por dirección | Buy vs Sell: operaciones, win rate, PnL, avg ganancia, avg pérdida. |
| Por hora del día | Para cada hora con ≥5 ops: cantidad, win rate, PnL, avg resultado. |
| Por día de semana | Lunes a viernes con ≥10 ops: win rate, PnL. |
| Por mes | Evolución mensual: ops, win rate, PnL. |
| Por sesión de mercado | Londres (07h-09h), Overlap (09h-12h), Nueva York (12h-17h), Fuera de sesión. |
| Rachas | Racha ganadora máxima, racha perdedora máxima, racha actual, cantidad de rachas perdedoras ≥3. |
| Distribución | Agrupación por rangos: `<-$20`, `-$20/-$10`, `-$10/-$5`, `-$5/$0`, `$0/$5`, `$5/$10`, `>$10`. |
| Simulaciones | PnL si se aplicara stop loss máximo de $5. PnL operando solo en las 3 mejores horas. |

### 4.5 Módulo de diagnóstico IA (AI ENGINE)

| ID | Requerimiento |
| --- | --- |
| RF-AI-01 | El sistema usa una interfaz abstracta `AIProvider` para generar diagnósticos. El proveedor es intercambiable (Claude, OpenAI, Gemini, Ollama). |
| RF-AI-02 | Cada usuario configura su propio proveedor de IA desde un formulario en su perfil. |
| RF-AI-03 | Las API keys de IA se almacenan cifradas (AES-256-GCM) en la tabla `ai_credentials`, una por usuario. |
| RF-AI-04 | Nunca se llama a un SDK de IA directamente desde la lógica de negocio. Siempre a través de `AIProvider`. |
| RF-AI-05 | Los diagnósticos se generan en el idioma seleccionado por el usuario (español o inglés). |
| RF-AI-06 | El contexto del trader (scalping XAUUSD, M1/M5/M10, Colombia UTC-5) se incluye en todos los prompts. |
| RF-AI-07 | Los diagnósticos se cachean 24 horas. No se regeneran si el set de datos no cambió. |
| RF-AI-08 | Plan Free: máximo 10 diagnósticos IA por día. Plan Pro: sin límite. |
| RF-AI-09 | Si el proveedor falla, el sistema retorna el análisis determinista básico como fallback. Nunca error al usuario. |
| RF-AI-10 | Tipos de análisis disponibles: diagnóstico completo, revisión mensual, plan de mejora, resumen rápido, análisis por sesión. |
| RF-AI-11 | Cada proveedor implementa retry con backoff exponencial (máximo 3 intentos). |
| RF-AI-12 | Si el usuario no tiene credenciales de IA configuradas, el sistema usa el fallback determinista. |

### 4.6 Módulo de alertas (ALERTS)

| ID | Requerimiento |
| --- | --- |
| RF-AL-01 | El usuario puede configurar alertas: pérdida máxima por operación, racha perdedora, límite de pérdida diaria, caída de win rate, caída de R:R. |
| RF-AL-02 | Las alertas se evalúan automáticamente cada vez que se procesan nuevas operaciones. |
| RF-AL-03 | Una misma alerta no puede dispararse más de una vez por hora. |
| RF-AL-04 | Plan Free: máximo 3 reglas activas. Plan Pro: ilimitado. |
| RF-AL-05 | Las alertas se envían como notificaciones push a la app móvil. |

---

## 5. Requerimientos No Funcionales

### 5.1 Rendimiento

- El análisis de un archivo de hasta 1,000 operaciones debe completarse en menos de 5 segundos.
- Los endpoints de consulta de métricas (con caché activo) deben responder en menos de 300ms.
- La sincronización con cTrader para un mes de datos debe completarse en menos de 30 segundos.

### 5.2 Seguridad

- Todas las comunicaciones usan HTTPS/TLS 1.3. No se acepta HTTP en producción.
- Las credenciales de cTrader se cifran con AES-256 antes de almacenarse.
- Las contraseñas de usuarios se hashean con bcrypt (factor de costo ≥12).
- Los tokens JWT se validan en cada request. Los tokens revocados se rechazan vía lista negra en Redis.
- Rate limiting: máximo 100 requests por minuto por usuario en endpoints de API.
- Los archivos subidos se escanean para verificar que son CSV/Excel válidos antes de procesarse.

### 5.3 Disponibilidad y resiliencia

- La plataforma debe tener disponibilidad del 99% en horas de mercado (lunes-viernes 07h-18h UTC-5).
- Si cTrader Open API no responde, el sistema continúa operando con carga manual de archivos.
- Si Claude API no responde, el sistema retorna el análisis determinista básico sin error visible al usuario.

### 5.4 Escalabilidad

- La arquitectura debe soportar escalar horizontalmente el servicio de API sin cambios de código.
- El procesamiento de archivos con Celery permite escalar workers independientemente de la API.
- La capa de caché en Redis reduce la carga de la base de datos en consultas frecuentes.

### 5.5 Internacionalización

- La interfaz web y móvil soporta español e inglés desde la primera versión.
- El idioma por defecto se detecta desde el navegador/dispositivo del usuario.
- Todos los textos visibles al usuario se almacenan en archivos de traducción (i18n), nunca hardcodeados.
- Los diagnósticos generados por IA se producen en el idioma configurado por el usuario.
- Las fechas y horas se muestran en UTC-5 (Colombia) por defecto, configurable por el usuario.

---

## 6. Arquitectura del Sistema

### 6.1 Componentes principales

| Componente | Tecnología | Repositorio | Responsabilidad |
| --- | --- | --- | --- |
| Backend API | FastAPI + Python 3.11 | `brujula-api` | Lógica de negocio, cálculos, integración cTrader, IA |
| AI Provider | Interfaz abstracta `AIProvider` | `brujula-api` | Abstracción intercambiable: Claude, OpenAI, Gemini, Ollama |
| Web App | Next.js 14 + Tailwind CSS | `brujula-web` | Dashboard, reportes, configuración |
| App Móvil | Flutter 3.x | `brujula-mobile` | Stats del día, alertas push, journal |
| Base de datos | PostgreSQL 15 | — (infra) | Usuarios, operaciones, métricas, alertas |
| Caché | Redis 7 | — (infra) | Caché de métricas, sesiones JWT, rate limiting |
| Worker | Celery + Redis | — (api) | Procesamiento async de archivos, llamadas IA |
| Infraestructura | Docker + Nginx + VPS | `brujula-infra` | Containerización, reverse proxy, CI/CD |

### 6.2 Flujo de datos principal

El flujo estándar de uso es el siguiente:

1. El usuario se autentica y accede al dashboard.
2. Elige importar datos: por conexión cTrader (API Key) o subiendo un archivo CSV/Excel.
3. Si usa cTrader: el backend consulta la API con el rango de fechas elegido (día/mes/año) y almacena las operaciones.
4. Si sube archivo: el backend valida el formato, lo almacena y lo pone en cola de procesamiento con Celery.
5. El worker procesa las operaciones: parsea, normaliza y calcula todas las métricas estadísticas.
6. El usuario accede al dashboard y ve los resultados. El caché en Redis evita recalcular en consultas repetidas.
7. Opcionalmente, el usuario solicita un diagnóstico IA. Celery llama a Claude con el contexto del trader.
8. El diagnóstico se muestra en el dashboard y se cachea por 24 horas.

### 6.3 Módulos del backend

| Módulo | Endpoints principales | Depende de |
| --- | --- | --- |
| `auth` | `POST /auth/register`, `/auth/login`, `/auth/logout`, `/auth/refresh` | users, Redis |
| `ctrader` | `POST /ctrader/connect`, `GET /ctrader/sync`, `GET /ctrader/test` | uploads, parser |
| `uploads` | `POST /uploads`, `GET /uploads`, `DELETE /uploads/{id}` | parser, storage |
| `parser` | — (interno, llamado por Celery) | trades model |
| `analytics` | `GET /analytics/{id}`, `/by-hour`, `/by-day`, `/simulate` | trades, Redis |
| `reports` | `GET /reports/{id}/monthly`, `/annual`, `POST /reports/export` | analytics |
| `ai_engine` | `POST /ai/{id}/analyze`, `GET /ai/jobs/{job_id}` | analytics, Claude API |
| `alerts` | `GET/POST/PUT/DELETE /alerts/rules`, `GET /alerts/history` | analytics, trades |
| `users` | `GET/PUT /users/profile`, `PUT /users/password` | auth |

---

## 7. Planes del Producto

| Característica | Plan Free | Plan Pro |
| --- | --- | --- |
| Precio | Gratis | A definir en Fase 4 |
| Uploads activos | 5 | Ilimitado |
| Conexión cTrader | ✓ | ✓ |
| Carga manual CSV/Excel | ✓ | ✓ |
| Dashboard completo | ✓ | ✓ |
| App móvil | ✓ | ✓ |
| Diagnósticos IA por día | 10 | Ilimitado |
| Reglas de alerta | 3 | Ilimitado |
| Exportar reportes PDF/CSV | ✗ | ✓ |
| Historial de análisis | 30 días | Ilimitado |
| Soporte | Comunidad | Prioritario |

---

## 8. Fases de Desarrollo

| Fase | Nombre | Duración estimada | Entregables clave |
| --- | --- | --- | --- |
| 1 | Core Engine | 2-3 semanas | Backend: auth, uploads, parser, analytics. Docker Compose local funcionando. |
| 2 | Web MVP | 2-3 semanas | Next.js con dashboard completo, carga de archivo, diagnóstico IA básico. |
| 3 | Integración cTrader | 1-2 semanas | Módulo ctrader completo con conexión por API Key, sync por día/mes/año, manejo de errores y fallback. |
| 4 | App Móvil | 3-4 semanas | Flutter: dashboard compacto, alertas push, journal de notas por sesión. |
| 5 | SaaS | 4-6 semanas | Planes Free/Pro, landing page, onboarding, pagos, multiidioma completo. |

> ⚠️ Comenzar siempre por la Fase 1. No pasar a la siguiente fase sin que la anterior esté estable y testeada.

---

## 9. Glosario

| Término | Definición |
| --- | --- |
| XAUUSD | Par de trading que representa el precio del oro (XAU) en dólares americanos (USD). |
| Scalping | Estilo de trading de muy corto plazo donde las operaciones duran segundos o pocos minutos. |
| Win Rate | Porcentaje de operaciones ganadoras sobre el total de operaciones. |
| Ratio R:R | Relación entre la ganancia promedio y la pérdida promedio. Un R:R de 1.0 significa que se gana y pierde lo mismo en promedio. |
| Breakeven Win Rate | Win rate mínimo necesario para no perder dinero dado un ratio R:R. Fórmula: `1 / (1 + R:R)`. |
| cTrader Open API | API pública de Spotware (creadores de cTrader) que permite acceder a datos de cuenta, historial de operaciones y mercado. |
| Deal | Término de cTrader para una operación ejecutada y cerrada. |
| Sesión de mercado | Período del día asociado a una bolsa o centro financiero activo (Londres, Nueva York). El oro tiene mayor volumen en el overlap Londres/NY. |
| UTC-5 | Zona horaria de Colombia. Todas las horas en el sistema se muestran en UTC-5 por defecto. |
| Racha perdedora | Serie de operaciones consecutivas con resultado negativo. Rachas de 3 o más son señal de alerta. |
| Profit Factor | Ganancia bruta dividida entre la pérdida bruta (en valor absoluto). Un PF > 1.0 indica sistema rentable. |
| JWT | JSON Web Token. Estándar para autenticación sin estado usado en la API. |
| Celery | Sistema de colas de tareas asíncronas para Python. Usado para procesamiento de archivos y llamadas a IA. |

---

## 10. Historial de Cambios

| Versión | Fecha | Autor | Cambios |
| --- | --- | --- | --- |
| 1.0 | Jun 2025 | Harold Torres Gallo | Versión inicial del SRS. Arquitectura completa, integración cTrader con API Key, fallback CSV/Excel, módulos definidos, fases de desarrollo. |

---

*La Brújula del Trader · SRS v1.0 · Documento Confidencial*  
*© 2025 Harold Torres Gallo — Todos los derechos reservados*
