# AGENTS.md — brujula-web (Frontend)

> **Leer antes de escribir cualquier línea de código.**
> Este documento es la fuente de verdad para el agente que construye el frontend de La Brújula del Trader.
> El SRS completo está en `LaBrujulaDelTrader_SRS_v1.0.md`. Este documento lo complementa con reglas técnicas de implementación.

---

## Contexto del proyecto

**La Brújula del Trader** es una plataforma de análisis estadístico para traders manuales de XAUUSD. El frontend es una Single Page Application en Next.js que consume la API de `brujula-api`. No contiene lógica de negocio ni cálculos estadísticos — solo presenta datos y maneja el estado de la UI.

---

## Stack tecnológico

| Componente | Tecnología | Versión mínima |
| --- | --- | --- |
| Framework | Next.js (App Router) | 14 |
| Lenguaje | TypeScript | 5.x |
| Estilos | Tailwind CSS | 3.x |
| Componentes UI | shadcn/ui | última estable |
| Gráficos | Recharts | última estable |
| Estado global | Zustand | última estable |
| HTTP client | Axios + React Query (TanStack) | última estable |
| Formularios | React Hook Form + Zod | última estable |
| Internacionalización | next-intl | última estable |
| Iconos | Lucide React | última estable |
| Testing | Vitest + Testing Library | última estable |

---

## Estructura de carpetas

```
brujula-web/
├── app/
│   ├── [locale]/
│   │   ├── layout.tsx
│   │   ├── page.tsx                     # Landing / redirect
│   │   ├── (auth)/
│   │   │   ├── login/page.tsx
│   │   │   └── register/page.tsx
│   │   └── (dashboard)/
│   │       ├── layout.tsx               # Shell del dashboard (sidebar + header)
│   │       ├── dashboard/page.tsx       # Vista principal de métricas
│   │       ├── uploads/
│   │       │   ├── page.tsx             # Lista de uploads
│   │       │   └── [id]/page.tsx        # Detalle de un upload
│   │       ├── analytics/
│   │       │   └── [uploadId]/
│   │       │       ├── page.tsx         # Análisis completo
│   │       │       ├── by-hour/page.tsx
│   │       │       ├── by-day/page.tsx
│   │       │       └── simulate/page.tsx
│   │       ├── ctrader/page.tsx         # Conexión y sync con cTrader
│   │       ├── alerts/page.tsx          # Reglas de alerta
│   │       ├── reports/page.tsx         # Reportes exportables
│   │       └── settings/page.tsx        # Perfil y configuración
│   ├── globals.css
│   └── layout.tsx
│
├── components/
│   ├── ui/                              # Componentes shadcn/ui (no modificar manualmente)
│   ├── layout/
│   │   ├── Sidebar.tsx
│   │   ├── Header.tsx
│   │   └── PageHeader.tsx
│   ├── charts/
│   │   ├── PnlByHourChart.tsx           # Barras horizontales PnL por hora
│   │   ├── WinRateByDayChart.tsx        # Barras por día de semana
│   │   ├── MonthlyPnlChart.tsx          # Barras por mes
│   │   ├── EquityCurveChart.tsx         # Línea de curva de capital
│   │   ├── DistributionChart.tsx        # Histograma de distribución
│   │   └── SessionPieChart.tsx          # Pie chart de sesiones
│   ├── metrics/
│   │   ├── MetricCard.tsx               # Tarjeta de métrica individual
│   │   ├── MetricsGrid.tsx              # Grid de 4 métricas principales
│   │   ├── RRDiagnostic.tsx             # Diagnóstico visual del ratio R:R
│   │   └── StreakBadge.tsx              # Badge de racha actual
│   ├── uploads/
│   │   ├── UploadDropzone.tsx           # Zona de drag & drop para archivos
│   │   ├── UploadStatusCard.tsx         # Card con status de procesamiento
│   │   └── UploadsList.tsx
│   ├── ctrader/
│   │   ├── CTraderConnectForm.tsx       # Formulario de credenciales
│   │   ├── CTraderSyncPanel.tsx         # Panel de sincronización por período
│   │   └── CTraderStatusBadge.tsx
│   ├── ai/
│   │   ├── AIDiagnosticPanel.tsx        # Panel de diagnóstico IA
│   │   └── AIInsightCard.tsx
│   ├── alerts/
│   │   ├── AlertRuleForm.tsx
│   │   └── AlertRulesList.tsx
│   └── shared/
│       ├── LoadingSpinner.tsx
│       ├── ErrorBoundary.tsx
│       ├── EmptyState.tsx
│       └── ConfirmDialog.tsx
│
├── lib/
│   ├── api/
│   │   ├── client.ts                    # Instancia Axios con interceptores
│   │   ├── auth.ts                      # Endpoints de auth
│   │   ├── uploads.ts
│   │   ├── analytics.ts
│   │   ├── ctrader.ts
│   │   ├── alerts.ts
│   │   └── ai.ts
│   ├── hooks/
│   │   ├── useAnalytics.ts              # React Query hooks para analytics
│   │   ├── useUploads.ts
│   │   ├── useCTrader.ts
│   │   └── useAlerts.ts
│   ├── stores/
│   │   ├── authStore.ts                 # Zustand: usuario autenticado, tokens
│   │   └── uiStore.ts                   # Zustand: sidebar open, theme, language
│   ├── utils/
│   │   ├── formatters.ts                # Formateo de números, fechas, porcentajes
│   │   └── colors.ts                    # Paleta de colores para gráficos
│   └── validations/
│       ├── authSchemas.ts               # Esquemas Zod para formularios de auth
│       └── alertSchemas.ts
│
├── messages/
│   ├── es.json                          # Traducciones español
│   └── en.json                          # Traducciones inglés
│
├── public/
│   └── logo.svg
│
├── tests/
│   ├── components/
│   └── hooks/
│
├── middleware.ts                         # next-intl middleware para i18n
├── next.config.js
├── tailwind.config.js
├── tsconfig.json
└── AGENTS.md
```

---

## Convenciones de código — OBLIGATORIAS

### TypeScript estricto
- `strict: true` en `tsconfig.json`. Sin `any` excepto en casos extremadamente justificados con comentario.
- Todos los tipos de respuesta de la API están en `lib/api/*.ts` con interfaces TypeScript explícitas.
- No usar `as` para castear tipos de respuesta de API. Usar Zod para validar en runtime si es necesario.

### Componentes
- Todos los componentes son funcionales con TypeScript. Sin class components.
- Los componentes reciben sus datos como props. No hacen fetch directamente — usan hooks de React Query.
- Props siempre tipadas con interfaces explícitas (no `React.FC<any>`).
- Componentes pequeños y enfocados. Si un componente supera 150 líneas, dividirlo.

### Estado
- Estado del servidor: React Query (TanStack Query). No usar `useState` para datos que vienen de la API.
- Estado global de UI: Zustand (sidebar, idioma, tema).
- Estado local de formularios: React Hook Form.
- No usar Context API para estado global — solo para theming de librerías si es necesario.

### Estilos
- Solo Tailwind CSS. Sin CSS modules, sin styled-components, sin estilos inline.
- Usar las clases de shadcn/ui como base. No reinventar componentes que shadcn ya tiene.
- Paleta de colores del proyecto definida en `tailwind.config.js` y `lib/utils/colors.ts`.
- Diseño responsive: mobile-first. Todas las páginas deben funcionar en 375px de ancho.

### Routing y navegación
- Usar Next.js App Router. Sin Pages Router.
- Todas las rutas bajo `[locale]/` para soporte i18n.
- Rutas protegidas: middleware valida JWT antes de renderizar el dashboard.

### Manejo de errores
- Todos los errores de API se muestran con toast notifications (shadcn/ui `Sonner`).
- Los estados de carga siempre tienen skeleton loaders, nunca pantalla en blanco.
- Los estados vacíos tienen componente `EmptyState` con mensaje descriptivo y acción sugerida.

---

## Páginas principales

### `/dashboard` — Vista principal
La página más importante del producto. Muestra:
1. **Selector de upload activo** en el header (dropdown con los últimos 5 uploads del usuario).
2. **Grid de 4 métricas clave**: Win Rate, PnL Neto, Ratio R:R, Total Operaciones.
3. **Diagnóstico rápido**: banner de color según si el sistema es rentable o no.
4. **Gráfico de PnL por hora** (barras horizontales, las horas rentables en verde, las destructivas en rojo).
5. **Gráfico de PnL por día de semana**.
6. **Botón "Diagnóstico IA"** que abre el panel `AIDiagnosticPanel`.

### `/uploads` — Gestión de archivos
- Lista de todos los uploads con status, período, cantidad de trades y PnL total.
- Dropzone para subir nuevo archivo (acepta drag & drop y click).
- Indicador de progreso en tiempo real para uploads procesándose (polling cada 2 segundos a `/uploads/{id}/status`).
- Botón para eliminar upload con confirmación.

### `/ctrader` — Conexión cTrader
Dividida en dos secciones:

**Sección 1 — Credenciales:**
- Formulario para ingresar Client ID, Client Secret, Access Token, Account ID.
- Botón "Probar conexión" que llama a `GET /ctrader/test` y muestra el resultado.
- Si ya hay credenciales guardadas, mostrar campos enmascarados con botón "Editar".

**Sección 2 — Sincronización:**
- Tres opciones: Por día (date picker), Por mes (month picker), Por año (year picker).
- Botón "Sincronizar" que inicia el job y muestra barra de progreso.
- Si la sincronización falla, mostrar el banner de fallback con opción de subir archivo manualmente.

### `/analytics/[uploadId]` — Análisis completo
- Tabs: Resumen | Por hora | Por día | Por sesión | Por mes | Simulaciones.
- Cada tab carga sus datos de forma lazy (React Query con `enabled`).
- El tab "Simulaciones" muestra el análisis comparativo: resultado real vs resultado con stop loss de $5 vs resultado operando solo en las mejores horas.

### `/alerts` — Alertas
- Lista de reglas activas con toggle para activar/desactivar.
- Formulario para crear nueva regla (máximo 3 en plan Free con mensaje de upgrade).
- Historial de alertas disparadas con fecha y valor que la activó.

### `/settings` — Configuración
- Sección Perfil: nombre, email (no editable), idioma (es/en), zona horaria.
- Sección Seguridad: cambiar contraseña.
- Sección Plan: plan actual con comparativa Free vs Pro.
- Sección Peligrosa: eliminar cuenta con confirmación por texto.

---

## Internacionalización (i18n)

- Idiomas soportados: `es` (español, defecto) y `en` (inglés).
- Configurado con `next-intl`. Todas las rutas bajo `[locale]`.
- Middleware en `middleware.ts` detecta el idioma del navegador y redirige.
- Selector de idioma en el header del dashboard.
- **Todos los textos visibles al usuario en `messages/es.json` y `messages/en.json`.** Nunca strings hardcodeados en JSX.
- Los números, fechas y monedas se formatean con `Intl` según el locale activo.

```json
// Estructura de messages/es.json (ejemplo)
{
  "dashboard": {
    "title": "Mi Dashboard",
    "metrics": {
      "winRate": "Win Rate",
      "netPnl": "PnL Neto",
      "rrRatio": "Ratio R:R",
      "totalTrades": "Total Operaciones"
    }
  },
  "uploads": {
    "dropzone": "Arrastrá tu archivo CSV o Excel aquí",
    "processing": "Procesando {filename}..."
  }
}
```

---

## Cliente HTTP (`lib/api/client.ts`)

```typescript
// Axios con interceptores para auth y manejo de errores
const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  timeout: 30000,
});

// Interceptor request: agrega Authorization header desde Zustand authStore
// Interceptor response: si 401, intenta refresh token automáticamente
//                       si el refresh falla, redirige a /login
//                       si 403, muestra toast de "Plan no incluye esta función"
//                       si 500, muestra toast genérico de error
```

---

## Paleta de colores para gráficos (`lib/utils/colors.ts`)

```typescript
export const CHART_COLORS = {
  positive: "#22c55e",    // verde — ganancia, win rate alto
  negative: "#ef4444",    // rojo — pérdida, win rate bajo
  neutral:  "#94a3b8",    // gris — datos sin valor positivo/negativo claro
  london:   "#3b82f6",    // azul — sesión Londres
  overlap:  "#8b5cf6",    // púrpura — overlap NY/Londres
  ny:       "#f59e0b",    // ámbar — sesión NY
  off:      "#6b7280",    // gris — fuera de sesión
};
```

---

## Variables de entorno (`.env.local.example`)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=La Brújula del Trader
NEXT_PUBLIC_DEFAULT_LOCALE=es
```

---

## Reglas de UX — OBLIGATORIAS

- **Sin pantallas en blanco.** Todo estado de carga tiene skeleton loader.
- **Sin acciones sin confirmación.** Eliminar uploads, eliminar cuenta y desconectar cTrader requieren `ConfirmDialog`.
- **El estado vacío es útil.** Si no hay uploads, mostrar instrucciones claras para importar el primer archivo.
- **El error es orientador.** Si falla la conexión con cTrader, mostrar exactamente qué hacer a continuación (subir archivo manualmente).
- **Los números siempre tienen contexto.** Un PnL de `-$636` siempre se muestra con color rojo y la etiqueta correcta. Nunca un número solo sin unidad.
- **El idioma sigue al usuario.** Si el usuario cambia el idioma en settings, toda la UI cambia inmediatamente sin recargar.

---

## Orden de implementación obligatorio

```
1. Configuración base: Next.js + Tailwind + shadcn/ui + next-intl + estructura de carpetas
2. Cliente HTTP + stores de Zustand (auth)
3. Páginas de auth: login y register
4. Shell del dashboard: sidebar + header + layout
5. Página /uploads: dropzone + lista + polling de status
6. Página /dashboard: métricas clave + gráficos principales
7. Página /analytics/[uploadId]: tabs con todos los gráficos
8. Página /ctrader: formulario de credenciales + panel de sync
9. Página /alerts: reglas y historial
10. Página /settings: perfil + cambio de contraseña
11. Panel de diagnóstico IA (AIDiagnosticPanel)
12. i18n completo: revisar que todos los strings estén en messages/
```
