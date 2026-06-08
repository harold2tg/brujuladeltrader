# AGENTS.md — brujula-mobile (App Móvil)

> **Leer antes de escribir cualquier línea de código.**
> Este documento es la fuente de verdad para el agente que construye la app móvil de La Brújula del Trader.
> El SRS completo está en `LaBrujulaDelTrader_SRS_v1.0.md`. Este documento lo complementa con reglas técnicas de implementación.

---

## Contexto del proyecto

**La Brújula del Trader** — app móvil en Flutter para iOS y Android. Es la versión compacta del dashboard web: permite al trader revisar sus métricas clave del día, recibir alertas push cuando supera sus límites, y agregar notas rápidas a sus sesiones de trading. No reemplaza el dashboard web — lo complementa para uso en movimiento.

---

## Stack tecnológico

| Componente | Tecnología | Versión mínima |
| --- | --- | --- |
| Framework | Flutter | 3.19+ |
| Lenguaje | Dart | 3.x |
| Estado | Riverpod | 2.x |
| HTTP | Dio | última estable |
| Navegación | go_router | última estable |
| Gráficos | fl_chart | última estable |
| Notificaciones push | firebase_messaging | última estable |
| Almacenamiento local | flutter_secure_storage | última estable |
| Internacionalización | flutter_localizations + intl | última estable |
| Testing | flutter_test + mockito | última estable |

---

## Estructura de carpetas

```
brujula-mobile/
├── lib/
│   ├── main.dart
│   ├── app.dart                         # MaterialApp + go_router + Riverpod
│   │
│   ├── core/
│   │   ├── api/
│   │   │   ├── api_client.dart          # Dio con interceptores auth
│   │   │   ├── auth_api.dart
│   │   │   ├── uploads_api.dart
│   │   │   ├── analytics_api.dart
│   │   │   ├── alerts_api.dart
│   │   │   └── ctrader_api.dart
│   │   ├── models/
│   │   │   ├── user.dart
│   │   │   ├── upload.dart
│   │   │   ├── trade.dart
│   │   │   ├── analytics.dart
│   │   │   └── alert.dart
│   │   ├── providers/
│   │   │   ├── auth_provider.dart
│   │   │   ├── uploads_provider.dart
│   │   │   ├── analytics_provider.dart
│   │   │   └── alerts_provider.dart
│   │   ├── storage/
│   │   │   └── secure_storage.dart      # JWT tokens en flutter_secure_storage
│   │   ├── notifications/
│   │   │   └── push_service.dart        # Firebase Cloud Messaging
│   │   └── utils/
│   │       ├── formatters.dart          # Formateo de números y fechas
│   │       └── colors.dart              # Paleta de colores del proyecto
│   │
│   ├── features/
│   │   ├── auth/
│   │   │   ├── login_screen.dart
│   │   │   └── register_screen.dart
│   │   ├── dashboard/
│   │   │   ├── dashboard_screen.dart    # Pantalla principal
│   │   │   └── widgets/
│   │   │       ├── metric_card.dart
│   │   │       ├── metrics_grid.dart
│   │   │       ├── pnl_by_hour_chart.dart
│   │   │       └── session_summary.dart
│   │   ├── uploads/
│   │   │   ├── uploads_screen.dart
│   │   │   ├── upload_detail_screen.dart
│   │   │   └── widgets/
│   │   │       ├── upload_card.dart
│   │   │       └── upload_status_chip.dart
│   │   ├── analytics/
│   │   │   ├── analytics_screen.dart
│   │   │   └── widgets/
│   │   │       ├── win_rate_chart.dart
│   │   │       ├── monthly_pnl_chart.dart
│   │   │       └── rr_diagnostic_card.dart
│   │   ├── alerts/
│   │   │   ├── alerts_screen.dart
│   │   │   └── widgets/
│   │   │       ├── alert_rule_tile.dart
│   │   │       └── alert_history_tile.dart
│   │   ├── journal/
│   │   │   ├── journal_screen.dart      # Notas rápidas por sesión
│   │   │   └── widgets/
│   │   │       └── note_card.dart
│   │   └── settings/
│   │       └── settings_screen.dart
│   │
│   └── l10n/
│       ├── app_es.arb                   # Traducciones español
│       └── app_en.arb                   # Traducciones inglés
│
├── test/
│   ├── unit/
│   └── widget/
├── android/
├── ios/
├── pubspec.yaml
└── AGENTS.md
```

---

## Convenciones de código — OBLIGATORIAS

### Dart y Flutter
- Dart 3 con null safety estricto. Sin `!` innecesarios — resolver el nullable correctamente.
- Sin `setState` en pantallas principales. Todo estado a través de Riverpod providers.
- Los widgets se dividen en archivos propios cuando superan 100 líneas.
- Los `const` constructors donde sea posible — mejora el rendimiento.
- Nombres de archivos en `snake_case`. Nombres de clases en `PascalCase`.

### Estado con Riverpod
- Usar `AsyncNotifierProvider` para datos que vienen de la API.
- Usar `NotifierProvider` para estado sincrónico (ej: tema, idioma).
- Usar `StateProvider` solo para estado UI simple (ej: tab seleccionado).
- No acceder a providers dentro de `build()` directamente — usar `ref.watch` para datos reactivos y `ref.read` solo en callbacks.

### Navegación
- Toda la navegación con `go_router`. Sin `Navigator.push` directo.
- Rutas definidas como constantes en `app.dart`. Sin strings hardcodeados de rutas.
- Rutas protegidas: el guard de `go_router` verifica el token antes de permitir acceso al dashboard.

### API y manejo de errores
- Todas las llamadas a la API en clases `*_api.dart`. Los providers llaman a los APIs, no las pantallas.
- Los errores de red se capturan en los providers y exponen `AsyncError` — la UI muestra el estado de error con mensaje descriptivo.
- Si el token expira, el interceptor de Dio intenta el refresh automáticamente. Si falla, redirige a login.

### Tokens
- El `access_token` y `refresh_token` se almacenan **exclusivamente** en `flutter_secure_storage`. Nunca en `SharedPreferences` ni en variables en memoria sin persistencia.

---

## Pantallas principales

### Login y Register
- Formularios simples con validación inline.
- Al hacer login exitoso, guardar tokens en `SecureStorage` y navegar al dashboard.
- Mostrar el logo de La Brújula del Trader en la pantalla de login.

### Dashboard (pantalla principal)

La pantalla más importante de la app. Estructura:

```
AppBar: "La Brújula del Trader" + selector de idioma (ícono)
─────────────────────────────────────────────────
Selector de upload activo (Dropdown)
─────────────────────────────────────────────────
Grid 2x2 de métricas clave:
  ┌─────────────┬─────────────┐
  │  Win Rate   │  PnL Neto   │
  │   58.2%     │  -$636      │
  ├─────────────┼─────────────┤
  │  Ratio R:R  │ Total Ops   │
  │   0.47x     │    605      │
  └─────────────┴─────────────┘
─────────────────────────────────────────────────
Gráfico: PnL por hora del día (barras horizontales)
  → Mínimo 5 barras visibles
  → Verde si PnL positivo, rojo si negativo
─────────────────────────────────────────────────
Card: Sesión actual
  → Indica en qué sesión de mercado está ahora (UTC-5)
  → Londres 07h-09h | Overlap 09h-12h | NY 12h-17h
─────────────────────────────────────────────────
Botón flotante (FAB): "Agregar nota de sesión"
```

### Uploads

- Lista de uploads con `Card` por cada uno: nombre, período, estado, cantidad de trades, PnL.
- Badge de estado: `Procesando` (ámbar), `Listo` (verde), `Error` (rojo).
- Pull-to-refresh para actualizar la lista.
- No hay carga de archivos en la app móvil — esa función es exclusiva del web. Si el usuario lo intenta, mostrar mensaje: "Subí archivos desde la versión web en brujula.app".

### Analytics

Pantalla con `TabBar` de 3 tabs:

**Tab 1 — Resumen:**
- Las 3 mejores horas (verde) y las 3 peores horas (rojo) en formato lista.
- Ratio R:R con diagnóstico visual: barra de progreso con marca en 0.7 (mínimo recomendado).
- Racha actual (positiva en verde, negativa en rojo).

**Tab 2 — Por período:**
- Gráfico de barras del PnL por mes.
- Gráfico de barras del PnL por día de semana.

**Tab 3 — Sesiones:**
- Resumen compacto de cada sesión: ops, win rate, PnL.
- Indicador visual de qué sesión es más rentable para el trader.

### Alertas

- Lista de reglas activas con Switch para activar/desactivar.
- Historial de las últimas 10 alertas disparadas.
- Botón para agregar nueva regla (modal con tipo de alerta y threshold).
- En plan Free, máximo 3 reglas — mostrar badge "Free · 2/3 reglas" y bloquear la creación de más con mensaje de upgrade.

### Journal (notas de sesión)

Pantalla simple para que el trader registre notas rápidas:
- `FloatingActionButton` abre un modal con:
  - Campo de texto libre (máximo 500 caracteres).
  - Selector de sesión (Londres / Overlap / NY / Fuera).
  - Resultado del día (positivo / negativo / neutral).
- Las notas se almacenan **localmente** en `flutter_secure_storage` (no en el backend en esta fase).
- Lista de notas ordenadas por fecha, con opción de eliminar.

### Settings

- Sección Perfil: nombre, email (no editable), idioma (toggle ES/EN).
- Sección Notificaciones: toggle global de notificaciones push.
- Sección Cuenta: botón "Cerrar sesión" (con confirmación).
- Sección App: versión actual, enlace a términos y privacidad.

---

## Notificaciones push

- Configuradas con Firebase Cloud Messaging (FCM).
- El token FCM se envía al backend al hacer login para que el servidor pueda enviar notificaciones.
- Tipos de notificaciones que el usuario puede recibir:
  - Alerta de racha perdedora: `"⚠️ Llevas 3 operaciones seguidas en pérdida"`
  - Alerta de límite diario: `"🛑 Alcanzaste tu límite de pérdida del día"`
  - Alerta de pérdida grande: `"⚠️ Operación con pérdida mayor a $X"`
  - Sync completado: `"✅ Sincronización con cTrader completada: 45 operaciones"`
- Al tocar la notificación, navegar a la pantalla relevante (analytics del upload procesado, o pantalla de alertas).
- Pedir permiso de notificaciones en el primer login, no en el splash.

---

## Internacionalización (i18n)

- Idiomas: español (`es`) e inglés (`en`).
- Usar `flutter_localizations` con archivos `.arb`.
- El idioma por defecto es el del dispositivo. Si el dispositivo no es ES ni EN, usar ES.
- El usuario puede cambiar el idioma desde Settings — se guarda en `SecureStorage`.
- Los números monetarios usan `NumberFormat.currency(locale: locale, symbol: '\$')`.
- Las fechas usan formato `dd/MM/yyyy` en ES y `MM/dd/yyyy` en EN.

```
// Estructura de app_es.arb
{
  "@@locale": "es",
  "dashboardTitle": "Mi Dashboard",
  "winRate": "Win Rate",
  "netPnl": "PnL Neto",
  "rrRatio": "Ratio R:R",
  "totalTrades": "Total Operaciones",
  "sessionLondon": "Apertura Londres",
  "sessionOverlap": "Overlap NY/Londres",
  "sessionNY": "Sesión Nueva York",
  "sessionOff": "Fuera de sesión"
}
```

---

## Paleta de colores

Usar la misma paleta que el frontend web para consistencia visual:

```dart
class AppColors {
  static const positive = Color(0xFF22C55E);  // verde — ganancia
  static const negative = Color(0xFFEF4444);  // rojo — pérdida
  static const neutral  = Color(0xFF94A3B8);  // gris
  static const navy     = Color(0xFF1B2F5E);  // azul oscuro — primario
  static const blue     = Color(0xFF2563EB);  // azul — secundario
  static const gold     = Color(0xFFD97706);  // dorado — acento (XAUUSD)
  static const london   = Color(0xFF3B82F6);  // sesión Londres
  static const overlap  = Color(0xFF8B5CF6);  // sesión overlap
  static const nySession= Color(0xFFF59E0B);  // sesión NY
}
```

---

## Variables de entorno

Flutter no tiene `.env` nativo. Usar `--dart-define` al compilar:

```bash
# Desarrollo
flutter run --dart-define=API_URL=http://localhost:8000

# Producción
flutter build apk --dart-define=API_URL=https://api.brujula.app
```

Leer en código:
```dart
const apiUrl = String.fromEnvironment('API_URL', defaultValue: 'http://localhost:8000');
```

---

## Reglas de UX — OBLIGATORIAS

- **Sin pantallas en blanco.** Todo estado de carga tiene `CircularProgressIndicator` o skeleton con `shimmer`.
- **Pull-to-refresh** en todas las listas de datos.
- **Sin acciones destructivas sin confirmación.** Cerrar sesión y eliminar notas requieren `AlertDialog` de confirmación.
- **El estado vacío es orientador.** Si no hay uploads, mostrar ícono + texto + botón que lleve a la pantalla de uploads.
- **Los números negativos siempre en rojo, positivos en verde.** Sin excepciones.
- **La sesión de mercado actual siempre visible** en el dashboard (el trader necesita saber si está en horario de Londres o NY).
- **Offline graceful.** Si no hay internet, mostrar banner informativo y mostrar los últimos datos cacheados en memoria.

---

## Orden de implementación obligatorio

```
1. Configuración base: Flutter + Riverpod + go_router + estructura de carpetas
2. Core: api_client.dart con Dio + secure_storage + interceptores auth
3. Auth: login_screen + register_screen + auth_provider
4. Dashboard: dashboard_screen con métricas grid y gráfico de horas
5. Uploads: uploads_screen + upload_detail_screen
6. Analytics: analytics_screen con tabs
7. Alerts: alerts_screen + integración con notificaciones push (FCM)
8. Journal: journal_screen con almacenamiento local
9. Settings: idioma + notificaciones + cerrar sesión
10. i18n: revisar que todos los strings estén en archivos .arb
11. Testing: tests unitarios de providers + tests de widgets principales
```

---

## Lo que la app móvil NO hace (diferencias con el web)

| Función | Web | Móvil |
| --- | --- | --- |
| Subir archivos CSV/Excel | ✓ | ✗ — redirigir al web |
| Conexión y sync cTrader | ✓ | ✗ — redirigir al web |
| Exportar reportes PDF | ✓ | ✗ |
| Diagnóstico IA completo | ✓ | Solo ver el último generado en web |
| Agregar notas de sesión | ✗ | ✓ — exclusivo móvil |
| Notificaciones push | ✗ | ✓ — exclusivo móvil |
| Ver métricas y gráficos | ✓ | ✓ |
